# -*- coding: utf-8 -*-
"""
认证 API 集成测试

测试内容：
- 登录认证
- Token 生成和验证
- 密码加密和验证
- Token 撤销（黑名单）
- 获取当前用户信息
- 权限检查
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.core.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    revoke_token,
    is_token_revoked,
)
from app.core.config import settings


@pytest.mark.integration
class TestPasswordAuth:
    """密码认证测试"""

    def test_password_hash(self):
        """测试密码哈希生成"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20

    def test_password_verify_correct(self):
        """测试正确的密码验证"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        is_valid = verify_password(password, hashed)

        assert is_valid is True

    def test_password_verify_incorrect(self):
        """测试错误的密码验证"""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        is_valid = verify_password(wrong_password, hashed)

        assert is_valid is False

    def test_password_hash_different(self):
        """测试相同密码生成不同哈希"""
        password = "test_password_123"
        hashed1 = get_password_hash(password)
        hashed2 = get_password_hash(password)

        # bcrypt 每次生成不同的 salt，所以哈希应该不同
        assert hashed1 != hashed2

        # 但验证时都应该正确
        assert verify_password(password, hashed1)
        assert verify_password(password, hashed2)


class TestTokenGeneration:
    """Token 生成测试"""

    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"user_id": 1, "username": "test_user"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT token 通常较长

    def test_create_access_token_with_expiry(self):
        """测试带过期时间的令牌"""
        from datetime import timedelta

        data = {"user_id": 1, "username": "test_user"}
        expiry = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expiry)

        assert token is not None
        assert isinstance(token, str)

    def test_token_decode(self):
        """测试令牌解码"""
        from jose import jwt

        data = {"user_id": 1, "username": "test_user"}
        token = create_access_token(data)

        # 解码令牌
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        # sub is only present when explicitly passed in data; here we passed user_id
        assert "user_id" in payload
        assert payload["user_id"] == 1
        assert "username" in payload
        assert payload["username"] == "test_user"
        assert "exp" in payload  # 过期时间
        assert "iat" in payload  # 签发时间
        assert "jti" in payload  # Token ID

    def test_token_blacklist_add(self):
        """测试添加令牌到黑名单"""
        data = {"user_id": 1, "username": "test_user"}
        token = create_access_token(data)

        # 撤销令牌
        revoke_token(token)

        # 验证令牌已被撤销
        assert is_token_revoked(token) is True

    def test_token_blacklist_nonexistent_token(self):
        """测试撤销不存在的令牌"""
        fake_token = "fake.token.string.123456"

        # 不应抛出异常
        revoke_token(fake_token)


class TestLoginAPI:
    """登录 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session: Session):
        """创建测试用户"""
        # 创建用户
        user = User(
            employee_id=1,
            username="test_login_user",
            password_hash=get_password_hash("test_password"),
            email="test_login@example.com",
            real_name="测试用户",
            is_active=True,
            is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        yield user

        # 清理
        db_session.delete(user)
        db_session.commit()

    def test_login_success(self, client: TestClient):
        """测试登录成功"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        """测试密码错误"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={
                "username": "admin",
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_user_not_exist(self, client: TestClient):
        """测试用户不存在"""
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={
                "username": "nonexistent_user",
                "password": "any_password",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_missing_fields(self, client: TestClient):
        """测试缺少字段"""
        # 缺少密码
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={
                "username": "admin",
            },
        )

        assert response.status_code == 422  # Validation Error


class TestGetCurrentUser:
    """获取当前用户测试"""

    @pytest.fixture
    def auth_headers(self, client: TestClient):
        """创建认证头"""
        # 先登录获取 token
        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={
                "username": "admin",
                "password": "admin123",
            },
        )

        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_current_user_success(self, client: TestClient, auth_headers: dict):
        """测试获取当前用户成功"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data

    def test_get_current_user_no_token(self, client: TestClient):
        """测试没有 token 获取用户"""
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
        )

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client: TestClient):
        """测试无效 token"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=headers,
        )

        assert response.status_code == 401
