# -*- coding: utf-8 -*-
"""
测试预警订阅匹配服务
"""

from datetime import time
from unittest.mock import MagicMock, patch


from app.models.enums import AlertLevelEnum
from app.services.alert_subscription_service import AlertSubscriptionService


# ===== Mock Classes =====


class MockAlertSubscription:
    """Mock AlertSubscription for testing"""

    def __init__(
        self,
        id,
        user_id,
        alert_type=None,
        project_id=None,
        min_level=None,
        notify_channels=None,
        quiet_start=None,
        quiet_end=None,
        is_active=True,
    ):
        self.id = id
        self.user_id = user_id
        self.alert_type = alert_type
        self.project_id = project_id
        self.min_level = min_level or AlertLevelEnum.INFO.value
        self.notify_channels = notify_channels or ["SYSTEM"]
        self.quiet_start = quiet_start
        self.quiet_end = quiet_end
        self.is_active = is_active


class MockAlertRule:
    """Mock AlertRule for testing"""

    def __init__(self, id, rule_type, notify_users=None, notify_channels=None):
        self.id = id
        self.rule_type = rule_type
        self.notify_users = notify_users or []
        self.notify_channels = notify_channels or []


class MockAlertRecord:
    """Mock AlertRecord for testing"""

    def __init__(self, id, alert_level, alert_type, project_id=None, rule=None):
        self.id = id
        self.alert_level = alert_level
        self.alert_type = alert_type
        self.project_id = project_id
        self.rule = rule


class MockProject:
    """Mock Project for testing"""

    def __init__(self, id, code):
        self.id = id
        self.code = code


class MockUser:
    """Mock User for testing"""

    def __init__(self, id, username):
        self.id = id
        self.username = username


# ===== Tests for _check_level_match =====


class TestCheckLevelMatch:
    """测试 _check_level_match 方法"""

    def test_check_level_match_exact_match(self):
        """测试级别完全匹配"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        result = service._check_level_match(
            AlertLevelEnum.WARNING.value, AlertLevelEnum.WARNING.value
        )
        assert result is True

    def test_check_level_match_higher_level(self):
        """测试预警级别高于最低级别"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # CRITICAL > WARNING
        result = service._check_level_match(
            AlertLevelEnum.CRITICAL.value, AlertLevelEnum.WARNING.value
        )
        assert result is True

        # URGENT > INFO
        result = service._check_level_match(
            AlertLevelEnum.URGENT.value, AlertLevelEnum.INFO.value
        )
        assert result is True

    def test_check_level_match_lower_level(self):
        """测试预警级别低于最低级别"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # INFO < WARNING
        result = service._check_level_match(
            AlertLevelEnum.INFO.value, AlertLevelEnum.WARNING.value
        )
        assert result is False

        # WARNING < CRITICAL
        result = service._check_level_match(
            AlertLevelEnum.WARNING.value, AlertLevelEnum.CRITICAL.value
        )
        assert result is False

    def test_check_level_match_invalid_levels(self):
        """测试无效级别"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # 两个都无效 - 0 >= 0 是 True
        result = service._check_level_match("INVALID", "INVALID")
        assert result is True  # Both get priority 0, 0 >= 0

        # 预警级别无效
        result = service._check_level_match("INVALID", AlertLevelEnum.WARNING.value)
        assert result is False  # 0 >= 2 is False

        # 最低级别无效
        result = service._check_level_match(AlertLevelEnum.WARNING.value, "INVALID")
        assert result is True  # 2 >= 0 is True


# ===== Tests for _is_quiet_hours =====


