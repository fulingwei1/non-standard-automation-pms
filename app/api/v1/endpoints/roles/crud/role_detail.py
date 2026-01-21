# -*- coding: utf-8 -*-
"""
角色详情和比较

提供角色详情查询和角色比较功能
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Permission, Role, RolePermission, User
from app.schemas.common import ResponseModel

from .utils import _get_parent_roles

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{role_id}/detail", response_model=ResponseModel)
def get_role_detail(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取角色完整详情

    - 包含直接分配的权限和继承的权限
    - 包含数据权限规则
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 获取父角色名称
    parent_name = None
    if role.parent_id:
        parent = db.query(Role).filter(Role.id == role.parent_id).first()
        if parent:
            parent_name = parent.role_name

    # 获取直接分配的权限
    direct_perms = db.query(Permission).join(RolePermission).filter(
        RolePermission.role_id == role_id,
        Permission.is_active == True
    ).all()

    direct_perm_ids = {p.id for p in direct_perms}
    direct_permissions = [
        {
            "id": p.id,
            "permission_code": p.permission_code,
            "permission_name": p.permission_name,
            "module": p.module,
            "page_code": p.page_code,
            "action": p.action,
            "description": p.description,
        }
        for p in direct_perms
    ]

    # 获取继承的权限
    inherited_permissions = []
    inherited_from = {}
    if role.parent_id:
        parent_roles = _get_parent_roles(db, role.parent_id)
        for parent_role in parent_roles:
            parent_perms = db.query(Permission).join(RolePermission).filter(
                RolePermission.role_id == parent_role.id,
                Permission.is_active == True
            ).all()
            for p in parent_perms:
                if p.id not in direct_perm_ids and p.id not in inherited_from:
                    inherited_from[p.id] = parent_role.role_name
                    inherited_permissions.append({
                        "id": p.id,
                        "permission_code": p.permission_code,
                        "permission_name": p.permission_name,
                        "module": p.module,
                        "page_code": p.page_code,
                        "action": p.action,
                        "description": p.description,
                        "inherited_from": parent_role.role_name,
                    })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "description": role.description,
            "data_scope": role.data_scope,
            "parent_id": role.parent_id,
            "parent_name": parent_name,
            "is_system": role.is_system,
            "is_active": role.is_active,
            "sort_order": role.sort_order or 0,
            "direct_permissions": direct_permissions,
            "inherited_permissions": inherited_permissions,
            "nav_groups": role.nav_groups,
            "ui_config": role.ui_config,
            "created_at": role.created_at.isoformat() if role.created_at else None,
            "updated_at": role.updated_at.isoformat() if role.updated_at else None,
        }
    )




@router.post("/compare", response_model=ResponseModel)
def compare_roles(
    *,
    db: Session = Depends(deps.get_db),
    role_ids: List[int],
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    对比多个角色的权限

    - **role_ids**: 要对比的角色ID列表（2-5个）
    """
    if len(role_ids) < 2 or len(role_ids) > 5:
        raise HTTPException(status_code=400, detail="请选择2-5个角色进行对比")

    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    if len(roles) != len(role_ids):
        raise HTTPException(status_code=400, detail="部分角色不存在")

    # 收集每个角色的权限
    role_permissions = {}
    for role in roles:
        perms = db.query(Permission).join(RolePermission).filter(
            RolePermission.role_id == role.id,
            Permission.is_active == True
        ).all()
        role_permissions[role.id] = {
            "role_id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "data_scope": role.data_scope,
            "permissions": [p.permission_code for p in perms],
            "permission_ids": [p.id for p in perms],
        }

    # 计算共同权限和差异权限
    all_perm_sets = [set(r["permissions"]) for r in role_permissions.values()]
    common_permissions = list(set.intersection(*all_perm_sets)) if all_perm_sets else []

    diff_permissions = {}
    for role_id, data in role_permissions.items():
        perm_set = set(data["permissions"])
        unique_perms = perm_set - set(common_permissions)
        diff_permissions[str(role_id)] = list(unique_perms)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "roles": list(role_permissions.values()),
            "common_permissions": common_permissions,
            "diff_permissions": diff_permissions,
        }
    )


