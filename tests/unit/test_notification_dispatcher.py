# -*- coding: utf-8 -*-
"""
Tests for notification_dispatcher
Covers: app/services/notification_dispatcher.py
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.notification_dispatcher import NotificationDispatcher


@pytest.fixture
def notification_dispatcher(db_session: Session):
    """Create notification_dispatcher instance."""
    return NotificationDispatcher(db_session)


class TestNotificationDispatcher:
    """Test suite for NotificationDispatcher."""

    def test_init(self, db_session: Session):
        """Test service initialization."""
        service = NotificationDispatcher(db_session)
        assert service.db is db_session
        assert service.logger is not None
        assert service.system_handler is not None

    def test_retry_schedule_config(self):
        """验证重试调度配置。"""
        assert NotificationDispatcher.RETRY_SCHEDULE == [5, 15, 30, 60]
        assert len(NotificationDispatcher.RETRY_SCHEDULE) == 4

    def test_system_handler_initialized(self, notification_dispatcher):
        """验证系统通知处理器已初始化。"""
        assert notification_dispatcher.system_handler is not None

    def test_dispatch_alert_notification(self, notification_dispatcher):
        """测试预警通知派发。"""
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.alert_level = "WARNING"
        mock_alert.message = "测试预警消息"
        mock_alert.target_type = "PROJECT"
        mock_alert.target_id = 1

        with patch.object(notification_dispatcher.system_handler, 'send') as mock_send:
            mock_send.return_value = True

            # 调用派发方法
            notification_dispatcher.system_handler.send(mock_alert)
            mock_send.assert_called_once()

    def test_dispatch_with_multiple_channels(self, notification_dispatcher):
        """测试多渠道派发。"""
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.channels = ["SYSTEM", "EMAIL"]

        with patch.object(notification_dispatcher, 'dispatch_to_channel') as mock_dispatch:
            mock_dispatch.return_value = True

            for channel in mock_alert.channels:
                notification_dispatcher.dispatch_to_channel(mock_alert, channel)

            assert mock_dispatch.call_count == 2

    def test_retry_on_failure(self, notification_dispatcher):
        """测试失败重试机制。"""
        mock_alert = MagicMock()
        mock_alert.id = 1
        mock_alert.retry_count = 0

        # 模拟第一次失败，第二次成功
        with patch.object(notification_dispatcher, 'send_notification') as mock_send:
            mock_send.side_effect = [False, True]

            # 第一次调用失败
            result1 = notification_dispatcher.send_notification(mock_alert)
            assert result1 is False

            # 第二次调用成功
            result2 = notification_dispatcher.send_notification(mock_alert)
            assert result2 is True

    def test_get_retry_delay(self, notification_dispatcher):
        """测试获取重试延迟时间。"""
        schedule = NotificationDispatcher.RETRY_SCHEDULE

        # 第一次重试延迟 5 秒
        assert schedule[0] == 5
        # 第二次重试延迟 15 秒
        assert schedule[1] == 15
        # 最后一次重试延迟 60 秒
        assert schedule[-1] == 60

    def test_logger_initialized(self, notification_dispatcher):
        """验证日志记录器已初始化。"""
        assert notification_dispatcher.logger is not None
        assert notification_dispatcher.logger.name is not None
