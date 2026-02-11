# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from app.services.alert_rule_engine.alert_creator import AlertCreator


class TestAlertCreator:
    def setup_method(self):
        self.db = MagicMock()
        with patch("app.services.alert_rule_engine.alert_creator.ConditionEvaluator.__init__", return_value=None):
            self.creator = AlertCreator.__new__(AlertCreator)
            self.creator.db = self.db
            self.creator._notification_service = None
            self.creator._subscription_service = None

    def test_should_create_alert_no_target(self):
        rule = MagicMock()
        result = self.creator.should_create_alert(rule, {}, "WARNING")
        assert result is None

    def test_should_create_alert_existing(self):
        rule = MagicMock(id=1)
        existing = MagicMock()
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing
        result = self.creator.should_create_alert(
            rule, {"target_type": "PROJECT", "target_id": 1}, "WARNING"
        )
        assert result == existing

    def test_should_create_alert_none_existing(self):
        rule = MagicMock(id=1)
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = self.creator.should_create_alert(
            rule, {"target_type": "PROJECT", "target_id": 1}, "WARNING"
        )
        assert result is None

    def test_create_alert_success(self):
        rule = MagicMock(id=1, target_field="cost", threshold_value="100")
        target_data = {"target_type": "PROJECT", "target_id": 1}
        self.creator.get_field_value = MagicMock(return_value=150)
        self.creator._subscription_service = MagicMock()
        self.creator._subscription_service.get_notification_recipients.return_value = {
            "user_ids": [1], "channels": ["email"]
        }
        self.creator._notification_service = MagicMock()

        with patch("app.services.alert_rule_engine.alert_generator.AlertGenerator") as MockGen:
            MockGen.generate_alert_no.return_value = "ALT001"
            MockGen.generate_alert_title.return_value = "title"
            MockGen.generate_alert_content.return_value = "content"

            with patch("app.services.alert_rule_engine.alert_creator.AlertRecord") as MockRecord:
                MockRecord.return_value = MagicMock()
                result = self.creator.create_alert(rule, target_data, "WARNING")

        self.db.add.assert_called()
        self.db.flush.assert_called()

    def test_create_alert_notification_failure_silent(self):
        rule = MagicMock(id=1, target_field=None, threshold_value=None)
        target_data = {"target_type": "PROJECT", "target_id": 1}
        self.creator.get_field_value = MagicMock(return_value=None)
        self.creator._subscription_service = MagicMock()
        self.creator._subscription_service.get_notification_recipients.side_effect = Exception("fail")

        with patch("app.services.alert_rule_engine.alert_generator.AlertGenerator") as MockGen, \
             patch("app.services.alert_rule_engine.alert_creator.AlertRecord") as MockRecord:
            MockGen.generate_alert_no.return_value = "ALT001"
            MockGen.generate_alert_title.return_value = "t"
            MockGen.generate_alert_content.return_value = "c"
            MockRecord.return_value = MagicMock()
            result = self.creator.create_alert(rule, target_data, "WARNING")

        assert result is not None
