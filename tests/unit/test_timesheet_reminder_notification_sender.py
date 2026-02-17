# -*- coding: utf-8 -*-
"""
NotificationSender 单元测试

覆盖：
- send_reminder_notification (分发到各渠道)
- _send_system_notification (系统通知)
- _send_email_notification (邮件通知)
- _send_wechat_notification (企业微信)
- _generate_email_html
- _generate_reminder_url
- send_batch_reminders (批量发送)
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.timesheet_reminder.notification_sender import NotificationSender


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def sender(db):
    return NotificationSender(db)


def _make_reminder(
    reminder_no="RM20240101000001",
    user_id=1,
    reminder_type=None,
    title="工时提醒",
    content="请及时填报工时",
    priority="NORMAL",
    notification_channels=None,
    source_type="timesheet",
    source_id=100,
    extra_data=None,
):
    r = MagicMock()
    r.reminder_no = reminder_no
    r.user_id = user_id
    r.reminder_type = MagicMock(value="MISSING_TIMESHEET")
    r.title = title
    r.content = content
    r.priority = priority
    r.notification_channels = notification_channels or ["SYSTEM"]
    r.source_type = source_type
    r.source_id = source_id
    r.extra_data = extra_data or {}
    return r


def _make_user(user_id=1, username="testuser", email=None):
    u = MagicMock()
    u.id = user_id
    u.username = username
    u.email = email
    return u


# ---------------------------------------------------------------------------
# Tests: send_reminder_notification
# ---------------------------------------------------------------------------

class TestSendReminderNotification:
    def test_user_not_found_returns_empty(self, sender, db):
        db.query.return_value.filter.return_value.first.return_value = None
        reminder = _make_reminder(user_id=999)
        result = sender.send_reminder_notification(reminder)
        assert result == {}

    def test_system_channel_success(self, sender, db):
        user = _make_user()
        db.query.return_value.filter.return_value.first.return_value = user

        with patch.object(sender, "_send_system_notification", return_value=True):
            result = sender.send_reminder_notification(
                _make_reminder(notification_channels=["SYSTEM"]),
                channels=["SYSTEM"],
            )
        assert result["SYSTEM"] is True

    def test_email_channel_fails_gracefully(self, sender, db):
        user = _make_user()
        db.query.return_value.filter.return_value.first.return_value = user

        with patch.object(sender, "_send_email_notification", side_effect=Exception("SMTP error")):
            result = sender.send_reminder_notification(
                _make_reminder(),
                channels=["EMAIL"],
            )
        assert result["EMAIL"] is False

    def test_unknown_channel_returns_false(self, sender, db):
        user = _make_user()
        db.query.return_value.filter.return_value.first.return_value = user

        result = sender.send_reminder_notification(
            _make_reminder(),
            channels=["UNKNOWN_CHAN"],
        )
        assert result["UNKNOWN_CHAN"] is False

    def test_default_channels_from_reminder(self, sender, db):
        user = _make_user()
        db.query.return_value.filter.return_value.first.return_value = user
        reminder = _make_reminder(notification_channels=["SYSTEM"])

        with patch.object(sender, "_send_system_notification", return_value=True):
            result = sender.send_reminder_notification(reminder)  # no channels arg
        assert "SYSTEM" in result

    def test_multiple_channels(self, sender, db):
        user = _make_user(email="u@example.com")
        db.query.return_value.filter.return_value.first.return_value = user

        with patch.object(sender, "_send_system_notification", return_value=True), \
             patch.object(sender, "_send_email_notification", return_value=True):
            result = sender.send_reminder_notification(
                _make_reminder(),
                channels=["SYSTEM", "EMAIL"],
            )
        assert result["SYSTEM"] is True
        assert result["EMAIL"] is True


# ---------------------------------------------------------------------------
# Tests: _send_system_notification
# ---------------------------------------------------------------------------

class TestSendSystemNotification:
    def test_success(self, sender, db):
        db.add = MagicMock()
        db.commit = MagicMock()
        reminder = _make_reminder()
        user = _make_user()

        result = sender._send_system_notification(reminder, user)
        assert result is True
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_db_error_returns_false(self, sender, db):
        db.add = MagicMock(side_effect=Exception("DB error"))
        db.rollback = MagicMock()

        result = sender._send_system_notification(_make_reminder(), _make_user())
        assert result is False
        db.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: _send_email_notification
# ---------------------------------------------------------------------------

class TestSendEmailNotification:
    def test_no_smtp_config_returns_false(self, sender, db):
        """settings 中没有 SMTP_HOST → 直接返回 False"""
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.SMTP_HOST = ""
            result = sender._send_email_notification(_make_reminder(), _make_user())
        assert result is False

    def test_no_user_email_returns_false(self, sender, db):
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.example.com"
            user = _make_user(email=None)
            user.email = None
            result = sender._send_email_notification(_make_reminder(), user)
        assert result is False

    def test_smtp_send_success(self, sender, db):
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings, \
             patch("app.services.timesheet_reminder.notification_sender.smtplib.SMTP") as mock_smtp:
            mock_settings.SMTP_HOST = "smtp.example.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_FROM = "noreply@example.com"
            mock_settings.SMTP_USER = "user"
            mock_settings.SMTP_PASSWORD = "pass"
            mock_settings.SMTP_TLS = True

            ctx = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=ctx)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

            user = _make_user(email="test@example.com")
            result = sender._send_email_notification(_make_reminder(), user)
        assert result is True


# ---------------------------------------------------------------------------
# Tests: _send_wechat_notification
# ---------------------------------------------------------------------------

class TestSendWechatNotification:
    def test_no_corp_id_returns_false(self, sender, db):
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.WECHAT_CORP_ID = ""
            result = sender._send_wechat_notification(_make_reminder(), _make_user())
        assert result is False

    def test_no_wechat_user_id_returns_false(self, sender, db):
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.WECHAT_CORP_ID = "wxcorp123"
            user = _make_user()
            del user.wechat_user_id  # 模拟没有这个属性
            result = sender._send_wechat_notification(_make_reminder(), user)
        assert result is False

    def test_token_fetch_fails_returns_false(self, sender, db):
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.WECHAT_CORP_ID = "wxcorp123"
            user = _make_user()
            user.wechat_user_id = "wx_user_001"

            with patch.object(sender, "_get_wechat_access_token", return_value=None):
                result = sender._send_wechat_notification(_make_reminder(), user)
        assert result is False


# ---------------------------------------------------------------------------
# Tests: _generate_email_html
# ---------------------------------------------------------------------------

class TestGenerateEmailHtml:
    def test_contains_title_and_content(self, sender):
        reminder = _make_reminder(title="工时提醒", content="请填报工时")
        user = _make_user()
        html = sender._generate_email_html(reminder, user)
        assert "工时提醒" in html
        assert "请填报工时" in html

    def test_contains_extra_data(self, sender):
        reminder = _make_reminder(extra_data={"项目": "测试项目", "缺少天数": 3})
        user = _make_user()
        html = sender._generate_email_html(reminder, user)
        assert "测试项目" in html

    def test_no_extra_data_no_crash(self, sender):
        reminder = _make_reminder(extra_data=None)
        user = _make_user()
        html = sender._generate_email_html(reminder, user)
        assert isinstance(html, str)


# ---------------------------------------------------------------------------
# Tests: _generate_reminder_url
# ---------------------------------------------------------------------------

class TestGenerateReminderUrl:
    def test_timesheet_source_url(self, sender):
        reminder = _make_reminder(source_type="timesheet", source_id=42)
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.FRONTEND_URL = "http://app.example.com"
            url = sender._generate_reminder_url(reminder)
        assert "timesheet/42" in url

    def test_default_url_for_unknown_source(self, sender):
        reminder = _make_reminder(source_type="other", source_id=None)
        with patch("app.services.timesheet_reminder.notification_sender.settings") as mock_settings:
            mock_settings.FRONTEND_URL = "http://app.example.com"
            url = sender._generate_reminder_url(reminder)
        assert "notifications" in url


# ---------------------------------------------------------------------------
# Tests: send_batch_reminders
# ---------------------------------------------------------------------------

class TestSendBatchReminders:
    def test_all_success(self, sender, db):
        reminders = [_make_reminder(f"RM{i}") for i in range(3)]
        with patch.object(sender, "send_reminder_notification", return_value={"SYSTEM": True}):
            result = sender.send_batch_reminders(reminders, channels=["SYSTEM"])
        assert result["total"] == 3
        assert result["success"] == 3
        assert result["failed"] == 0

    def test_all_fail(self, sender, db):
        reminders = [_make_reminder(f"RM{i}") for i in range(2)]
        with patch.object(sender, "send_reminder_notification", return_value={"SYSTEM": False}):
            result = sender.send_batch_reminders(reminders, channels=["SYSTEM"])
        assert result["failed"] == 2

    def test_exception_counts_as_failed(self, sender, db):
        reminders = [_make_reminder("RM_ERR")]
        with patch.object(sender, "send_reminder_notification", side_effect=Exception("error")):
            result = sender.send_batch_reminders(reminders)
        assert result["failed"] == 1

    def test_empty_list(self, sender, db):
        result = sender.send_batch_reminders([])
        assert result["total"] == 0
        assert result["success"] == 0
        assert result["failed"] == 0
