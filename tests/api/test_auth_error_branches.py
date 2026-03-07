# -*- coding: utf-8 -*-
"""
认证API异常分支测试

补充认证端点的异常处理分支测试,提升分支覆盖率
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings


class TestLoginErrorBranches:
    """登录端点异常分支测试"""

    def test_login_missing_username(self, client: TestClient):
        """缺少用户名参数"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"password": "admin123"}
        )
        assert response.status_code == 422

    def test_login_missing_password(self, client: TestClient):
        """缺少密码参数"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "admin"}
        )
        assert response.status_code == 422

    def test_login_empty_username(self, client: TestClient):
        """空用户名"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "", "password": "admin123"}
        )
        assert response.status_code in [400, 422]

    def test_login_empty_password(self, client: TestClient):
        """空密码"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "admin", "password": ""}
        )
        assert response.status_code in [400, 401, 422]

    def test_login_wrong_password(self, client: TestClient):
        """错误的密码"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "admin", "password": "wrongpassword123"}
        )
        assert response.status_code in [400, 401]
        if response.status_code == 400:
            data = response.json()
            assert "error_code" in data.get("detail", {}) or "detail" in data

    def test_login_nonexistent_user(self, client: TestClient):
        """不存在的用户"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "nonexistent_user_999", "password": "admin123"}
        )
        assert response.status_code in [400, 401, 404]

    @pytest.mark.parametrize("username,password", [
        ("admin' OR '1'='1", "admin123"),  # SQL注入尝试
        ("admin--", "admin123"),  # SQL注释注入
        ("<script>alert('xss')</script>", "admin123"),  # XSS尝试
        ("admin\x00", "admin123"),  # NULL字节注入
    ])
    def test_login_malicious_input(self, client: TestClient, username: str, password: str):
        """恶意输入测试"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": username, "password": password}
        )
        # 应该被安全处理,返回401或400
        assert response.status_code in [400, 401, 422]

    def test_login_extremely_long_username(self, client: TestClient):
        """超长用户名"""
        long_username = "a" * 1000
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": long_username, "password": "admin123"}
        )
        assert response.status_code in [400, 401, 422]

    def test_login_extremely_long_password(self, client: TestClient):
        """超长密码"""
        long_password = "a" * 1000
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": "admin", "password": long_password}
        )
        assert response.status_code in [400, 401, 422]


class TestGetCurrentUserErrorBranches:
    """获取当前用户端点异常分支测试"""

    def test_get_current_user_no_token(self, client: TestClient):
        """无Token"""
        response = client.get(f"{settings.API_V1_PREFIX}/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """无效Token"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )
        assert response.status_code == 401

    def test_get_current_user_malformed_token(self, client: TestClient):
        """格式错误的Token"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers={"Authorization": "InvalidFormat"}
        )
        assert response.status_code == 401

    def test_get_current_user_expired_token(self, client: TestClient):
        """过期Token (模拟)"""
        # 使用明显过期的JWT
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxfQ.invalid"
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401


class TestRefreshTokenErrorBranches:
    """刷新Token端点异常分支测试"""

    def test_refresh_token_missing_token(self, client: TestClient):
        """缺少refresh_token参数"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            json={}
        )
        assert response.status_code == 422

    def test_refresh_token_invalid_token(self, client: TestClient):
        """无效的refresh_token"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            json={"refresh_token": "invalid_refresh_token_xyz"}
        )
        assert response.status_code in [401, 422]

    def test_refresh_token_empty_token(self, client: TestClient):
        """空的refresh_token"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            json={"refresh_token": ""}
        )
        assert response.status_code in [400, 401, 422]

    def test_refresh_token_wrong_format(self, client: TestClient):
        """格式错误的请求"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            json={"wrong_field": "some_value"}
        )
        assert response.status_code == 422


class TestPasswordChangeErrorBranches:
    """修改密码端点异常分支测试"""

    def test_change_password_no_token(self, client: TestClient):
        """无Token修改密码"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/change-password",
            json={
                "old_password": "admin123",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 401

    def test_change_password_wrong_old_password(self, client: TestClient, admin_token: str):
        """旧密码错误"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/change-password",
            json={
                "old_password": "wrongoldpassword",
                "new_password": "newpassword123"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 401]

    def test_change_password_weak_new_password(self, client: TestClient, admin_token: str):
        """新密码太弱"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/change-password",
            json={
                "old_password": "admin123",
                "new_password": "123"  # 太短的密码
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code in [400, 422]

    def test_change_password_missing_old_password(self, client: TestClient, admin_token: str):
        """缺少旧密码"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/change-password",
            json={"new_password": "newpassword123"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_change_password_missing_new_password(self, client: TestClient, admin_token: str):
        """缺少新密码"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/change-password",
            json={"old_password": "admin123"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 422

    def test_change_password_same_as_old(self, client: TestClient, admin_token: str):
        """新密码与旧密码相同"""
        if not admin_token:
            pytest.skip("Admin token not available")

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/change-password",
            json={
                "old_password": "admin123",
                "new_password": "admin123"  # 与旧密码相同
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # 某些系统允许,某些不允许
        assert response.status_code in [200, 400, 422]