class TestIsQuietHours:
    """测试 _is_quiet_hours 方法"""

    def test_is_quiet_hours_no_config(self):
        """测试未配置免打扰时段"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        subscription = MockAlertSubscription(
            id=1, user_id=1, quiet_start=None, quiet_end=None
        )

        result = service._is_quiet_hours(subscription)
        assert result is False

    def test_is_quiet_hours_same_day_inside(self):
        """测试同一天内，当前时间在免打扰时段内"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # 假设当前时间是 22:30
        with patch("app.services.alert_subscription_service.datetime") as mock_dt:
            mock_dt.now.return_value.time.return_value = time(22, 30)

            subscription = MockAlertSubscription(
                id=1, user_id=1, quiet_start="22:00", quiet_end="06:00"
            )

            result = service._is_quiet_hours(subscription)
            assert result is True

    def test_is_quiet_hours_same_day_outside(self):
        """测试同一天内，当前时间不在免打扰时段内"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # 假设当前时间是 10:00，不在 12:00-14:00 之间
        with patch("app.services.alert_subscription_service.datetime") as mock_dt:
            mock_dt.now.return_value.time.return_value = time(10, 0)

            subscription = MockAlertSubscription(
                id=1, user_id=1, quiet_start="12:00", quiet_end="14:00"
            )

            result = service._is_quiet_hours(subscription)
            assert result is False

    def test_is_quiet_hours_cross_day_in_first_part(self):
        """测试跨天情况，当前时间在第一部分（晚上）"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # 22:00 - 08:00，当前时间 23:00
        with patch("app.services.alert_subscription_service.datetime") as mock_dt:
            mock_dt.now.return_value.time.return_value = time(23, 0)

            subscription = MockAlertSubscription(
                id=1, user_id=1, quiet_start="22:00", quiet_end="08:00"
            )

            result = service._is_quiet_hours(subscription)
            assert result is True

    def test_is_quiet_hours_cross_day_in_second_part(self):
        """测试跨天情况，当前时间在第二部分（早上）"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # 22:00 - 08:00，当前时间 02:00
        with patch("app.services.alert_subscription_service.datetime") as mock_dt:
            mock_dt.now.return_value.time.return_value = time(2, 0)

            subscription = MockAlertSubscription(
                id=1, user_id=1, quiet_start="22:00", quiet_end="08:00"
            )

            result = service._is_quiet_hours(subscription)
            assert result is True

    def test_is_quiet_hours_cross_day_outside(self):
        """测试跨天情况，当前时间不在免打扰时段内"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # 22:00 - 08:00，当前时间 12:00
        with patch("app.services.alert_subscription_service.datetime") as mock_dt:
            mock_dt.now.return_value.time.return_value = time(12, 0)

            subscription = MockAlertSubscription(
                id=1, user_id=1, quiet_start="22:00", quiet_end="08:00"
            )

            result = service._is_quiet_hours(subscription)
            assert result is False

    def test_is_quiet_hours_invalid_format(self):
        """测试时间格式错误"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        subscription = MockAlertSubscription(
            id=1, user_id=1, quiet_start="invalid", quiet_end="08:00"
        )

        result = service._is_quiet_hours(subscription)
        assert result is False


# ===== Tests for match_subscriptions =====


class TestMatchSubscriptions:
    """测试 match_subscriptions 方法"""

    def test_match_subscriptions_no_rule(self):
        """测试没有规则的情况"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            rule=None,
        )

        result = service.match_subscriptions(alert)
        assert result == []

    def test_match_subscriptions_by_type(self):
        """测试按预警类型匹配"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        # 创建一个规则
        rule = MockAlertRule(id=1, rule_type="DELAY")

        # 创建预警记录
        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            rule=rule,
        )

        # 创建订阅配置 - 两个都匹配 DELAY 类型
        sub1 = MockAlertSubscription(id=1, user_id=1, alert_type="DELAY")
        sub2 = MockAlertSubscription(id=2, user_id=2, alert_type=None)  # 匹配所有类型

        # Mock 查询结果 - 假设数据库查询返回匹配类型的订阅
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sub1, sub2]
        db_session.query.return_value = mock_query

        result = service.match_subscriptions(alert, rule)

        # 应该匹配到两个订阅（假设DB已按类型过滤）
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_match_subscriptions_by_project(self):
        """测试按项目匹配"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        rule = MockAlertRule(id=1, rule_type="DELAY")

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            project_id=100,
            rule=rule,
        )

        # 创建订阅配置
        sub1 = MockAlertSubscription(id=1, user_id=1, project_id=100)
        sub2 = MockAlertSubscription(id=2, user_id=2, project_id=None)  # 匹配所有项目

        # Mock 查询结果
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sub1, sub2]
        db_session.query.return_value = mock_query

        result = service.match_subscriptions(alert, rule)

        # 应该匹配到两个订阅
        assert len(result) == 2

    def test_match_subscriptions_filter_by_level(self):
        """测试按预警级别过滤"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        rule = MockAlertRule(id=1, rule_type="DELAY")

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.INFO.value,  # INFO 级别
            alert_type="DELAY",
            rule=rule,
        )

        # 创建订阅配置
        sub1 = MockAlertSubscription(
            id=1,
            user_id=1,
            alert_type="DELAY",
            min_level=AlertLevelEnum.INFO.value,  # INFO 级别，应该匹配
        )
        sub2 = MockAlertSubscription(
            id=2,
            user_id=2,
            alert_type="DELAY",
            min_level=AlertLevelEnum.WARNING.value,  # WARNING 级别，不应该匹配
        )

        # Mock 查询结果
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sub1, sub2]
        db_session.query.return_value = mock_query

        result = service.match_subscriptions(alert, rule)

        # 应该只匹配到 sub1
        assert len(result) == 1
        assert result[0].id == 1

    def test_match_subscriptions_filter_by_quiet_hours(self):
        """测试按免打扰时段过滤"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        rule = MockAlertRule(id=1, rule_type="DELAY")

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            rule=rule,
        )

        # 假设当前时间是 12:00
        with patch("app.services.alert_subscription_service.datetime") as mock_dt:
            mock_dt.now.return_value.time.return_value = time(12, 0)

            sub1 = MockAlertSubscription(
                id=1,
                user_id=1,
                alert_type="DELAY",
                quiet_start="22:00",  # 不在免打扰时段
                quiet_end="08:00",
            )
            sub2 = MockAlertSubscription(
                id=2,
                user_id=2,
                alert_type="DELAY",
                quiet_start="10:00",  # 在免打扰时段
                quiet_end="14:00",
            )

            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.all.return_value = [sub1, sub2]
            db_session.query.return_value = mock_query

            result = service.match_subscriptions(alert, rule)

            # 应该只匹配到 sub1（不在免打扰时段）
            assert len(result) == 1
            assert result[0].id == 1


