# -*- coding: utf-8 -*-
"""
安全机制集成测试

测试各种安全机制的协同工作
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


class TestSecurityIntegration:
    """安全机制集成测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """认证头"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        if response.status_code == 200:
            token = response.json()["data"]["access_token"]
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        return {"Content-Type": "application/json"}

    # ============================================
    # 1. 完整的API请求流程测试
    # ============================================

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_complete_api_request_flow(self, client, auth_headers):
        """测试：完整的API请求流程（认证+CSRF+安全头）"""
        headers = {
            **auth_headers,
            "Origin": "https://app.example.com"
        }
        
        response = client.get("/api/v1/roles", headers=headers)
        
        # 请求应该成功（或因权限失败，但不是CSRF失败）
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")
        
        # 响应应该有完整的安全头
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "Content-Security-Policy" in response.headers

    # ============================================
    # 2. 多层安全防护测试
    # ============================================

    def test_layered_security_defense(self, client):
        """测试：多层安全防护"""
        # 1. 没有认证头
        response = client.put(
            "/api/v1/roles/1/permissions",
            json={"permission_ids": [1, 2, 3]}
        )
        # 应该在认证层被拦截
        assert response.status_code in [401, 403]

    @patch("app.core.csrf.settings.DEBUG", False)
    def test_csrf_after_authentication(self, client, auth_headers):
        """测试：通过认证后仍然检查CSRF"""
        # 有JWT Token，但没有Origin
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=auth_headers,
            json={"permission_ids": [1, 2, 3]}
        )
        
        # 应该在CSRF层被拦截
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    # ============================================
    # 3. 安全头在所有响应中测试
    # ============================================

    def test_security_headers_on_error_responses(self, client):
        """测试：错误响应也应该有安全头"""
        # 404错误
        response = client.get("/nonexistent")
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers
        
        # 401错误
        response = client.get("/api/v1/roles")
        assert "X-Frame-Options" in response.headers

    def test_security_headers_on_success_responses(self, client):
        """测试：成功响应有安全头"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers

    # ============================================
    # 4. 不同端点的安全策略测试
    # ============================================

    def test_public_endpoint_security(self, client):
        """测试：公开端点的安全策略"""
        response = client.get("/health")
        
        # 公开端点仍应该有安全头
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_auth_endpoint_security(self, client):
        """测试：认证端点的安全策略"""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": "test"}
        )
        
        # 认证端点应该有安全头
        assert "X-Frame-Options" in response.headers
        
        # 认证端点应该禁止缓存
        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_protected_endpoint_security(self, client, auth_headers):
        """测试：受保护端点的安全策略"""
        headers = {
            **auth_headers,
            "Origin": "https://app.example.com"
        }
        
        response = client.get("/api/v1/roles", headers=headers)
        
        # 受保护端点需要：认证 + CSRF验证 + 安全头
        assert "X-Frame-Options" in response.headers
        # 不应该因CSRF失败
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    # ============================================
    # 5. 速率限制测试（如果配置了）
    # ============================================

    @pytest.mark.skip(reason="需要Redis支持")
    def test_rate_limiting(self, client):
        """测试：速率限制"""
        # 快速发送大量请求
        for i in range(100):
            response = client.get("/health")
            if response.status_code == 429:
                # 触发速率限制
                assert "rate limit" in response.json().get("detail", "").lower()
                return
        
        # 如果没有触发，可能是速率限制未配置
        pytest.skip("Rate limiting not configured or threshold too high")

    # ============================================
    # 6. 跨域请求测试
    # ============================================

    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_cors_allowed_origin(self, client, auth_headers):
        """测试：允许的跨域请求"""
        headers = {
            **auth_headers,
            "Origin": "https://app.example.com"
        }
        
        response = client.options("/api/v1/roles", headers=headers)
        
        # CORS预检请求应该成功
        assert response.status_code in [200, 204]

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_cors_blocked_origin(self, client, auth_headers):
        """测试：拒绝的跨域请求"""
        headers = {
            **auth_headers,
            "Origin": "https://evil.com"
        }
        
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=headers,
            json={"permission_ids": [1, 2, 3]}
        )
        
        # 应该被CSRF防护拦截
        assert response.status_code == 403

    # ============================================
    # 7. 环境差异测试
    # ============================================

    @patch("app.core.security_headers.settings.DEBUG", True)
    def test_debug_mode_relaxed_security(self, client):
        """测试：DEBUG模式的宽松安全策略"""
        response = client.get("/health")
        
        csp = response.headers["Content-Security-Policy"]
        
        # DEBUG模式允许unsafe-inline（方便开发）
        assert "unsafe-inline" in csp
        
        # DEBUG模式不应该有HSTS
        assert "Strict-Transport-Security" not in response.headers

    @patch("app.core.security_headers.settings.DEBUG", False)
    def test_production_mode_strict_security(self, client):
        """测试：生产模式的严格安全策略"""
        response = client.get("/health")
        
        csp = response.headers["Content-Security-Policy"]
        
        # 生产模式应该有nonce或禁用unsafe-inline
        assert "nonce-" in csp or "unsafe-inline" not in csp
        
        # 生产模式应该有HSTS
        assert "Strict-Transport-Security" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
