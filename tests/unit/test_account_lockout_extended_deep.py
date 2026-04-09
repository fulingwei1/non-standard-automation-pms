# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 账户锁定服务（扩展）"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


class TestAccountLockoutServiceExtendedBusinessLogic:
    """账户锁定服务扩展业务逻辑测试"""

    def test_get_attempt_stats_from_db(self):
        """测试从数据库获取失败统计"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()

        # Mock查询
        mock_db.query.return_value.filter.return_value.count.return_value = 3
        mock_attempt = MagicMock()
        mock_attempt.created_at = datetime(2026, 4, 10, 10, 0, 0)
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_attempt

        count, latest = AccountLockoutService._get_attempt_stats_from_db("test_user", mock_db)

        assert count == 3
        assert latest is not None

    def test_get_db_locked_until_not_enough_attempts(self):
        """测试失败次数不足时不会锁定"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()

        with patch.object(AccountLockoutService, '_get_attempt_stats_from_db', return_value=(3, datetime.now())):
            result = AccountLockoutService._get_db_locked_until("test_user", mock_db)

            # 3次失败，阈值为5，不应该锁定
            assert result is None

    def test_get_db_locked_until_enough_attempts(self):
        """测试失败次数达到阈值时锁定"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()
        latest_failed = datetime(2026, 4, 10, 10, 0, 0)

        with patch.object(AccountLockoutService, '_get_attempt_stats_from_db', return_value=(5, latest_failed)):
            result = AccountLockoutService._get_db_locked_until("test_user", mock_db)

            # 5次失败达到阈值，应该锁定
            assert result is not None
            expected_lockout = latest_failed + timedelta(minutes=AccountLockoutService.LOCKOUT_DURATION_MINUTES)
            assert result == expected_lockout

    def test_get_ip_failed_count_from_db(self):
        """测试IP失败次数统计"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        count = AccountLockoutService._get_ip_failed_count_from_db("192.168.1.100", mock_db)

        assert count == 10

    def test_record_failed_login_redis_success(self):
        """测试Redis记录失败登录"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 3
        mock_redis.expire.return_value = True
        mock_redis.get.return_value = None  # 未锁定

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("test_user", "127.0.0.1")

            assert result["attempts"] == 3
            assert result["locked"] == False

    def test_record_failed_login_triggers_lockout(self):
        """测试失败登录触发锁定"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.incr.return_value = 5  # 达到阈值
        mock_redis.expire.return_value = True
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.record_failed_login("test_user", "127.0.0.1")

            assert result["attempts"] == 5
            assert result["locked"] == True

    def test_record_successful_login_clears_attempts(self):
        """测试成功登录清除失败记录"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 2

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            AccountLockoutService.record_successful_login("test_user")

            # 应该删除失败记录和锁定状态
            assert mock_redis.delete.call_count >= 1

    def test_is_ip_blacklisted_true(self):
        """测试IP黑名单检查（是黑名单）"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.return_value = "25"  # 超过阈值

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.is_ip_blacklisted("192.168.1.100")

            assert result == True

    def test_is_ip_blacklisted_false(self):
        """测试IP黑名单检查（不是黑名单）"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.get.return_value = "10"  # 未超过阈值

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.is_ip_blacklisted("192.168.1.100")

            assert result == False

    def test_unlock_account_success(self):
        """测试解锁账户成功"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = MagicMock()
        mock_redis.delete.return_value = 2

        with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
            result = AccountLockoutService.unlock_account("locked_user")

            assert result["success"] == True

    def test_check_lockout_with_db_fallback(self):
        """测试Redis不可用时数据库降级"""
        from app.services.account_lockout_service import AccountLockoutService

        mock_redis = None  # Redis不可用
        mock_db = MagicMock()

        # Mock数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with patch.object(AccountLockoutService, '_get_attempt_stats_from_db', return_value=(2, None)):
            with patch('app.services.account_lockout_service.get_redis_client', return_value=mock_redis):
                result = AccountLockoutService.check_lockout("test_user", mock_db)

                # 应该使用数据库降级逻辑
                assert result["locked"] == False


class TestAccountLockoutServiceConfiguration:
    """配置测试"""

    def test_threshold_constants(self):
        """测试阈值常量"""
        from app.services.account_lockout_service import AccountLockoutService

        assert AccountLockoutService.LOCKOUT_THRESHOLD == 5
        assert AccountLockoutService.LOCKOUT_DURATION_MINUTES == 15
        assert AccountLockoutService.ATTEMPT_WINDOW_MINUTES == 15
        assert AccountLockoutService.CAPTCHA_THRESHOLD == 3
        assert AccountLockoutService.IP_BLACKLIST_THRESHOLD == 20

    def test_threshold_values_reasonable(self):
        """测试阈值合理性"""
        from app.services.account_lockout_service import AccountLockoutService

        # 阈值应该大于验证码阈值
        assert AccountLockoutService.LOCKOUT_THRESHOLD > AccountLockoutService.CAPTCHA_THRESHOLD

        # 锁定时间应该合理
        assert 1 <= AccountLockoutService.LOCKOUT_DURATION_MINUTES <= 60

        # IP黑名单阈值应该较高
        assert AccountLockoutService.IP_BLACKLIST_THRESHOLD >= 10