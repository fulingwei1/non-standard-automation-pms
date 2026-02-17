# -*- coding: utf-8 -*-
"""
G3组 - 通知调度器服务单元测试（扩展）
目标文件: app/services/notification_dispatcher.py
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call

from app.services.notification_dispatcher import NotificationDispatcher
from app.services.channel_handlers.base import NotificationChannel, NotificationPriority


def make_dispatcher(db=None):
    """工厂：创建 NotificationDispatcher，patch 掉底层服务"""
    if db is None:
        db = MagicMock()
    mock_service = MagicMock()
    with patch("app.services.notification_dispatcher.get_notification_service",
               return_value=mock_service):
        dispatcher = NotificationDispatcher(db)
    dispatcher.unified_service = mock_service
    return dispatcher, mock_service, db


class TestNotificationDispatcherInit:
    def test_init_stores_db(self):
        db = MagicMock()
        dispatcher, _, _ = make_dispatcher(db)
        assert dispatcher.db is db

    def test_init_creates_unified_service(self):
        _, svc, _ = make_dispatcher()
        assert svc is not None


class TestMapChannelToUnified:
    """测试渠道映射"""

    def setup_method(self):
        self.dispatcher, _, _ = make_dispatcher()

    def test_system_channel(self):
        result = self.dispatcher._map_channel_to_unified("SYSTEM")
        assert result == NotificationChannel.SYSTEM

    def test_email_channel(self):
        result = self.dispatcher._map_channel_to_unified("EMAIL")
        assert result == NotificationChannel.EMAIL

    def test_wechat_channel(self):
        result = self.dispatcher._map_channel_to_unified("WECHAT")
        assert result == NotificationChannel.WECHAT

    def test_sms_channel(self):
        result = self.dispatcher._map_channel_to_unified("SMS")
        assert result == NotificationChannel.SMS

    def test_webhook_channel(self):
        result = self.dispatcher._map_channel_to_unified("WEBHOOK")
        assert result == NotificationChannel.WEBHOOK

    def test_unknown_channel_defaults_to_system(self):
        result = self.dispatcher._map_channel_to_unified("UNKNOWN_CHAN")
        assert result == NotificationChannel.SYSTEM


class TestMapAlertLevelToPriority:
    """测试告警级别到优先级映射"""

    def setup_method(self):
        self.dispatcher, _, _ = make_dispatcher()

    def test_urgent_level(self):
        result = self.dispatcher._map_alert_level_to_priority("URGENT")
        assert result == NotificationPriority.URGENT

    def test_critical_level(self):
        result = self.dispatcher._map_alert_level_to_priority("CRITICAL")
        assert result == NotificationPriority.URGENT

    def test_warning_level(self):
        result = self.dispatcher._map_alert_level_to_priority("WARNING")
        assert result == NotificationPriority.HIGH

    def test_info_level(self):
        result = self.dispatcher._map_alert_level_to_priority("INFO")
        assert result == NotificationPriority.NORMAL

    def test_unknown_level_defaults_to_normal(self):
        result = self.dispatcher._map_alert_level_to_priority("WHATEVER")
        assert result == NotificationPriority.NORMAL

    def test_none_level_defaults_to_normal(self):
        result = self.dispatcher._map_alert_level_to_priority(None)
        assert result == NotificationPriority.NORMAL


class TestComputeNextRetry:
    """测试重试时间计算"""

    def setup_method(self):
        self.dispatcher, _, _ = make_dispatcher()

    def test_first_retry(self):
        result = self.dispatcher._compute_next_retry(1)
        assert isinstance(result, datetime)
        diff = (result - datetime.now()).total_seconds()
        # RETRY_SCHEDULE[0] = 5 分钟
        assert 4 * 60 < diff < 6 * 60

    def test_second_retry(self):
        result = self.dispatcher._compute_next_retry(2)
        assert isinstance(result, datetime)
        diff = (result - datetime.now()).total_seconds()
        # RETRY_SCHEDULE[1] = 15 分钟
        assert 14 * 60 < diff < 16 * 60

    def test_beyond_schedule_uses_last(self):
        result = self.dispatcher._compute_next_retry(100)
        assert isinstance(result, datetime)


class TestCreateSystemNotification:
    """测试创建站内通知记录"""

    def setup_method(self):
        self.dispatcher, _, self.db = make_dispatcher()

    def test_creates_notification_and_adds_to_db(self):
        notif = self.dispatcher.create_system_notification(
            recipient_id=1,
            notification_type="ALERT",
            title="测试通知",
            content="通知内容",
            source_type="alert",
            source_id=42,
        )

        self.db.add.assert_called_once_with(notif)
        assert notif.user_id == 1
        assert notif.title == "测试通知"
        assert notif.content == "通知内容"
        assert notif.source_id == 42

    def test_creates_notification_minimal_params(self):
        notif = self.dispatcher.create_system_notification(
            recipient_id=5,
            notification_type="INFO",
            title="简单通知",
            content="",
        )
        assert notif.user_id == 5


class TestDispatch:
    """测试 dispatch 方法"""

    def setup_method(self):
        self.dispatcher, self.mock_service, self.db = make_dispatcher()

    def _make_notification(self, channel="SYSTEM", user_id=1):
        notif = MagicMock()
        notif.notify_channel = channel
        notif.notify_user_id = user_id
        notif.status = "PENDING"
        notif.retry_count = 0
        notif.next_retry_at = None
        notif.error_message = None
        return notif

    def _make_alert(self, level="WARNING"):
        alert = MagicMock()
        alert.id = 1
        alert.alert_level = level
        alert.alert_title = "测试告警"
        alert.alert_content = "告警内容"
        alert.alert_no = "ALT-001"
        alert.target_type = "PROJECT"
        alert.target_name = "项目A"
        return alert

    def test_dispatch_success_marks_sent(self):
        self.mock_service.send_notification.return_value = {"success": True}
        # Patch quiet hours check
        self.db.query.return_value.filter.return_value.first.return_value = None

        notif = self._make_notification()
        alert = self._make_alert()
        user = MagicMock()
        user.id = 1

        with patch("app.services.notification_dispatcher.is_quiet_hours", return_value=False):
            result = self.dispatcher.dispatch(notif, alert, user)

        assert result is True
        assert notif.status == "SENT"

    def test_dispatch_failure_marks_failed(self):
        self.mock_service.send_notification.side_effect = Exception("connection error")
        self.db.query.return_value.filter.return_value.first.return_value = None

        notif = self._make_notification()
        alert = self._make_alert()
        user = MagicMock()
        user.id = 1

        with patch("app.services.notification_dispatcher.is_quiet_hours", return_value=False):
            result = self.dispatcher.dispatch(notif, alert, user)

        assert result is False
        assert notif.status == "FAILED"
        assert notif.retry_count == 1

    def test_dispatch_quiet_hours_delays(self):
        settings = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = settings

        notif = self._make_notification()
        notif.retry_count = 0
        alert = self._make_alert()
        user = MagicMock()
        user.id = 1

        with patch("app.services.notification_dispatcher.is_quiet_hours", return_value=True), \
             patch("app.services.notification_dispatcher.next_quiet_resume",
                   return_value=datetime.now() + timedelta(hours=1)):
            result = self.dispatcher.dispatch(notif, alert, user)

        assert result is True
        assert notif.status == "PENDING"

    def test_dispatch_sends_notification_request(self):
        """验证调用了 unified_service.send_notification"""
        self.mock_service.send_notification.return_value = {"success": True}
        self.db.query.return_value.filter.return_value.first.return_value = None

        notif = self._make_notification(channel="EMAIL")
        alert = self._make_alert(level="CRITICAL")
        user = MagicMock()
        user.id = 3

        with patch("app.services.notification_dispatcher.is_quiet_hours", return_value=False):
            self.dispatcher.dispatch(notif, alert, user)

        self.mock_service.send_notification.assert_called_once()

    def test_resolve_recipients_by_ids_empty(self):
        result = self.dispatcher._resolve_recipients_by_ids([])
        assert result == {}

    def test_resolve_recipients_filters_non_int(self):
        result = self.dispatcher._resolve_recipients_by_ids(["invalid", None])
        assert result == {}
