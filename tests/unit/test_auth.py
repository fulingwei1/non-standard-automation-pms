# -*- coding: utf-8 -*-
"""
认证模块单元测试

测试 app/core/auth.py 中的认证功能
"""

import sys
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt

# Mock redis before importing auth module
redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

from app.core.auth import (
    _token_blacklist,
    _token_blacklist_lock,
    check_permission,
    create_access_token,
    get_password_hash,
    is_token_revoked,
    revoke_token,
    verify_password,
)
from app.core.config import settings


class TestPasswordHashing:
    """密码哈希相关测试"""

    def test_get_password_hash_returns_string(self):
        """测试密码哈希返回字符串"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_get_password_hash_different_for_same_password(self):
        """测试相同密码生成不同哈希（因为使用盐值）"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        # 由于盐值不同，哈希应该不同
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        password = "correct_password"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """测试空密码验证"""
        password = "some_password"
        hashed = get_password_hash(password)
        assert verify_password("", hashed) is False

    def test_verify_password_unicode(self):
        """测试Unicode密码"""
        password = "密码测试123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True
        assert verify_password("错误密码", hashed) is False


class TestAccessToken:
    """访问令牌相关测试"""

    def test_create_access_token_basic(self):
        """测试基本令牌创建"""
        data = {"sub": "123"}
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_subject(self):
        """测试令牌包含主题信息"""
        user_id = "456"
        data = {"sub": user_id}
        token = create_access_token(data)

        # 解码令牌验证内容
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == user_id

    def test_create_access_token_has_expiry(self):
        """测试令牌有过期时间"""
        data = {"sub": "123"}
        token = create_access_token(data)

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_has_jti(self):
        """测试令牌包含JTI（JWT ID）"""
        data = {"sub": "123"}
        token = create_access_token(data)

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert "jti" in payload
        assert len(payload["jti"]) == 32  # 16字节的hex编码

    def test_create_access_token_custom_expiry(self):
        """测试自定义过期时间"""
        data = {"sub": "123"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires_delta)

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # 验证令牌已创建且可解码
        assert payload["sub"] == "123"

    def test_create_access_token_unique_jti(self):
        """测试每个令牌JTI唯一"""
        data = {"sub": "123"}
        token1 = create_access_token(data)
        token2 = create_access_token(data)

        payload1 = jwt.decode(
            token1, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        payload2 = jwt.decode(
            token2, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        assert payload1["jti"] != payload2["jti"]


class TestTokenBlacklist:
    """令牌黑名单相关测试"""

    def setup_method(self):
        """每个测试前清空内存黑名单"""
        with _token_blacklist_lock:
            _token_blacklist.clear()

    @patch("app.core.auth.get_redis_client")
    def test_revoke_token_none(self, mock_redis):
        """测试撤销空令牌"""
        mock_redis.return_value = None
        revoke_token(None)
        # 不应该抛出异常

    @patch("app.core.auth.get_redis_client")
    def test_revoke_token_empty_string(self, mock_redis):
        """测试撤销空字符串令牌"""
        mock_redis.return_value = None
        revoke_token("")
        # 不应该抛出异常

    @patch("app.core.auth.get_redis_client")
    def test_revoke_token_memory_fallback(self, mock_redis):
        """测试Redis不可用时使用内存黑名单"""
        mock_redis.return_value = None

        token = create_access_token({"sub": "123"})
        revoke_token(token)

        with _token_blacklist_lock:
            assert token in _token_blacklist

    @patch("app.core.auth.get_redis_client")
    def test_revoke_token_redis_available(self, mock_redis):
        """测试Redis可用时使用Redis存储"""
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client

        token = create_access_token({"sub": "123"})
        revoke_token(token)

        # 验证Redis setex被调用
        mock_redis_client.setex.assert_called_once()

    @patch("app.core.auth.get_redis_client")
    def test_is_token_revoked_none(self, mock_redis):
        """测试检查空令牌"""
        mock_redis.return_value = None
        assert is_token_revoked(None) is False

    @patch("app.core.auth.get_redis_client")
    def test_is_token_revoked_not_revoked(self, mock_redis):
        """测试检查未撤销的令牌"""
        mock_redis.return_value = None
        token = create_access_token({"sub": "123"})
        assert is_token_revoked(token) is False

    @patch("app.core.auth.get_redis_client")
    def test_is_token_revoked_memory(self, mock_redis):
        """测试内存黑名单检查"""
        mock_redis.return_value = None

        token = create_access_token({"sub": "123"})
        revoke_token(token)

        assert is_token_revoked(token) is True

    @patch("app.core.auth.get_redis_client")
    def test_is_token_revoked_redis(self, mock_redis):
        """测试Redis黑名单检查"""
        mock_redis_client = MagicMock()
        mock_redis_client.exists.return_value = True
        mock_redis.return_value = mock_redis_client

        token = create_access_token({"sub": "123"})
        assert is_token_revoked(token) is True


class TestCheckPermission:
    """权限检查相关测试"""

    def _create_mock_user(self, is_superuser: bool = False, roles: list = None):
        """创建模拟用户对象"""
        user = MagicMock()
        user.is_superuser = is_superuser
        user.id = 1
        user.roles = roles or []
        return user

    def _create_mock_role(self, role_code: str, permissions: list = None):
        """创建模拟角色对象"""
        user_role = MagicMock()
        user_role.role = MagicMock()
        user_role.role.permissions = []

        for perm_code in (permissions or []):
            role_perm = MagicMock()
            role_perm.permission = MagicMock()
            role_perm.permission.permission_code = perm_code
            user_role.role.permissions.append(role_perm)

        return user_role

    def test_check_permission_superuser(self):
        """测试超级用户权限检查"""
        user = self._create_mock_user(is_superuser=True)
        assert check_permission(user, "any:permission") is True

    def test_check_permission_no_db_no_roles(self):
        """测试无数据库会话且无角色的用户"""
        user = self._create_mock_user(is_superuser=False, roles=[])
        assert check_permission(user, "some:permission") is False

    def test_check_permission_with_orm_matching_permission(self):
        """测试ORM方式检查匹配的权限"""
        role = self._create_mock_role("ADMIN", ["project:read", "project:write"])
        user = self._create_mock_user(is_superuser=False, roles=[role])

        # 不提供db时使用ORM
        assert check_permission(user, "project:read") is True

    def test_check_permission_with_orm_no_matching_permission(self):
        """测试ORM方式检查不匹配的权限"""
        role = self._create_mock_role("ADMIN", ["project:read"])
        user = self._create_mock_user(is_superuser=False, roles=[role])

        assert check_permission(user, "project:delete") is False

    def test_check_permission_with_db_session(self):
        """测试使用数据库会话检查权限"""
        user = self._create_mock_user(is_superuser=False)

        db = MagicMock()
        db.execute.return_value.scalar.return_value = 1

        assert check_permission(user, "project:read", db) is True
        db.execute.assert_called_once()

    def test_check_permission_with_db_session_no_permission(self):
        """测试使用数据库会话检查无权限"""
        user = self._create_mock_user(is_superuser=False)

        db = MagicMock()
        db.execute.return_value.scalar.return_value = 0

        assert check_permission(user, "project:read", db) is False


class TestRequirePermission:
    """权限依赖装饰器测试"""

    def test_require_permission_returns_callable(self):
        """测试require_permission返回可调用对象"""
        from app.core.auth import require_permission

        checker = require_permission("project:read")
        assert callable(checker)

    @pytest.mark.asyncio
    async def test_require_permission_with_permission(self):
        """测试有权限时通过"""
        from app.core.auth import require_permission

        user = MagicMock()
        user.is_superuser = True
        user.is_active = True

        db = MagicMock()

        checker = require_permission("project:read")

        # 直接调用内部的permission_checker协程
        result = await checker(current_user=user, db=db)
        assert result == user

    @pytest.mark.asyncio
    async def test_require_permission_without_permission(self):
        """测试无权限时抛出异常"""
        from fastapi import HTTPException

        from app.core.auth import require_permission

        user = MagicMock()
        user.is_superuser = False
        user.is_active = True
        user.id = 1
        user.roles = []

        db = MagicMock()
        db.execute.return_value.scalar.return_value = 0

        checker = require_permission("project:read")

        with pytest.raises(HTTPException) as exc_info:
            await checker(current_user=user, db=db)

        assert exc_info.value.status_code == 403


class TestGetCurrentUser:
    """获取当前用户测试"""

    @pytest.mark.asyncio
    async def test_get_current_user_revoked_token(self):
        """测试已撤销的令牌"""
        from fastapi import HTTPException

        from app.core.auth import get_current_user

        token = create_access_token({"sub": "123"})

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = True

            db = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=token, db=db)

            assert exc_info.value.status_code == 401
            assert "Token已失效" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """测试无效令牌"""
        from fastapi import HTTPException

        from app.core.auth import get_current_user

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = False

            db = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token="invalid_token", db=db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_no_subject(self):
        """测试无主题的令牌"""
        from fastapi import HTTPException

        from app.core.auth import get_current_user

        # 创建没有sub的令牌
        token = create_access_token({})

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = False

            db = MagicMock()

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=token, db=db)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """测试用户不存在"""
        from fastapi import HTTPException

        from app.core.auth import get_current_user

        token = create_access_token({"sub": "999"})

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = False

            db = MagicMock()
            db.query.return_value.filter.return_value.first.return_value = None
            # 模拟SQL查询也返回None
            db.execute.return_value.fetchone.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token=token, db=db)

            assert exc_info.value.status_code == 401


