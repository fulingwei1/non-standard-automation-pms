# -*- coding: utf-8 -*-
"""
API 速率限制核心逻辑

实现完整的速率限制机制，防止暴力破解和DDoS攻击
支持：
- 基于IP地址的限流
- 基于用户ID的限流
- 组合策略（IP + 用户）
- Redis存储（可降级到内存）
"""
import logging
from typing import Callable, Optional

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_user_id_from_request(request: Request) -> str:
    """
    从请求中获取用户ID（用于基于用户的限流）
    
    如果用户未认证，返回IP地址
    """
    # 尝试从请求状态中获取当前用户
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    
    # 未认证用户，使用IP地址
    return f"ip:{get_remote_address(request)}"


def get_user_or_ip(request: Request) -> str:
    """
    组合策略：优先使用用户ID，否则使用IP
    
    这是推荐的策略，既能防止用户滥用，也能防止未认证的攻击
    """
    return get_user_id_from_request(request)


def get_ip_and_user(request: Request) -> str:
    """
    严格组合策略：同时限制IP和用户
    
    用于极其敏感的操作（如密码修改、账户删除）
    """
    ip = get_remote_address(request)
    if hasattr(request.state, "user") and request.state.user:
        return f"ip:{ip}:user:{request.state.user.id}"
    return f"ip:{ip}"


def create_limiter(
    storage_uri: Optional[str] = None,
    default_limits: Optional[list] = None,
    key_func: Optional[Callable] = None,
) -> Limiter:
    """
    创建速率限制器实例
    
    Args:
        storage_uri: Redis存储URI，如果为None则使用内存存储
        default_limits: 默认限制列表，如 ["100/minute", "1000/hour"]
        key_func: 键提取函数，默认使用IP地址
    
    Returns:
        配置好的Limiter实例
    """
    if storage_uri is None:
        storage_uri = settings.RATE_LIMIT_STORAGE_URL
    
    if default_limits is None:
        default_limits = [settings.RATE_LIMIT_DEFAULT]
    
    if key_func is None:
        key_func = get_remote_address
    
    # 尝试使用Redis存储
    if storage_uri:
        try:
            limiter = Limiter(
                key_func=key_func,
                storage_uri=storage_uri,
                default_limits=default_limits,
                headers_enabled=True,  # 在响应头中包含限流信息
            )
            logger.info(f"速率限制器已启用，使用Redis存储: {storage_uri}")
            return limiter
        except Exception as e:
            logger.warning(
                f"无法连接到Redis存储 {storage_uri}，降级到内存存储: {e}"
            )
    
    # 降级到内存存储
    limiter = Limiter(
        key_func=key_func,
        default_limits=default_limits,
        headers_enabled=True,
    )
    logger.warning(
        "速率限制器使用内存存储，在分布式部署中可能不准确。"
        "建议配置Redis存储以获得准确的限流。"
    )
    return limiter


# 创建全局限制器实例
limiter = create_limiter()

# 创建基于用户的限制器
user_limiter = create_limiter(key_func=get_user_or_ip)

# 创建严格限制器（IP + 用户）
strict_limiter = create_limiter(key_func=get_ip_and_user)


def get_rate_limit_status(request: Request) -> dict:
    """
    获取当前请求的速率限制状态
    
    返回包含限制信息的字典，用于监控和调试
    """
    try:
        # 从响应头中提取限流信息
        # 这些信息由slowapi自动添加
        return {
            "limit": request.state.view_rate_limit if hasattr(request.state, "view_rate_limit") else None,
            "remaining": request.state.view_rate_limit_remaining if hasattr(request.state, "view_rate_limit_remaining") else None,
            "reset": request.state.view_rate_limit_reset if hasattr(request.state, "view_rate_limit_reset") else None,
        }
    except Exception as e:
        logger.error(f"获取速率限制状态失败: {e}")
        return {}


__all__ = [
    "limiter",
    "user_limiter", 
    "strict_limiter",
    "get_remote_address",
    "get_user_id_from_request",
    "get_user_or_ip",
    "get_ip_and_user",
    "get_rate_limit_status",
]
