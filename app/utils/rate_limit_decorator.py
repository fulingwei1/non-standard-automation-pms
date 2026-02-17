# -*- coding: utf-8 -*-
"""
速率限制装饰器工具

提供方便的装饰器，用于给特定端点添加速率限制
"""
import functools
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limiting import limiter, user_limiter, strict_limiter

logger = logging.getLogger(__name__)


def rate_limit(
    limit: Optional[str] = None,
    key_func: Optional[Callable] = None,
    per_method: bool = False,
    methods: Optional[list] = None,
):
    """
    速率限制装饰器（基于IP）
    
    Args:
        limit: 限制字符串，如 "5/minute", "100/hour"
        key_func: 自定义键提取函数
        per_method: 是否按HTTP方法分别限制
        methods: 仅限制指定的HTTP方法
    
    Example:
        @app.post("/api/v1/auth/login")
        @rate_limit("5/minute")
        async def login(...):
            pass
    """
    def decorator(func: Callable) -> Callable:
        if not settings.RATE_LIMIT_ENABLED:
            return func
        
        actual_limit = limit or settings.RATE_LIMIT_DEFAULT
        # 直接应用 slowapi 装饰器，要求端点函数自身包含 response: Response 参数
        return limiter.limit(actual_limit, key_func=key_func, per_method=per_method, methods=methods)(func)
    
    return decorator


def user_rate_limit(
    limit: Optional[str] = None,
    per_method: bool = False,
    methods: Optional[list] = None,
):
    """
    基于用户的速率限制装饰器
    
    优先使用用户ID，未认证用户使用IP地址
    适用于需要区分用户行为的场景
    
    Example:
        @app.post("/api/v1/data/batch-import")
        @user_rate_limit("10/minute")
        async def batch_import(...):
            pass
    """
    def decorator(func: Callable) -> Callable:
        if not settings.RATE_LIMIT_ENABLED:
            return func
        
        actual_limit = limit or settings.RATE_LIMIT_DEFAULT
        return user_limiter.limit(actual_limit, per_method=per_method, methods=methods)(func)
    
    return decorator


def strict_rate_limit(
    limit: Optional[str] = None,
    per_method: bool = False,
    methods: Optional[list] = None,
):
    """
    严格速率限制装饰器（IP + 用户组合）
    
    同时限制IP和用户ID，提供最严格的保护
    适用于极其敏感的操作（密码修改、账户删除等）
    
    Example:
        @app.post("/api/v1/auth/change-password")
        @strict_rate_limit("3/hour")
        async def change_password(...):
            pass
    """
    def decorator(func: Callable) -> Callable:
        if not settings.RATE_LIMIT_ENABLED:
            return func
        
        actual_limit = limit or settings.RATE_LIMIT_DEFAULT
        return strict_limiter.limit(actual_limit, per_method=per_method, methods=methods)(func)
    
    return decorator


# 预定义的常用限制装饰器
def login_rate_limit():
    """登录端点限制：5次/分钟"""
    return rate_limit(settings.RATE_LIMIT_LOGIN)


def register_rate_limit():
    """注册端点限制：3次/小时"""
    return rate_limit(settings.RATE_LIMIT_REGISTER)


def refresh_token_rate_limit():
    """Token刷新限制：10次/分钟"""
    return user_rate_limit(settings.RATE_LIMIT_REFRESH)


def password_change_rate_limit():
    """密码修改限制：3次/小时（严格模式）"""
    return strict_rate_limit(settings.RATE_LIMIT_PASSWORD_CHANGE)


def delete_rate_limit():
    """删除操作限制：20次/分钟"""
    return user_rate_limit(settings.RATE_LIMIT_DELETE)


def batch_operation_rate_limit():
    """批量操作限制：10次/分钟"""
    return user_rate_limit(settings.RATE_LIMIT_BATCH)


__all__ = [
    "rate_limit",
    "user_rate_limit",
    "strict_rate_limit",
    "login_rate_limit",
    "register_rate_limit",
    "refresh_token_rate_limit",
    "password_change_rate_limit",
    "delete_rate_limit",
    "batch_operation_rate_limit",
]
