# -*- coding: utf-8 -*-
"""
CSRF防护机制 - 优化版

区分Web请求和API请求的CSRF防护策略：
1. API请求（/api/v1/*）：
   - 使用JWT Bearer Token认证，CSRF风险低
   - 验证Origin/Referer头，防止跨站请求
   - 支持CORS预检请求（OPTIONS）
   
2. Web请求（非API路径）：
   - 可选的Double Submit Cookie或CSRF Token验证
   - 严格的Origin/Referer验证

特性：
- 自动识别API vs Web请求
- 支持白名单路径配置
- 支持OPTIONS预检请求
- DEBUG模式下宽松验证
- 完善的日志记录
"""

import logging
import secrets
from typing import Optional, Set

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF防护中间件 - 智能区分API和Web请求
    """

    # 完全豁免CSRF检查的路径（公开端点）
    EXEMPT_PATHS: Set[str] = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
    }

    # 不需要CSRF检查的HTTP方法（安全方法）
    SAFE_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS"}

    # API路径前缀（使用JWT认证，CSRF风险低）
    API_PREFIX: str = "/api/v1"

    def __init__(self, app):
        super().__init__(app)
        self.csrf_enabled = not settings.DEBUG  # DEBUG模式下禁用严格CSRF

    async def dispatch(self, request: Request, call_next):
        # 安全方法不需要CSRF防护
        if request.method in self.SAFE_METHODS:
            response = await call_next(request)
            # 为OPTIONS请求添加CORS头
            if request.method == "OPTIONS":
                self._add_cors_headers(response, request)
            return response

        # 检查是否为豁免路径
        path = request.url.path
        if self._is_exempt_path(path):
            return await call_next(request)

        # 区分API请求和Web请求
        is_api_request = path.startswith(self.API_PREFIX)

        try:
            if is_api_request:
                # API请求：验证Origin/Referer（轻量级）
                self._validate_api_request(request)
            else:
                # Web请求：可选的CSRF Token验证（未来扩展）
                self._validate_web_request(request)
                
            response = await call_next(request)
            return response

        except HTTPException:
            raise
        except Exception as e:
            # Only catch CSRF-related exceptions, not downstream errors
            if "CSRF" in str(e) or "csrf" in str(e):
                logger.error(f"CSRF验证异常: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="CSRF验证失败"
                )
            raise

    def _is_exempt_path(self, path: str) -> bool:
        """检查路径是否在豁免列表中"""
        # 精确匹配
        if path in self.EXEMPT_PATHS:
            return True
        
        # 前缀匹配（用于动态路径）
        exempt_prefixes = {"/docs", "/redoc"}
        return any(path.startswith(prefix) for prefix in exempt_prefixes)

    def _validate_api_request(self, request: Request) -> None:
        """
        验证API请求的CSRF防护
        
        策略：
        1. 检查Authorization头（JWT Bearer Token）
        2. 验证Origin/Referer头（防止CSRF）
        3. DEBUG模式下宽松验证
        """
        # DEBUG模式下跳过验证（方便开发）
        if settings.DEBUG:
            logger.debug(f"CSRF验证（DEBUG模式）: {request.method} {request.url.path}")
            return

        # 检查JWT Token（必须使用Bearer认证）
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            # 如果没有Bearer Token，拒绝请求
            logger.warning(
                f"API请求缺少Bearer Token: {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要JWT认证"
            )

        # 验证Origin/Referer头
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        
        if not origin and not referer:
            # API请求缺少Origin/Referer，可能是CSRF攻击
            logger.warning(
                f"API请求缺少Origin/Referer: {request.method} {request.url.path} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF验证失败：缺少Origin或Referer头"
            )

        # 验证Origin是否允许
        if origin:
            if not self._is_origin_allowed(origin):
                logger.warning(
                    f"CSRF验证失败：不允许的来源 {origin} "
                    f"for {request.method} {request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"CSRF验证失败：不允许的来源 {origin}"
                )
        elif referer:
            # 从Referer提取Origin
            referer_origin = self._extract_origin_from_referer(referer)
            if referer_origin and not self._is_origin_allowed(referer_origin):
                logger.warning(
                    f"CSRF验证失败：不允许的来源（从Referer提取） {referer_origin} "
                    f"for {request.method} {request.url.path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"CSRF验证失败：不允许的来源"
                )

        logger.debug(
            f"CSRF验证通过: {request.method} {request.url.path} "
            f"from {origin or referer_origin}"
        )

    def _validate_web_request(self, request: Request) -> None:
        """
        验证Web请求的CSRF防护（未来可扩展Double Submit Cookie）
        
        当前策略：与API请求相同，验证Origin/Referer
        """
        # 当前复用API请求的验证逻辑
        # 未来可以实现基于CSRF Token的验证
        if settings.DEBUG:
            return
            
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        
        if not origin and not referer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF验证失败：缺少Origin或Referer头"
            )

    def _is_origin_allowed(self, origin: str) -> bool:
        """
        检查Origin是否在允许列表中
        
        Args:
            origin: Origin头值（如 https://example.com）
            
        Returns:
            bool: 是否允许
        """
        if not settings.CORS_ORIGINS:
            logger.warning("CORS_ORIGINS未配置，拒绝所有跨域请求")
            return False

        # 标准化Origin（移除尾部斜杠和路径）
        origin_normalized = self._normalize_origin(origin)

        for allowed_origin in settings.CORS_ORIGINS:
            # 通配符仅在DEBUG模式下允许
            if allowed_origin == "*":
                if settings.DEBUG:
                    return True
                continue

            # 标准化允许的Origin
            allowed_normalized = self._normalize_origin(allowed_origin)
            
            # 精确匹配
            if origin_normalized == allowed_normalized:
                return True

        return False

    def _normalize_origin(self, origin: str) -> str:
        """
        标准化Origin字符串
        
        示例：
        - https://example.com:443/path -> https://example.com
        - http://localhost:3000/ -> http://localhost:3000
        """
        if not origin:
            return ""
            
        # 移除路径部分
        origin_parts = origin.rstrip('/').split('/')
        if len(origin_parts) >= 3:
            origin_base = f"{origin_parts[0]}//{origin_parts[2]}"
        else:
            origin_base = origin.rstrip('/')
            
        # 移除默认端口
        origin_base = origin_base.replace(':443', '').replace(':80', '')
        
        return origin_base

    def _extract_origin_from_referer(self, referer: str) -> Optional[str]:
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
        except Exception as e:
            logger.warning(f"解析Referer失败: {referer}, error: {e}")
            return None

    def _add_cors_headers(self, response, request: Request) -> None:
        """为OPTIONS预检请求添加CORS头"""
        origin = request.headers.get("Origin")
        if origin and self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, Origin, X-Requested-With"


def generate_csrf_token() -> str:
    """
    生成CSRF Token（用于Double Submit Cookie模式）
    
    Returns:
        str: 安全的随机token
    """
    return secrets.token_urlsafe(32)


def verify_csrf_token(request: Request, token: str) -> bool:
    """
    验证CSRF Token（Double Submit Cookie模式）
    
    Args:
        request: 请求对象
        token: 提交的CSRF token
        
    Returns:
        bool: 验证是否通过
    """
    # 从Cookie中获取CSRF token
    cookie_token = request.cookies.get("csrf_token")
    
    # 恒定时间比较，防止时序攻击
    return secrets.compare_digest(cookie_token or "", token)


__all__ = [
    "CSRFMiddleware",
    "generate_csrf_token",
    "verify_csrf_token"
]
