# -*- coding: utf-8 -*-
"""
权限 CRUD 业务逻辑服务
基于统一的 BaseService 实现（已迁移到新的 ApiPermission 模型）
"""

from typing import Any, List, Optional
from sqlalchemy.orm import Session

from app.common.crud.base import BaseService
from app.models.user import ApiPermission
from app.schemas.auth import PermissionResponse


class PermissionCRUDService(BaseService[ApiPermission, Any, Any, PermissionResponse]):
    """
    权限 CRUD 服务类（使用新的 ApiPermission 模型）
    """

    def __init__(self, db: Session):
        super().__init__(
            model=ApiPermission,
            db=db,
            response_schema=PermissionResponse,
            resource_name="权限",
        )

    def _to_response(self, obj: ApiPermission) -> PermissionResponse:
        """
        转换为权限响应对象
        """
        return PermissionResponse(
            id=obj.id,
            permission_code=obj.perm_code,
            permission_name=obj.perm_name,
            module=obj.module,
            resource=None,  # 新模型没有 resource 字段
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

        permissions = query.order_by(self.model.module, self.model.perm_code).all()
        return [self._to_response(p) for p in permissions]
