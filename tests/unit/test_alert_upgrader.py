# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch


class TestAlertUpgrader:
    def setup_method(self):
        self.db = MagicMock()
        from app.services.alert.rule_engine.alert_upgrader import AlertUpgrader

        self.upgrader = AlertUpgrader(self.db)

    def test_upgrade_alert_updates_level_and_content(self):
        alert = MagicMock()
        alert.alert_level = "WARNING"
        alert.rule = MagicMock(target_field="cost")
        target_data = {"target_type": "PROJECT", "target_id": 1}

        self.upgrader.get_field_value = MagicMock(return_value=100)
        self.upgrader._subscription_service = MagicMock()
        self.upgrader._subscription_service.get_notification_recipients.return_value = {
            "user_ids": [1],
            "channels": ["email"],
        }
        self.upgrader._notification_service = MagicMock()

        with patch("app.services.alert.rule_engine.alert_upgrader.AlertGenerator") as mock_gen:
            mock_gen.generate_alert_title.return_value = "title"
            mock_gen.generate_alert_content.return_value = "content"
            result = self.upgrader.upgrade_alert(alert, "CRITICAL", target_data)

        assert result.alert_level == "CRITICAL"
        assert result.is_escalated is True
        self.db.add.assert_called()
        self.db.flush.assert_called()

    def test_upgrade_alert_notification_failure_does_not_raise(self):
        alert = MagicMock()
        alert.alert_level = "WARNING"
        alert.rule = None
        self.upgrader._notification_service = MagicMock(side_effect=Exception("fail"))

        result = self.upgrader.upgrade_alert(alert, "CRITICAL", {})
        assert result.alert_level == "CRITICAL"

    def test_check_level_escalation_no_rule(self):
        alert = MagicMock(rule=None)
        assert self.upgrader.check_level_escalation(alert, {}) is None

    def test_check_level_escalation_recently_escalated(self):
        alert = MagicMock()
        alert.rule = MagicMock()
        alert.is_escalated = True
        alert.escalated_at = datetime.now() - timedelta(hours=1)
        assert self.upgrader.check_level_escalation(alert, {}) is None

    def test_check_level_escalation_upgrades_when_higher(self):
        alert = MagicMock()
        alert.rule = MagicMock()
        alert.is_escalated = False
        alert.escalated_at = None
        alert.alert_level = "WARNING"

        self.upgrader.level_priority = MagicMock(side_effect=lambda x: {"WARNING": 1, "CRITICAL": 2}[x])
        self.upgrader.upgrade_alert = MagicMock(return_value=alert)

        with patch("app.services.alert.rule_engine.level_determiner.LevelDeterminer") as mock_ld:
            mock_ld.determine_alert_level.return_value = "CRITICAL"
            result = self.upgrader.check_level_escalation(alert, {})

        assert result is not None
        self.upgrader.upgrade_alert.assert_called_once()

    def test_check_level_escalation_no_upgrade_when_same_level(self):
        alert = MagicMock()
        alert.rule = MagicMock()
        alert.is_escalated = False
        alert.escalated_at = None
        alert.alert_level = "WARNING"

        self.upgrader.level_priority = MagicMock(return_value=1)

        with patch("app.services.alert.rule_engine.level_determiner.LevelDeterminer") as mock_ld:
            mock_ld.determine_alert_level.return_value = "WARNING"
            result = self.upgrader.check_level_escalation(alert, {})

        assert result is None
