# -*- coding: utf-8 -*-
"""
CSRF防护测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core.config import settings


class TestCSRFProtection:
    """CSRF防护测试"""

    @pytest.fixture
    def client(self):
        """测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """认证头（包含JWT Token）"""
        # 登录获取token
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        token = response.json()["data"]["access_token"]
        
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    # ============================================
    # 1. 安全方法（GET/HEAD/OPTIONS）测试
    # ============================================

    def test_get_request_no_csrf_check(self, client, auth_headers):
        """测试：GET请求不需要CSRF检查"""
        response = client.get(
            "/api/v1/roles",
            headers=auth_headers
        )
        # 应该成功（可能因权限失败，但不会因CSRF失败）
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    def test_options_request_allowed(self, client):
        """测试：OPTIONS预检请求应该被允许"""
        response = client.options("/api/v1/roles/1/permissions")
        # OPTIONS请求应该成功
        assert response.status_code in [200, 204, 404]

    # ============================================
    # 2. 豁免路径测试
    # ============================================

    def test_exempt_path_no_csrf_check(self, client):
        """测试：豁免路径不需要CSRF检查"""
        # 健康检查端点
        response = client.get("/health")
        assert response.status_code == 200
        
        # 登录端点
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "test", "password": "test"}
        )
        # 可能401（认证失败），但不会403（CSRF失败）
        assert response.status_code != 403

    # ============================================
    # 3. API请求CSRF验证测试
    # ============================================

    @patch("app.core.csrf.settings.DEBUG", False)
    def test_api_request_without_bearer_token(self, client):
        """测试：API请求缺少Bearer Token应该被拒绝"""
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers={
                "Content-Type": "application/json",
                "Origin": "https://app.example.com"
            },
            json={"permission_ids": [1, 2, 3]}
        )
        assert response.status_code == 401

    @patch("app.core.csrf.settings.DEBUG", False)
    def test_api_request_without_origin(self, client, auth_headers):
        """测试：API请求缺少Origin/Referer应该被拒绝（生产模式）"""
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=auth_headers,
            json={"permission_ids": [1, 2, 3]}
        )
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://allowed.com"])
    def test_api_request_with_invalid_origin(self, client, auth_headers):
        """测试：API请求Origin不在白名单应该被拒绝"""
        headers = {
            **auth_headers,
            "Origin": "https://evil.com"
        }
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=headers,
            json={"permission_ids": [1, 2, 3]}
        )
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_api_request_with_valid_origin(self, client, auth_headers):
        """测试：API请求Origin在白名单应该通过CSRF检查"""
        headers = {
            **auth_headers,
            "Origin": "https://app.example.com"
        }
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=headers,
            json={"permission_ids": [1, 2, 3]}
        )
        # 可能因权限或其他原因失败，但不应该是CSRF失败
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_api_request_with_referer(self, client, auth_headers):
        """测试：API请求可以使用Referer代替Origin"""
        headers = {
            **auth_headers,
            "Referer": "https://app.example.com/admin/roles"
        }
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=headers,
            json={"permission_ids": [1, 2, 3]}
        )
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    # ============================================
    # 4. DEBUG模式测试
    # ============================================

    @patch("app.core.csrf.settings.DEBUG", True)
    def test_debug_mode_bypass_csrf(self, client, auth_headers):
        """测试：DEBUG模式下应该跳过CSRF验证"""
        # 没有Origin/Referer也应该通过
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=auth_headers,
            json={"permission_ids": [1, 2, 3]}
        )
        # 不应该因CSRF失败
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    # ============================================
    # 5. Origin标准化测试
    # ============================================

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_origin_normalization_with_port(self, client, auth_headers):
        """测试：Origin标准化（去除默认端口）"""
        headers = {
            **auth_headers,
            "Origin": "https://app.example.com:443"  # 默认HTTPS端口
        }
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=headers,
            json={"permission_ids": [1, 2, 3]}
        )
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["http://localhost:3000"])
    def test_origin_normalization_localhost(self, client, auth_headers):
        """测试：localhost端口匹配"""
        headers = {
            **auth_headers,
            "Origin": "http://localhost:3000"
        }
        response = client.put(
            "/api/v1/roles/1/permissions",
            headers=headers,
            json={"permission_ids": [1, 2, 3]}
        )
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    # ============================================
    # 6. 不同HTTP方法测试
    # ============================================

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_post_request_csrf_check(self, client, auth_headers):
        """测试：POST请求的CSRF验证"""
        headers = {
            **auth_headers,
            "Origin": "https://app.example.com"
        }
        response = client.post(
            "/api/v1/roles",
            headers=headers,
            json={"role_code": "TEST", "role_name": "Test Role"}
        )
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_delete_request_csrf_check(self, client, auth_headers):
        """测试：DELETE请求的CSRF验证"""
        headers = {
            **auth_headers,
            "Origin": "https://app.example.com"
        }
        response = client.delete(
            "/api/v1/roles/999",
            headers=headers
        )
        # 可能404，但不应该是CSRF错误
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")

    @patch("app.core.csrf.settings.DEBUG", False)
    @patch("app.core.csrf.settings.CORS_ORIGINS", ["https://app.example.com"])
    def test_patch_request_csrf_check(self, client, auth_headers):
        """测试：PATCH请求的CSRF验证"""
        headers = {
            **auth_headers,
            "Origin": "https://app.example.com"
        }
        response = client.patch(
            "/api/v1/roles/1",
            headers=headers,
            json={"role_name": "Updated Name"}
        )
        assert response.status_code != 403 or "CSRF" not in response.json().get("detail", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
