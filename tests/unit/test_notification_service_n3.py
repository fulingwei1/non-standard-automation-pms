# -*- coding: utf-8 -*-
"""
NotificationService / AlertNotificationService 深度覆盖测试（N3组）

覆盖：
- NotificationService.__init__ / _get_enabled_channels
- _map_old_channel_to_new / _map_old_priority_to_new / _infer_category
- send_notification (正常/无db/异常)
- send_task_assigned_notification / send_task_completed_notification
- send_deadline_reminder (urgent/normal)
- get_notification_service_instance
- AlertNotificationService.__init__
- create_alert_notification
- send_alert_notification (正常/无recipient/异常)
- get_user_notifications / mark_notification_read
- get_unread_count / batch_mark_read
"""

from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock
import pytest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_settings(**kwargs):
    s = MagicMock()
    s.EMAIL_ENABLED = kwargs.get("EMAIL_ENABLED", False)
    s.SMS_ENABLED = kwargs.get("SMS_ENABLED", False)
    s.WECHAT_ENABLED = kwargs.get("WECHAT_ENABLED", False)
    s.WECHAT_WEBHOOK_URL = kwargs.get("WECHAT_WEBHOOK_URL", None)
    return s


# ---------------------------------------------------------------------------
# NotificationService – initialization
# ---------------------------------------------------------------------------

