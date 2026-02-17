# -*- coding: utf-8 -*-
"""
G3组 - 统一通知服务单元测试（扩展）
目标文件: app/services/unified_notification_service.py
"""
import pytest
from datetime import datetime
from hashlib import md5
from unittest.mock import MagicMock, patch

from app.services.unified_notification_service import NotificationService, get_notification_service
from app.services.channel_handlers.base import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
    NotificationResult,
)


def make_service(db=None):
    """工厂：创建 NotificationService，patch 所有渠道处理器"""
    if db is None:
        db = MagicMock()
    mock_handlers = {
        NotificationChannel.SYSTEM: MagicMock(),
        NotificationChannel.EMAIL: MagicMock(),
        NotificationChannel.WECHAT: MagicMock(),
        NotificationChannel.SMS: MagicMock(),
        NotificationChannel.WEBHOOK: MagicMock(),
    }
    with patch("app.services.unified_notification_service.SystemChannelHandler",
               return_value=mock_handlers[NotificationChannel.SYSTEM]), \
         patch("app.services.unified_notification_service.EmailChannelHandler",
               return_value=mock_handlers[NotificationChannel.EMAIL]), \
         patch("app.services.unified_notification_service.WeChatChannelHandler",
               return_value=mock_handlers[NotificationChannel.WECHAT]), \
         patch("app.services.unified_notification_service.SMSChannelHandler",
               return_value=mock_handlers[NotificationChannel.SMS]), \
         patch("app.services.unified_notification_service.WebhookChannelHandler",
               return_value=mock_handlers[NotificationChannel.WEBHOOK]):
        svc = NotificationService(db)
    svc._handlers = mock_handlers
    return svc, mock_handlers, db


def make_request(**kwargs):
    defaults = dict(
        recipient_id=1,
        notification_type="TEST",
        category="task",
        title="测试通知",
        content="内容",
        priority=NotificationPriority.NORMAL,
        channels=None,
        force_send=False,
    )
    defaults.update(kwargs)
    return NotificationRequest(**defaults)


class TestNotificationServiceInit:
    def test_init_creates_handlers(self):
        svc, handlers, _ = make_service()
        assert NotificationChannel.SYSTEM in svc._handlers
        assert NotificationChannel.EMAIL in svc._handlers

    def test_init_stores_db(self):
        db = MagicMock()
        svc, _, _ = make_service(db)
        assert svc.db is db


class TestDedupLogic:
    """测试去重逻辑"""

    def setup_method(self):
        self.svc, self.handlers, self.db = make_service()
        # 清除去重缓存
        NotificationService._dedup_cache.clear()

    def test_dedup_key_deterministic(self):
        req = make_request(
            recipient_id=1,
            notification_type="ALERT",
            source_type="alert",
            source_id=99,
        )
        key1 = self.svc._dedup_key(req)
        key2 = self.svc._dedup_key(req)
        assert key1 == key2

    def test_different_requests_different_keys(self):
        req1 = make_request(recipient_id=1, source_id=1)
        req2 = make_request(recipient_id=2, source_id=1)
        assert self.svc._dedup_key(req1) != self.svc._dedup_key(req2)

    def test_check_dedup_false_when_cache_empty(self):
        req = make_request(recipient_id=1, source_id=10)
        assert self.svc._check_dedup(req) is False

    def test_check_dedup_true_when_recently_sent(self):
        req = make_request(recipient_id=1, source_id=20)
        self.svc._update_dedup_cache(req)
        assert self.svc._check_dedup(req) is True

    def test_force_send_bypasses_dedup(self):
        req = make_request(recipient_id=1, source_id=30, force_send=True)
        self.svc._update_dedup_cache(req)
        assert self.svc._check_dedup(req) is False  # force_send = True 跳过检查


class TestQuietHoursCheck:
    """测试免打扰时间检查"""

    def setup_method(self):
        self.svc, _, _ = make_service()

    def test_no_settings_returns_false(self):
        result = self.svc._check_quiet_hours(None)
        assert result is False

    def test_settings_without_quiet_hours(self):
        settings = MagicMock()
        settings.quiet_hours_start = None
        settings.quiet_hours_end = None
        result = self.svc._check_quiet_hours(settings)
        assert result is False

    def test_quiet_hours_active(self):
        settings = MagicMock()
        settings.quiet_hours_start = "00:00"
        settings.quiet_hours_end = "23:59"
        result = self.svc._check_quiet_hours(settings)
        assert result is True

    def test_quiet_hours_not_active(self):
        settings = MagicMock()
        # 设置一个已经过去的时间窗口（深夜2-3点）
        settings.quiet_hours_start = "02:00"
        settings.quiet_hours_end = "03:00"
        # 此测试在非深夜运行时应返回 False
        # 直接测试逻辑：用 patch 固定当前时间
        with patch("app.services.unified_notification_service.datetime") as mock_dt:
            mock_dt.now.return_value.time.return_value = datetime(2026, 1, 1, 12, 0).time()
            mock_dt.strptime.side_effect = datetime.strptime
            result = self.svc._check_quiet_hours(settings)
        assert result is False


