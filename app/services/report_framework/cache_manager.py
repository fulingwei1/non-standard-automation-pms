# -*- coding: utf-8 -*-
"""
报告缓存管理器

为报告框架提供缓存支持
"""

import hashlib
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ReportCacheManager:
    """
    报告缓存管理器

    负责报告数据的缓存管理，提高报告生成性能
    """

    def __init__(self, default_ttl: int = 300):
        """
        初始化缓存管理器

        Args:
            default_ttl: 默认缓存过期时间（秒），默认5分钟
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, Any] = {}
        
        # 尝试使用Redis缓存
        try:
            from app.services.cache.redis_cache import get_cache
            self.redis_cache = get_cache()
            self.use_redis = self.redis_cache.is_available()
            if self.use_redis:
                logger.info("报告缓存管理器使用Redis缓存")
            else:
                logger.warning("Redis不可用，报告缓存管理器使用内存缓存")
        except Exception as e:
            logger.warning(f"无法初始化Redis缓存: {e}，使用内存缓存")
            self.redis_cache = None
            self.use_redis = False

    def _generate_key(self, report_code: str, params: Dict[str, Any]) -> str:
        """
        生成缓存键

        Args:
            report_code: 报告代码
            params: 报告参数

        Returns:
            str: 缓存键
        """
        # 将参数序列化并生成哈希值
        params_str = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:16]
        return f"report:{report_code}:{params_hash}"

    def get(self, report_code: str, params: Dict[str, Any]) -> Optional[Any]:
        """
        获取缓存的报告数据

        Args:
            report_code: 报告代码
            params: 报告参数

        Returns:
            Any: 缓存的报告数据，不存在返回None
        """
        key = self._generate_key(report_code, params)
        
        if self.use_redis:
            try:
                return self.redis_cache.get(key)
            except Exception as e:
                logger.error(f"从Redis获取报告缓存失败: {e}")
                return None
        else:
            return self._cache.get(key)

    def set(
        self,
        report_code: str,
        params: Dict[str, Any],
        data: Any,
        ttl: Optional[int] = None,
    ):
        """
        设置报告数据缓存

        Args:
            report_code: 报告代码
            params: 报告参数
            data: 报告数据
            ttl: 缓存过期时间（秒），None则使用默认值
        """
        key = self._generate_key(report_code, params)
        ttl = ttl or self.default_ttl
        
        if self.use_redis:
            try:
                self.redis_cache.set(key, data, expire=ttl)
            except Exception as e:
                logger.error(f"设置Redis报告缓存失败: {e}")
        else:
            self._cache[key] = data
            # 内存缓存不支持过期时间，需要手动管理

    def invalidate(self, report_code: str, params: Optional[Dict[str, Any]] = None):
        """
        使报告缓存失效

        Args:
            report_code: 报告代码
            params: 报告参数，None则清除该报告的所有缓存
        """
        if params is None:
            # 清除该报告的所有缓存
            pattern = f"report:{report_code}:*"
            if self.use_redis:
                try:
                    self.redis_cache.clear_pattern(pattern)
                except Exception as e:
                    logger.error(f"清除Redis报告缓存失败: {e}")
            else:
                # 清除内存缓存中的匹配项
                prefix = f"report:{report_code}:"
                keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self._cache[key]
        else:
            # 清除特定参数的缓存
            key = self._generate_key(report_code, params)
            if self.use_redis:
                try:
                    self.redis_cache.delete(key)
                except Exception as e:
                    logger.error(f"删除Redis报告缓存失败: {e}")
            else:
                self._cache.pop(key, None)

    def clear_all(self):
        """清除所有报告缓存"""
        if self.use_redis:
            try:
                self.redis_cache.clear_pattern("report:*")
            except Exception as e:
                logger.error(f"清除所有Redis报告缓存失败: {e}")
        else:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        if self.use_redis:
            return {
                "type": "redis",
                "available": self.redis_cache.is_available(),
            }
        else:
            return {
                "type": "memory",
                "size": len(self._cache),
            }
