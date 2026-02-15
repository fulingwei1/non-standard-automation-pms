# -*- coding: utf-8 -*-
"""
速率限制中间件

在中间件级别应用速率限制，提供全局保护
"""
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limiting import limiter, get_rate_limit_status

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    速率限制中间件
    
    在中间件层面应用全局速率限制，适用于需要统一保护的场景
    注意：slowapi 本身通过装饰器和异常处理器工作，
    这个中间件主要用于：
    1. 记录速率限制事件
    2. 添加额外的限流逻辑
    3. 统一监控和日志
    """
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled and settings.RATE_LIMIT_ENABLED
        
        if self.enabled:
            logger.info("速率限制中间件已启用")
        else:
            logger.info("速率限制中间件已禁用")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并应用速率限制
        """
        if not self.enabled:
            return await call_next(request)
        
        try:
            # 记录请求信息（用于调试）
            if settings.DEBUG:
                logger.debug(
                    f"速率限制检查: {request.method} {request.url.path} "
                    f"from {request.client.host if request.client else 'unknown'}"
                )
            
            # 继续处理请求
            response = await call_next(request)
            
            # 添加速率限制状态到响应头（如果可用）
            rate_limit_info = get_rate_limit_status(request)
            if rate_limit_info.get("limit"):
                response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
            if rate_limit_info.get("remaining") is not None:
                response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
            if rate_limit_info.get("reset"):
                response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])
            
            return response
            
        except RateLimitExceeded as e:
            # 速率限制异常会被slowapi的异常处理器捕获
            # 这里我们只记录日志
            logger.warning(
                f"速率限制触发: {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            raise
        except Exception as e:
            logger.error(f"速率限制中间件错误: {e}", exc_info=True)
            # 即使中间件出错，也不影响正常请求处理
            return await call_next(request)


def setup_rate_limit_middleware(app, enabled: bool = True):
    """
    设置速率限制中间件
    
    Args:
        app: FastAPI应用实例
        enabled: 是否启用中间件
    """
    app.add_middleware(RateLimitMiddleware, enabled=enabled)
    logger.info(f"速率限制中间件已{'启用' if enabled else '禁用'}")


__all__ = ["RateLimitMiddleware", "setup_rate_limit_middleware"]