class TestNotificationServiceInit:
    def test_web_channel_always_enabled(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        assert NotificationChannel.WEB in svc.enabled_channels

    def test_email_channel_when_enabled(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        with patch("app.services.notification_service.settings", _make_settings(EMAIL_ENABLED=True)):
            svc = NotificationService(MagicMock())
        assert NotificationChannel.EMAIL in svc.enabled_channels

    def test_sms_channel_when_enabled(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        with patch("app.services.notification_service.settings", _make_settings(SMS_ENABLED=True)):
            svc = NotificationService(MagicMock())
        assert NotificationChannel.SMS in svc.enabled_channels

    def test_wechat_channel_when_enabled(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        with patch("app.services.notification_service.settings", _make_settings(WECHAT_ENABLED=True)):
            svc = NotificationService(MagicMock())
        assert NotificationChannel.WECHAT in svc.enabled_channels

    def test_webhook_channel_when_url_set(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        with patch("app.services.notification_service.settings", _make_settings(WECHAT_WEBHOOK_URL="https://example.com")):
            svc = NotificationService(MagicMock())
        assert NotificationChannel.WEBHOOK in svc.enabled_channels

    def test_no_optional_channels_when_disabled(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        assert NotificationChannel.EMAIL not in svc.enabled_channels
        assert NotificationChannel.SMS not in svc.enabled_channels

    def test_init_with_db_session(self):
        from app.services.notification_service import NotificationService
        mock_db = MagicMock()
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(db=mock_db)
        assert svc._db is mock_db


# ---------------------------------------------------------------------------
# _map_old_channel_to_new
# ---------------------------------------------------------------------------

class TestMapOldChannelToNew:
    def test_maps_web_to_system(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        from app.services.channel_handlers.base import NotificationChannel as UC
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(db_session)
        result = svc._map_old_channel_to_new(NotificationChannel.WEB)
        assert result == UC.SYSTEM

    def test_maps_email_to_email(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        from app.services.channel_handlers.base import NotificationChannel as UC
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(db_session)
        result = svc._map_old_channel_to_new(NotificationChannel.EMAIL)
        assert result == UC.EMAIL

    def test_maps_wechat_to_wechat(self):
        from app.services.notification_service import NotificationService, NotificationChannel
        from app.services.channel_handlers.base import NotificationChannel as UC
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        result = svc._map_old_channel_to_new(NotificationChannel.WECHAT)
        assert result == UC.WECHAT


# ---------------------------------------------------------------------------
# _map_old_priority_to_new
# ---------------------------------------------------------------------------

class TestMapOldPriorityToNew:
    def test_enum_returns_value(self):
        from app.services.notification_service import NotificationService, NotificationPriority
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        assert svc._map_old_priority_to_new(NotificationPriority.HIGH) == "high"

    def test_string_returns_as_is(self):
        from app.services.notification_service import NotificationService
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        assert svc._map_old_priority_to_new("urgent") == "urgent"

    def test_non_string_converted_to_str(self):
        from app.services.notification_service import NotificationService
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        result = svc._map_old_priority_to_new(42)
        assert result == "42"


# ---------------------------------------------------------------------------
# _infer_category
# ---------------------------------------------------------------------------

class TestInferCategory:
    def test_task_type_infers_task_category(self):
        from app.services.notification_service import NotificationService, NotificationType
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        assert svc._infer_category(NotificationType.TASK_ASSIGNED) == "task"

    def test_project_update_infers_project(self):
        from app.services.notification_service import NotificationService, NotificationType
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        assert svc._infer_category(NotificationType.PROJECT_UPDATE) == "project"

    def test_unknown_type_returns_general(self):
        from app.services.notification_service import NotificationService
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        assert svc._infer_category("some_random_type") == "general"

    def test_deadline_reminder_returns_task(self):
        from app.services.notification_service import NotificationService, NotificationType
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        assert svc._infer_category(NotificationType.DEADLINE_REMINDER) == "task"


# ---------------------------------------------------------------------------
# send_notification
# ---------------------------------------------------------------------------

class TestSendNotification:
    def _make_service(self):
        from app.services.notification_service import NotificationService
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        return svc

    def test_returns_false_when_no_db(self):
        svc = self._make_service()
        from app.services.notification_service import NotificationType, NotificationPriority
        result = svc.send_notification(
            db=None,
            recipient_id=1,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="T",
            content="C",
        )
        assert result is False

    def test_returns_true_on_success(self):
        svc = self._make_service()
        from app.services.notification_service import NotificationType, NotificationPriority
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            result = svc.send_notification(
                db=mock_db,
                recipient_id=1,
                notification_type=NotificationType.TASK_ASSIGNED,
                title="测试",
                content="内容",
            )
        assert result is True

    def test_returns_false_on_service_failure(self):
        svc = self._make_service()
        from app.services.notification_service import NotificationType
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": False}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            result = svc.send_notification(
                db=mock_db,
                recipient_id=1,
                notification_type=NotificationType.TASK_ASSIGNED,
                title="T",
                content="C",
            )
        assert result is False

    def test_sends_with_specified_channels(self):
        svc = self._make_service()
        from app.services.notification_service import NotificationType, NotificationChannel
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            result = svc.send_notification(
                db=mock_db,
                recipient_id=2,
                notification_type=NotificationType.PROJECT_UPDATE,
                title="T",
                content="C",
                channels=[NotificationChannel.WEB, NotificationChannel.EMAIL],
            )
        assert result is True
        call_args = mock_unified.send_notification.call_args[0][0]
        assert call_args.channels is not None

    def test_sends_with_extra_data_and_link(self):
        svc = self._make_service()
        from app.services.notification_service import NotificationType
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            svc.send_notification(
                db=mock_db,
                recipient_id=1,
                notification_type=NotificationType.TASK_COMPLETED,
                title="T",
                content="C",
                data={"task_id": 5},
                link="/tasks/5",
            )
        call_args = mock_unified.send_notification.call_args[0][0]
        assert call_args.extra_data == {"task_id": 5}
        assert call_args.link_url == "/tasks/5"


# ---------------------------------------------------------------------------
# send_task_assigned_notification
# ---------------------------------------------------------------------------

class TestSendTaskAssignedNotification:
    def _make_service(self):
        from app.services.notification_service import NotificationService
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        return svc

    def test_includes_due_date_in_content(self):
        svc = self._make_service()
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            svc.send_task_assigned_notification(
                db=mock_db,
                assignee_id=1,
                task_name="装配工作",
                project_name="Alpha项目",
                task_id=10,
                due_date=datetime(2025, 6, 30),
            )
        request = mock_unified.send_notification.call_args[0][0]
        assert "2025-06-30" in request.content

    def test_no_due_date_works(self):
        svc = self._make_service()
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            result = svc.send_task_assigned_notification(
                db=mock_db,
                assignee_id=1,
                task_name="调试任务",
                project_name="Beta项目",
                task_id=20,
            )
        # should not raise


# ---------------------------------------------------------------------------
# send_task_completed_notification
# ---------------------------------------------------------------------------

class TestSendTaskCompletedNotification:
    def test_sends_completed_notification(self):
        from app.services.notification_service import NotificationService
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            svc.send_task_completed_notification(
                db=mock_db,
                task_owner_id=5,
                task_name="安装任务",
                project_name="Gamma项目",
            )
        request = mock_unified.send_notification.call_args[0][0]
        assert "安装任务" in request.title
        assert "Gamma项目" in request.content


# ---------------------------------------------------------------------------
# send_deadline_reminder
# ---------------------------------------------------------------------------

class TestSendDeadlineReminder:
    def _get_service(self):
        from app.services.notification_service import NotificationService
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = NotificationService(MagicMock())
        return svc

    def test_urgent_title_when_1_day_remaining(self):
        svc = self._get_service()
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            svc.send_deadline_reminder(
                db=mock_db,
                recipient_id=1,
                task_name="紧急任务",
                due_date=datetime(2025, 5, 1),
                days_remaining=1,
            )
        request = mock_unified.send_notification.call_args[0][0]
        assert "紧急" in request.title

    def test_normal_title_when_5_days_remaining(self):
        svc = self._get_service()
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            svc.send_deadline_reminder(
                db=mock_db,
                recipient_id=1,
                task_name="普通任务",
                due_date=datetime(2025, 5, 10),
                days_remaining=5,
            )
        request = mock_unified.send_notification.call_args[0][0]
        assert "紧急" not in request.title
        assert "提醒" in request.title

    def test_zero_days_also_triggers_urgent_message(self):
        svc = self._get_service()
        mock_db = MagicMock()
        mock_unified = MagicMock()
        mock_unified.send_notification.return_value = {"success": True}
        with patch("app.services.notification_service.get_notification_service", return_value=mock_unified):
            svc.send_deadline_reminder(
                db=mock_db,
                recipient_id=2,
                task_name="到期任务",
                due_date=datetime(2025, 4, 30),
                days_remaining=0,
            )
        request = mock_unified.send_notification.call_args[0][0]
        assert "紧急" in request.title


# ---------------------------------------------------------------------------
# get_notification_service_instance
# ---------------------------------------------------------------------------

class TestGetNotificationServiceInstance:
    def test_returns_notification_service(self):
        from app.services.notification_service import (
            get_notification_service_instance,
            NotificationService,
        )
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = get_notification_service_instance()
        assert isinstance(svc, NotificationService)

    def test_accepts_db_param(self):
        from app.services.notification_service import get_notification_service_instance
        mock_db = MagicMock()
        with patch("app.services.notification_service.settings", _make_settings()):
            svc = get_notification_service_instance(db=mock_db)
        assert svc._db is mock_db


# ---------------------------------------------------------------------------
# AlertNotificationService
# ---------------------------------------------------------------------------

class TestAlertNotificationService:
    def _make_service(self):
        from app.services.notification_service import AlertNotificationService
        mock_db = MagicMock()
        with patch("app.services.notification_service.get_notification_service", return_value=MagicMock()):
            svc = AlertNotificationService(db=mock_db)
        svc.db = mock_db
        return svc, mock_db

    def test_create_alert_notification_basic(self):
        from app.services.notification_service import AlertNotificationService
        mock_db = MagicMock()
        alert = MagicMock()
        alert.id = 1
        alert.assignee_id = 5
        result = AlertNotificationService.create_alert_notification(mock_db, alert, "SYSTEM")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_send_alert_notification_no_recipient_returns_false(self):
        svc, mock_db = self._make_service()
        alert = MagicMock()
        alert.project_id = 1
        # No assignee_id, no handler_id, no user
        alert.assignee_id = None
        alert.handler_id = None
        from unittest.mock import patch as p
        with p("app.services.notification_service.AlertNotificationService.send_alert_notification",
               wraps=svc.send_alert_notification):
            result = svc.send_alert_notification(alert=alert)
        assert result is False

    def test_send_alert_notification_uses_user_id(self):
        svc, mock_db = self._make_service()
        alert = MagicMock()
        alert.project_id = 1
        alert.alert_title = "缺料预警"
        alert.alert_content = "物料A缺料"
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch_alert_notifications.return_value = {"queued": True}
        with patch("app.services.notification_service.NotificationDispatcher", return_value=mock_dispatcher):
            user = MagicMock()
            user.id = 42
            result = svc.send_alert_notification(alert=alert, user=user, channels=["SYSTEM"])
        assert result is True

    def test_send_alert_notification_channel_normalization(self):
        svc, mock_db = self._make_service()
        alert = MagicMock()
        alert.project_id = 1
        alert.alert_title = "Test"
        alert.alert_content = "Content"
        alert.assignee_id = 1
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch_alert_notifications.return_value = {"sent": True}
        with patch("app.services.notification_service.NotificationDispatcher", return_value=mock_dispatcher):
            result = svc.send_alert_notification(
                alert=alert, user_ids=[1], channels=["WEB", "EMAIL", None, "INVALID"]
            )
        assert result is True

    def test_send_alert_notification_exception_returns_false(self):
        svc, mock_db = self._make_service()
        alert = MagicMock()
        alert.project_id = 1
        alert.assignee_id = 1
        with patch(
            "app.services.notification_service.NotificationDispatcher",
            side_effect=Exception("DB error"),
        ):
            result = svc.send_alert_notification(alert=alert, user_ids=[1])
        assert result is False

    def test_get_user_notifications_success(self):
        svc, mock_db = self._make_service()
        notif = MagicMock()
        notif.id = 1
        notif.alert_id = 5
        notif.notify_channel = "SYSTEM"
        notif.status = "SENT"
        notif.created_at = datetime(2024, 1, 1)
        notif.sent_at = datetime(2024, 1, 1, 1)
        notif.notify_title = "Test"
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [notif]
        alert = MagicMock()
        alert.alert_title = "缺料"
        alert.alert_level = "HIGH"
        mock_db.query.return_value.filter.return_value.first.return_value = alert
        result = svc.get_user_notifications(user_id=1)
        assert result["success"] is True
        assert result["total"] == 1

    def test_get_user_notifications_exception(self):
        svc, mock_db = self._make_service()
        mock_db.query.side_effect = Exception("query error")
        result = svc.get_user_notifications(user_id=1)
        assert result["success"] is False
        assert result["total"] == 0

    def test_mark_notification_read_success(self):
        svc, mock_db = self._make_service()
        notif = MagicMock()
        notif.status = "PENDING"
        mock_db.query.return_value.filter.return_value.first.return_value = notif
        result = svc.mark_notification_read(notification_id=1, user_id=2)
        assert result is True
        assert notif.status == "SENT"

    def test_mark_notification_read_not_found(self):
        svc, mock_db = self._make_service()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = svc.mark_notification_read(notification_id=999, user_id=1)
        assert result is False

    def test_mark_notification_read_exception(self):
        svc, mock_db = self._make_service()
        mock_db.query.side_effect = Exception("error")
        result = svc.mark_notification_read(notification_id=1, user_id=1)
        assert result is False

    def test_get_unread_count_returns_number(self):
        svc, mock_db = self._make_service()
        mock_db.query.return_value.filter.return_value.count.return_value = 7
        count = svc.get_unread_count(user_id=1)
        assert count == 7

    def test_get_unread_count_exception_returns_zero(self):
        svc, mock_db = self._make_service()
        mock_db.query.side_effect = Exception("error")
        count = svc.get_unread_count(user_id=1)
        assert count == 0

    def test_batch_mark_read_success(self):
        svc, mock_db = self._make_service()
        notif1 = MagicMock()
        notif1.status = "PENDING"
        notif2 = MagicMock()
        notif2.status = "PENDING"
        mock_db.query.return_value.filter.return_value.all.return_value = [notif1, notif2]
        result = svc.batch_mark_read(notification_ids=[1, 2], user_id=1)
        assert result["success"] is True
        assert result["success_count"] == 2
        assert notif1.status == "SENT"
        assert notif2.status == "SENT"

    def test_batch_mark_read_exception(self):
        svc, mock_db = self._make_service()
        mock_db.query.side_effect = Exception("error")
        result = svc.batch_mark_read(notification_ids=[1, 2], user_id=1)
        assert result["success"] is False
        assert result["success_count"] == 0
