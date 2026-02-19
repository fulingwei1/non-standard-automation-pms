# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 预警升级器 (AlertUpgrader)
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

try:
    from app.services.alert_rule_engine.alert_upgrader import AlertUpgrader
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="alert_upgrader 导入失败")


def _make_upgrader():
    """构造测试用升级器实例（绕过__init__）"""
    upgrader = object.__new__(AlertUpgrader)
    upgrader.db = MagicMock()
    upgrader._notification_service = MagicMock()
    upgrader._subscription_service = MagicMock()
    return upgrader


class TestUpgradeAlert:
    def test_updates_alert_level(self):
        """升级后预警级别更新"""
        upgrader = _make_upgrader()
        upgrader.get_field_value = MagicMock(return_value=10)
        upgrader._subscription_service.get_notification_recipients.return_value = {
            "user_ids": [1], "channels": ["wechat"]
        }

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.target_field = "delay_days"

        with patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="升级标题"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="升级内容"
        ):
            result = upgrader.upgrade_alert(alert, "RED", {"target_name": "PJ001"})

        assert alert.alert_level == "RED"
        assert alert.is_escalated is True
        assert alert.escalated_at is not None

    def test_sends_force_notification_on_upgrade(self):
        """升级时强制发送通知"""
        upgrader = _make_upgrader()
        upgrader.get_field_value = MagicMock(return_value=None)
        upgrader._subscription_service.get_notification_recipients.return_value = {
            "user_ids": [2, 3], "channels": ["email"]
        }

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.target_field = None

        with patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="标题"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="内容"
        ):
            upgrader.upgrade_alert(alert, "RED", {})

        upgrader._notification_service.send_alert_notification.assert_called_once()
        call_kwargs = upgrader._notification_service.send_alert_notification.call_args
        # force_send should be True
        assert call_kwargs.kwargs.get("force_send") is True

    def test_no_rule_sends_force_notification(self):
        """无关联规则时仍强制发送通知"""
        upgrader = _make_upgrader()

        alert = MagicMock()
        alert.rule = None

        result = upgrader.upgrade_alert(alert, "RED", {})

        upgrader._notification_service.send_alert_notification.assert_called_once_with(
            alert=alert, force_send=True
        )

    def test_notification_failure_does_not_raise(self):
        """通知失败不影响升级操作"""
        upgrader = _make_upgrader()
        upgrader.get_field_value = MagicMock(return_value=None)
        upgrader._subscription_service.get_notification_recipients.side_effect = RuntimeError("通知异常")

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.target_field = None

        with patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="标题"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="内容"
        ):
            # 不应抛出异常
            result = upgrader.upgrade_alert(alert, "ORANGE", {})

        assert alert.alert_level == "ORANGE"

    def test_db_add_and_flush_called(self):
        """升级时调用db.add和db.flush"""
        upgrader = _make_upgrader()
        upgrader.get_field_value = MagicMock(return_value=None)
        upgrader._subscription_service.get_notification_recipients.return_value = {
            "user_ids": [], "channels": []
        }

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.rule.target_field = None

        with patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_title",
            return_value="标题"
        ), patch(
            "app.services.alert_rule_engine.alert_generator.AlertGenerator.generate_alert_content",
            return_value="内容"
        ):
            upgrader.upgrade_alert(alert, "RED", {})

        upgrader.db.add.assert_called_once_with(alert)
        upgrader.db.flush.assert_called_once()


class TestCheckLevelEscalation:
    def test_no_rule_returns_none(self):
        """无关联规则时返回None"""
        upgrader = _make_upgrader()

        alert = MagicMock()
        alert.rule = None

        result = upgrader.check_level_escalation(alert, {})
        assert result is None

    def test_recently_escalated_returns_none(self):
        """24小时内已升级时返回None"""
        upgrader = _make_upgrader()

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.is_escalated = True
        alert.escalated_at = datetime.now() - timedelta(hours=5)  # 5小时前

        result = upgrader.check_level_escalation(alert, {})
        assert result is None

    def test_higher_level_triggers_upgrade(self):
        """新级别更高时触发升级"""
        upgrader = _make_upgrader()
        upgrader.upgrade_alert = MagicMock(return_value=MagicMock())
        upgrader.level_priority = MagicMock(
            side_effect=lambda l: {"YELLOW": 1, "RED": 2, "ORANGE": 3}.get(l, 0)
        )

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.is_escalated = False
        alert.alert_level = "YELLOW"

        with patch(
            "app.services.alert_rule_engine.level_determiner.LevelDeterminer"
        ) as mock_ld:
            mock_ld.determine_alert_level.return_value = "RED"
            result = upgrader.check_level_escalation(alert, {"delay_days": 15})

        upgrader.upgrade_alert.assert_called_once()
        assert result is not None

    def test_same_level_no_upgrade(self):
        """新级别相同时不触发升级"""
        upgrader = _make_upgrader()
        upgrader.upgrade_alert = MagicMock()
        upgrader.level_priority = MagicMock(
            side_effect=lambda l: {"YELLOW": 1, "RED": 2}.get(l, 0)
        )

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.is_escalated = False
        alert.alert_level = "RED"

        with patch(
            "app.services.alert_rule_engine.level_determiner.LevelDeterminer"
        ) as mock_ld:
            mock_ld.determine_alert_level.return_value = "RED"
            result = upgrader.check_level_escalation(alert, {})

        upgrader.upgrade_alert.assert_not_called()
        assert result is None

    def test_old_escalation_allows_new_upgrade(self):
        """超过24小时的升级记录允许再次升级"""
        upgrader = _make_upgrader()
        upgrader.upgrade_alert = MagicMock(return_value=MagicMock())
        upgrader.level_priority = MagicMock(
            side_effect=lambda l: {"YELLOW": 1, "RED": 2}.get(l, 0)
        )

        alert = MagicMock()
        alert.rule = MagicMock()
        alert.is_escalated = True
        alert.escalated_at = datetime.now() - timedelta(hours=25)  # 超过24小时
        alert.alert_level = "YELLOW"

        with patch(
            "app.services.alert_rule_engine.level_determiner.LevelDeterminer"
        ) as mock_ld:
            mock_ld.determine_alert_level.return_value = "RED"
            result = upgrader.check_level_escalation(alert, {})

        upgrader.upgrade_alert.assert_called_once()
