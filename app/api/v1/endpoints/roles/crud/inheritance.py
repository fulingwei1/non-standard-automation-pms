# -*- coding: utf-8 -*-
"""
角色继承树

提供角色继承树查询功能
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Role, User
from app.schemas.common import ResponseModel

from .utils import _get_child_role_ids

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/inheritance-tree", response_model=ResponseModel)
def get_role_inheritance_tree(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取角色继承树结构

    返回所有角色的树形继承关系
    """
    roles = db.query(Role).filter(Role.is_active == True).all()

    # 构建角色字典
    role_dict = {r.id: r for r in roles}

    # 构建树形结构
    def build_tree(role_id: int) -> dict:
        role = role_dict.get(role_id)
        if not role:
            return None

        children = [r for r in roles if r.parent_id == role_id]
        perm_count = db.query(RolePermission).filter(RolePermission.role_id == role_id).count()

        return {
            "id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "data_scope": role.data_scope,
            "permission_count": perm_count,
            "is_system": role.is_system,
            "children": [build_tree(c.id) for c in children],
        }

    # 找到顶级角色（没有父角色的）
    root_roles = [r for r in roles if r.parent_id is None]
    tree = [build_tree(r.id) for r in root_roles]

    return ResponseModel(
        code=200,
        message="success",
        data={"tree": tree}
    )
