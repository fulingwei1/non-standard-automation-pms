# -*- coding: utf-8 -*-
"""
角色权限分配

提供角色权限分配功能
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Permission, Role, RolePermission, User
from app.schemas.common import ResponseModel
from app.services.permission_audit_service import PermissionAuditService

from .utils import _invalidate_role_cache

logger = logging.getLogger(__name__)

router = APIRouter()


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

    # 权限变更，使相关用户缓存失效
    _invalidate_role_cache(db, role.id, include_children=True)

    return ResponseModel(code=200, message="角色权限分配成功")


