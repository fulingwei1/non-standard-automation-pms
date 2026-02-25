# -*- coding: utf-8 -*-
"""AccountLockoutService 综合测试"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.account_lockout_service import AccountLockoutService


@pytest.fixture
def mock_redis():
    r = MagicMock()
    r.get.return_value = None
    r.incr.return_value = 1
    r.exists.return_value = 0
    r.scan_iter.return_value = []
    return r


@pytest.fixture
def mock_db():
    return MagicMock()


class TestCheckLockout:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_not_locked(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.get.return_value = None
        result = AccountLockoutService.check_lockout("user1")
        assert result["locked"] is False
        assert result["remaining_attempts"] == 5

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_locked(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        future = (datetime.now() + timedelta(minutes=10)).isoformat()
        mock_redis.get.side_effect = lambda k: future if k == "lockout:user1" else "0"
        result = AccountLockoutService.check_lockout("user1")
        assert result["locked"] is True
        assert result["remaining_attempts"] == 0

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_lockout_parse_error(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.get.side_effect = lambda k: "invalid_date" if k == "lockout:user1" else "0"
        # Should not crash, falls through to attempt check
        result = AccountLockoutService.check_lockout("user1")
        # After parse error it continues to check attempts
        assert isinstance(result, dict)

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_requires_captcha(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.get.side_effect = lambda k: None if "lockout" in k else "3"
        result = AccountLockoutService.check_lockout("user1")
        assert result["requires_captcha"] is True
        assert result["remaining_attempts"] == 2

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_redis_no_db(self, mock_get_redis):
        mock_get_redis.return_value = None
        result = AccountLockoutService.check_lockout("user1")
        assert result["locked"] is False
        assert result["remaining_attempts"] == 5

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_with_db_fallback(self, mock_get_redis, mock_db):
        mock_get_redis.return_value = None
        mock_db.query.return_value.filter.return_value.count.return_value = 2
        result = AccountLockoutService.check_lockout("user1", db=mock_db)
        assert result["locked"] is False


class TestGetAttemptCount:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_from_redis(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        result = AccountLockoutService._get_attempt_count("user1", mock_redis)
        assert result == 0

    def test_from_redis_with_count(self, mock_redis):
        mock_redis.get.return_value = "3"
        result = AccountLockoutService._get_attempt_count("user1", mock_redis)
        assert result == 3

    def test_redis_error_fallback_to_db(self, mock_redis, mock_db):
        mock_redis.get.side_effect = Exception("connection error")
        mock_db.query.return_value.filter.return_value.count.return_value = 2
        result = AccountLockoutService._get_attempt_count("user1", mock_redis, mock_db)
        assert result == 2

    def test_no_redis_no_db(self):
        result = AccountLockoutService._get_attempt_count("user1", None, None)
        assert result == 0

    def test_db_error(self, mock_redis, mock_db):
        mock_redis.get.side_effect = Exception("err")
        mock_db.query.side_effect = Exception("db err")
        result = AccountLockoutService._get_attempt_count("user1", mock_redis, mock_db)
        assert result == 0


class TestRecordFailedLogin:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_normal_failure(self, mock_get_redis, mock_redis, mock_db):
        mock_get_redis.return_value = mock_redis
        mock_redis.incr.return_value = 1
        result = AccountLockoutService.record_failed_login("user1", "1.2.3.4", db=mock_db)
        assert result["attempts"] == 1
        assert result["locked"] is False

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_lockout_triggered(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.incr.return_value = 5
        result = AccountLockoutService.record_failed_login("user1", "1.2.3.4")
        assert result["locked"] is True
        assert result["locked_until"] is not None

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_redis(self, mock_get_redis, mock_db):
        mock_get_redis.return_value = None
        result = AccountLockoutService.record_failed_login("user1", "1.2.3.4", db=mock_db)
        assert result["attempts"] == 0
        assert result["locked"] is False

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_redis_error(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.incr.side_effect = Exception("err")
        result = AccountLockoutService.record_failed_login("user1", "1.2.3.4")
        assert result["locked"] is False

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_db_commit_error(self, mock_get_redis, mock_redis, mock_db):
        mock_get_redis.return_value = mock_redis
        mock_redis.incr.return_value = 1
        mock_db.commit.side_effect = Exception("db err")
        result = AccountLockoutService.record_failed_login("user1", "1.2.3.4", db=mock_db)
        mock_db.rollback.assert_called_once()


class TestCheckIpBlacklist:
    def test_below_threshold(self, mock_redis):
        mock_redis.incr.return_value = 5
        result = AccountLockoutService._check_ip_blacklist("1.2.3.4", mock_redis)
        assert result is False

    def test_at_threshold(self, mock_redis):
        mock_redis.incr.return_value = 20
        result = AccountLockoutService._check_ip_blacklist("1.2.3.4", mock_redis)
        assert result is True

    def test_redis_error(self, mock_redis):
        mock_redis.incr.side_effect = Exception("err")
        result = AccountLockoutService._check_ip_blacklist("1.2.3.4", mock_redis)
        assert result is False


class TestIsIpBlacklisted:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_blacklisted(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.exists.return_value = 1
        assert AccountLockoutService.is_ip_blacklisted("1.2.3.4") is True

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_not_blacklisted(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.exists.return_value = 0
        assert AccountLockoutService.is_ip_blacklisted("1.2.3.4") is False

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_redis(self, mock_get_redis):
        mock_get_redis.return_value = None
        assert AccountLockoutService.is_ip_blacklisted("1.2.3.4") is False

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_redis_error(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.exists.side_effect = Exception("err")
        assert AccountLockoutService.is_ip_blacklisted("1.2.3.4") is False


class TestRecordSuccessfulLogin:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_clears_redis(self, mock_get_redis, mock_redis, mock_db):
        mock_get_redis.return_value = mock_redis
        AccountLockoutService.record_successful_login("user1", "1.2.3.4", db=mock_db)
        mock_redis.delete.assert_any_call("login_attempts:user1")
        mock_redis.delete.assert_any_call("lockout:user1")

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_redis(self, mock_get_redis, mock_db):
        mock_get_redis.return_value = None
        AccountLockoutService.record_successful_login("user1", "1.2.3.4", db=mock_db)
        mock_db.add.assert_called_once()

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_db_error(self, mock_get_redis, mock_db):
        mock_get_redis.return_value = None
        mock_db.commit.side_effect = Exception("err")
        AccountLockoutService.record_successful_login("user1", "1.2.3.4", db=mock_db)
        mock_db.rollback.assert_called_once()


class TestUnlockAccount:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_success(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        assert AccountLockoutService.unlock_account("user1", "admin") is True

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_redis(self, mock_get_redis):
        mock_get_redis.return_value = None
        assert AccountLockoutService.unlock_account("user1") is False

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_redis_error(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.delete.side_effect = Exception("err")
        assert AccountLockoutService.unlock_account("user1") is False


class TestGetLockedAccounts:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_locked(self, mock_get_redis, mock_redis, mock_db):
        mock_get_redis.return_value = mock_redis
        mock_redis.scan_iter.return_value = []
        result = AccountLockoutService.get_locked_accounts(mock_db)
        assert result == []

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_with_locked(self, mock_get_redis, mock_redis, mock_db):
        mock_get_redis.return_value = mock_redis
        mock_redis.scan_iter.return_value = ["lockout:user1"]
        mock_redis.get.side_effect = lambda k: "2024-01-01T12:00:00" if "lockout" in k else "5"
        result = AccountLockoutService.get_locked_accounts(mock_db)
        assert len(result) == 1
        assert result[0]["username"] == "user1"

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_redis(self, mock_get_redis, mock_db):
        mock_get_redis.return_value = None
        result = AccountLockoutService.get_locked_accounts(mock_db)
        assert result == []


class TestGetLoginHistory:
    def test_no_db(self):
        result = AccountLockoutService.get_login_history("user1")
        assert result == []

    def test_with_records(self, mock_db):
        attempt = MagicMock()
        attempt.id = 1
        attempt.username = "user1"
        attempt.ip_address = "1.2.3.4"
        attempt.user_agent = "test"
        attempt.success = True
        attempt.failure_reason = None
        attempt.locked = False
        attempt.created_at = datetime(2024, 1, 1)
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [attempt]
        result = AccountLockoutService.get_login_history("user1", db=mock_db)
        assert len(result) == 1
        assert result[0]["username"] == "user1"

    def test_db_error(self, mock_db):
        mock_db.query.side_effect = Exception("err")
        result = AccountLockoutService.get_login_history("user1", db=mock_db)
        assert result == []


class TestRemoveIpFromBlacklist:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_success(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        assert AccountLockoutService.remove_ip_from_blacklist("1.2.3.4", "admin") is True

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_redis(self, mock_get_redis):
        mock_get_redis.return_value = None
        assert AccountLockoutService.remove_ip_from_blacklist("1.2.3.4") is False

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_redis_error(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.delete.side_effect = Exception("err")
        assert AccountLockoutService.remove_ip_from_blacklist("1.2.3.4") is False


class TestGetBlacklistedIps:
    @patch("app.services.account_lockout_service.get_redis_client")
    def test_empty(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.scan_iter.return_value = []
        assert AccountLockoutService.get_blacklisted_ips() == []

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_with_ips(self, mock_get_redis, mock_redis):
        mock_get_redis.return_value = mock_redis
        mock_redis.scan_iter.return_value = ["ip_blacklist:1.2.3.4"]
        result = AccountLockoutService.get_blacklisted_ips()
        assert len(result) == 1
        assert result[0]["ip"] == "1.2.3.4"

    @patch("app.services.account_lockout_service.get_redis_client")
    def test_no_redis(self, mock_get_redis):
        mock_get_redis.return_value = None
        assert AccountLockoutService.get_blacklisted_ips() == []


class TestConstants:
    def test_thresholds(self):
        assert AccountLockoutService.LOCKOUT_THRESHOLD == 5
        assert AccountLockoutService.LOCKOUT_DURATION_MINUTES == 15
        assert AccountLockoutService.CAPTCHA_THRESHOLD == 3
        assert AccountLockoutService.IP_BLACKLIST_THRESHOLD == 20
