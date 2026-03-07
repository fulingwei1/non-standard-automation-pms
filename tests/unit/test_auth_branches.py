# -*- coding: utf-8 -*-
"""
认证模块分支测试 - 提升分支覆盖率到70%+

测试目标文件:
- app/core/auth.py - JWT认证核心逻辑
- app/core/middleware/auth_middleware.py - 认证中间件
- app/core/account_lockout.py - 账户锁定逻辑

目标: 将分支覆盖率从0%提升到70%以上
"""

import sys
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from jose import JWTError, jwt

# Mock redis before importing auth module
redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    extract_jti_from_token,
    get_password_hash,
    is_superuser,
    is_token_revoked,
    revoke_token,
    validate_user_tenant_consistency,
    verify_password,
    verify_refresh_token,
    verify_token_and_get_user,
)
from app.core.config import settings


# =============================================================================
# Token验证分支测试 (8个)
# =============================================================================


class TestTokenValidationBranches:
    """Token验证分支测试"""

    @patch("app.core.auth.get_redis_client")
    def test_verify_refresh_token_expired(self, mock_redis):
        """测试Refresh Token过期分支"""
        mock_redis.return_value = None

        # 创建一个已过期的refresh token
        expired_token = create_refresh_token(
            {"sub": "123"}, expires_delta=timedelta(seconds=-10)
        )

        # 验证应该失败（过期）
        result = verify_refresh_token(expired_token)
        assert result is None

    @patch("app.core.auth.get_redis_client")
    def test_verify_refresh_token_invalid_signature(self, mock_redis):
        """测试Refresh Token签名无效分支"""
        mock_redis.return_value = None

        # 创建一个正常的token
        valid_token = create_refresh_token({"sub": "123"})

        # 修改token最后几个字符，破坏签名
        invalid_token = valid_token[:-10] + "invalidxxx"

        # 验证应该失败（签名无效）
        result = verify_refresh_token(invalid_token)
        assert result is None

    @patch("app.core.auth.get_redis_client")
    def test_verify_refresh_token_malformed(self, mock_redis):
        """测试Refresh Token格式错误分支"""
        mock_redis.return_value = None

        # 完全错误的token格式
        malformed_token = "not.a.jwt.token"

        # 验证应该失败
        result = verify_refresh_token(malformed_token)
        assert result is None

    @patch("app.core.auth.get_redis_client")
    def test_verify_refresh_token_wrong_type_access(self, mock_redis):
        """测试使用Access Token验证Refresh Token（类型错误）"""
        mock_redis.return_value = None

        # 创建一个access token（而非refresh token）
        access_token = create_access_token({"sub": "123"})

        # 尝试作为refresh token验证，应该失败
        result = verify_refresh_token(access_token)
        assert result is None

    @patch("app.core.auth.get_redis_client")
    def test_verify_refresh_token_revoked(self, mock_redis):
        """测试已撤销的Refresh Token分支"""
        # Mock Redis存在检查返回True（表示在黑名单中）
        mock_redis_client = MagicMock()
        mock_redis_client.exists.return_value = True
        mock_redis.return_value = mock_redis_client

        refresh_token = create_refresh_token({"sub": "123"})

        # 验证应该失败（已撤销）
        result = verify_refresh_token(refresh_token)
        assert result is None

    @patch("app.core.auth.get_redis_client")
    def test_verify_refresh_token_success(self, mock_redis):
        """测试Refresh Token验证成功分支"""
        mock_redis_client = MagicMock()
        mock_redis_client.exists.return_value = False  # 未在黑名单
        mock_redis.return_value = mock_redis_client

        refresh_token = create_refresh_token({"sub": "456"})

        # 验证应该成功
        result = verify_refresh_token(refresh_token)
        assert result is not None
        assert result["sub"] == "456"
        assert result["token_type"] == "refresh"

    def test_extract_jti_from_expired_token(self):
        """测试从已过期Token提取JTI（不验证有效性）"""
        # 创建过期的token
        expired_token = create_access_token(
            {"sub": "123"}, expires_delta=timedelta(seconds=-10)
        )

        # 应该仍能提取JTI（因为不验证过期）
        jti = extract_jti_from_token(expired_token)
        assert jti is not None
        assert len(jti) == 32

    def test_extract_jti_from_invalid_token(self):
        """测试从无效Token提取JTI失败分支"""
        invalid_token = "totally.invalid.token"

        # 应该返回None
        jti = extract_jti_from_token(invalid_token)
        assert jti is None


