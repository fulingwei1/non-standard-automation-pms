# -*- coding: utf-8 -*-
"""
Redis客户端工具
"""

import logging
from typing import Optional

import redis
from redis.exceptions import ConnectionError, RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局Redis客户端实例
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    获取Redis客户端实例

    Returns:
        Redis客户端实例，如果Redis未配置或连接失败则返回None
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    if not settings.REDIS_URL:
        logger.warning("Redis未配置，Token黑名单将使用内存存储（重启后失效）")
        return None

    try:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        # 测试连接
        _redis_client.ping()
        logger.info("Redis连接成功")
        return _redis_client
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis连接失败: {e}，Token黑名单将使用内存存储（重启后失效）")
        _redis_client = None
        return None


def close_redis_client():
    """关闭Redis连接"""
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
        except Exception as e:
            logger.error(f"关闭Redis连接时出错: {e}")
        finally:
            _redis_client = None


