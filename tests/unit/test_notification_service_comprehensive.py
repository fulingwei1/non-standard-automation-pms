# -*- coding: utf-8 -*-
"""notification_service 综合测试"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.notification_service import (
    NotificationChannel,
    NotificationPriority,
    NotificationService,
    AlertNotificationService,
    get_notification_service_instance,
)


class TestNotificationChannel:
    def test_system(self):
        assert NotificationChannel.SYSTEM == "system"

    def test_email(self):
        assert NotificationChannel.EMAIL == "email"

    def test_sms(self):
        assert NotificationChannel.SMS == "sms"

    def test_wechat(self):
        assert NotificationChannel.WECHAT == "wechat"

    def test_web(self):
        assert NotificationChannel.WEB == "web"

    def test_webhook(self):
        assert NotificationChannel.WEBHOOK == "webhook"

    def test_all_values(self):
        assert len(NotificationChannel) == 6


class TestNotificationPriority:
    def test_low(self):
        assert NotificationPriority.LOW == "low"

    def test_values_exist(self):
        assert len(NotificationPriority) >= 3


class TestNotificationService:
    def test_init_no_db(self):
        svc = NotificationService()
        assert svc is not None

    def test_init_with_db(self):
        db = MagicMock()
        svc = NotificationService(db=db)
        assert svc is not None

    def test_get_enabled_channels(self):
        svc = NotificationService()
        channels = svc._get_enabled_channels()
        assert isinstance(channels, list)

    def test_map_old_channel_system(self):
        svc = NotificationService()
        result = svc._map_old_channel_to_new(NotificationChannel.SYSTEM)
        assert isinstance(result, str)

    def test_map_old_channel_email(self):
        svc = NotificationService()
        result = svc._map_old_channel_to_new(NotificationChannel.EMAIL)
        assert isinstance(result, str)

    def test_map_old_channel_sms(self):
        svc = NotificationService()
        result = svc._map_old_channel_to_new(NotificationChannel.SMS)
        assert isinstance(result, str)

    def test_map_old_channel_wechat(self):
        svc = NotificationService()
        result = svc._map_old_channel_to_new(NotificationChannel.WECHAT)
        assert isinstance(result, str)

    def test_map_old_priority_low(self):
        svc = NotificationService()
        result = svc._map_old_priority_to_new(NotificationPriority.LOW)
        assert isinstance(result, str)

    def test_send_notification_no_db(self):
        svc = NotificationService()
        # Without db, should return False
        from app.services.notification_service import NotificationType
        result = svc.send_notification(
            db=None,
            recipient_id=1,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="测试",
            content="测试内容",
        )
        assert result is False


class TestGetNotificationServiceInstance:
    def test_returns_instance(self):
        svc = get_notification_service_instance()
        assert isinstance(svc, NotificationService)


class TestAlertNotificationService:
    def test_init(self):
        db = MagicMock()
        svc = AlertNotificationService(db)
        assert svc.db is db

    def test_mark_notification_read_not_found(self):
        db = MagicMock()
        svc = AlertNotificationService(db)
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.mark_notification_read(999, 1)
        assert result is False

    def test_mark_notification_read_found(self):
        db = MagicMock()
        svc = AlertNotificationService(db)
        notif = MagicMock()
        notif.user_id = 1
        db.query.return_value.filter.return_value.first.return_value = notif
        result = svc.mark_notification_read(1, 1)
        assert result is True

    def test_get_unread_count(self):
        db = MagicMock()
        svc = AlertNotificationService(db)
        db.query.return_value.filter.return_value.count.return_value = 5
        count = svc.get_unread_count(1)
        assert count == 5

    def test_batch_mark_read(self):
        db = MagicMock()
        svc = AlertNotificationService(db)
        db.query.return_value.filter.return_value.update.return_value = 3
        result = svc.batch_mark_read([1, 2, 3], 1)
        assert isinstance(result, dict)