# ===== Tests for get_notification_recipients =====


class TestGetNotificationRecipients:
    """测试 get_notification_recipients 方法"""

    def test_get_notification_recipients_no_rule(self):
        """测试没有规则的情况"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            rule=None,
        )

        result = service.get_notification_recipients(alert)

        expected = {"user_ids": [], "channels": ["SYSTEM"], "subscriptions": []}
        assert result == expected

    def test_get_notification_recipients_with_subscriptions(self):
        """测试有匹配订阅的情况"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        rule = MockAlertRule(id=1, rule_type="DELAY")

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            rule=rule,
        )

        # 创建订阅配置
        sub1 = MockAlertSubscription(
            id=1, user_id=1, alert_type="DELAY", notify_channels=["SYSTEM", "EMAIL"]
        )
        sub2 = MockAlertSubscription(
            id=2, user_id=2, alert_type="DELAY", notify_channels=["SYSTEM"]
        )

        # Mock match_subscriptions
        with patch.object(service, "match_subscriptions", return_value=[sub1, sub2]):
            result = service.get_notification_recipients(alert, rule)

            assert set(result["user_ids"]) == {1, 2}
            assert set(result["channels"]) == {"SYSTEM", "EMAIL"}
            assert len(result["subscriptions"]) == 2

    def test_get_notification_recipients_with_rule_config(self):
        """测试使用规则配置的情况"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        rule = MockAlertRule(
            id=1,
            rule_type="DELAY",
            notify_users=[10, 20],
            notify_channels=["EMAIL", "SMS"],
        )

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            rule=rule,
        )

        # 没有匹配的订阅
        with patch.object(service, "match_subscriptions", return_value=[]):
            result = service.get_notification_recipients(alert, rule)

            assert set(result["user_ids"]) == {10, 20}
            assert set(result["channels"]) == {"EMAIL", "SMS"}
            assert len(result["subscriptions"]) == 0

    def test_get_notification_recipients_merge_subscription_and_rule(self):
        """测试合并订阅和规则配置"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        rule = MockAlertRule(
            id=1, rule_type="DELAY", notify_users=[10], notify_channels=["EMAIL"]
        )

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            rule=rule,
        )

        sub1 = MockAlertSubscription(
            id=1, user_id=1, alert_type="DELAY", notify_channels=["SYSTEM"]
        )

        with patch.object(service, "match_subscriptions", return_value=[sub1]):
            result = service.get_notification_recipients(alert, rule)

            # 应该合并用户ID和通知渠道
            assert set(result["user_ids"]) == {1, 10}
            assert set(result["channels"]) == {"SYSTEM", "EMAIL"}
            assert len(result["subscriptions"]) == 1

    def test_get_notification_recipients_no_config(self):
        """测试没有任何配置的情况"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        rule = MockAlertRule(
            id=1, rule_type="DELAY", notify_users=None, notify_channels=None
        )

        alert = MockAlertRecord(
            id=1,
            alert_level=AlertLevelEnum.WARNING.value,
            alert_type="DELAY",
            rule=rule,
        )

        with patch.object(service, "match_subscriptions", return_value=[]):
            result = service.get_notification_recipients(alert, rule)

            assert result["user_ids"] == []
            assert result["channels"] == ["SYSTEM"]
            assert len(result["subscriptions"]) == 0


# ===== Tests for get_user_subscriptions =====


class TestGetUserSubscriptions:
    """测试 get_user_subscriptions 方法"""

    def test_get_user_subscriptions_basic(self):
        """测试获取用户订阅"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        sub1 = MockAlertSubscription(id=1, user_id=1, alert_type="DELAY")
        sub2 = MockAlertSubscription(id=2, user_id=1, alert_type="BUDGET")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sub1, sub2]
        db_session.query.return_value = mock_query

        result = service.get_user_subscriptions(user_id=1)

        assert len(result) == 2

        # 验证查询参数
        db_session.query.assert_called_once()

    def test_get_user_subscriptions_with_alert_type(self):
        """测试按预警类型过滤"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        sub1 = MockAlertSubscription(id=1, user_id=1, alert_type="DELAY")

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sub1]
        db_session.query.return_value = mock_query

        result = service.get_user_subscriptions(user_id=1, alert_type="DELAY")

        assert len(result) == 1

    def test_get_user_subscriptions_with_project_id(self):
        """测试按项目ID过滤"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        sub1 = MockAlertSubscription(id=1, user_id=1, project_id=100)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sub1]
        db_session.query.return_value = mock_query

        result = service.get_user_subscriptions(user_id=1, project_id=100)

        assert len(result) == 1

    def test_get_user_subscriptions_inactive_filtered(self):
        """测试非激活订阅被过滤"""
        db_session = MagicMock()
        service = AlertSubscriptionService(db_session)

        sub1 = MockAlertSubscription(id=1, user_id=1, is_active=True)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sub1]
        db_session.query.return_value = mock_query

        result = service.get_user_subscriptions(user_id=1)

        # 应该只返回激活的订阅
        assert len(result) == 1
        assert result[0].is_active is True
