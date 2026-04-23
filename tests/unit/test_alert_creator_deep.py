# -*- coding: utf-8 -*-
"""AlertCreator 深度覆盖测试。"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.alert.rule_engine.alert_creator import AlertCreator


class TestAlertCreatorDeep:
    def test_should_create_alert_returns_none_when_target_missing(self):
        db = MagicMock()
        creator = AlertCreator(db)
        rule = SimpleNamespace(id=1)

        assert creator.should_create_alert(rule, {"target_type": "project"}, "HIGH") is None
        db.query.assert_not_called()

    def test_should_create_alert_returns_existing_alert(self):
        existing_alert = SimpleNamespace(id=99)
        query = MagicMock()
        query.filter.return_value.first.return_value = existing_alert
        db = MagicMock()
        db.query.return_value = query

        creator = AlertCreator(db)
        rule = SimpleNamespace(id=1)
        result = creator.should_create_alert(
            rule,
            {"target_type": "project", "target_id": 123},
            "HIGH",
        )

        assert result is existing_alert
        db.query.assert_called_once()

    def test_notification_service_lazy_loads_from_legacy_import_path(self):
        db = MagicMock()
        creator = AlertCreator(db)

        fake_module = SimpleNamespace()
        fake_module.AlertNotificationService = MagicMock(return_value="notify-service")

        with patch.dict(sys.modules, {"app.services.notification.notification_service": fake_module}):
            result = creator.notification_service

        assert result == "notify-service"
        fake_module.AlertNotificationService.assert_called_once_with(db)

    def test_subscription_service_lazy_loads_from_legacy_import_path(self):
        db = MagicMock()
        creator = AlertCreator(db)

        fake_module = SimpleNamespace()
        fake_module.AlertSubscriptionService = MagicMock(return_value="subscription-service")

        with patch.dict(sys.modules, {"app.services.alert.alert_subscription_service": fake_module}):
            result = creator.subscription_service

        assert result == "subscription-service"
        fake_module.AlertSubscriptionService.assert_called_once_with(db)

    def test_create_alert_sends_notification_to_subscription_recipients(self):
        db = MagicMock()
        creator = AlertCreator(db)
        creator._subscription_service = MagicMock()
        creator._notification_service = MagicMock()
        creator._subscription_service.get_notification_recipients.return_value = {
            "user_ids": [7, 8],
            "channels": ["IN_APP", "EMAIL"],
        }
        creator.get_field_value = MagicMock(return_value=88)

        rule = SimpleNamespace(id=11, target_field="progress", threshold_value=90)
        target_data = {
            "target_type": "project",
            "target_id": 3,
            "target_no": "PRJ-003",
            "target_name": "测试项目",
            "project_id": 3,
        }

        with patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_no",
            return_value="ALERT-001",
        ), patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="标题",
        ), patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="内容",
        ):
            alert = creator.create_alert(rule, target_data, "HIGH", context={"x": 1})

        assert alert.alert_no == "ALERT-001"
        assert alert.trigger_value == "88"
        assert alert.threshold_value == 90
        db.add.assert_called_once_with(alert)
        db.flush.assert_called_once()
        creator._notification_service.send_alert_notification.assert_called_once_with(
            alert=alert,
            user_ids=[7, 8],
            channels=["IN_APP", "EMAIL"],
        )

    def test_create_alert_falls_back_to_default_notification(self):
        db = MagicMock()
        creator = AlertCreator(db)
        creator._subscription_service = MagicMock()
        creator._notification_service = MagicMock()
        creator._subscription_service.get_notification_recipients.return_value = {
            "user_ids": [],
            "channels": ["IN_APP"],
        }
        creator.get_field_value = MagicMock(return_value=None)

        rule = SimpleNamespace(id=12, target_field=None, threshold_value=50)
        target_data = {"target_type": "machine", "target_id": 5, "machine_id": 5}

        with patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_no",
            return_value="ALERT-002",
        ), patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="标题2",
        ), patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="内容2",
        ):
            alert = creator.create_alert(rule, target_data, "MEDIUM")

        assert alert.trigger_value is None
        creator._notification_service.send_alert_notification.assert_called_once_with(alert=alert)

    def test_create_alert_keeps_working_when_notification_fails(self):
        db = MagicMock()
        creator = AlertCreator(db)
        creator._subscription_service = MagicMock()
        creator._notification_service = MagicMock()
        creator._subscription_service.get_notification_recipients.return_value = {
            "user_ids": [1],
            "channels": ["EMAIL"],
        }
        creator._notification_service.send_alert_notification.side_effect = RuntimeError("boom")
        creator.get_field_value = MagicMock(return_value=12)

        rule = SimpleNamespace(id=13, target_field="score", threshold_value=10)
        target_data = {"target_type": "project", "target_id": 6}

        with patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_no",
            return_value="ALERT-003",
        ), patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="标题3",
        ), patch(
            "app.services.alert.rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="内容3",
        ), patch("logging.getLogger") as mock_get_logger:
            alert = creator.create_alert(rule, target_data, "LOW")

        assert alert.alert_no == "ALERT-003"
        mock_get_logger.return_value.error.assert_called_once()
