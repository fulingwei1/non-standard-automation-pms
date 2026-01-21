# -*- coding: utf-8 -*-
"""
权限缓存服务

实现用户/角色权限的缓存和即时生效机制：
- 缓存用户的完整权限列表
- 缓存角色的权限列表
- 角色权限变更时自动失效相关用户缓存
- 支持 Redis 和内存缓存降级
"""

import logging
from typing import Any, Dict, List, Optional, Set

from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

# 缓存键前缀
CACHE_PREFIX_USER_PERMISSIONS = "perm:user"  # 用户权限缓存
CACHE_PREFIX_ROLE_PERMISSIONS = "perm:role"  # 角色权限缓存
CACHE_PREFIX_USER_ROLES = "perm:user_roles"  # 用户角色列表缓存
CACHE_PREFIX_ROLE_USERS = "perm:role_users"  # 角色下用户列表缓存（用于批量失效）

# 缓存过期时间（秒）
PERMISSION_CACHE_TTL = 600  # 10 分钟
ROLE_CACHE_TTL = 1800  # 30 分钟


class PermissionCacheService:
    """权限缓存服务"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._cache = CacheService()
        self._initialized = True

    # ==================== 用户权限缓存 ====================

    def get_user_permissions(self, user_id: int) -> Optional[Set[str]]:
        """
        获取用户权限缓存

        Args:
            user_id: 用户 ID

        Returns:
            用户权限编码集合，缓存不存在返回 None
        """
        key = f"{CACHE_PREFIX_USER_PERMISSIONS}:{user_id}"
        data = self._cache.get(key)
        if data:
            return set(data)
        return None

    def set_user_permissions(self, user_id: int, permissions: Set[str]) -> bool:
        """
        设置用户权限缓存

        Args:
            user_id: 用户 ID
            permissions: 权限编码集合

        Returns:
            是否设置成功
        """
        key = f"{CACHE_PREFIX_USER_PERMISSIONS}:{user_id}"
        return self._cache.set(key, list(permissions), PERMISSION_CACHE_TTL)

    def invalidate_user_permissions(self, user_id: int) -> bool:
        """
        使用户权限缓存失效

        Args:
            user_id: 用户 ID

        Returns:
            是否成功
        """
        key = f"{CACHE_PREFIX_USER_PERMISSIONS}:{user_id}"
        logger.info(f"Invalidating user permission cache: user_id={user_id}")
        return self._cache.delete(key)

    def invalidate_all_user_permissions(self) -> int:
        """
        使所有用户权限缓存失效

        Returns:
            删除的缓存数量
        """
        logger.info("Invalidating all user permission caches")
        return self._cache.delete_pattern(f"{CACHE_PREFIX_USER_PERMISSIONS}:*")

    # ==================== 角色权限缓存 ====================

    def get_role_permissions(self, role_id: int) -> Optional[Dict[str, Any]]:
        """
        获取角色权限缓存

        Args:
            role_id: 角色 ID

        Returns:
            角色权限数据（包含直接权限和继承权限）
        """
        key = f"{CACHE_PREFIX_ROLE_PERMISSIONS}:{role_id}"
        return self._cache.get(key)

    def set_role_permissions(self, role_id: int, data: Dict[str, Any]) -> bool:
        """
        设置角色权限缓存

        Args:
            role_id: 角色 ID
            data: 角色权限数据

        Returns:
            是否设置成功
        """
        key = f"{CACHE_PREFIX_ROLE_PERMISSIONS}:{role_id}"
        return self._cache.set(key, data, ROLE_CACHE_TTL)

    def invalidate_role_permissions(self, role_id: int) -> bool:
        """
        使角色权限缓存失效

        Args:
            role_id: 角色 ID

        Returns:
            是否成功
        """
        key = f"{CACHE_PREFIX_ROLE_PERMISSIONS}:{role_id}"
        logger.info(f"Invalidating role permission cache: role_id={role_id}")
        return self._cache.delete(key)

    def invalidate_all_role_permissions(self) -> int:
        """
        使所有角色权限缓存失效

        Returns:
            删除的缓存数量
        """
        logger.info("Invalidating all role permission caches")
        return self._cache.delete_pattern(f"{CACHE_PREFIX_ROLE_PERMISSIONS}:*")

    # ==================== 用户-角色关联缓存 ====================

    def get_user_role_ids(self, user_id: int) -> Optional[List[int]]:
        """
        获取用户的角色 ID 列表缓存

        Args:
            user_id: 用户 ID

        Returns:
            角色 ID 列表
        """
        key = f"{CACHE_PREFIX_USER_ROLES}:{user_id}"
        return self._cache.get(key)

    def set_user_role_ids(self, user_id: int, role_ids: List[int]) -> bool:
        """
        设置用户的角色 ID 列表缓存

        Args:
            user_id: 用户 ID
            role_ids: 角色 ID 列表

        Returns:
            是否设置成功
        """
        key = f"{CACHE_PREFIX_USER_ROLES}:{user_id}"
        return self._cache.set(key, role_ids, PERMISSION_CACHE_TTL)

    def get_role_user_ids(self, role_id: int) -> Optional[List[int]]:
        """
        获取角色下的用户 ID 列表缓存

        Args:
            role_id: 角色 ID

        Returns:
            用户 ID 列表
        """
        key = f"{CACHE_PREFIX_ROLE_USERS}:{role_id}"
        return self._cache.get(key)

    def set_role_user_ids(self, role_id: int, user_ids: List[int]) -> bool:
        """
        设置角色下的用户 ID 列表缓存

        Args:
            role_id: 角色 ID
            user_ids: 用户 ID 列表

        Returns:
            是否设置成功
        """
        key = f"{CACHE_PREFIX_ROLE_USERS}:{role_id}"
        return self._cache.set(key, user_ids, ROLE_CACHE_TTL)

    # ==================== 批量失效操作 ====================

    def invalidate_role_and_users(self, role_id: int, user_ids: Optional[List[int]] = None) -> int:
        """
        角色权限变更时，使角色缓存和相关用户缓存失效

        Args:
            role_id: 角色 ID
            user_ids: 可选的用户 ID 列表，如果不提供则尝试从缓存获取

        Returns:
            失效的缓存数量
        """
        count = 0

        # 1. 使角色权限缓存失效
        self.invalidate_role_permissions(role_id)
        count += 1

        # 2. 获取角色下的用户列表
        if user_ids is None:
            user_ids = self.get_role_user_ids(role_id) or []

        # 3. 使所有相关用户的权限缓存失效
        for user_id in user_ids:
            self.invalidate_user_permissions(user_id)
            count += 1

        # 4. 清除角色-用户关联缓存
        key = f"{CACHE_PREFIX_ROLE_USERS}:{role_id}"
        self._cache.delete(key)
        count += 1

        logger.info(f"Invalidated role and user caches: role_id={role_id}, affected_users={len(user_ids)}")
        return count

    def invalidate_user_role_change(self, user_id: int, old_role_ids: List[int], new_role_ids: List[int]) -> int:
        """
        用户角色变更时，更新相关缓存

        Args:
            user_id: 用户 ID
            old_role_ids: 旧角色 ID 列表
            new_role_ids: 新角色 ID 列表

        Returns:
            失效的缓存数量
        """
        count = 0

        # 1. 使用户权限缓存失效
        self.invalidate_user_permissions(user_id)
        count += 1

        # 2. 清除用户-角色关联缓存
        key = f"{CACHE_PREFIX_USER_ROLES}:{user_id}"
        self._cache.delete(key)
        count += 1

        # 3. 更新角色-用户关联缓存（从旧角色中移除，添加到新角色）
        removed_roles = set(old_role_ids) - set(new_role_ids)
        added_roles = set(new_role_ids) - set(old_role_ids)

        for role_id in removed_roles | added_roles:
            key = f"{CACHE_PREFIX_ROLE_USERS}:{role_id}"
            self._cache.delete(key)
            count += 1

        logger.info(f"Invalidated user role change caches: user_id={user_id}, "
                   f"removed_roles={removed_roles}, added_roles={added_roles}")
        return count

    def invalidate_all(self) -> int:
        """
        使所有权限相关缓存失效

        Returns:
            删除的缓存数量
        """
        count = 0
        count += self._cache.delete_pattern(f"{CACHE_PREFIX_USER_PERMISSIONS}:*")
        count += self._cache.delete_pattern(f"{CACHE_PREFIX_ROLE_PERMISSIONS}:*")
        count += self._cache.delete_pattern(f"{CACHE_PREFIX_USER_ROLES}:*")
        count += self._cache.delete_pattern(f"{CACHE_PREFIX_ROLE_USERS}:*")
        logger.info(f"Invalidated all permission caches: count={count}")
        return count

    # ==================== 统计信息 ====================

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息
        """
        base_stats = self._cache.get_stats()
        return {
            **base_stats,
            "cache_type": "permission",
            "ttl_user": PERMISSION_CACHE_TTL,
            "ttl_role": ROLE_CACHE_TTL,
        }


# 全局单例
_permission_cache_service: Optional[PermissionCacheService] = None


def get_permission_cache_service() -> PermissionCacheService:
    """获取权限缓存服务单例"""
    global _permission_cache_service
    if _permission_cache_service is None:
        _permission_cache_service = PermissionCacheService()
    return _permission_cache_service
