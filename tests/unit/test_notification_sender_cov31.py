# -*- coding: utf-8 -*-
"""
Unit tests for NotificationSender (第三十一批)
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.timesheet_reminder.notification_sender import NotificationSender


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def sender(mock_db):
    return NotificationSender(db=mock_db)


def _make_reminder(channels=None):
    reminder = MagicMock()
    reminder.user_id = 1
    reminder.reminder_no = "RMD-001"
    reminder.notification_channels = channels or ["SYSTEM"]
    reminder.reminder_type.value = "TIMESHEET_MISSING"
    reminder.title = "工时提醒"
    reminder.content = "请填写本周工时"
    reminder.priority = "NORMAL"
    reminder.source_type = "TIMESHEET"
    reminder.source_id = 100
    reminder.extra_data = {}
    return reminder


def _make_user(user_id=1, email="test@example.com"):
    user = MagicMock()
    user.id = user_id
    user.username = "user01"
    user.email = email
    return user


# ---------------------------------------------------------------------------
# send_reminder_notification
# ---------------------------------------------------------------------------

class TestSendReminderNotification:
    def test_returns_empty_when_user_not_found(self, sender, mock_db):
        reminder = _make_reminder()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None

        result = sender.send_reminder_notification(reminder)
        assert result == {}

    def test_system_channel_sends_notification(self, sender, mock_db):
        reminder = _make_reminder(channels=["SYSTEM"])
        user = _make_user()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = user

        with patch.object(sender, "_send_system_notification", return_value=True) as mock_sys:
            result = sender.send_reminder_notification(reminder)

        mock_sys.assert_called_once()
        assert result.get("SYSTEM") is True

    def test_email_channel_sends_notification(self, sender, mock_db):
        reminder = _make_reminder(channels=["EMAIL"])
        user = _make_user()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = user

        with patch.object(sender, "_send_email_notification", return_value=True) as mock_email:
            result = sender.send_reminder_notification(reminder)

        mock_email.assert_called_once()
        assert result.get("EMAIL") is True

    def test_wechat_channel_sends_notification(self, sender, mock_db):
        reminder = _make_reminder(channels=["WECHAT"])
        user = _make_user()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = user

        with patch.object(sender, "_send_wechat_notification", return_value=False) as mock_wechat:
            result = sender.send_reminder_notification(reminder)

        mock_wechat.assert_called_once()
        assert result.get("WECHAT") is False

    def test_unknown_channel_returns_false(self, sender, mock_db):
        reminder = _make_reminder(channels=["UNKNOWN"])
        user = _make_user()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = user

        result = sender.send_reminder_notification(reminder)
        assert result.get("UNKNOWN") is False

    def test_multiple_channels(self, sender, mock_db):
        reminder = _make_reminder(channels=["SYSTEM", "EMAIL"])
        user = _make_user()
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = user

        with patch.object(sender, "_send_system_notification", return_value=True), \
             patch.object(sender, "_send_email_notification", return_value=True):
            result = sender.send_reminder_notification(reminder)

        assert result.get("SYSTEM") is True
        assert result.get("EMAIL") is True


# ---------------------------------------------------------------------------
# _send_system_notification
# ---------------------------------------------------------------------------

class TestSendSystemNotification:
    def test_adds_notification_and_commits(self, sender, mock_db):
        reminder = _make_reminder()
        user = _make_user()

        with patch(
            "app.services.timesheet_reminder.notification_sender.Notification"
        ) as MockNotification:
            mock_notif = MagicMock()
            MockNotification.return_value = mock_notif

            result = sender._send_system_notification(reminder, user)

        assert result is True
        mock_db.add.assert_called_once_with(mock_notif)
        mock_db.commit.assert_called_once()

    def test_returns_false_on_exception(self, sender, mock_db):
        reminder = _make_reminder()
        user = _make_user()
        mock_db.add.side_effect = Exception("DB error")

        with patch("app.services.timesheet_reminder.notification_sender.Notification"):
            result = sender._send_system_notification(reminder, user)

        assert result is False
        mock_db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# _send_email_notification
# ---------------------------------------------------------------------------

class TestSendEmailNotification:
    def test_returns_false_when_smtp_not_configured(self, sender, mock_db):
        reminder = _make_reminder()
        user = _make_user()

        with patch(
            "app.services.timesheet_reminder.notification_sender.settings"
        ) as mock_settings:
            mock_settings.SMTP_HOST = ""

            result = sender._send_email_notification(reminder, user)

        assert result is False

    def test_returns_false_when_user_has_no_email(self, sender, mock_db):
        reminder = _make_reminder()
        user = _make_user(email="")

        with patch(
            "app.services.timesheet_reminder.notification_sender.settings"
        ) as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"

            result = sender._send_email_notification(reminder, user)

        assert result is False
