# -*- coding: utf-8 -*-
"""
角色业务逻辑服务
基于统一的 BaseService 实现
"""

import logging
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.common.crud.base import BaseService
from app.models.user import Role
from app.schemas.auth import RoleCreate, RoleUpdate, RoleResponse

logger = logging.getLogger(__name__)


class RoleService(BaseService[Role, RoleCreate, RoleUpdate, RoleResponse]):
    """
    角色服务类
    """

    def __init__(self, db: Session):
        super().__init__(
            model=Role,
            db=db,
            response_schema=RoleResponse,
            resource_name="角色",
        )

    def _to_response(self, obj: Role) -> RoleResponse:
        """
        转换为角色响应对象，包含权限列表
        """
        # 获取角色的权限名称列表
        perm_sql = """
            SELECT p.perm_name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = :role_id
        """
        perm_result = self.db.execute(text(perm_sql), {"role_id": obj.id})
        permissions = [row[0] for row in perm_result.fetchall() if row[0]]

        # 处理父角色名称
        parent_name = None
        if obj.parent_id:
            parent = self.db.query(Role).filter(Role.id == obj.parent_id).first()
            if parent:
                parent_name = parent.role_name

        return RoleResponse(
            id=obj.id,
            role_code=obj.role_code or "",
            role_name=obj.role_name or "",
            description=obj.description,
            data_scope=obj.data_scope or "OWN",
            parent_id=obj.parent_id,
            parent_name=parent_name,
            is_system=bool(obj.is_system),
            is_active=bool(obj.is_active if obj.is_active is not None else True),
            sort_order=getattr(obj, "sort_order", 0),
            permissions=permissions,
            permission_count=len(permissions),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    def list_roles(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        获取角色列表
        """
        from app.common.crud.types import QueryParams

        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active

        params = QueryParams(
            page=page,
            page_size=page_size,
            search=keyword,
            search_fields=["role_code", "role_name"],
            filters=filters,
            sort_by="created_at",
            sort_order="desc",
        )

        result = self.list(params)

        return {
            "items": result.items,
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "pages": (result.total + result.page_size - 1) // result.page_size,
        }