# =============================================================================
# 权限检查分支测试 (6个)
# =============================================================================


class TestPermissionCheckBranches:
    """权限检查分支测试"""

    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_no_token(self):
        """测试无Token分支"""
        db = MagicMock()

        # Token为空字符串或None，应该触发验证失败
        with pytest.raises(HTTPException) as exc:
            await verify_token_and_get_user(token="", db=db)
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_revoked(self):
        """测试已撤销Token分支"""
        token = create_access_token({"sub": "123"})
        db = MagicMock()

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = True

            with pytest.raises(HTTPException) as exc:
                await verify_token_and_get_user(token=token, db=db)

            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Token已失效" in exc.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_invalid_subject(self):
        """测试Token中sub字段无效分支"""
        # 创建没有sub的token
        token = create_access_token({"foo": "bar"})
        db = MagicMock()

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = False

            with pytest.raises(HTTPException) as exc:
                await verify_token_and_get_user(token=token, db=db)

            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_invalid_user_id(self):
        """测试Token中user_id无法转换为整数分支"""
        # sub字段是非数字字符串
        token = create_access_token({"sub": "not_a_number"})
        db = MagicMock()

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = False

            with pytest.raises(HTTPException) as exc:
                await verify_token_and_get_user(token=token, db=db)

            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_not_found(self):
        """测试用户不存在分支"""
        token = create_access_token({"sub": "9999"})
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = False

            with pytest.raises(HTTPException) as exc:
                await verify_token_and_get_user(token=token, db=db)

            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_token_and_get_user_db_error(self):
        """测试数据库查询异常分支"""
        token = create_access_token({"sub": "123"})
        db = MagicMock()
        db.query.side_effect = Exception("Database error")

        with patch("app.core.auth.is_token_revoked") as mock_revoked:
            mock_revoked.return_value = False

            with pytest.raises(HTTPException) as exc:
                await verify_token_and_get_user(token=token, db=db)

            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


# =============================================================================
# 账户锁定分支测试 (5个)
# =============================================================================


class TestAccountLockoutBranches:
    """账户锁定分支测试"""

    def setup_method(self):
        """每个测试前重置锁定状态"""
        from app.core.account_lockout import account_lockout

        account_lockout._failures.clear()
        account_lockout._locked_until.clear()

    def test_record_failure_increment(self):
        """测试失败次数递增分支"""
        from app.core.account_lockout import account_lockout

        username = "test_user"

        # 第1次失败
        triggered = account_lockout.record_failure(username)
        assert triggered is False
        assert account_lockout.remaining_attempts(username) == 4

        # 第2次失败
        triggered = account_lockout.record_failure(username)
        assert triggered is False
        assert account_lockout.remaining_attempts(username) == 3

    def test_lockout_trigger(self):
        """测试触发锁定分支"""
        from app.core.account_lockout import account_lockout

        username = "test_user"

        # 连续失败4次
        for _ in range(4):
            triggered = account_lockout.record_failure(username)
            assert triggered is False

        # 第5次失败应该触发锁定
        triggered = account_lockout.record_failure(username)
        assert triggered is True

        # 检查锁定状态
        is_locked, remaining = account_lockout.is_locked(username)
        assert is_locked is True
        assert remaining > 0

    def test_lockout_check_when_locked(self):
        """测试锁定状态检查分支"""
        from app.core.account_lockout import account_lockout

        username = "test_user"

        # 触发锁定
        for _ in range(5):
            account_lockout.record_failure(username)

        # 检查应该返回锁定状态
        is_locked, remaining = account_lockout.is_locked(username)
        assert is_locked is True
        assert remaining > 0
        assert remaining <= account_lockout.LOCKOUT_DURATION

    def test_lockout_auto_expire(self):
        """测试锁定自动过期分支"""
        from app.core.account_lockout import account_lockout

        username = "test_user"

        # 手动设置一个已过期的锁定时间
        past_time = time.time() - 100
        account_lockout._locked_until[username] = past_time

        # 检查应该返回未锁定，并清理状态
        is_locked, remaining = account_lockout.is_locked(username)
        assert is_locked is False
        assert remaining == 0.0

        # 锁定记录应该被清理
        assert username not in account_lockout._locked_until
        assert len(account_lockout._failures.get(username, [])) == 0

    def test_lockout_reset(self):
        """测试锁定重置分支"""
        from app.core.account_lockout import account_lockout

        username = "test_user"

        # 触发锁定
        for _ in range(5):
            account_lockout.record_failure(username)

        # 确认已锁定
        is_locked, _ = account_lockout.is_locked(username)
        assert is_locked is True

        # 重置
        account_lockout.reset(username)

        # 应该解除锁定
        is_locked, _ = account_lockout.is_locked(username)
        assert is_locked is False
        assert account_lockout.remaining_attempts(username) == 5


