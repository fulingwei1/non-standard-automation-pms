# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 账户锁定服务（扩展）"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAccountLockoutServiceExtendedBusinessLogic:
    """账户锁定服务扩展业务逻辑测试"""

    def test_get_attempt_stats_from_db(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        mock_attempt = MagicMock()
        mock_attempt.created_at = datetime(2026, 4, 10, 10, 0, 0)
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_attempt

        count, latest = AccountLockoutService._get_attempt_stats_from_db("test_user", mock_db)
        assert count == 3
        assert latest is not None

    def test_get_db_locked_until_not_enough_attempts(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()
        with patch.object(AccountLockoutService, "_get_attempt_stats_from_db", return_value=(3, datetime.now())):
            result = AccountLockoutService._get_db_locked_until("test_user", mock_db)
            assert result is None

    def test_get_db_locked_until_enough_attempts(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()
        latest_failed = datetime(2026, 4, 10, 10, 0, 0)

        with patch.object(AccountLockoutService, "_get_attempt_stats_from_db", return_value=(5, latest_failed)):
            result = AccountLockoutService._get_db_locked_until("test_user", mock_db)
            expected_lockout = latest_failed + timedelta(minutes=AccountLockoutService.LOCKOUT_DURATION_MINUTES)
            assert result == expected_lockout

    def test_get_ip_failed_count_from_db(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        count = AccountLockoutService._get_ip_failed_count_from_db("192.168.1.100", mock_db)
        assert count == 10

    def test_record_failed_login_redis_success(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.incr.side_effect = [3, 3]
        mock_redis.expire.return_value = True

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("test_user", "127.0.0.1")
            assert result["attempts"] == 3
            assert result["locked"] is False

    def test_record_failed_login_triggers_lockout(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.incr.side_effect = [5, 5]
        mock_redis.expire.return_value = True
        mock_redis.setex.return_value = True

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("test_user", "127.0.0.1")
            assert result["attempts"] == 5
            assert result["locked"] is True

    def test_record_successful_login_clears_attempts(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 2

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            AccountLockoutService.record_successful_login("test_user", "127.0.0.1")
            assert mock_redis.delete.call_count >= 1

    def test_is_ip_blacklisted_true(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.is_ip_blacklisted("192.168.1.100")
            assert result is True

    def test_is_ip_blacklisted_false(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.is_ip_blacklisted("192.168.1.100")
            assert result is False

    def test_unlock_account_success(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 2

        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.unlock_account("locked_user")
            assert result is True

    def test_check_lockout_with_db_fallback(self):
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()
        with patch.object(AccountLockoutService, "_get_attempt_stats_from_db", return_value=(2, None)):
            with patch("app.services.account_lockout_service.get_redis_client", return_value=None):
                result = AccountLockoutService.check_lockout("test_user", mock_db)
                assert result["locked"] is False


class TestAccountLockoutServiceConfiguration:
    """配置测试"""

    def test_threshold_constants(self):
        from app.services.account_lockout_service import AccountLockoutService

        assert AccountLockoutService.LOCKOUT_THRESHOLD == 5
        assert AccountLockoutService.LOCKOUT_DURATION_MINUTES == 15
        assert AccountLockoutService.ATTEMPT_WINDOW_MINUTES == 15
        assert AccountLockoutService.CAPTCHA_THRESHOLD == 3
        assert AccountLockoutService.IP_BLACKLIST_THRESHOLD == 20

    def test_threshold_values_reasonable(self):
        from app.services.account_lockout_service import AccountLockoutService

        assert AccountLockoutService.LOCKOUT_THRESHOLD > AccountLockoutService.CAPTCHA_THRESHOLD
        assert 1 <= AccountLockoutService.LOCKOUT_DURATION_MINUTES <= 60
        assert AccountLockoutService.IP_BLACKLIST_THRESHOLD >= 10
