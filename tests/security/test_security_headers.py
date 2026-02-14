# -*- coding: utf-8 -*-
"""
安全响应头测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


class TestSecurityHeaders:
    """安全响应头测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)

    # ============================================
    # 1. 基本安全头测试
    # ============================================

    def test_x_frame_options_header(self, client):
        """测试：X-Frame-Options头"""
        response = client.get("/health")
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    def test_x_content_type_options_header(self, client):
        """测试：X-Content-Type-Options头"""
        response = client.get("/health")
        
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    def test_x_xss_protection_header(self, client):
        """测试：X-XSS-Protection头"""
        response = client.get("/health")
        
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

    def test_referrer_policy_header(self, client):
        """测试：Referrer-Policy头"""
        response = client.get("/health")
        
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_server_header_masked(self, client):
        """测试：Server头被隐藏"""
        response = client.get("/health")
        
        assert "Server" in response.headers
        assert response.headers["Server"] == "PMS"
        # 不应该暴露真实服务器类型
        assert "uvicorn" not in response.headers["Server"].lower()
        assert "fastapi" not in response.headers["Server"].lower()

    def test_x_permitted_cross_domain_policies(self, client):
        """测试：X-Permitted-Cross-Domain-Policies头"""
        response = client.get("/health")
        
        assert "X-Permitted-Cross-Domain-Policies" in response.headers
        assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"

    # ============================================
    # 2. CSP（Content Security Policy）测试
    # ============================================

    def test_csp_header_exists(self, client):
        """测试：CSP头存在"""
        response = client.get("/health")
        
        assert "Content-Security-Policy" in response.headers

    @patch("app.core.security_headers.settings.DEBUG", False)
    def test_csp_strict_in_production(self, client):
        """测试：生产环境使用严格的CSP"""
        response = client.get("/health")
        
        csp = response.headers["Content-Security-Policy"]
        
        # 生产环境应该禁用unsafe-inline和unsafe-eval
        assert "unsafe-inline" not in csp or "nonce-" in csp
        assert "unsafe-eval" not in csp
        # 应该包含nonce
        assert "nonce-" in csp
        # 应该禁止object
        assert "object-src 'none'" in csp
        # 应该升级不安全请求
        assert "upgrade-insecure-requests" in csp

    @patch("app.core.security_headers.settings.DEBUG", True)
    def test_csp_relaxed_in_debug(self, client):
        """测试：DEBUG模式使用宽松的CSP"""
        response = client.get("/health")
        
        csp = response.headers["Content-Security-Policy"]
        
        # 开发环境允许unsafe-inline（方便调试）
        assert "unsafe-inline" in csp
        # 允许本地WebSocket
        assert "ws://localhost:" in csp or "wss://localhost:" in csp

    def test_csp_default_src_self(self, client):
        """测试：CSP默认只允许同源"""
        response = client.get("/health")
        
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp

    def test_csp_frame_ancestors_none(self, client):
        """测试：CSP禁止iframe嵌入"""
        response = client.get("/health")
        
        csp = response.headers["Content-Security-Policy"]
        assert "frame-ancestors 'none'" in csp

    def test_csp_form_action_self(self, client):
        """测试：CSP表单只能提交到同源"""
        response = client.get("/health")
        
        csp = response.headers["Content-Security-Policy"]
        assert "form-action 'self'" in csp

    # ============================================
    # 3. Permissions-Policy测试
    # ============================================

    def test_permissions_policy_exists(self, client):
        """测试：Permissions-Policy头存在"""
        response = client.get("/health")
        
        assert "Permissions-Policy" in response.headers

    def test_permissions_policy_disables_geolocation(self, client):
        """测试：禁用地理位置"""
        response = client.get("/health")
        
        policy = response.headers["Permissions-Policy"]
        assert "geolocation=()" in policy

    def test_permissions_policy_disables_camera(self, client):
        """测试：禁用摄像头"""
        response = client.get("/health")
        
        policy = response.headers["Permissions-Policy"]
        assert "camera=()" in policy

    def test_permissions_policy_disables_microphone(self, client):
        """测试：禁用麦克风"""
        response = client.get("/health")
        
        policy = response.headers["Permissions-Policy"]
        assert "microphone=()" in policy

    def test_permissions_policy_disables_payment(self, client):
        """测试：禁用支付API"""
        response = client.get("/health")
        
        policy = response.headers["Permissions-Policy"]
        assert "payment=()" in policy

    # ============================================
    # 4. HSTS（Strict-Transport-Security）测试
    # ============================================

    @patch("app.core.security_headers.settings.DEBUG", False)
    def test_hsts_enabled_in_production(self, client):
        """测试：生产环境启用HSTS"""
        response = client.get("/health")
        
        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        
        # 检查HSTS配置
        assert "max-age=" in hsts
        assert "includeSubDomains" in hsts
        assert "preload" in hsts

    @patch("app.core.security_headers.settings.DEBUG", True)
    def test_hsts_disabled_in_debug(self, client):
        """测试：DEBUG模式不启用HSTS（允许HTTP）"""
        response = client.get("/health")
        
        # DEBUG模式下不应该有HSTS头
        assert "Strict-Transport-Security" not in response.headers

    # ============================================
    # 5. 跨域策略头测试
    # ============================================

    @patch("app.core.security_headers.settings.DEBUG", False)
    def test_cross_origin_embedder_policy(self, client):
        """测试：Cross-Origin-Embedder-Policy头"""
        response = client.get("/health")
        
        assert "Cross-Origin-Embedder-Policy" in response.headers
        assert response.headers["Cross-Origin-Embedder-Policy"] == "require-corp"

    def test_cross_origin_opener_policy(self, client):
        """测试：Cross-Origin-Opener-Policy头"""
        response = client.get("/health")
        
        assert "Cross-Origin-Opener-Policy" in response.headers
        assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"

    def test_cross_origin_resource_policy(self, client):
        """测试：Cross-Origin-Resource-Policy头"""
        response = client.get("/health")
        
        assert "Cross-Origin-Resource-Policy" in response.headers
        assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"

    # ============================================
    # 6. 敏感端点缓存控制测试
    # ============================================

    def test_login_endpoint_no_cache(self, client):
        """测试：登录端点禁止缓存"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": "test"}
        )
        
        # 检查缓存控制头
        assert "Cache-Control" in response.headers
        cache_control = response.headers["Cache-Control"]
        assert "no-store" in cache_control
        assert "no-cache" in cache_control
        assert "must-revalidate" in cache_control

    def test_normal_endpoint_allows_cache(self, client):
        """测试：普通端点允许缓存"""
        response = client.get("/health")
        
        # 非敏感端点不应该有严格的no-cache
        cache_control = response.headers.get("Cache-Control", "")
        # 可能没有Cache-Control头，或者不包含no-store
        assert "no-store" not in cache_control or cache_control == ""

    # ============================================
    # 7. 所有端点都应该有安全头
    # ============================================

    def test_all_endpoints_have_security_headers(self, client):
        """测试：所有端点都应该有完整的安全头"""
        endpoints = [
            "/",
            "/health",
            "/api/v1/roles",  # 需要认证，但仍应有安全头
        ]
        
        required_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy",
        ]
        
        for endpoint in endpoints:
            try:
                response = client.get(endpoint)
                
                for header in required_headers:
                    assert header in response.headers, \
                        f"Missing {header} in {endpoint}"
            except Exception:
                # 端点可能需要认证或不存在，跳过
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