# =============================================================================
# 认证中间件分支测试 (6个)
# =============================================================================


class TestAuthMiddlewareBranches:
    """认证中间件分支测试"""

    def test_whitelist_exact_match(self):
        """测试白名单精确匹配分支"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware

        middleware = GlobalAuthMiddleware(app=None)

        # 精确匹配的白名单路径
        assert middleware._is_whitelisted("/api/v1/auth/login") is True
        assert middleware._is_whitelisted("/health") is True
        assert middleware._is_whitelisted("/") is True

    def test_whitelist_prefix_match(self):
        """测试白名单前缀匹配分支"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware

        middleware = GlobalAuthMiddleware(app=None)

        # 前缀匹配
        assert middleware._is_whitelisted("/static/css/main.css") is True
        assert middleware._is_whitelisted("/assets/img/logo.png") is True

    def test_whitelist_debug_mode_docs(self):
        """测试DEBUG模式下文档路径白名单分支"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware

        middleware = GlobalAuthMiddleware(app=None)

        # 保存原始DEBUG设置
        original_debug = settings.DEBUG

        try:
            # DEBUG模式下应该放行文档路径
            settings.DEBUG = True
            assert middleware._is_whitelisted("/docs") is True
            assert middleware._is_whitelisted("/redoc") is True
            assert middleware._is_whitelisted("/openapi.json") is True

            # 非DEBUG模式下不应该放行
            settings.DEBUG = False
            assert middleware._is_whitelisted("/docs") is False
            assert middleware._is_whitelisted("/redoc") is False
        finally:
            settings.DEBUG = original_debug

    @pytest.mark.asyncio
    async def test_middleware_options_request_bypass(self):
        """测试OPTIONS请求跳过认证分支"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware

        middleware = GlobalAuthMiddleware(app=None)

        # Mock request和call_next
        request = MagicMock()
        request.method = "OPTIONS"
        request.url.path = "/api/v1/projects/"

        call_next = AsyncMock()
        expected_response = MagicMock()
        call_next.return_value = expected_response

        # OPTIONS请求应该直接通过
        response = await middleware.dispatch(request, call_next)
        assert response == expected_response
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_middleware_missing_auth_header(self):
        """测试缺少Authorization header分支"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware

        middleware = GlobalAuthMiddleware(app=None)

        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/v1/projects/"
        request.headers.get.return_value = None  # 无Authorization header

        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)

        # 应该返回401
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        response_data = response.body.decode()
        assert "MISSING_TOKEN" in response_data

    @pytest.mark.asyncio
    async def test_middleware_invalid_token_format(self):
        """测试Authorization header格式错误分支"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware

        middleware = GlobalAuthMiddleware(app=None)

        request = MagicMock()
        request.method = "GET"
        request.url.path = "/api/v1/projects/"

        # 测试多种错误格式
        invalid_formats = [
            "InvalidFormat",  # 缺少Bearer前缀
            "Bearer",  # 只有Bearer，无token
            "Bearer ",  # Bearer后只有空格
        ]

        call_next = AsyncMock()

        for invalid_format in invalid_formats:
            request.headers.get.return_value = invalid_format
            response = await middleware.dispatch(request, call_next)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            response_data = response.body.decode()
            assert "INVALID_TOKEN_FORMAT" in response_data or "MISSING_TOKEN" in response_data


# =============================================================================
# 其他边界情况和异常处理分支测试 (5个)
# =============================================================================


