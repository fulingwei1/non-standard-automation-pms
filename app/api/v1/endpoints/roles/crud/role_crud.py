# -*- coding: utf-8 -*-
"""
角色CRUD操作

提供角色的创建和更新功能
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Permission, Role, RolePermission, User, UserRole
from app.schemas.auth import RoleCreate, RoleResponse, RoleUpdate
from app.services.permission_audit_service import PermissionAuditService

from .utils import (
    _count_inherited_permissions,
    _get_role_user_ids,
    _invalidate_role_cache,
    _would_create_cycle,
)

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
    - 支持设置父角色以实现权限继承
    """
    role = db.query(Role).filter(Role.role_code == role_in.role_code).first()
    if role:
        raise HTTPException(
            status_code=400,
            detail="该角色编码已存在",
        )

    # 验证父角色是否存在
    parent_name = None
    if role_in.parent_id:
        parent_role = db.query(Role).filter(Role.id == role_in.parent_id).first()
        if not parent_role:
            raise HTTPException(status_code=400, detail="父角色不存在")
        if not parent_role.is_active:
            raise HTTPException(status_code=400, detail="父角色已被禁用")
        parent_name = parent_role.role_name

    role = Role(
        role_code=role_in.role_code,
        role_name=role_in.role_name,
        description=role_in.description,
        data_scope=role_in.data_scope,
        parent_id=role_in.parent_id,
        nav_groups=role_in.nav_groups,
        ui_config=role_in.ui_config,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    if role_in.permission_ids:
        for p_id in role_in.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=p_id))
        db.commit()
        db.refresh(role)

    # 计算权限数量
    direct_count = db.query(RolePermission).filter(RolePermission.role_id == role.id).count()

    # 构建响应
    response = RoleResponse(
        id=role.id,
        role_code=role.role_code,
        role_name=role.role_name,
        description=role.description,
        data_scope=role.data_scope,
        parent_id=role.parent_id,
        parent_name=parent_name,
        is_system=role.is_system,
        is_active=role.is_active,
        sort_order=role.sort_order or 0,
        permissions=[rp.permission.permission_name for rp in role.permissions],
        permission_count=direct_count,
        inherited_permission_count=0,  # 新建时暂不计算继承
        nav_groups=role.nav_groups,
        ui_config=role.ui_config,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )

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
                "parent_id": role.parent_id,
                "permission_ids": role_in.permission_ids,
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        logger.warning("审计日志记录失败（create_role），不影响主流程", exc_info=True)

    return response


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
    - 支持更新父角色（会检查循环引用）
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
        "parent_id": role.parent_id,
    }

    update_data = role_in.model_dump(exclude_unset=True)
    permission_ids = None

    # 验证父角色
    parent_name = None
    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]
        if new_parent_id is not None:
            # 不能设置自己为父角色
            if new_parent_id == role_id:
                raise HTTPException(status_code=400, detail="不能将自己设为父角色")
            # 检查父角色是否存在
            parent_role = db.query(Role).filter(Role.id == new_parent_id).first()
            if not parent_role:
                raise HTTPException(status_code=400, detail="父角色不存在")
            if not parent_role.is_active:
                raise HTTPException(status_code=400, detail="父角色已被禁用")
            # 检查循环引用
            if _would_create_cycle(db, role_id, new_parent_id):
                raise HTTPException(status_code=400, detail="设置该父角色会导致循环引用")
            parent_name = parent_role.role_name
    elif role.parent_id:
        parent_role = db.query(Role).filter(Role.id == role.parent_id).first()
        if parent_role:
            parent_name = parent_role.role_name

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

    # 计算权限数量
    direct_count = db.query(RolePermission).filter(RolePermission.role_id == role.id).count()
    inherited_count = _count_inherited_permissions(db, role.parent_id) if role.parent_id else 0

    # 构建响应
    response = RoleResponse(
        id=role.id,
        role_code=role.role_code,
        role_name=role.role_name,
        description=role.description,
        data_scope=role.data_scope,
        parent_id=role.parent_id,
        parent_name=parent_name,
        is_system=role.is_system,
        is_active=role.is_active,
        sort_order=role.sort_order or 0,
        permissions=[rp.permission.permission_name for rp in role.permissions],
        permission_count=direct_count,
        inherited_permission_count=inherited_count,
        nav_groups=role.nav_groups,
        ui_config=role.ui_config,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )

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

    # 权限或继承关系变更时，使相关用户缓存失效
    if permission_ids is not None or "parent_id" in role_in.model_dump(exclude_unset=True):
        _invalidate_role_cache(db, role.id, include_children=True)

    return response


