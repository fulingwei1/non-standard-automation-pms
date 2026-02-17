# -*- coding: utf-8 -*-
"""AccountLockoutService 单元测试 - mock Redis，测试锁定/解锁逻辑"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAccountLockoutCheckLockout:
    """check_lockout 方法测试"""

    def test_locked_account_returns_locked_true(self):
        """Redis 中存在锁定记录时返回 locked=True"""
        from app.services.account_lockout_service import AccountLockoutService
        locked_until = (datetime.now() + timedelta(minutes=10)).isoformat()
        mock_redis = MagicMock()
        mock_redis.get.return_value = locked_until
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.check_lockout("testuser")
        assert result["locked"] is True
        assert result["remaining_attempts"] == 0

    def test_unlocked_account_with_no_attempts(self):
        """无失败记录时返回 locked=False 且 remaining=THRESHOLD"""
        from app.services.account_lockout_service import AccountLockoutService
        mock_redis = MagicMock()
        mock_redis.get.side_effect = [None, None]  # 无锁定，无失败次数
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.check_lockout("newuser")
        assert result["locked"] is False
        assert result["remaining_attempts"] == AccountLockoutService.LOCKOUT_THRESHOLD

    def test_captcha_required_after_threshold(self):
        """失败次数 >= CAPTCHA_THRESHOLD 时 requires_captcha=True"""
        from app.services.account_lockout_service import AccountLockoutService
        threshold = AccountLockoutService.CAPTCHA_THRESHOLD
        mock_redis = MagicMock()
        mock_redis.get.side_effect = [None, str(threshold)]  # 无锁定，失败次数=threshold
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.check_lockout("captchauser")
        assert result["requires_captcha"] is True

    def test_no_redis_fallback_db(self):
        """Redis 不可用时降级到数据库查询"""
        from app.services.account_lockout_service import AccountLockoutService
        db = MagicMock()
        db.query.return_value.filter.return_value.count.return_value = 2
        with patch("app.services.account_lockout_service.get_redis_client", return_value=None):
            result = AccountLockoutService.check_lockout("dbuser", db=db)
        assert result["locked"] is False
        assert result["remaining_attempts"] == AccountLockoutService.LOCKOUT_THRESHOLD - 2


class TestAccountLockoutRecordFailedLogin:
    """record_failed_login 方法测试"""

    def test_first_failure_no_lockout(self):
        """第一次失败不触发锁定"""
        from app.services.account_lockout_service import AccountLockoutService
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = [1, 1]  # login_attempts=1, ip_attempts=1
        mock_redis.get.return_value = None
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("user1", "127.0.0.1")
        assert result["locked"] is False
        assert result["attempts"] == 1

    def test_lockout_triggered_at_threshold(self):
        """达到 LOCKOUT_THRESHOLD 时触发锁定"""
        from app.services.account_lockout_service import AccountLockoutService
        threshold = AccountLockoutService.LOCKOUT_THRESHOLD
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = [threshold, 1]
        mock_redis.get.return_value = None
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("lockeduser", "10.0.0.1")
        assert result["locked"] is True
        assert result["attempts"] == threshold

    def test_record_persists_to_db(self):
        """失败记录应同步写入数据库"""
        from app.services.account_lockout_service import AccountLockoutService
        mock_redis = MagicMock()
        mock_redis.incr.side_effect = [1, 1]
        mock_redis.get.return_value = None
        db = MagicMock()
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            AccountLockoutService.record_failed_login("dbuser2", "192.168.1.1", db=db)
        db.add.assert_called_once()
        db.commit.assert_called_once()


class TestAccountLockoutUnlock:
    """unlock_account 方法测试"""

    def test_unlock_clears_redis_keys(self):
        """手动解锁应删除 Redis 中的 lockout 和 login_attempts 键"""
        from app.services.account_lockout_service import AccountLockoutService
        mock_redis = MagicMock()
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.unlock_account("lockeduser", admin_user="admin")
        assert result is True
        mock_redis.delete.assert_any_call("login_attempts:lockeduser")
        mock_redis.delete.assert_any_call("lockout:lockeduser")

    def test_unlock_returns_false_when_no_redis(self):
        """Redis 不可用时解锁返回 False"""
        from app.services.account_lockout_service import AccountLockoutService
        with patch("app.services.account_lockout_service.get_redis_client", return_value=None):
            result = AccountLockoutService.unlock_account("user", admin_user="admin")
        assert result is False


class TestAccountLockoutIpBlacklist:
    """IP 黑名单相关测试"""

    def test_ip_blacklisted_returns_true(self):
        """黑名单中的 IP 应返回 True"""
        from app.services.account_lockout_service import AccountLockoutService
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 1
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            assert AccountLockoutService.is_ip_blacklisted("1.2.3.4") is True

    def test_ip_not_blacklisted_returns_false(self):
        """不在黑名单的 IP 应返回 False"""
        from app.services.account_lockout_service import AccountLockoutService
        mock_redis = MagicMock()
        mock_redis.exists.return_value = 0
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            assert AccountLockoutService.is_ip_blacklisted("192.168.0.1") is False

    def test_remove_ip_from_blacklist(self):
        """移除 IP 黑名单应调用 Redis delete"""
        from app.services.account_lockout_service import AccountLockoutService
        mock_redis = MagicMock()
        with patch("app.services.account_lockout_service.get_redis_client", return_value=mock_redis):
            result = AccountLockoutService.remove_ip_from_blacklist("1.2.3.4", admin_user="admin")
        assert result is True
        mock_redis.delete.assert_any_call("ip_blacklist:1.2.3.4")
