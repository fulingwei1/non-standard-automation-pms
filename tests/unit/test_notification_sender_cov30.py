# -*- coding: utf-8 -*-
"""
Unit tests for NotificationSender (第三十批)
"""
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.timesheet_reminder.notification_sender import NotificationSender


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def sender(mock_db):
    return NotificationSender(db=mock_db)


@pytest.fixture
def mock_reminder():
    reminder = MagicMock()
    reminder.reminder_no = "REM-20240101-001"
    reminder.user_id = 1
    reminder.title = "工时提醒"
    reminder.content = "请填写工时"
    reminder.notification_channels = ["SYSTEM"]
    reminder.reminder_type = MagicMock()
    reminder.reminder_type.value = "DAILY_REMINDER"
    reminder.priority = "NORMAL"
    reminder.source_type = "timesheet"
    reminder.source_id = 100
    reminder.extra_data = {}
    return reminder


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.username = "user01"
    user.email = "user01@example.com"
    return user


# ---------------------------------------------------------------------------
# send_reminder_notification
# ---------------------------------------------------------------------------

class TestSendReminderNotification:
    def test_returns_empty_dict_when_user_not_found(self, sender, mock_db, mock_reminder):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = sender.send_reminder_notification(mock_reminder)
        assert result == {}

    def test_sends_system_notification_by_default(self, sender, mock_db, mock_reminder, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_reminder.notification_channels = ["SYSTEM"]

        with patch.object(sender, "_send_system_notification", return_value=True) as mock_sys:
            result = sender.send_reminder_notification(mock_reminder)

        assert result.get("SYSTEM") is True
        mock_sys.assert_called_once_with(mock_reminder, mock_user)

    def test_handles_multiple_channels(self, sender, mock_db, mock_reminder, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_reminder.notification_channels = ["SYSTEM", "EMAIL"]

        with patch.object(sender, "_send_system_notification", return_value=True):
            with patch.object(sender, "_send_email_notification", return_value=False):
                result = sender.send_reminder_notification(mock_reminder)

        assert result["SYSTEM"] is True
        assert result["EMAIL"] is False

    def test_uses_provided_channels_override(self, sender, mock_db, mock_reminder, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch.object(sender, "_send_email_notification", return_value=True) as mock_email:
            result = sender.send_reminder_notification(mock_reminder, channels=["EMAIL"])

        mock_email.assert_called_once()
        assert result["EMAIL"] is True

    def test_handles_unknown_channel_gracefully(self, sender, mock_db, mock_reminder, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_reminder.notification_channels = ["UNKNOWN_CHANNEL"]

        result = sender.send_reminder_notification(mock_reminder)
        assert result.get("UNKNOWN_CHANNEL") is False

    def test_handles_channel_exception_gracefully(self, sender, mock_db, mock_reminder, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_reminder.notification_channels = ["SYSTEM"]

        with patch.object(sender, "_send_system_notification", side_effect=Exception("DB error")):
            result = sender.send_reminder_notification(mock_reminder)

        assert result.get("SYSTEM") is False


# ---------------------------------------------------------------------------
# _send_system_notification
# ---------------------------------------------------------------------------

class TestSendSystemNotification:
    def test_creates_notification_and_commits(self, sender, mock_db, mock_reminder, mock_user):
        result = sender._send_system_notification(mock_reminder, mock_user)

        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_rollbacks_on_error(self, sender, mock_db, mock_reminder, mock_user):
        mock_db.add.side_effect = Exception("DB failure")

        result = sender._send_system_notification(mock_reminder, mock_user)

        assert result is False
        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# _send_email_notification
# ---------------------------------------------------------------------------

class TestSendEmailNotification:
    def test_returns_false_when_smtp_not_configured(self, sender, mock_reminder, mock_user):
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.SMTP_HOST = None

            result = sender._send_email_notification(mock_reminder, mock_user)
        assert result is False

    def test_returns_false_when_user_has_no_email(self, sender, mock_reminder, mock_user):
        mock_user.email = None
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"

            result = sender._send_email_notification(mock_reminder, mock_user)
        assert result is False


# ---------------------------------------------------------------------------
# _send_wechat_notification
# ---------------------------------------------------------------------------

class TestSendWechatNotification:
    def test_returns_false_when_wechat_not_configured(self, sender, mock_reminder, mock_user):
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.WECHAT_CORP_ID = None

            result = sender._send_wechat_notification(mock_reminder, mock_user)
        assert result is False