class TestGetCurrentActiveUser:
    """获取当前活跃用户测试"""

    @pytest.mark.asyncio
    async def test_get_current_active_user_active(self):
        """测试活跃用户"""
        from app.core.auth import get_current_active_user

        user = MagicMock()
        user.is_active = True

        result = await get_current_active_user(current_user=user)
        assert result == user

    @pytest.mark.asyncio
    async def test_get_current_active_user_inactive(self):
        """测试非活跃用户"""
        from fastapi import HTTPException

        from app.core.auth import get_current_active_user

        user = MagicMock()
        user.is_active = False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=user)

        assert exc_info.value.status_code == 400
        assert "禁用" in exc_info.value.detail


class TestGetCurrentActiveSuperuser:
    """获取当前超级管理员测试"""

    @pytest.mark.asyncio
    async def test_get_current_active_superuser_is_superuser(self):
        """测试超级管理员"""
        from app.core.auth import get_current_active_superuser

        user = MagicMock()
        user.is_superuser = True

        result = await get_current_active_superuser(current_user=user)
        assert result == user

    @pytest.mark.asyncio
    async def test_get_current_active_superuser_not_superuser(self):
        """测试非超级管理员"""
        from fastapi import HTTPException

        from app.core.auth import get_current_active_superuser

        user = MagicMock()
        user.is_superuser = False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_superuser(current_user=user)

        assert exc_info.value.status_code == 403
        assert "管理员权限" in exc_info.value.detail
