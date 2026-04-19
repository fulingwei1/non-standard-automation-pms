# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - AccountLockoutService"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestAccountLockoutServiceBusinessLogic:
    """账户锁定服务业务逻辑测试"""

    def test_check_lockout_not_locked(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.check_lockout("test_user")

            assert result["locked"] is False
            assert result["remaining_attempts"] >= 0

    def test_check_lockout_locked_account(self):
        from app.services.account_lockout_service import AccountLockoutService

        locked_until = datetime.now() + timedelta(minutes=15)
        mock_redis = MagicMock()
        mock_redis.get.return_value = locked_until.isoformat()

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.check_lockout("locked_user")

            assert result["locked"] is True
            assert result["remaining_attempts"] == 0
            assert "锁定" in result["message"]

    def test_check_lockout_requires_captcha(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.side_effect = [None, "3"]

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.check_lockout("captcha_user")

            assert result["locked"] is False
            assert result["requires_captcha"] is True

    def test_record_failed_login(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.incr.side_effect = [1, 1]
        mock_redis.expire.return_value = True

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("test_user", "127.0.0.1")

            assert result["attempts"] == 1
            assert result["locked"] is False
            assert result["ip_blacklisted"] is False

    def test_record_successful_login_clears_attempts(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            AccountLockoutService.record_successful_login("test_user", "127.0.0.1")

            assert mock_redis.delete.called

    def test_unlock_account(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 1

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.unlock_account("locked_user")

            assert result is True

    def test_is_ip_blacklisted(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.is_ip_blacklisted("192.168.1.100")

            assert result is True

    def test_lockout_threshold_exceeded(self):
        from app.services.account_lockout_service import AccountLockoutService

        assert AccountLockoutService.LOCKOUT_THRESHOLD == 5
        assert AccountLockoutService.LOCKOUT_DURATION_MINUTES == 15
        assert AccountLockoutService.CAPTCHA_THRESHOLD == 3

    def test_get_attempt_count_with_redis(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.return_value = "3"

        count = AccountLockoutService._get_attempt_count("test_user", mock_redis)
        assert count == 3

    def test_get_attempt_count_redis_failure(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis error")

        count = AccountLockoutService._get_attempt_count("test_user", mock_redis)
        assert count == 0


class TestLoginAttemptModel:
    """登录尝试模型测试"""

    def test_login_attempt_creation(self):
        try:
            from app.models.login_attempt import LoginAttempt

            attempt = LoginAttempt(
                username="test_user",
                ip_address="127.0.0.1",
                success=False,
                created_at=datetime.now(),
            )

            assert attempt.username == "test_user"
            assert attempt.success is False
        except ImportError:
            pytest.skip("Model not found")
