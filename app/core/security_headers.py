# -*- coding: utf-8 -*-
"""
安全HTTP响应头中间件

防止常见的Web安全攻击：
- Clickjacking（X-Frame-Options）
- MIME类型混淆（X-Content-Type-Options）
- XSS（Content-Security-Policy）
- 简单的跨域脚本（Strict-Transport-Security）
- 反射型XSS（X-XSS-Protection）
- 信息泄露（Referrer-Policy）
"""

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全HTTP响应头中间件

    为所有响应添加标准的安全响应头
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 防止点击劫持 - 不允许在iframe中嵌入
        response.headers["X-Frame-Options"] = "DENY"

        # 防止MIME类型混淆 - 浏览器不会尝试猜测文件类型
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS保护 - 启用浏览器内置的XSS过滤器
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 内容安全策略 - 限制可以加载的资源
        # 根据DEBUG模式调整CSP严格程度
        if settings.DEBUG:
            # 开发环境：允许eval和inline脚本用于调试
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' ws://localhost:* wss://localhost:*; "
                "frame-ancestors 'none'; "
                "form-action 'self';"
            )
        else:
            # 生产环境：严格的CSP策略
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'nonce-{nonce}'; "
                "style-src 'self' 'nonce-{nonce}'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' {cors_origins}; "
                "frame-ancestors 'none'; "
                "form-action 'self'; "
                "object-src 'none'; "
                "base-uri 'self';"
            )

        response.headers["Content-Security-Policy"] = csp

        # 推荐人策略 - 限制Referer头泄露敏感信息
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略 - 控制浏览器功能和API访问
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy

        # 严格传输安全（仅HTTPS）- 生产环境启用
        if not settings.DEBUG:
            # max-age=31536000秒 = 1年
            # includeSubDomains - 应用于所有子域名
            # preload - 允许浏览器预加载HSTS
            hsts = "max-age=31536000; includeSubDomains; preload"
            response.headers["Strict-Transport-Security"] = hsts

        # 服务器信息隐藏 - 不暴露服务器版本
        response.headers["Server"] = "PMS"

        # 缓存控制 - 防止敏感数据被缓存
        if request.url.path in ["/api/v1/auth/login", "/api/v1/auth/refresh"]:
            # 登录相关的响应不应被缓存
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


def setup_security_headers(app: FastAPI) -> None:
    """
    配置安全响应头中间件

    Args:
        app: FastAPI应用实例
    """
    # 添加安全响应头中间件（必须在CORS中间件之后）
    app.add_middleware(SecurityHeadersMiddleware)

    # 确保CORS配置正确（已在main.py中配置）
    # 生产环境应限制允许的来源、方法和头部
    if settings.DEBUG:
        # 开发环境：允许更多来源用于调试
        pass
    else:
        # 生产环境：严格的CORS配置
        # 确保CORS_ORIGINS只包含信任的域名
        pass


__all__ = ["SecurityHeadersMiddleware", "setup_security_headers"]
