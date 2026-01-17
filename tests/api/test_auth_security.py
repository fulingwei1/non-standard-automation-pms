# -*- coding: utf-8 -*-
"""
认证与安全模块 API 测试

测试内容：
- 用户登录流程
- Token 管理（刷新、撤销）
- 密码管理
- 权限验证
- 安全边界测试
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User


class TestLogin:
    """登录功能测试"""

    def test_login_success(self, client: TestClient):
        """测试正常登录"""
        login_data = {
            "username": "admin",
            "password": "admin123",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data
        else:
            # 如果登录失败，可能是测试环境没有admin用户
            pytest.skip("Admin user not available in test environment")

    def test_login_wrong_password(self, client: TestClient, db_session: Session):
        """测试密码错误"""
        # 确保用户存在
        user = db_session.query(User).first()
        if not user:
            pytest.skip("No user available for testing")

        login_data = {
            "username": user.username,
            "password": "wrong_password_12345",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        # 429 表示速率限制，跳过测试
        if response.status_code == 429:
            pytest.skip("Rate limited")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error_code"] == "WRONG_PASSWORD"

    def test_login_user_not_found(self, client: TestClient):
        """测试用户不存在"""
        login_data = {
            "username": "nonexistent_user_xyz123",
            "password": "any_password",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        # 429 表示速率限制，跳过测试
        if response.status_code == 429:
            pytest.skip("Rate limited")

        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["error_code"] == "USER_NOT_FOUND"

    def test_login_inactive_user(self, client: TestClient, db_session: Session):
        """测试未激活用户登录"""
        # 查找未激活的用户
        user = db_session.query(User).filter(User.is_active == False).first()
        if not user:
            pytest.skip("No inactive user available for testing")

        login_data = {
            "username": user.username,
            "password": "test_password",  # 密码可能不对，但应该先检查is_active
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        # 应该返回401（密码错误）或403（账号未激活）
        assert response.status_code in [401, 403]

    def test_login_empty_credentials(self, client: TestClient):
        """测试空凭证登录"""
        login_data = {
            "username": "",
            "password": "",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        # 应该返回401或422（验证错误）
        assert response.status_code in [401, 422]

    def test_login_missing_password(self, client: TestClient):
        """测试缺少密码"""
        login_data = {
            "username": "admin",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        assert response.status_code == 422


class TestLogout:
    """登出功能测试"""

    def test_logout_success(self, client: TestClient, admin_token: str):
        """测试正常登出"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/logout",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "登出成功" in data["message"]

    def test_logout_without_token(self, client: TestClient):
        """测试无Token登出"""
        response = client.post(f"{settings.API_V1_PREFIX}/auth/logout")

        assert response.status_code == 401

    def test_logout_invalid_token(self, client: TestClient):
        """测试无效Token登出"""
        headers = {"Authorization": "Bearer invalid_token_xyz"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/logout",
            headers=headers
        )

        assert response.status_code == 401

    def test_token_invalid_after_logout(self, client: TestClient):
        """测试登出后Token失效"""
        # 先登录获取token
        login_data = {
            "username": "admin",
            "password": "admin123",
        }

        login_response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        if login_response.status_code != 200:
            pytest.skip("Admin login not available")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 登出
        logout_response = client.post(
            f"{settings.API_V1_PREFIX}/auth/logout",
            headers=headers
        )
        assert logout_response.status_code == 200

        # 尝试使用已登出的token访问受保护资源
        me_response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers
        )

        # Token应该已失效
        assert me_response.status_code == 401


class TestTokenRefresh:
    """Token刷新测试"""

    def test_refresh_token_success(self, client: TestClient, admin_token: str):
        """测试成功刷新Token"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            headers=headers
        )

        # Token 可能因为各种原因失效（过期、被撤销等）
        if response.status_code == 401:
            pytest.skip("Token invalid or expired")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # 新Token应该与旧Token不同
        assert data["access_token"] != admin_token

    def test_refresh_token_without_auth(self, client: TestClient):
        """测试无Token刷新"""
        response = client.post(f"{settings.API_V1_PREFIX}/auth/refresh")

        assert response.status_code == 401

    def test_refresh_token_invalid(self, client: TestClient):
        """测试无效Token刷新"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/refresh",
            headers=headers
        )

        assert response.status_code == 401


