# -*- coding: utf-8 -*-
"""
角色业务逻辑服务
基于统一的 BaseService 实现
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.user import Role
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate

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
        转换为角色响应对象，包含权限列表（使用新的 api_permissions 表）
        """
        # 获取角色的权限名称列表（已迁移到新表）
        perm_sql = """
            SELECT ap.perm_name
            FROM role_api_permissions rap
            JOIN api_permissions ap ON rap.permission_id = ap.id
            WHERE rap.role_id = :role_id AND ap.is_active = 1
        """
        perm_result = self.db.execute(text(perm_sql), {"role_id": obj.id})
        permissions = [row[0] for row in perm_result.fetchall() if row and len(row) > 0 and row[0]]

        # 处理父角色名称
        parent_name = None
        if obj.parent_id:
            parent = self.db.query(Role).filter(Role.id == obj.parent_id).first()
            if parent:
                parent_name = parent.role_name

        return RoleResponse(
            id=obj.id,
            tenant_id=obj.tenant_id,
            source_template_id=getattr(obj, "source_template_id", None),
            role_code=obj.role_code or "",
            role_name=obj.role_name or "",
            description=obj.description,
            data_scope=obj.data_scope or "OWN",
            parent_id=obj.parent_id,
            parent_name=parent_name,
            nav_groups=getattr(obj, "nav_groups", None) or [],
            ui_config=getattr(obj, "ui_config", None) or {},
            is_system=bool(obj.is_system),
            is_active=bool(obj.is_active if obj.is_active is not None else True),
            sort_order=getattr(obj, "sort_order", None) or 0,
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
        tenant_id: Optional[int] = None,
        include_all_tenants: bool = True,
    ) -> Dict[str, Any]:
        """
        获取角色列表（优化了N+1查询）
        """
        query = self.db.query(Role)
        if not include_all_tenants:
            if tenant_id is None:
                query = query.filter(Role.tenant_id.is_(None))
            else:
                query = query.filter(or_(Role.tenant_id.is_(None), Role.tenant_id == tenant_id))
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(or_(Role.role_code.ilike(pattern), Role.role_name.ilike(pattern)))

        total = query.count()
        roles = (
            query.order_by(Role.created_at.desc(), Role.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 批量预加载所有角色的权限（避免N+1查询）
        role_ids = [r.id for r in roles]
        permissions_map = {}
        if role_ids:
            # SQLAlchemy IN clause needs proper formatting
            placeholders = ",".join([str(rid) for rid in role_ids])
            perm_sql_formatted = f"""
                SELECT rap.role_id, ap.perm_name
                FROM role_api_permissions rap
                JOIN api_permissions ap ON rap.permission_id = ap.id
                WHERE rap.role_id IN ({placeholders}) AND ap.is_active = 1
            """
            perm_result = self.db.execute(text(perm_sql_formatted))
            for role_id, perm_name in perm_result.fetchall():
                if role_id not in permissions_map:
                    permissions_map[role_id] = []
                if perm_name:
                    permissions_map[role_id].append(perm_name)

        # 批量预加载父角色名称（避免N+1查询）
        parent_ids = [r.parent_id for r in roles if r.parent_id]
        parents_map = {}
        if parent_ids:
            parents = self.db.query(Role.id, Role.role_name).filter(Role.id.in_(parent_ids)).all()
            parents_map = {p.id: p.role_name for p in parents}

        # 转换为响应对象，使用预加载的数据
        items = []
        for role in roles:
            permissions = permissions_map.get(role.id, [])
            parent_name = parents_map.get(role.parent_id) if role.parent_id else None

            items.append(
                RoleResponse(
                    id=role.id,
                    tenant_id=role.tenant_id,
                    source_template_id=getattr(role, "source_template_id", None),
                    role_code=role.role_code or "",
                    role_name=role.role_name or "",
                    description=role.description,
                    data_scope=role.data_scope or "OWN",
                    parent_id=role.parent_id,
                    parent_name=parent_name,
                    nav_groups=getattr(role, "nav_groups", None) or [],
                    ui_config=getattr(role, "ui_config", None) or {},
                    is_system=bool(role.is_system),
                    is_active=bool(role.is_active if role.is_active is not None else True),
                    sort_order=getattr(role, "sort_order", None) or 0,
                    permissions=permissions,
                    permission_count=len(permissions),
                    created_at=role.created_at,
                    updated_at=role.updated_at,
                )
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
