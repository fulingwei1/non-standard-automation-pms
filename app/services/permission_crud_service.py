# -*- coding: utf-8 -*-
"""
权限 CRUD 业务逻辑服务
基于统一的 BaseService 实现
"""

from typing import Any, List, Optional
from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.user import Permission
from app.schemas.auth import PermissionResponse


class PermissionCRUDService(BaseService[Permission, Any, Any, PermissionResponse]):
    """
    权限 CRUD 服务类
    """

    def __init__(self, db: Session):
        super().__init__(
            model=Permission,
            db=db,
            response_schema=PermissionResponse,
            resource_name="权限",
        )

    def _to_response(self, obj: Permission) -> PermissionResponse:
        """
        转换为权限响应对象
        """
        return PermissionResponse(
            id=obj.id,
            permission_code=obj.permission_code,
            permission_name=obj.permission_name,
            module=obj.module,
            resource=obj.resource,
            action=obj.action,
            description=obj.description,
            is_active=bool(obj.is_active if obj.is_active is not None else True),
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    def list_permissions(
        self, module: Optional[str] = None, is_active: bool = True
    ) -> List[PermissionResponse]:
        """
        获取权限列表
        """
        query = self.db.query(self.model)
        if module:
            query = query.filter(self.model.module == module)
        if is_active:
            query = query.filter(self.model.is_active.is_(True))

        permissions = query.order_by(
            self.model.module, self.model.permission_code
        ).all()
        return [self._to_response(p) for p in permissions]
