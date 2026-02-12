# -*- coding: utf-8 -*-
"""
项目数据缓存服务（通用缓存层）

提供 Redis + 内存降级的通用缓存服务。当 Redis 不可用时自动降级到内存缓存。

缓存系统架构说明：
- 本模块 (CacheService): 通用缓存服务，支持 Redis + 内存降级。
 被 permission_cache_service 等上层服务使用。
- app.services.cache.redis_cache (RedisCache): 纯 Redis 缓存操作封装，
 被 business_cache 使用。
- app.services.cache.business_cache (BusinessCacheService): 业务层缓存封装。
- app.services.report_framework.cache_manager (ReportCacheManager): 报表框架专用缓存。
- app.services.permission_cache_service (PermissionCacheService): 权限专用缓存。

Issue 5.3: 实现项目数据的缓存机制，提升系统响应速度
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# 尝试导入Redis（可选）
try:
    import redis  # noqa: F401
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheService:
    """项目数据缓存服务"""

    def __init__(self, redis_client: Optional[Any] = None):
        """
        初始化缓存服务

        Args:
            redis_client: Redis客户端（可选，如果不提供则尝试从工具获取）
        """
        # Sprint 5.3: 完善Redis配置 - 优先使用传入的客户端，否则尝试从工具获取
        if redis_client is None:
            try:
                from app.utils.redis_client import get_redis_client
                redis_client = get_redis_client()
            except Exception as e:
                logger.warning(f"无法获取Redis客户端: {e}，将使用内存缓存")
                redis_client = None

        self.redis_client = redis_client
        self.memory_cache: Dict[str, tuple] = {}  # 内存缓存：{key: (value, expire_at)}
        self.use_redis = REDIS_AVAILABLE and redis_client is not None

        # Sprint 5.3: 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        生成缓存键

        Args:
            prefix: 键前缀
            **kwargs: 键参数

        Returns:
            str: 缓存键
        """
        # 将参数排序后序列化，确保相同参数生成相同键
        params_str = json.dumps(kwargs, sort_keys=True, default=str)
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:8]
        return f"{prefix}:{params_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值，如果不存在或已过期则返回None
        """
        if self.use_redis:
            try:
                value = self.redis_client.get(key)
                if value:
                    self.stats["hits"] += 1
                    return json.loads(value)
                else:
                    self.stats["misses"] += 1
            except Exception as e:
                # Redis失败时降级到内存缓存
                logger.warning(f"Redis获取失败，降级到内存缓存: {e}")
                self.stats["errors"] += 1

        # 内存缓存
        if key in self.memory_cache:
            value, expire_at = self.memory_cache[key]
            if expire_at is None or datetime.now() < expire_at:
                self.stats["hits"] += 1
                return value
            else:
                # 已过期，删除
                del self.memory_cache[key]
                self.stats["misses"] += 1
        else:
            self.stats["misses"] += 1

        return None

    def set(self, key: str, value: Any, expire_seconds: int = 300) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire_seconds: 过期时间（秒），默认5分钟

        Returns:
            bool: 是否设置成功
        """
        expire_at = datetime.now() + timedelta(seconds=expire_seconds) if expire_seconds > 0 else None

        if self.use_redis:
            try:
                self.redis_client.setex(
                    key,
                    expire_seconds,
                    json.dumps(value, default=str)
                )
                self.stats["sets"] += 1
                return True
            except Exception as e:
                # Redis失败时降级到内存缓存
                logger.warning(f"Redis设置失败，降级到内存缓存: {e}")
                self.stats["errors"] += 1

        # 内存缓存
        self.memory_cache[key] = (value, expire_at)
        self.stats["sets"] += 1
        return True

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            bool: 是否删除成功
        """
        deleted = False
        if self.use_redis:
            try:
                self.redis_client.delete(key)
                deleted = True
            except Exception:
                logger.debug("Redis 删除缓存失败，已忽略", exc_info=True)

        if key in self.memory_cache:
            del self.memory_cache[key]
            deleted = True

        if deleted:
            self.stats["deletes"] += 1

        return True

    def delete_pattern(self, pattern: str) -> int:
        """
        按模式删除缓存（支持通配符）

        Args:
            pattern: 模式（如 "project:*"）

        Returns:
            int: 删除的缓存数量
        """
        deleted_count = 0

        if self.use_redis:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
            except Exception:
                logger.debug("Redis 按模式删除缓存失败，已忽略", exc_info=True)

        # 内存缓存（简单实现，不支持通配符）
        keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(pattern.replace("*", ""))]
        for key in keys_to_delete:
            del self.memory_cache[key]
            deleted_count += 1

        return deleted_count

    def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            bool: 是否清空成功
        """
        if self.use_redis:
            try:
                self.redis_client.flushdb()
            except Exception:
                logger.debug("Redis flushdb 失败，已忽略", exc_info=True)

        self.memory_cache.clear()
        return True

    # ==================== 项目相关缓存方法 ====================

    def get_project_detail(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目详情缓存"""
        key = f"project:detail:{project_id}"
        return self.get(key)

    def set_project_detail(self, project_id: int, data: Dict[str, Any], expire_seconds: int = 600) -> bool:
        """设置项目详情缓存（默认10分钟）"""
        key = f"project:detail:{project_id}"
        return self.set(key, data, expire_seconds)

    def invalidate_project_detail(self, project_id: int) -> bool:
        """使项目详情缓存失效"""
        key = f"project:detail:{project_id}"
        return self.delete(key)

    def get_project_list(self, **filters) -> Optional[Dict[str, Any]]:
        """获取项目列表缓存"""
        key = self._generate_cache_key("project:list", **filters)
        return self.get(key)

    def set_project_list(self, data: Dict[str, Any], expire_seconds: int = 300, **filters) -> bool:
        """设置项目列表缓存（默认5分钟）"""
        key = self._generate_cache_key("project:list", **filters)
        return self.set(key, data, expire_seconds)

    def invalidate_project_list(self) -> int:
        """使所有项目列表缓存失效"""
        return self.delete_pattern("project:list:*")

    def get_project_statistics(self, **filters) -> Optional[Dict[str, Any]]:
        """获取项目统计缓存"""
        key = self._generate_cache_key("project:statistics", **filters)
        return self.get(key)

    def set_project_statistics(self, data: Dict[str, Any], expire_seconds: int = 600, **filters) -> bool:
        """设置项目统计缓存（默认10分钟）"""
        key = self._generate_cache_key("project:statistics", **filters)
        return self.set(key, data, expire_seconds)

    def invalidate_project_statistics(self) -> int:
        """使所有项目统计缓存失效"""
        return self.delete_pattern("project:statistics:*")

    def invalidate_all_project_cache(self) -> int:
        """使所有项目相关缓存失效"""
        return self.delete_pattern("project:*")

    # ==================== Sprint 5.3: 缓存统计和监控 ====================

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            dict: 缓存统计信息
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "deletes": self.stats["deletes"],
            "errors": self.stats["errors"],
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "cache_type": "redis" if self.use_redis else "memory",
            "memory_cache_size": len(self.memory_cache),
        }

    def reset_stats(self) -> None:
        """重置缓存统计"""
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }

    def get_redis_info(self) -> Optional[Dict[str, Any]]:
        """
        获取Redis信息（如果使用Redis）

        Returns:
            dict: Redis信息，如果不使用Redis则返回None
        """
        if not self.use_redis:
            return None

        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_keys": sum([
                    int(count) for count in info.get("db0", {}).get("keys", "0").split(",")
                ]) if "db0" in info else 0,
            }
        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return None
