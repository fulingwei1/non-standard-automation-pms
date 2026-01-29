# -*- coding: utf-8 -*-
"""
权限缓存服务（多租户隔离版本）

提供用户/角色权限的缓存和即时生效机制。
支持多租户隔离，防止跨租户数据泄露。
"""

import logging
from typing import Any, Dict, List, Optional, Set

from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

# 缓存键前缀（包含租户维度：perm:t{tenant_id}:user:{user_id}）
CACHE_PREFIX_USER_PERMISSIONS = "perm:t{tenant_id}:user"
CACHE_PREFIX_ROLE_PERMISSIONS = "perm:t{tenant_id}:role"
CACHE_PREFIX_USER_ROLES = "perm:t{tenant_id}:user_roles"
CACHE_PREFIX_ROLE_USERS = "perm:t{tenant_id}:role_users"
CACHE_PREFIX_TENANT = "perm:tenant"

# 缓存过期时间（秒）
PERMISSION_CACHE_TTL = 600  # 10 分钟
ROLE_CACHE_TTL = 1800  # 30 分钟


class PermissionCacheService:
    """权限缓存服务（多租户隔离版）

    所有缓存键都包含 tenant_id 维度，确保：
    1. 不同租户的权限缓存完全隔离
    2. 清除租户缓存时不影响其他租户
    3. 防止缓存键冲突导致的数据泄露
    """

    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_cache"):
            self._cache = CacheService()

    def _build_key(self, prefix: str, tenant_id: Optional[int], resource_id: int) -> str:
        """构建租户隔离的缓存键

        Args:
            prefix: 缓存前缀模板
            tenant_id: 租户ID（None 表示系统级/超级管理员）
            resource_id: 资源ID（用户ID或角色ID）

        Returns:
            格式化的缓存键
        """
        tid = tenant_id if tenant_id is not None else 0
        return f"{prefix.format(tenant_id=tid)}:{resource_id}"

    # ==================== 用户权限缓存 ====================

    def get_user_permissions(
        self, user_id: int, tenant_id: Optional[int] = None
    ) -> Optional[Set[str]]:
        """获取用户权限缓存

        Args:
            user_id: 用户ID
            tenant_id: 租户ID（可选，用于租户隔离）
        """
        key = self._build_key(CACHE_PREFIX_USER_PERMISSIONS, tenant_id, user_id)
        data = self._cache.get(key)
        return set(data) if data else None

    def set_user_permissions(
        self, user_id: int, permissions: Set[str], tenant_id: Optional[int] = None
    ) -> bool:
        """设置用户权限缓存

        Args:
            user_id: 用户ID
            permissions: 权限编码集合
            tenant_id: 租户ID（可选）
        """
        key = self._build_key(CACHE_PREFIX_USER_PERMISSIONS, tenant_id, user_id)
        return self._cache.set(key, list(permissions), PERMISSION_CACHE_TTL)

    def invalidate_user_permissions(
        self, user_id: int, tenant_id: Optional[int] = None
    ) -> bool:
        """使用户权限缓存失效

        Args:
            user_id: 用户ID
            tenant_id: 租户ID（可选）
        """
        key = self._build_key(CACHE_PREFIX_USER_PERMISSIONS, tenant_id, user_id)
        logger.info(f"Invalidating user permission cache: tenant_id={tenant_id}, user_id={user_id}")
        return self._cache.delete(key)

    def invalidate_tenant_user_permissions(self, tenant_id: int) -> int:
        """使指定租户的所有用户权限缓存失效

        Args:
            tenant_id: 租户ID

        Returns:
            删除的缓存数量
        """
        pattern = f"perm:t{tenant_id}:user:*"
        logger.info(f"Invalidating all user permissions for tenant: tenant_id={tenant_id}")
        return self._cache.delete_pattern(pattern)

    def invalidate_all_user_permissions(self) -> int:
        """使所有用户权限缓存失效（跨所有租户）"""
        logger.info("Invalidating all user permission caches (all tenants)")
        return self._cache.delete_pattern("perm:t*:user:*")

    # ==================== 角色权限缓存 ====================

    def get_role_permissions(
        self, role_id: int, tenant_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """获取角色权限缓存"""
        key = self._build_key(CACHE_PREFIX_ROLE_PERMISSIONS, tenant_id, role_id)
        return self._cache.get(key)

    def set_role_permissions(
        self, role_id: int, data: Dict[str, Any], tenant_id: Optional[int] = None
    ) -> bool:
        """设置角色权限缓存"""
        key = self._build_key(CACHE_PREFIX_ROLE_PERMISSIONS, tenant_id, role_id)
        return self._cache.set(key, data, ROLE_CACHE_TTL)

    def invalidate_role_permissions(
        self, role_id: int, tenant_id: Optional[int] = None
    ) -> bool:
        """使角色权限缓存失效"""
        key = self._build_key(CACHE_PREFIX_ROLE_PERMISSIONS, tenant_id, role_id)
        logger.info(f"Invalidating role permission cache: tenant_id={tenant_id}, role_id={role_id}")
        return self._cache.delete(key)

    def invalidate_tenant_role_permissions(self, tenant_id: int) -> int:
        """使指定租户的所有角色权限缓存失效"""
        pattern = f"perm:t{tenant_id}:role:*"
        logger.info(f"Invalidating all role permissions for tenant: tenant_id={tenant_id}")
        return self._cache.delete_pattern(pattern)

    def invalidate_all_role_permissions(self) -> int:
        """使所有角色权限缓存失效"""
        logger.info("Invalidating all role permission caches")
        return self._cache.delete_pattern("perm:t*:role:*")

    # ==================== 用户-角色关联缓存 ====================

    def get_user_role_ids(
        self, user_id: int, tenant_id: Optional[int] = None
    ) -> Optional[List[int]]:
        """获取用户的角色 ID 列表缓存"""
        key = self._build_key(CACHE_PREFIX_USER_ROLES, tenant_id, user_id)
        return self._cache.get(key)

    def set_user_role_ids(
        self, user_id: int, role_ids: List[int], tenant_id: Optional[int] = None
    ) -> bool:
        """设置用户的角色 ID 列表缓存"""
        key = self._build_key(CACHE_PREFIX_USER_ROLES, tenant_id, user_id)
        return self._cache.set(key, role_ids, PERMISSION_CACHE_TTL)

    def get_role_user_ids(
        self, role_id: int, tenant_id: Optional[int] = None
    ) -> Optional[List[int]]:
        """获取角色下的用户 ID 列表缓存"""
        key = self._build_key(CACHE_PREFIX_ROLE_USERS, tenant_id, role_id)
        return self._cache.get(key)

    def set_role_user_ids(
        self, role_id: int, user_ids: List[int], tenant_id: Optional[int] = None
    ) -> bool:
        """设置角色下的用户 ID 列表缓存"""
        key = self._build_key(CACHE_PREFIX_ROLE_USERS, tenant_id, role_id)
        return self._cache.set(key, user_ids, ROLE_CACHE_TTL)

    # ==================== 批量失效操作 ====================

    def invalidate_role_and_users(
        self,
        role_id: int,
        user_ids: Optional[List[int]] = None,
        tenant_id: Optional[int] = None,
    ) -> int:
        """角色权限变更时，使角色缓存和相关用户缓存失效"""
        count = 0

        # 1. 使角色权限缓存失效
        self.invalidate_role_permissions(role_id, tenant_id)
        count += 1

        # 2. 获取角色下的用户列表
        if user_ids is None:
            user_ids = self.get_role_user_ids(role_id, tenant_id) or []

        # 3. 使所有相关用户的权限缓存失效
        for user_id in user_ids:
            self.invalidate_user_permissions(user_id, tenant_id)
            count += 1

        # 4. 清除角色-用户关联缓存
        key = self._build_key(CACHE_PREFIX_ROLE_USERS, tenant_id, role_id)
        self._cache.delete(key)
        count += 1

        logger.info(
            f"Invalidated role and user caches: tenant_id={tenant_id}, "
            f"role_id={role_id}, affected_users={len(user_ids)}"
        )
        return count

    def invalidate_user_role_change(
        self,
        user_id: int,
        old_role_ids: List[int],
        new_role_ids: List[int],
        tenant_id: Optional[int] = None,
    ) -> int:
        """用户角色变更时，更新相关缓存"""
        count = 0

        # 1. 使用户权限缓存失效
        self.invalidate_user_permissions(user_id, tenant_id)
        count += 1

        # 2. 清除用户-角色关联缓存
        key = self._build_key(CACHE_PREFIX_USER_ROLES, tenant_id, user_id)
        self._cache.delete(key)
        count += 1

        # 3. 更新角色-用户关联缓存（从旧角色中移除，添加到新角色）
        removed_roles = set(old_role_ids) - set(new_role_ids)
        added_roles = set(new_role_ids) - set(old_role_ids)

        for role_id in removed_roles | added_roles:
            key = self._build_key(CACHE_PREFIX_ROLE_USERS, tenant_id, role_id)
            self._cache.delete(key)
            count += 1

        logger.info(
            f"Invalidated user role change caches: tenant_id={tenant_id}, "
            f"user_id={user_id}, removed_roles={removed_roles}, added_roles={added_roles}"
        )
        return count

    def invalidate_tenant(self, tenant_id: int) -> int:
        """使指定租户的所有权限缓存失效

        当租户配置变更、权限批量更新时调用

        Args:
            tenant_id: 租户ID

        Returns:
            删除的缓存数量
        """
        count = 0
        count += self._cache.delete_pattern(f"perm:t{tenant_id}:*")
        logger.info(f"Invalidated all permission caches for tenant: tenant_id={tenant_id}, count={count}")
        return count

    def invalidate_all(self) -> int:
        """使所有权限相关缓存失效（谨慎使用，影响所有租户）"""
        count = 0
        count += self._cache.delete_pattern("perm:t*:*")
        logger.info(f"Invalidated all permission caches: count={count}")
        return count

    # ==================== 统计信息 ====================

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        base_stats = self._cache.get_stats()
        return {
            **base_stats,
            "cache_type": "permission",
            "ttl_user": PERMISSION_CACHE_TTL,
            "ttl_role": ROLE_CACHE_TTL,
            "tenant_isolation": True,
        }


# 全局单例
_permission_cache_service: Optional[PermissionCacheService] = None


def get_permission_cache_service() -> PermissionCacheService:
    """获取权限缓存服务单例"""
    global _permission_cache_service
    if _permission_cache_service is None:
        _permission_cache_service = PermissionCacheService()
    return _permission_cache_service