class TestBoundaryAndExceptionBranches:
    """边界情况和异常处理测试"""

    @patch("app.core.auth.get_redis_client")
    def test_revoke_token_no_jti_fallback(self, mock_redis):
        """测试撤销无JTI的token时的降级处理分支"""
        mock_redis.return_value = None

        # 创建一个没有JTI的token（理论上不应该发生，但要测试降级）
        # 通过直接编码JWT绕过正常流程
        payload = {"sub": "123", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
        token_no_jti = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # 应该使用哈希值作为降级
        revoke_token(token_no_jti)

        # 验证token被加入内存黑名单
        from app.core.auth import _token_blacklist, _token_blacklist_lock

        # 由于没有JTI，应该使用整个token或其哈希
        # 具体实现会将其加入内存黑名单
        with _token_blacklist_lock:
            # 应该有记录被添加
            assert len(_token_blacklist) > 0

    @patch("app.core.auth.get_redis_client")
    def test_revoke_token_redis_error_fallback(self, mock_redis):
        """测试Redis错误时降级到内存存储分支"""
        mock_redis_client = MagicMock()
        mock_redis_client.setex.side_effect = Exception("Redis connection error")
        mock_redis.return_value = mock_redis_client

        token = create_access_token({"sub": "123"})

        # 应该降级到内存存储
        revoke_token(token)

        # 验证降级到内存黑名单
        from app.core.auth import _token_blacklist, _token_blacklist_lock

        with _token_blacklist_lock:
            assert token in _token_blacklist

    def test_is_superuser_true(self):
        """测试超级管理员判断 - True分支"""
        user = MagicMock()
        user.is_superuser = True
        user.tenant_id = None

        assert is_superuser(user) is True

    def test_is_superuser_false_has_tenant(self):
        """测试超级管理员判断 - 有tenant_id分支"""
        user = MagicMock()
        user.is_superuser = True
        user.tenant_id = 1  # 有租户，不是超级管理员

        assert is_superuser(user) is False

    def test_validate_user_tenant_consistency_superuser_with_tenant_error(self):
        """测试超级管理员数据不一致异常分支"""
        user = MagicMock()
        user.is_superuser = True
        user.tenant_id = 1  # 超级管理员不应该有tenant_id
        user.id = 999

        with pytest.raises(ValueError) as exc:
            validate_user_tenant_consistency(user)

        assert "Invalid superuser data" in str(exc.value)
        assert "999" in str(exc.value)

    def test_validate_user_tenant_consistency_tenant_user_without_tenant_error(self):
        """测试租户用户缺少tenant_id异常分支"""
        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = None  # 租户用户必须有tenant_id
        user.id = 888

        with pytest.raises(ValueError) as exc:
            validate_user_tenant_consistency(user)

        assert "Invalid tenant user data" in str(exc.value)
        assert "888" in str(exc.value)

    def test_validate_user_tenant_consistency_success(self):
        """测试用户数据一致性验证成功分支"""
        # 正常的超级管理员
        superuser = MagicMock()
        superuser.is_superuser = True
        superuser.tenant_id = None
        superuser.id = 1

        validate_user_tenant_consistency(superuser)  # 不应该抛出异常

        # 正常的租户用户
        tenant_user = MagicMock()
        tenant_user.is_superuser = False
        tenant_user.tenant_id = 1
        tenant_user.id = 2

        validate_user_tenant_consistency(tenant_user)  # 不应该抛出异常

    def test_create_token_pair_with_custom_expiry(self):
        """测试创建Token对时使用自定义过期时间分支"""
        data = {"sub": "123"}
        access_exp = timedelta(hours=1)
        refresh_exp = timedelta(days=14)

        access_token, refresh_token, access_jti, refresh_jti = create_token_pair(
            data=data, access_expires=access_exp, refresh_expires=refresh_exp
        )

        # 验证返回值
        assert access_token is not None
        assert refresh_token is not None
        assert access_jti is not None
        assert refresh_jti is not None
        assert access_jti != refresh_jti

        # 解码验证
        access_payload = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        refresh_payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        assert access_payload["jti"] == access_jti
        assert refresh_payload["jti"] == refresh_jti
        assert access_payload["token_type"] == "access"
        assert refresh_payload["token_type"] == "refresh"

    def test_password_hashing_long_password_truncation(self):
        """测试超长密码截断分支（bcrypt限制72字节）"""
        # 创建一个超过72字节的密码
        long_password = "a" * 100
        hashed = get_password_hash(long_password)

        # 应该能成功哈希
        assert hashed is not None

        # 验证前72字节
        assert verify_password("a" * 72, hashed) is True

        # 验证超过72字节的部分被忽略
        assert verify_password("a" * 100, hashed) is True
