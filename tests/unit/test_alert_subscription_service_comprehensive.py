# -*- coding: utf-8 -*-
"""
AlertSubscriptionService 综合单元测试

测试覆盖:
- match_subscriptions: 匹配预警的订阅配置
- get_notification_recipients: 获取预警的通知接收人
- _check_level_match: 检查预警级别是否匹配
- _is_quiet_hours: 检查是否在免打扰时段
- get_user_subscriptions: 获取用户的订阅配置
"""

from datetime import datetime, time
from unittest.mock import MagicMock, patch

import pytest


class TestCheckLevelMatch:
    """测试 _check_level_match 方法"""

    def test_info_matches_info(self):
        """测试INFO级别匹配INFO"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        result = service._check_level_match('INFO', 'INFO')

        assert result is True

    def test_warning_matches_info(self):
        """测试WARNING级别匹配INFO最低级别"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        result = service._check_level_match('WARNING', 'INFO')

        assert result is True

    def test_info_does_not_match_warning(self):
        """测试INFO级别不匹配WARNING最低级别"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        result = service._check_level_match('INFO', 'WARNING')

        assert result is False

    def test_urgent_matches_all(self):
        """测试URGENT级别匹配所有最低级别"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        assert service._check_level_match('URGENT', 'INFO') is True
        assert service._check_level_match('URGENT', 'WARNING') is True
        assert service._check_level_match('URGENT', 'CRITICAL') is True
        assert service._check_level_match('URGENT', 'URGENT') is True

    def test_handles_unknown_level(self):
        """测试处理未知级别"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        result = service._check_level_match('UNKNOWN', 'INFO')

        assert result is False


class TestIsQuietHours:
    """测试 _is_quiet_hours 方法"""

    def test_returns_false_when_no_quiet_hours(self):
        """测试无免打扰设置时返回False"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_subscription = MagicMock()
        mock_subscription.quiet_start = None
        mock_subscription.quiet_end = None

        result = service._is_quiet_hours(mock_subscription)

        assert result is False

    def test_returns_true_within_quiet_hours(self):
        """测试在免打扰时段内返回True"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_subscription = MagicMock()
        mock_subscription.quiet_start = "00:00"
        mock_subscription.quiet_end = "23:59"

        result = service._is_quiet_hours(mock_subscription)

        assert result is True

    def test_returns_false_outside_quiet_hours(self):
        """测试在免打扰时段外返回False"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        # 设置一个不可能的时间段
        mock_subscription = MagicMock()
        mock_subscription.quiet_start = "03:00"
        mock_subscription.quiet_end = "03:01"

        # 通过mock datetime.now来控制当前时间
        with patch('app.services.alert_subscription_service.datetime') as mock_datetime:
            mock_datetime.now.return_value.time.return_value = time(12, 0)

            result = service._is_quiet_hours(mock_subscription)

            assert result is False

    def test_handles_overnight_quiet_hours(self):
        """测试处理跨天免打扰时段"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_subscription = MagicMock()
        mock_subscription.quiet_start = "22:00"
        mock_subscription.quiet_end = "08:00"

        with patch('app.services.alert_subscription_service.datetime') as mock_datetime:
            # 测试晚上23:00在免打扰时段内
            mock_datetime.now.return_value.time.return_value = time(23, 0)

            result = service._is_quiet_hours(mock_subscription)

            assert result is True

    def test_handles_invalid_time_format(self):
        """测试处理无效时间格式"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_subscription = MagicMock()
        mock_subscription.quiet_start = "invalid"
        mock_subscription.quiet_end = "format"

        result = service._is_quiet_hours(mock_subscription)

        assert result is False


class TestMatchSubscriptions:
    """测试 match_subscriptions 方法"""

    def test_returns_empty_when_no_rule(self):
        """测试无规则时返回空"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_alert = MagicMock()
        mock_alert.rule = None

        result = service.match_subscriptions(mock_alert)

        assert result == []

    def test_matches_active_subscriptions(self):
        """测试匹配活跃的订阅"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_alert = MagicMock()
        mock_alert.project_id = 1
        mock_alert.alert_level = 'WARNING'

        mock_rule = MagicMock()
        mock_rule.rule_type = 'BUDGET'

        mock_subscription = MagicMock()
        mock_subscription.is_active = True
        mock_subscription.min_level = 'INFO'
        mock_subscription.quiet_start = None
        mock_subscription.quiet_end = None

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_subscription]

        result = service.match_subscriptions(mock_alert, mock_rule)

        assert len(result) == 1
        assert result[0] == mock_subscription

    def test_filters_by_alert_level(self):
        """测试按预警级别过滤"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_alert = MagicMock()
        mock_alert.project_id = 1
        mock_alert.alert_level = 'INFO'

        mock_rule = MagicMock()
        mock_rule.rule_type = 'COST'

        mock_subscription = MagicMock()
        mock_subscription.is_active = True
        mock_subscription.min_level = 'WARNING'  # 高于INFO
        mock_subscription.quiet_start = None
        mock_subscription.quiet_end = None

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_subscription]

        result = service.match_subscriptions(mock_alert, mock_rule)

        assert len(result) == 0

    def test_filters_by_quiet_hours(self):
        """测试按免打扰时段过滤"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_alert = MagicMock()
        mock_alert.project_id = 1
        mock_alert.alert_level = 'WARNING'

        mock_rule = MagicMock()
        mock_rule.rule_type = 'BUDGET'

        mock_subscription = MagicMock()
        mock_subscription.is_active = True
        mock_subscription.min_level = 'INFO'
        mock_subscription.quiet_start = "00:00"
        mock_subscription.quiet_end = "23:59"  # 全天免打扰

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_subscription]

        result = service.match_subscriptions(mock_alert, mock_rule)

        assert len(result) == 0


