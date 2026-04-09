# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AccountLockoutService"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta


class TestAccountLockoutServiceBusinessLogic:
    """账户锁定服务业务逻辑测试"""

    def test_check_lockout_not_locked(self):
        """测试未锁定账户"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # 未锁定

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.check_lockout("test_user")

            assert result["locked"] == False
            assert result["remaining_attempts"] >= 0

    def test_check_lockout_locked_account(self):
        """测试已锁定账户"""
        from app.services.account_lockout_service import AccountLockoutService

        locked_until = datetime.now() + timedelta(minutes=15)
        mock_redis = MagicMock()
        mock_redis.get.return_value = locked_until.isoformat()

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.check_lockout("locked_user")

            assert result["locked"] == True
            assert result["remaining_attempts"] == 0
            assert "锁定" in result["message"]

    def test_check_lockout_requires_captcha(self):
        """测试需要验证码场景"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.side_effect = [None, "3"]  # 未锁定，但有3次失败

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.check_lockout("captcha_user")

            assert result["locked"] == False
            assert result["requires_captcha"] == True

    def test_record_failed_login(self):
        """测试记录失败登录"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 1
        mock_redis.expire.return_value = True

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("test_user", "127.0.0.1")

            assert "success" in result

    def test_record_successful_login_clears_attempts(self):
        """测试成功登录清除失败计数"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            AccountLockoutService.record_successful_login("test_user")

            # 应该删除失败计数和锁定状态
            assert mock_redis.delete.called

    def test_unlock_account(self):
        """测试手动解锁账户"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.unlock_account("locked_user")

            assert result["success"] == True

    def test_is_ip_blacklisted(self):
        """测试IP黑名单检查"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.return_value = "25"  # 超过阈值

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.is_ip_blacklisted("192.168.1.100")

            assert result == True

    def test_lockout_threshold_exceeded(self):
        """测试超过锁定阈值"""
        from app.services.account_lockout_service import AccountLockoutService

        # 验证阈值常量
        assert AccountLockoutService.LOCKOUT_THRESHOLD == 5
        assert AccountLockoutService.LOCKOUT_DURATION_MINUTES == 15
        assert AccountLockoutService.CAPTCHA_THRESHOLD == 3

    def test_get_attempt_count_with_redis(self):
        """测试Redis获取失败次数"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.return_value = "3"

        count = AccountLockoutService._get_attempt_count("test_user", mock_redis)

        assert count == 3

    def test_get_attempt_count_redis_failure(self):
        """测试Redis失败时的降级"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis error")

        count = AccountLockoutService._get_attempt_count("test_user", mock_redis)

        # Redis失败时返回0
        assert count == 0


class TestLoginAttemptModel:
    """登录尝试模型测试"""

    def test_login_attempt_creation(self):
        """测试登录尝试记录创建"""
        try:
            from app.models.login_attempt import LoginAttempt

            attempt = LoginAttempt(
                username="test_user",
                ip_address="127.0.0.1",
                success=False,
                timestamp=datetime.now()
            )

            assert attempt.username == "test_user"
            assert attempt.success == False
        except ImportError:
            pytest.skip("Model not found")