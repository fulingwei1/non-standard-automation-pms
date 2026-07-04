# -*- coding: utf-8 -*-
"""alert_subscription_service单元测试"""
from unittest.mock import Mock

from app.services.alert.alert_subscription_service import AlertSubscriptionService


class TestAlertSubscriptionServiceInit:
    def test_init(self):
        service = AlertSubscriptionService(Mock())
        assert service is not None


class TestAlertSubscriptionServiceDefaultRecipients:
    def test_defaults_to_project_pm_and_handler_when_no_subscription_or_rule_users(self):
        """AS-25: 无订阅/规则指定用户时，不能返回空导致预警无人接收。"""
        service = AlertSubscriptionService(Mock())
        service.match_subscriptions = Mock(return_value=[])

        rule = Mock(
            id=10,
            rule_type="MILESTONE_DUE",
            rule_name="里程碑超期",
            notify_users=None,
            notify_channels=None,
        )
        alert = Mock(rule=rule, project_id=20, handler_id=7)
        alert.project = Mock(pm_id=3)

        result = service.get_notification_recipients(alert, rule)

        assert sorted(result["user_ids"]) == [3, 7]
        assert result["channels"] == ["SYSTEM"]
