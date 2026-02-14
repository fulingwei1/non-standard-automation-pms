# -*- coding: utf-8 -*-
"""
CSRF防护机制

对于REST API使用JWT认证的典型场景，CSRF防护重点：
1. 验证Origin/Referer头（防止跨站请求）
2. 可选的CSRF Token机制（用于需要额外保护的端点）
3. 确保SameSite Cookie属性（如果使用cookie）

注：由于本系统使用JWT Bearer Token认证，CSRF风险相对较低。
此模块主要用于双重验证Origin头，为state-changing操作提供额外保护。
"""

from typing import Optional, Union

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF防护中间件

    验证state-changing请求的Origin/Referer头
    """

    # 不需要CSRF检查的路径（如健康检查、公开API）
    EXEMPT_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/api/v1/auth/login",
        "/api/v1/openapi.json",
    }

    # 允许的HTTP方法（通常不需要CSRF防护）
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

    async def dispatch(self, request: Request, call_next):
        # GET请求通常不需要CSRF防护
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # 检查是否为豁免路径
        path = request.url.path
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        # 获取Origin和Referer头
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")

        # 检查Origin或Referer是否允许
        self._validate_origin_or_referer(origin, referer, request)

        return await call_next(request)

    def _validate_origin_or_referer(
        self, origin: Optional[str], referer: Optional[str], request: Request
    ) -> None:
        """
        验证Origin或Referer头是否在允许的来源列表中

        Args:
            origin: Origin头
            referer: Referer头
            request: 当前请求对象

        Raises:
            HTTPException: 如果Origin/Referer无效
        """
        # 在DEBUG模式下，跳过严格验证以便本地测试
        if settings.DEBUG:
            return

        # 如果没有Origin和Referer，拒绝请求
        if not origin and not referer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF验证失败：缺少Origin或Referer头",
            )

        # 优先检查Origin头（更可靠）
        if origin:
            if not self._is_origin_allowed(origin):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"CSRF验证失败：不允许的来源 {origin}",
                )
        else:
            # 如果没有Origin，检查Referer
            if referer:
                referer_origin = self._extract_origin_from_referer(referer)
                if referer_origin and not self._is_origin_allowed(referer_origin):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"CSRF验证失败：不允许的来源 {referer_origin}",
                    )

    def _is_origin_allowed(self, origin: str) -> bool:
        """
        检查Origin是否在允许的列表中

        Args:
            origin: Origin头值

        Returns:
            bool: 是否允许
        """
        if not settings.CORS_ORIGINS:
            return False

        # 移除路径部分，只比较协议+域名+端口
        origin_parts = origin.split("/")
        if len(origin_parts) >= 3:
            origin_base = f"{origin_parts[0]}//{origin_parts[2]}"
        else:
            origin_base = origin

        # 检查是否在CORS允许的来源中
        for allowed_origin in settings.CORS_ORIGINS:
            # 通配符仅在 DEBUG 模式下允许（开发环境）
            if allowed_origin == "*":
                if settings.DEBUG:
                    return True
                continue

            # 精确匹配
            if origin_base == allowed_origin:
                return True

        return False

    def _extract_origin_from_referer(self, referer: str) -> Union[str, None]:
        """
        从Referer头提取Origin

        Args:
            referer: Referer头值

        Returns:
            提取的Origin，或None
        """
        if not referer:
            return None

        try:
            from urllib.parse import urlparse

            parsed = urlparse(referer)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            return None


def get_csrf_exempt_decorator():
    """
    获取CSRF豁免装饰器（用于特殊端点）

    注意：此装饰器仅在使用CSRF中间件时需要
    """
    # 由于CSRF中间件基于路径豁免，此处仅为占位符
    # 未来可能实现基于token的CSRF防护
    pass


__all__ = ["CSRFMiddleware", "get_csrf_exempt_decorator"]
