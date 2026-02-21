# -*- coding: utf-8 -*-
"""
安全响应头中间件测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security_headers import SecurityHeadersMiddleware, setup_security_headers


class TestSecurityHeadersMiddleware:
    """测试安全响应头中间件"""
    
    def test_init(self):
        """测试初始化"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        assert middleware is not None
        assert isinstance(middleware, BaseHTTPMiddleware)
    
    def test_sensitive_paths(self):
        """测试敏感路径配置"""
        assert "/api/v1/auth/login" in SecurityHeadersMiddleware.SENSITIVE_PATHS
        assert "/api/v1/auth/refresh" in SecurityHeadersMiddleware.SENSITIVE_PATHS
        assert "/api/v1/auth/logout" in SecurityHeadersMiddleware.SENSITIVE_PATHS
        assert "/api/v1/users/me" in SecurityHeadersMiddleware.SENSITIVE_PATHS
    
    @pytest.mark.asyncio
    async def test_dispatch_adds_security_headers(self):
        """测试dispatch添加安全头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        # 模拟请求和响应
        request = Mock()
        request.url.path = "/api/test"
        
        response = Mock()
        response.headers = {}
        
        async def call_next(req):
            return response
        
        result = await middleware.dispatch(request, call_next)
        
        # 验证基本安全头存在
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "Content-Security-Policy" in response.headers
    
    @pytest.mark.asyncio
    async def test_dispatch_sensitive_path_no_cache(self):
        """测试敏感路径添加禁止缓存头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        request = Mock()
        request.url.path = "/api/v1/auth/login"
        
        response = Mock()
        response.headers = {}
        
        async def call_next(req):
            return response
        
        await middleware.dispatch(request, call_next)
        
        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]
        assert "Pragma" in response.headers
        assert "Expires" in response.headers


class TestAddSecurityHeaders:
    """测试_add_security_headers方法"""
    
    def test_add_security_headers_frame_options(self):
        """测试X-Frame-Options头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        request = Mock()
        
        middleware._add_security_headers(response, request, "test_nonce")
        
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_add_security_headers_content_type_options(self):
        """测试X-Content-Type-Options头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        request = Mock()
        
        middleware._add_security_headers(response, request, "test_nonce")
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
    
    def test_add_security_headers_xss_protection(self):
        """测试X-XSS-Protection头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        request = Mock()
        
        middleware._add_security_headers(response, request, "test_nonce")
        
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
    
    def test_add_security_headers_referrer_policy(self):
        """测试Referrer-Policy头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        request = Mock()
        
        middleware._add_security_headers(response, request, "test_nonce")
        
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_add_security_headers_server(self):
        """测试Server头隐藏"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        request = Mock()
        
        middleware._add_security_headers(response, request, "test_nonce")
        
        assert response.headers["Server"] == "PMS"
    
    @patch('app.core.security_headers.settings')
    def test_add_security_headers_hsts_production(self, mock_settings):
        """测试生产环境HSTS头"""
        mock_settings.DEBUG = False
        
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        request = Mock()
        
        middleware._add_security_headers(response, request, "test_nonce")
        
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    
    @patch('app.core.security_headers.settings')
    def test_add_security_headers_no_hsts_debug(self, mock_settings):
        """测试调试模式无HSTS头"""
        mock_settings.DEBUG = True
        
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        request = Mock()
        
        middleware._add_security_headers(response, request, "test_nonce")
        
        assert "Strict-Transport-Security" not in response.headers


class TestBuildCSPPolicy:
    """测试CSP策略构建"""
    
    @patch('app.core.security_headers.settings')
    def test_build_csp_debug_mode(self, mock_settings):
        """测试调试模式CSP"""
        mock_settings.DEBUG = True
        
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        csp = middleware._build_csp_policy("test_nonce")
        
        assert "default-src 'self'" in csp
        assert "'unsafe-inline'" in csp
        assert "'unsafe-eval'" in csp
    
    @patch('app.core.security_headers.settings')
    def test_build_csp_production_mode(self, mock_settings):
        """测试生产模式CSP"""
        mock_settings.DEBUG = False
        mock_settings.CORS_ORIGINS = ["https://example.com"]
        
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        csp = middleware._build_csp_policy("test_nonce")
        
        assert "default-src 'self'" in csp
        assert "'nonce-test_nonce'" in csp
        assert "'unsafe-inline'" not in csp
        assert "upgrade-insecure-requests" in csp
    
    @patch('app.core.security_headers.settings')
    def test_build_csp_contains_nonce(self, mock_settings):
        """测试CSP包含nonce"""
        mock_settings.DEBUG = False
        mock_settings.CORS_ORIGINS = []
        
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        nonce = "abc123"
        csp = middleware._build_csp_policy(nonce)
        
        assert f"'nonce-{nonce}'" in csp
    
    @patch('app.core.security_headers.settings')
    def test_build_csp_frame_ancestors(self, mock_settings):
        """测试CSP frame-ancestors指令"""
        mock_settings.DEBUG = False
        mock_settings.CORS_ORIGINS = []
        
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        csp = middleware._build_csp_policy("nonce")
        
        assert "frame-ancestors 'none'" in csp


class TestBuildPermissionsPolicy:
    """测试权限策略构建"""
    
    def test_build_permissions_policy(self):
        """测试权限策略构建"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        policy = middleware._build_permissions_policy()
        
        assert "geolocation=()" in policy
        assert "microphone=()" in policy
        assert "camera=()" in policy
        assert "payment=()" in policy
    
    def test_build_permissions_policy_fullscreen(self):
        """测试全屏权限"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        policy = middleware._build_permissions_policy()
        
        assert "fullscreen=(self)" in policy


class TestAddNoCacheHeaders:
    """测试禁止缓存头"""
    
    def test_add_no_cache_headers(self):
        """测试添加禁止缓存头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        
        middleware._add_no_cache_headers(response)
        
        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]
        assert "no-cache" in response.headers["Cache-Control"]
        assert "must-revalidate" in response.headers["Cache-Control"]
        assert "private" in response.headers["Cache-Control"]
    
    def test_add_no_cache_pragma(self):
        """测试Pragma头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        
        middleware._add_no_cache_headers(response)
        
        assert response.headers["Pragma"] == "no-cache"
    
    def test_add_no_cache_expires(self):
        """测试Expires头"""
        app = FastAPI()
        middleware = SecurityHeadersMiddleware(app)
        
        response = Mock()
        response.headers = {}
        
        middleware._add_no_cache_headers(response)
        
        assert response.headers["Expires"] == "0"


class TestSetupSecurityHeaders:
    """测试setup_security_headers函数"""
    
    def test_setup_security_headers(self):
        """测试设置安全响应头"""
        app = FastAPI()
        
        setup_security_headers(app)
        
        # 验证中间件已添加
        # FastAPI中间件存储在user_middleware中
        middleware_added = any(
            middleware.cls == SecurityHeadersMiddleware
            for middleware in app.user_middleware
        )
        
        assert middleware_added