class TestGetNotificationRecipients:
    """测试 get_notification_recipients 方法"""

    def test_returns_empty_when_no_rule(self):
        """测试无规则时返回空"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_alert = MagicMock()
        mock_alert.rule = None

        result = service.get_notification_recipients(mock_alert)

        assert result['user_ids'] == []
        assert result['channels'] == ['SYSTEM']
        assert result['subscriptions'] == []

    def test_collects_user_ids_from_subscriptions(self):
        """测试从订阅中收集用户ID"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_alert = MagicMock()
        mock_alert.project_id = 1
        mock_alert.alert_level = 'WARNING'

        mock_rule = MagicMock()
        mock_rule.rule_type = 'COST'
        mock_rule.notify_users = None
        mock_rule.notify_channels = None

        mock_subscription1 = MagicMock()
        mock_subscription1.user_id = 10
        mock_subscription1.notify_channels = ['email', 'sms']
        mock_subscription1.is_active = True
        mock_subscription1.min_level = 'INFO'
        mock_subscription1.quiet_start = None
        mock_subscription1.quiet_end = None

        mock_subscription2 = MagicMock()
        mock_subscription2.user_id = 20
        mock_subscription2.notify_channels = ['system']
        mock_subscription2.is_active = True
        mock_subscription2.min_level = 'INFO'
        mock_subscription2.quiet_start = None
        mock_subscription2.quiet_end = None

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_subscription1, mock_subscription2
        ]

        result = service.get_notification_recipients(mock_alert, mock_rule)

        assert 10 in result['user_ids']
        assert 20 in result['user_ids']
        assert 'EMAIL' in result['channels']
        assert 'SMS' in result['channels']
        assert 'SYSTEM' in result['channels']

    def test_adds_rule_notify_users(self):
        """测试添加规则配置的通知用户"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_alert = MagicMock()
        mock_alert.project_id = 1
        mock_alert.alert_level = 'WARNING'

        mock_rule = MagicMock()
        mock_rule.rule_type = 'COST'
        mock_rule.notify_users = [100, 200]
        mock_rule.notify_channels = ['wechat']

        mock_subscription = MagicMock()
        mock_subscription.user_id = 10
        mock_subscription.notify_channels = ['email']
        mock_subscription.is_active = True
        mock_subscription.min_level = 'INFO'
        mock_subscription.quiet_start = None
        mock_subscription.quiet_end = None

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [mock_subscription]

        result = service.get_notification_recipients(mock_alert, mock_rule)

        assert 10 in result['user_ids']
        assert 100 in result['user_ids']
        assert 200 in result['user_ids']
        assert 'WECHAT' in result['channels']

    def test_uses_default_when_no_subscriptions(self):
        """测试无订阅时使用默认配置"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_alert = MagicMock()
        mock_alert.project_id = 1
        mock_alert.alert_level = 'WARNING'

        mock_rule = MagicMock()
        mock_rule.rule_type = 'COST'
        mock_rule.notify_users = [50]
        mock_rule.notify_channels = ['dingding']

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.get_notification_recipients(mock_alert, mock_rule)

        assert 50 in result['user_ids']
        assert 'DINGDING' in result['channels']


class TestGetUserSubscriptions:
    """测试 get_user_subscriptions 方法"""

    def test_returns_user_subscriptions(self):
        """测试返回用户订阅"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_subscription = MagicMock()
        mock_subscription.user_id = 1
        mock_subscription.is_active = True

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_subscription]

        result = service.get_user_subscriptions(user_id=1)

        assert len(result) == 1

    def test_filters_by_alert_type(self):
        """测试按预警类型过滤"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.get_user_subscriptions(user_id=1, alert_type='BUDGET')

        mock_db.query.assert_called()

    def test_filters_by_project_id(self):
        """测试按项目ID过滤"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.get_user_subscriptions(user_id=1, project_id=10)

        mock_db.query.assert_called()

    def test_filters_by_both(self):
        """测试同时按类型和项目过滤"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        mock_db = MagicMock()
        service = AlertSubscriptionService(mock_db)

        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = service.get_user_subscriptions(user_id=1, alert_type='COST', project_id=5)

        mock_db.query.assert_called()


class TestLevelPriority:
    """测试级别优先级常量"""

    def test_level_priority_order(self):
        """测试级别优先级顺序"""
        from app.services.alert_subscription_service import AlertSubscriptionService

        priority = AlertSubscriptionService.LEVEL_PRIORITY

        assert priority['INFO'] < priority['WARNING']
        assert priority['WARNING'] < priority['CRITICAL']
        assert priority['CRITICAL'] < priority['URGENT']
