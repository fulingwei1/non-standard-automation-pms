# -*- coding: utf-8 -*-
"""
notification_service.py 单元测试（第二批）
"""
import pytest
from unittest.mock import MagicMock, patch, MagicMock


# ─── 1. Enums 枚举值 ─────────────────────────────────────────────────────────
def test_notification_channel_values():
    from app.services.notification_service import NotificationChannel
    assert NotificationChannel.SYSTEM.value == "system"
    assert NotificationChannel.EMAIL.value == "email"
    assert NotificationChannel.WEB.value == "web"


def test_notification_priority_values():
    from app.services.notification_service import NotificationPriority
    assert NotificationPriority.LOW.value == "low"
    assert NotificationPriority.URGENT.value == "urgent"


def test_notification_type_values():
    from app.services.notification_service import NotificationType
    assert NotificationType.TASK_ASSIGNED.value == "task_assigned"
    assert NotificationType.DEADLINE_REMINDER.value == "deadline_reminder"


# ─── 2. NotificationService._infer_category ──────────────────────────────────
def test_infer_category_task():
    from app.services.notification_service import NotificationService, NotificationType

    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = False
        mock_settings.SMS_ENABLED = False
        mock_settings.WECHAT_ENABLED = False
        mock_settings.WECHAT_WEBHOOK_URL = None
        svc = NotificationService(MagicMock())

    cat = svc._infer_category(NotificationType.TASK_ASSIGNED)
    assert cat == "task"


def test_infer_category_project():
    from app.services.notification_service import NotificationService, NotificationType

    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = False
        mock_settings.SMS_ENABLED = False
        mock_settings.WECHAT_ENABLED = False
        mock_settings.WECHAT_WEBHOOK_URL = None
        svc = NotificationService(MagicMock())

    cat = svc._infer_category(NotificationType.PROJECT_UPDATE)
    assert cat == "project"


def test_infer_category_general():
    from app.services.notification_service import NotificationService, NotificationType

    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = False
        mock_settings.SMS_ENABLED = False
        mock_settings.WECHAT_ENABLED = False
        mock_settings.WECHAT_WEBHOOK_URL = None
        svc = NotificationService(MagicMock())

    cat = svc._infer_category(NotificationType.SYSTEM_ANNOUNCEMENT)
    assert cat == "general"


# ─── 3. NotificationService._get_enabled_channels ───────────────────────────
def test_enabled_channels_web_only():
    from app.services.notification_service import NotificationService, NotificationChannel

    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = False
        mock_settings.SMS_ENABLED = False
        mock_settings.WECHAT_ENABLED = False
        mock_settings.WECHAT_WEBHOOK_URL = None
        svc = NotificationService(MagicMock())
        channels = svc._get_enabled_channels()

    assert NotificationChannel.WEB in channels


def test_enabled_channels_with_email():
    from app.services.notification_service import NotificationService, NotificationChannel

    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.EMAIL_ENABLED = True
        mock_settings.SMS_ENABLED = False
        mock_settings.WECHAT_ENABLED = False
        mock_settings.WECHAT_WEBHOOK_URL = None
        svc = NotificationService(MagicMock())
        channels = svc._get_enabled_channels()

    assert NotificationChannel.EMAIL in channels


# ─── 4. AlertNotificationService.get_unread_count ───────────────────────────
def test_get_unread_count_returns_int():
    from app.services.notification_service import AlertNotificationService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.count.return_value = 3

    with patch("app.services.notification_service.get_notification_service"):
        svc = AlertNotificationService(mock_db)
        count = svc.get_unread_count(user_id=1)

    assert count == 3


def test_get_unread_count_on_error():
    from app.services.notification_service import AlertNotificationService

    mock_db = MagicMock()
    mock_db.query.side_effect = Exception("DB error")

    with patch("app.services.notification_service.get_notification_service"):
        svc = AlertNotificationService(mock_db)
        count = svc.get_unread_count(user_id=1)

    assert count == 0


# ─── 5. AlertNotificationService.mark_notification_read ─────────────────────
def test_mark_notification_read_not_found():
    from app.services.notification_service import AlertNotificationService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.notification_service.get_notification_service"):
        svc = AlertNotificationService(mock_db)
        result = svc.mark_notification_read(999, 1)

    assert result is False


def test_mark_notification_read_success():
    from app.services.notification_service import AlertNotificationService

    mock_notif = MagicMock()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_notif

    with patch("app.services.notification_service.get_notification_service"):
        svc = AlertNotificationService(mock_db)
        result = svc.mark_notification_read(1, 1)

    assert result is True
    assert mock_notif.status == "SENT"
    mock_db.commit.assert_called_once()


# ─── 6. AlertNotificationService.batch_mark_read ────────────────────────────
def test_batch_mark_read_success():
    from app.services.notification_service import AlertNotificationService

    n1 = MagicMock()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [n1]

    with patch("app.services.notification_service.get_notification_service"):
        svc = AlertNotificationService(mock_db)
        result = svc.batch_mark_read([1], user_id=1)

    assert result["success"] is True
    assert result["success_count"] == 1
