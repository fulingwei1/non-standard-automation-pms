# -*- coding: utf-8 -*-
"""
权限管理服务层

提供权限的 CRUD 操作、角色权限关联和用户权限查询功能。
支持多租户数据隔离。
"""

import logging
from typing import List, Optional, Dict, Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.user import (
    ApiPermission,
    Role,
    RoleApiPermission,
    User,
)

logger = logging.getLogger(__name__)


class PermissionManagementService:
    """权限管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================================
    # 权限 CRUD 业务逻辑
    # ============================================================
    
    def list_permissions(
        self,
        tenant_id: int,
        page: int,
        page_size: int,
        module: Optional[str] = None,
        action: Optional[str] = None,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        获取权限列表（支持多租户隔离）
        
        返回: {"items": [...], "total": int}
        """
        query = self.db.query(ApiPermission).filter(
            or_(
                ApiPermission.tenant_id.is_(None),  # 系统级权限
                ApiPermission.tenant_id == tenant_id  # 租户级权限
            )
        )
        
        # 筛选条件
        if module:
            query = query.filter(ApiPermission.module == module)
        if action:
            query = query.filter(ApiPermission.action == action)
        if is_active is not None:
            query = query.filter(ApiPermission.is_active == is_active)
        if keyword:
            query = query.filter(
                or_(
                    ApiPermission.perm_code.contains(keyword),
                    ApiPermission.perm_name.contains(keyword),
                    ApiPermission.description.contains(keyword),
                )
            )
        
        # 分页查询
        total = query.count()
        permissions = (
            query.order_by(ApiPermission.module, ApiPermission.perm_code)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        return {
            "items": permissions,
            "total": total,
        }
    
    def list_modules(self, tenant_id: int) -> List[str]:
        """获取所有权限模块列表（去重）"""
        modules = (
            self.db.query(ApiPermission.module)
            .filter(
                ApiPermission.module.isnot(None),
                or_(
                    ApiPermission.tenant_id.is_(None),
                    ApiPermission.tenant_id == tenant_id
                )
            )
            .distinct()
            .order_by(ApiPermission.module)
            .all()
        )
        
        return [m[0] for m in modules if m[0]]
    
    def get_permission(
        self,
        permission_id: int,
        tenant_id: int,
    ) -> Optional[ApiPermission]:
        """获取权限详情"""
        return self.db.query(ApiPermission).filter(
            ApiPermission.id == permission_id,
            or_(
                ApiPermission.tenant_id.is_(None),
                ApiPermission.tenant_id == tenant_id
            )
        ).first()
    
    def check_permission_code_exists(
        self,
        perm_code: str,
        tenant_id: int,
    ) -> bool:
        """检查权限编码是否已存在"""
        existing = self.db.query(ApiPermission).filter(
            ApiPermission.perm_code == perm_code,
            or_(
                ApiPermission.tenant_id.is_(None),
                ApiPermission.tenant_id == tenant_id
            )
        ).first()
        
        return existing is not None
    
    def create_permission(
        self,
        tenant_id: int,
        perm_code: str,
        perm_name: str,
        module: Optional[str] = None,
        page_code: Optional[str] = None,
        action: Optional[str] = None,
        description: Optional[str] = None,
        permission_type: str = "API",
    ) -> ApiPermission:
        """创建权限（租户级）"""
        permission = ApiPermission(
            tenant_id=tenant_id,
            perm_code=perm_code,
            perm_name=perm_name,
            module=module,
            page_code=page_code,
            action=action,
            description=description,
            permission_type=permission_type,
            is_active=True,
            is_system=False,
        )
        
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        
        return permission
    
    def update_permission(
        self,
        permission: ApiPermission,
        perm_name: Optional[str] = None,
        module: Optional[str] = None,
        page_code: Optional[str] = None,
        action: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> ApiPermission:
        """更新权限"""
        if perm_name is not None:
            permission.perm_name = perm_name
        if module is not None:
            permission.module = module
        if page_code is not None:
            permission.page_code = page_code
        if action is not None:
            permission.action = action
        if description is not None:
            permission.description = description
        if is_active is not None:
            permission.is_active = is_active
        
        self.db.commit()
        self.db.refresh(permission)
        
        return permission
    
    def count_roles_using_permission(self, permission_id: int) -> int:
        """统计使用该权限的角色数量"""
        return self.db.query(RoleApiPermission).filter(
            RoleApiPermission.permission_id == permission_id
        ).count()
    
    def delete_permission(self, permission: ApiPermission) -> None:
        """删除权限"""
        self.db.delete(permission)
        self.db.commit()
    
    # ============================================================
    # 角色权限关联业务逻辑
    # ============================================================
    
    def get_role(
        self,
        role_id: int,
        tenant_id: int,
    ) -> Optional[Role]:
        """获取角色（支持多租户隔离）"""
        return self.db.query(Role).filter(
            Role.id == role_id,
            or_(
                Role.tenant_id.is_(None),
                Role.tenant_id == tenant_id
            )
        ).first()
    
    def get_role_permissions(self, role_id: int) -> List[ApiPermission]:
        """获取角色的所有权限"""
        return (
            self.db.query(ApiPermission)
            .join(RoleApiPermission, RoleApiPermission.permission_id == ApiPermission.id)
            .filter(RoleApiPermission.role_id == role_id)
            .filter(ApiPermission.is_active)
            .order_by(ApiPermission.module, ApiPermission.perm_code)
            .all()
        )
    
    def assign_role_permissions(
        self,
        role_id: int,
        permission_ids: List[int],
        tenant_id: int,
    ) -> int:
        """
        为角色分配权限（覆盖式更新）
        
        返回: 成功分配的权限数量
        """
        # 删除现有权限关联
        self.db.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == role_id
        ).delete()
        
        # 验证权限ID并添加新的关联
        valid_count = 0
        for perm_id in permission_ids:
            permission = self.db.query(ApiPermission).filter(
                ApiPermission.id == perm_id,
                or_(
                    ApiPermission.tenant_id.is_(None),
                    ApiPermission.tenant_id == tenant_id
                )
            ).first()
            
            if permission:
                self.db.add(RoleApiPermission(role_id=role_id, permission_id=perm_id))
                valid_count += 1
        
        self.db.commit()
        
        return valid_count
    
    def invalidate_permission_cache(
        self,
        role_id: int,
        tenant_id: int,
    ) -> None:
        """清除权限缓存"""
        try:
            from app.services.permission_cache_service import get_permission_cache_service
            cache_service = get_permission_cache_service()
            cache_service.invalidate_role_and_users(role_id, tenant_id=tenant_id)
        except Exception as e:
            logger.warning(f"清除权限缓存失败: {e}")
    
    # ============================================================
    # 用户权限查询业务逻辑
    # ============================================================
    
    def get_user(self, user_id: int) -> Optional[User]:
        """获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_permissions(
        self,
        user_id: int,
        tenant_id: int,
    ) -> List[ApiPermission]:
        """
        获取用户的所有权限（通过角色继承）
        
        - 包含直接分配的角色权限
        - 支持角色继承（如果启用）
        - 返回去重后的权限列表
        """
        from app.services.permission_service import PermissionService
        
        permission_codes = PermissionService.get_user_permissions(
            self.db, user_id, tenant_id
        )
        
        # 获取权限详情
        return (
            self.db.query(ApiPermission)
            .filter(
                ApiPermission.perm_code.in_(permission_codes),
                ApiPermission.is_active
            )
            .order_by(ApiPermission.module, ApiPermission.perm_code)
            .all()
        )
    
    def check_user_permission(
        self,
        user_id: int,
        permission_code: str,
        user: User,
        tenant_id: int,
    ) -> bool:
        """检查用户是否有指定权限"""
        from app.services.permission_service import PermissionService
        
        return PermissionService.check_permission(
            self.db, user_id, permission_code, user, tenant_id
        )
