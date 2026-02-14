# -*- coding: utf-8 -*-
"""
安全HTTP响应头中间件 - 优化版

防止常见的Web安全攻击：
- Clickjacking（X-Frame-Options）
- MIME类型混淆（X-Content-Type-Options）
- XSS（Content-Security-Policy）
- 中间人攻击（Strict-Transport-Security）
- 信息泄露（Referrer-Policy, Server隐藏）
- 浏览器功能滥用（Permissions-Policy）

优化特性：
- 严格的CSP策略（生产环境）
- 完善的安全头配置
- 区分开发/生产环境
- CSP nonce支持（防XSS）
- 敏感端点缓存控制
"""

import secrets
from typing import Optional

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全HTTP响应头中间件
    
    为所有响应添加标准的安全响应头
    """

    # 敏感端点（不应被缓存）
    SENSITIVE_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/users/me",
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 生成CSP nonce（用于内联脚本）
        csp_nonce = secrets.token_urlsafe(16)
        
        # 添加安全响应头
        self._add_security_headers(response, request, csp_nonce)
        
        # 敏感路径的缓存控制
        if request.url.path in self.SENSITIVE_PATHS:
            self._add_no_cache_headers(response)
        
        return response

    def _add_security_headers(self, response, request: Request, csp_nonce: str) -> None:
        """添加所有安全响应头"""
        
        # ============================================
        # 1. X-Frame-Options - 防止点击劫持
        # ============================================
        # DENY: 不允许在任何iframe中嵌入
        # SAMEORIGIN: 只允许同源iframe
        response.headers["X-Frame-Options"] = "DENY"
        
        # ============================================
        # 2. X-Content-Type-Options - 防止MIME类型混淆
        # ============================================
        # nosniff: 浏览器不会尝试猜测文件类型
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # ============================================
        # 3. X-XSS-Protection - XSS保护（旧版浏览器）
        # ============================================
        # 现代浏览器依赖CSP，但保留兼容性
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # ============================================
        # 4. Content-Security-Policy - 内容安全策略
        # ============================================
        csp = self._build_csp_policy(csp_nonce)
        response.headers["Content-Security-Policy"] = csp
        
        # ============================================
        # 5. Referrer-Policy - 推荐人策略
        # ============================================
        # strict-origin-when-cross-origin: 跨域时只发送origin，同源发送完整URL
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # ============================================
        # 6. Permissions-Policy - 权限策略（替代Feature-Policy）
        # ============================================
        permissions_policy = self._build_permissions_policy()
        response.headers["Permissions-Policy"] = permissions_policy
        
        # ============================================
        # 7. Strict-Transport-Security - 强制HTTPS
        # ============================================
        if not settings.DEBUG:
            # 仅在生产环境启用HSTS
            # max-age=31536000: 1年
            # includeSubDomains: 应用于所有子域名
            # preload: 允许浏览器预加载HSTS
            hsts = "max-age=31536000; includeSubDomains; preload"
            response.headers["Strict-Transport-Security"] = hsts
        
        # ============================================
        # 8. Server - 隐藏服务器信息
        # ============================================
        # 不暴露服务器类型和版本
        response.headers["Server"] = "PMS"
        
        # ============================================
        # 9. X-Permitted-Cross-Domain-Policies - 跨域策略
        # ============================================
        # none: 不允许Flash/PDF等跨域访问
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
        # ============================================
        # 10. Cross-Origin-Embedder-Policy - 跨域嵌入策略
        # ============================================
        # require-corp: 要求跨域资源设置CORP头
        if not settings.DEBUG:
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        
        # ============================================
        # 11. Cross-Origin-Opener-Policy - 跨域打开策略
        # ============================================
        # same-origin: 仅允许同源窗口访问
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        
        # ============================================
        # 12. Cross-Origin-Resource-Policy - 跨域资源策略
        # ============================================
        # same-origin: 仅允许同源访问
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

    def _build_csp_policy(self, nonce: str) -> str:
        """
        构建Content Security Policy
        
        Args:
            nonce: CSP nonce值（用于内联脚本）
            
        Returns:
            str: CSP策略字符串
        """
        if settings.DEBUG:
            # ============================================
            # 开发环境CSP（宽松）
            # ============================================
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # 允许内联和eval（调试用）
                "style-src 'self' 'unsafe-inline'",  # 允许内联样式
                "img-src 'self' data: https: blob:",  # 允许data URL和HTTPS图片
                "font-src 'self' data:",  # 允许字体
                "connect-src 'self' ws://localhost:* wss://localhost:* http://localhost:* https://localhost:*",  # 允许本地WebSocket
                "frame-ancestors 'none'",  # 禁止嵌入iframe
                "form-action 'self'",  # 表单只能提交到同源
                "base-uri 'self'",  # 限制<base>标签
            ]
        else:
            # ============================================
            # 生产环境CSP（严格）
            # ============================================
            # 构建CORS origins用于connect-src
            cors_origins = " ".join(settings.CORS_ORIGINS) if settings.CORS_ORIGINS else "'self'"
            
            csp_directives = [
                "default-src 'self'",
                f"script-src 'self' 'nonce-{nonce}'",  # 只允许nonce标记的脚本
                f"style-src 'self' 'nonce-{nonce}'",  # 只允许nonce标记的样式
                "img-src 'self' data: https:",  # 允许HTTPS图片
                "font-src 'self' data:",
                f"connect-src 'self' {cors_origins}",  # 允许配置的CORS来源
                "frame-ancestors 'none'",  # 禁止嵌入iframe
                "form-action 'self'",
                "base-uri 'self'",
                "object-src 'none'",  # 禁止<object>、<embed>、<applet>
                "media-src 'self'",  # 音视频只能来自同源
                "worker-src 'self'",  # Web Worker只能来自同源
                "manifest-src 'self'",  # PWA manifest只能来自同源
                "frame-src 'none'",  # 禁止iframe
                "upgrade-insecure-requests",  # 自动升级HTTP到HTTPS
            ]
        
        return "; ".join(csp_directives)

    def _build_permissions_policy(self) -> str:
        """
        构建Permissions Policy（替代Feature-Policy）
        
        Returns:
            str: Permissions Policy字符串
        """
        # 禁用所有不必要的浏览器功能和API
        policies = [
            "geolocation=()",  # 禁用地理位置
            "microphone=()",  # 禁用麦克风
            "camera=()",  # 禁用摄像头
            "payment=()",  # 禁用支付API
            "usb=()",  # 禁用USB
            "magnetometer=()",  # 禁用磁力计
            "gyroscope=()",  # 禁用陀螺仪
            "accelerometer=()",  # 禁用加速度计
            "ambient-light-sensor=()",  # 禁用环境光传感器
            "autoplay=()",  # 禁用自动播放
            "encrypted-media=()",  # 禁用加密媒体
            "fullscreen=(self)",  # 全屏只允许同源
            "picture-in-picture=()",  # 禁用画中画
            "screen-wake-lock=()",  # 禁用屏幕唤醒锁
            "web-share=()",  # 禁用Web分享
        ]
        
        return ", ".join(policies)

    def _add_no_cache_headers(self, response) -> None:
        """为敏感端点添加禁止缓存头"""
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"


def setup_security_headers(app: FastAPI) -> None:
    """
    配置安全响应头中间件
    
    Args:
        app: FastAPI应用实例
    """
    # 添加安全响应头中间件
    # 注意：必须在CORS中间件之后添加，以确保CORS头不被覆盖
    app.add_middleware(SecurityHeadersMiddleware)


__all__ = [
    "SecurityHeadersMiddleware",
    "setup_security_headers"
]