class TestShouldSendByCategory:
    """测试按分类过滤"""

    def setup_method(self):
        self.svc, _, _ = make_service()

    def test_no_settings_allows_send(self):
        req = make_request(category="task")
        result = self.svc._should_send_by_category(req, None)
        assert result is True

    def test_force_send_bypasses_category(self):
        settings = MagicMock()
        settings.task_notifications = False
        req = make_request(category="task", force_send=True)
        result = self.svc._should_send_by_category(req, settings)
        assert result is True

    def test_task_notifications_disabled(self):
        settings = MagicMock()
        settings.task_notifications = False
        req = make_request(category="task", force_send=False)
        result = self.svc._should_send_by_category(req, settings)
        assert result is False

    def test_alert_notifications_enabled(self):
        settings = MagicMock()
        settings.alert_notifications = True
        req = make_request(category="alert", force_send=False)
        result = self.svc._should_send_by_category(req, settings)
        assert result is True

    def test_unknown_category_defaults_to_allowed(self):
        settings = MagicMock()
        req = make_request(category="unknown_cat", force_send=False)
        result = self.svc._should_send_by_category(req, settings)
        assert result is True


class TestSendNotification:
    """测试发送通知核心流程"""

    def setup_method(self):
        self.svc, self.handlers, self.db = make_service()
        NotificationService._dedup_cache.clear()

    def test_send_success(self):
        mock_result = NotificationResult(channel=NotificationChannel.SYSTEM, success=True)
        self.handlers[NotificationChannel.SYSTEM].send.return_value = mock_result
        self.db.query.return_value.filter.return_value.first.return_value = None  # no settings

        req = make_request(recipient_id=1, channels=[NotificationChannel.SYSTEM])
        result = self.svc.send_notification(req)

        assert result["success"] is True
        assert NotificationChannel.SYSTEM in result["channels_sent"]

    def test_send_deduped(self):
        req = make_request(recipient_id=1, source_id=77)
        self.svc._update_dedup_cache(req)  # 模拟已发送

        result = self.svc.send_notification(req)

        assert result["deduped"] is True
        assert result["success"] is False

    def test_send_quiet_hours_skipped(self):
        settings = MagicMock()
        settings.quiet_hours_start = "00:00"
        settings.quiet_hours_end = "23:59"
        settings.task_notifications = True
        settings.alert_notifications = True
        self.db.query.return_value.filter.return_value.first.return_value = settings

        req = make_request(recipient_id=1, channels=[NotificationChannel.SYSTEM])
        result = self.svc.send_notification(req)

        assert result.get("quiet_hours") is True

    def test_send_bulk_notification(self):
        mock_result = NotificationResult(channel=NotificationChannel.SYSTEM, success=True)
        self.handlers[NotificationChannel.SYSTEM].send.return_value = mock_result
        self.db.query.return_value.filter.return_value.first.return_value = None

        reqs = [
            make_request(recipient_id=i, channels=[NotificationChannel.SYSTEM])
            for i in range(1, 4)
        ]
        results = self.svc.send_bulk_notification(reqs)
        assert len(results) == 3

    def test_send_task_assigned(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        mock_result = NotificationResult(channel=NotificationChannel.SYSTEM, success=True)
        self.handlers[NotificationChannel.SYSTEM].send.return_value = mock_result

        result = self.svc.send_task_assigned(
            recipient_id=2, task_id=10, task_name="开发任务", assigner_name="张三"
        )
        assert result is not None

    def test_send_approval_pending(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        mock_result = NotificationResult(channel=NotificationChannel.SYSTEM, success=True)
        self.handlers[NotificationChannel.SYSTEM].send.return_value = mock_result

        result = self.svc.send_approval_pending(
            recipient_id=3, approval_id=5, title="差旅报销", submitter_name="李四"
        )
        assert result is not None


class TestGetNotificationService:
    """测试工厂函数"""

    def test_factory_returns_service(self):
        db = MagicMock()
        with patch("app.services.unified_notification_service.SystemChannelHandler"), \
             patch("app.services.unified_notification_service.EmailChannelHandler"), \
             patch("app.services.unified_notification_service.WeChatChannelHandler"), \
             patch("app.services.unified_notification_service.SMSChannelHandler"), \
             patch("app.services.unified_notification_service.WebhookChannelHandler"):
            svc = get_notification_service(db)
        assert isinstance(svc, NotificationService)