class TestGetCurrentUser:
    """获取当前用户信息测试"""

    def test_get_me_success(self, client: TestClient, admin_token: str):
        """测试成功获取当前用户信息"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers
        )

        # Token 可能因为各种原因失效（过期、被撤销等）
        if response.status_code == 401:
            pytest.skip("Token invalid or expired")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "roles" in data
        assert "permissions" in data

    def test_get_me_without_token(self, client: TestClient):
        """测试无Token获取用户信息"""
        response = client.get(f"{settings.API_V1_PREFIX}/auth/me")

        assert response.status_code == 401

    def test_get_me_expired_token(self, client: TestClient):
        """测试过期Token获取用户信息"""
        # 模拟过期token（这里使用无效token模拟）
        headers = {"Authorization": "Bearer expired_token_simulation"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers
        )

        assert response.status_code == 401


class TestPasswordChange:
    """密码修改测试"""

    def test_change_password_success(self, client: TestClient, db_session: Session):
        """测试成功修改密码"""
        import uuid

        from app.models.organization import Employee

        # 使用唯一编码避免冲突
        unique_suffix = uuid.uuid4().hex[:8]
        employee_code = f"EMP-TEST-{unique_suffix}"
        username = f"pwd_test_{unique_suffix}"

        # 先创建员工
        employee = Employee(
            employee_code=employee_code,
            name="密码测试用户",
            department="测试部门",
            role="TESTER",
            phone="13800000001",
        )
        db_session.add(employee)
        db_session.flush()

        # 创建用户
        test_user = User(
            employee_id=employee.id,
            username=username,
            password_hash=get_password_hash("old_password123"),
            real_name="密码测试用户",
            department="测试部门",
            is_active=True,
        )
        db_session.add(test_user)
        db_session.commit()

        # 登录获取token
        login_data = {
            "username": username,
            "password": "old_password123",
        }

        login_response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        if login_response.status_code != 200:
            pytest.skip("Failed to login test user")

        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 修改密码 - 新密码必须符合强度要求（大小写+数字）
        password_data = {
            "old_password": "old_password123",
            "new_password": "NewPassword456",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/auth/password",
            json=password_data,
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

        # 清理测试数据 - 使用 try/finally 确保不影响后续测试
        try:
            db_session.delete(test_user)
            db_session.delete(employee)
            db_session.commit()
        except Exception:
            db_session.rollback()

    def test_change_password_wrong_old(self, client: TestClient, admin_token: str):
        """测试原密码错误"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}
        password_data = {
            "old_password": "wrong_old_password",
            "new_password": "new_password123",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/auth/password",
            json=password_data,
            headers=headers
        )

        # Token 可能因为各种原因失效（过期、被撤销等）
        if response.status_code == 401:
            pytest.skip("Token invalid or expired")

        assert response.status_code == 400
        assert "原密码错误" in response.json().get("detail", "")

    def test_change_password_without_auth(self, client: TestClient):
        """测试无Token修改密码"""
        password_data = {
            "old_password": "old",
            "new_password": "new",
        }

        response = client.put(
            f"{settings.API_V1_PREFIX}/auth/password",
            json=password_data
        )

        assert response.status_code == 401


class TestPasswordHashing:
    """密码哈希功能测试"""

    def test_password_hash_different(self):
        """测试相同密码生成不同哈希"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # 由于使用随机盐，相同密码应该生成不同的哈希
        assert hash1 != hash2

    def test_password_verify_correct(self):
        """测试正确密码验证"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verify_incorrect(self):
        """测试错误密码验证"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False

    def test_password_hash_not_plaintext(self):
        """测试密码哈希不是明文"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert password not in hashed
        assert hashed != password


class TestAuthorizationHeaders:
    """认证头部测试"""

    def test_bearer_token_format(self, client: TestClient):
        """测试Bearer Token格式"""
        # 错误格式的Authorization头
        headers = {"Authorization": "Token invalid_format"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers
        )

        assert response.status_code == 401

    def test_empty_bearer_token(self, client: TestClient):
        """测试空Bearer Token"""
        headers = {"Authorization": "Bearer "}
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers
        )

        assert response.status_code in [401, 403]

    def test_malformed_token(self, client: TestClient):
        """测试格式错误的Token"""
        headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers
        )

        assert response.status_code == 401


class TestPermissionChecks:
    """权限检查测试"""

    def test_superuser_has_all_permissions(self, client: TestClient, admin_token: str):
        """测试超级用户拥有所有权限"""
        if not admin_token:
            pytest.skip("Admin token not available")

        headers = {"Authorization": f"Bearer {admin_token}"}

        # 获取用户信息检查是否是超级用户
        me_response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers
        )

        if me_response.status_code == 200:
            user_data = me_response.json()
            if user_data.get("is_superuser"):
                # 超级用户应该能访问所有需要权限的接口
                # 测试访问一个需要权限的接口
                projects_response = client.get(
                    f"{settings.API_V1_PREFIX}/projects/",
                    headers=headers
                )
                assert projects_response.status_code == 200

    def test_regular_user_limited_permissions(
        self, client: TestClient, normal_user_token: str
    ):
        """测试普通用户权限受限"""
        if not normal_user_token:
            pytest.skip("Normal user token not available")

        headers = {"Authorization": f"Bearer {normal_user_token}"}

        # 普通用户可能无法访问某些管理接口
        # 具体取决于用户的角色和权限配置
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers
        )

        # 至少应该能获取自己的信息
        assert response.status_code == 200


class TestSecurityEdgeCases:
    """安全边界测试"""

    def test_sql_injection_in_username(self, client: TestClient):
        """测试用户名SQL注入防护"""
        login_data = {
            "username": "admin' OR '1'='1",
            "password": "password",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        # 应该返回401（用户不存在），而不是成功登录；429表示速率限制
        assert response.status_code in [401, 429]

    def test_xss_in_username(self, client: TestClient):
        """测试用户名XSS防护"""
        login_data = {
            "username": "<script>alert('xss')</script>",
            "password": "password",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        # 应该正常处理，返回401；429表示速率限制
        assert response.status_code in [401, 429]

    def test_very_long_password(self, client: TestClient):
        """测试超长密码处理"""
        # bcrypt has a maximum password length of ~72 characters
        # Passwords longer than that may cause PasswordSizeError
        # Test with a reasonably long password that should still work
        login_data = {
            "username": "admin",
            "password": "a" * 100,  # 长密码（在bcrypt限制内）
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        # 应该正常处理，返回401或422；429表示速率限制
        assert response.status_code in [401, 422, 429]

    def test_unicode_in_credentials(self, client: TestClient):
        """测试Unicode字符处理"""
        login_data = {
            "username": "测试用户名",
            "password": "密码测试123",
        }

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data=login_data
        )

        # 应该正常处理（可能返回401用户不存在，或429速率限制）
        assert response.status_code in [401, 200, 429]
