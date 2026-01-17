# -*- coding: utf-8 -*-
"""
角色CRUD和权限分配端点
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Permission, Role, RolePermission, User
from app.schemas.auth import RoleCreate, RoleResponse, RoleUpdate
from app.schemas.common import ResponseModel
from app.services.permission_audit_service import PermissionAuditService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role_in: RoleCreate,
    request: Request,
    current_user: User = Depends(security.require_permission("ROLE_CREATE")),
) -> Any:
    """
    创建新角色

    - **role_in**: 角色创建数据
    """
    role = db.query(Role).filter(Role.role_code == role_in.role_code).first()
    if role:
        raise HTTPException(
            status_code=400,
            detail="该角色编码已存在",
        )

    role = Role(
        role_code=role_in.role_code,
        role_name=role_in.role_name,
        description=role_in.description,
        data_scope=role_in.data_scope,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    if role_in.permission_ids:
        for p_id in role_in.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=p_id))
        db.commit()
        db.refresh(role)

    # 设置权限列表
    role.permissions = [rp.permission.permission_name for rp in role.permissions]

    # 记录审计日志
    try:
        PermissionAuditService.log_role_operation(
            db=db,
            operator_id=current_user.id,
            role_id=role.id,
            action=PermissionAuditService.ACTION_ROLE_CREATED,
            changes={
                "role_code": role.role_code,
                "role_name": role.role_name,
                "data_scope": role.data_scope,
                "permission_ids": role_in.permission_ids,
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        logger.warning("审计日志记录失败（create_role），不影响主流程", exc_info=True)

    return role


@router.put("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK)
def update_role(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    role_in: RoleUpdate,
    request: Request,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    更新角色信息

    - **role_id**: 角色ID
    - **role_in**: 角色更新数据
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system:
        raise HTTPException(status_code=400, detail="系统预置角色不允许修改")

    # 记录变更前的状态
    old_is_active = role.is_active
    old_data = {
        "role_name": role.role_name,
        "description": role.description,
        "data_scope": role.data_scope,
        "is_active": role.is_active,
    }

    update_data = role_in.model_dump(exclude_unset=True)
    permission_ids = None

    # 处理权限分配
    if "permission_ids" in update_data:
        permission_ids = update_data.pop("permission_ids")
        # 删除原有权限关联
        db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
        # 添加新权限关联
        for p_id in permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=p_id))

    # 更新其他字段
    for field, value in update_data.items():
        setattr(role, field, value)

    db.add(role)
    db.commit()
    db.refresh(role)

    # 设置权限列表
    role.permissions = [rp.permission.permission_name for rp in role.permissions]

    # 记录审计日志
    try:
        changes = {
            k: v for k, v in update_data.items() if k in old_data and old_data[k] != v
        }
        if permission_ids is not None:
            changes["permission_ids"] = permission_ids

        # 检查状态变更
        if old_is_active != role.is_active:
            action = (
                PermissionAuditService.ACTION_ROLE_ACTIVATED
                if role.is_active
                else PermissionAuditService.ACTION_ROLE_DEACTIVATED
            )
        else:
            action = PermissionAuditService.ACTION_ROLE_UPDATED

        PermissionAuditService.log_role_operation(
            db=db,
            operator_id=current_user.id,
            role_id=role.id,
            action=action,
            changes=changes,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        logger.warning("审计日志记录失败（update_role），不影响主流程", exc_info=True)

    return role


@router.put(
    "/{role_id}/permissions",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def assign_role_permissions(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    permission_ids: List[int],
    request: Request,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    分配角色权限

    - **role_id**: 角色ID
    - **permission_ids**: 权限ID列表
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system:
        raise HTTPException(status_code=400, detail="系统预置角色不允许修改权限")

    # 验证权限是否存在
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    if len(permissions) != len(permission_ids):
        raise HTTPException(status_code=400, detail="部分权限不存在")

    # 删除原有权限关联
    db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()

    # 添加新权限关联
    for permission_id in permission_ids:
        db.add(RolePermission(role_id=role.id, permission_id=permission_id))

    db.commit()

    # 记录审计日志
    try:
        PermissionAuditService.log_role_permission_assignment(
            db=db,
            operator_id=current_user.id,
            role_id=role.id,
            permission_ids=permission_ids,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        logger.warning("审计日志记录失败（assign_role_permissions），不影响主流程", exc_info=True)

    return ResponseModel(code=200, message="角色权限分配成功")
