# -*- coding: utf-8 -*-
"""
NotificationDispatcher 综合单元测试

测试覆盖:
- 初始化和配置
- 重试计划计算
- 通道映射
- 优先级映射
- 通知分发逻辑
- 成功/失败处理
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestNotificationDispatcherInit:
    """测试 NotificationDispatcher 初始化"""

    def test_init_sets_db_session(self):
        """测试初始化设置数据库会话"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        assert dispatcher.db == mock_db

    def test_init_creates_logger(self):
        """测试初始化创建日志记录器"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        assert dispatcher.logger is not None

    def test_init_creates_unified_service(self):
        """测试初始化创建统一通知服务"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        assert dispatcher.unified_service is not None

    def test_retry_schedule_is_list(self):
        """测试重试计划是列表"""
        from app.services.notification_dispatcher import NotificationDispatcher

        assert isinstance(NotificationDispatcher.RETRY_SCHEDULE, list)
        assert len(NotificationDispatcher.RETRY_SCHEDULE) == 4

    def test_retry_schedule_values(self):
        """测试重试计划值"""
        from app.services.notification_dispatcher import NotificationDispatcher

        assert NotificationDispatcher.RETRY_SCHEDULE == [5, 15, 30, 60]


class TestComputeNextRetry:
    """测试 _compute_next_retry 方法"""

    def test_first_retry_uses_first_schedule(self):
        """测试第一次重试使用第一个计划"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        before = datetime.now()
        result = dispatcher._compute_next_retry(1)
        after = datetime.now()

        # 应该是 5 分钟后
        expected_min = before + timedelta(minutes=5)
        expected_max = after + timedelta(minutes=5)

        assert expected_min <= result <= expected_max

    def test_second_retry_uses_second_schedule(self):
        """测试第二次重试使用第二个计划"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        before = datetime.now()
        result = dispatcher._compute_next_retry(2)

        # 应该是 15 分钟后
        expected = before + timedelta(minutes=15)
        assert result >= expected - timedelta(seconds=1)

    def test_fourth_retry_uses_fourth_schedule(self):
        """测试第四次重试使用第四个计划"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        before = datetime.now()
        result = dispatcher._compute_next_retry(4)

        # 应该是 60 分钟后
        expected = before + timedelta(minutes=60)
        assert result >= expected - timedelta(seconds=1)

    def test_excess_retry_uses_last_schedule(self):
        """测试超过计划次数使用最后一个计划"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        before = datetime.now()
        result = dispatcher._compute_next_retry(10)

        # 应该是 60 分钟后（最后一个计划）
        expected = before + timedelta(minutes=60)
        assert result >= expected - timedelta(seconds=1)

    def test_zero_retry_uses_first_schedule(self):
        """测试零次重试使用第一个计划"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        before = datetime.now()
        result = dispatcher._compute_next_retry(0)

        # idx = -1，使用第一个计划
        expected = before + timedelta(minutes=5)
        assert result >= expected - timedelta(seconds=1)


class TestMapChannelToUnified:
    """测试 _map_channel_to_unified 方法"""

    def test_system_channel_mapping(self):
        """测试系统通道映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationChannel

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_channel_to_unified("SYSTEM")
        assert result == NotificationChannel.SYSTEM

    def test_email_channel_mapping(self):
        """测试邮件通道映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationChannel

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_channel_to_unified("EMAIL")
        assert result == NotificationChannel.EMAIL

    def test_wechat_channel_mapping(self):
        """测试微信通道映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationChannel

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_channel_to_unified("WECHAT")
        assert result == NotificationChannel.WECHAT

    def test_sms_channel_mapping(self):
        """测试短信通道映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationChannel

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_channel_to_unified("SMS")
        assert result == NotificationChannel.SMS

    def test_lowercase_channel_mapping(self):
        """测试小写通道映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationChannel

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_channel_to_unified("system")
        assert result == NotificationChannel.SYSTEM

    def test_unknown_channel_defaults_to_system(self):
        """测试未知通道默认映射到系统"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationChannel

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_channel_to_unified("UNKNOWN")
        assert result == NotificationChannel.SYSTEM


class TestMapAlertLevelToPriority:
    """测试 _map_alert_level_to_priority 方法"""

    def test_urgent_level_mapping(self):
        """测试紧急级别映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationPriority

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_alert_level_to_priority("URGENT")
        assert result == NotificationPriority.URGENT

    def test_critical_level_mapping(self):
        """测试严重级别映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationPriority

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_alert_level_to_priority("CRITICAL")
        assert result == NotificationPriority.URGENT

    def test_warning_level_mapping(self):
        """测试警告级别映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationPriority

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_alert_level_to_priority("WARNING")
        assert result == NotificationPriority.HIGH

    def test_info_level_mapping(self):
        """测试信息级别映射"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationPriority

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_alert_level_to_priority("INFO")
        assert result == NotificationPriority.NORMAL

    def test_none_level_defaults_to_normal(self):
        """测试空级别默认为普通"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationPriority

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_alert_level_to_priority(None)
        assert result == NotificationPriority.NORMAL

    def test_unknown_level_defaults_to_normal(self):
        """测试未知级别默认为普通"""
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationPriority

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        result = dispatcher._map_alert_level_to_priority("UNKNOWN")
        assert result == NotificationPriority.NORMAL


class TestDispatch:
    """测试 dispatch 方法"""

    def test_dispatch_success_updates_notification_status(self):
        """测试分发成功更新通知状态"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.notify_user_id = 1
        notification.notify_title = "测试标题"
        notification.notify_content = "测试内容"
        notification.notify_target = "user@example.com"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1
        alert.alert_no = "ALT001"
        alert.alert_title = "预警标题"
        alert.alert_content = "预警内容"
        alert.alert_level = "WARNING"
        alert.target_type = "PROJECT"
        alert.target_name = "测试项目"

        # Mock unified service
        dispatcher.unified_service = MagicMock()
        dispatcher.unified_service.send_notification.return_value = {"success": True}

        with patch(
            "app.services.notification_dispatcher.record_notification_success"
        ):
            result = dispatcher.dispatch(notification, alert, None)

        assert result is True
        assert notification.status == "SENT"
        assert notification.sent_at is not None

    def test_dispatch_failure_updates_notification_status(self):
        """测试分发失败更新通知状态"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.notify_user_id = 1
        notification.notify_title = "测试标题"
        notification.notify_content = "测试内容"
        notification.notify_target = "user@example.com"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1
        alert.alert_no = "ALT001"
        alert.alert_title = "预警标题"
        alert.alert_content = "预警内容"
        alert.alert_level = "WARNING"
        alert.target_type = "PROJECT"
        alert.target_name = "测试项目"

        # Mock unified service to fail
        dispatcher.unified_service = MagicMock()
        dispatcher.unified_service.send_notification.return_value = {
            "success": False,
            "message": "发送失败",
        }

        with patch(
            "app.services.notification_dispatcher.record_notification_failure"
        ):
            result = dispatcher.dispatch(notification, alert, None)

        assert result is False
        assert notification.status == "FAILED"
        assert notification.retry_count == 1
        assert notification.next_retry_at is not None

    def test_dispatch_exception_updates_notification_status(self):
        """测试分发异常更新通知状态"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.notify_user_id = 1
        notification.notify_title = "测试标题"
        notification.notify_content = "测试内容"
        notification.notify_target = "user@example.com"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1
        alert.alert_no = "ALT001"
        alert.alert_title = "预警标题"
        alert.alert_content = "预警内容"
        alert.alert_level = "WARNING"
        alert.target_type = "PROJECT"
        alert.target_name = "测试项目"

        # Mock unified service to raise exception
        dispatcher.unified_service = MagicMock()
        dispatcher.unified_service.send_notification.side_effect = Exception(
            "连接失败"
        )

        with patch(
            "app.services.notification_dispatcher.record_notification_failure"
        ):
            result = dispatcher.dispatch(notification, alert, None)

        assert result is False
        assert notification.status == "FAILED"
        assert "连接失败" in notification.error_message
        assert notification.retry_count == 1

    def test_dispatch_uses_user_id_as_recipient(self):
        """测试分发使用用户ID作为接收者"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.notify_user_id = None  # 无用户ID
        notification.notify_title = "测试标题"
        notification.notify_content = "测试内容"
        notification.notify_target = "user@example.com"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1
        alert.alert_no = "ALT001"
        alert.alert_title = "预警标题"
        alert.alert_content = "预警内容"
        alert.alert_level = "WARNING"
        alert.target_type = "PROJECT"
        alert.target_name = "测试项目"

        user = MagicMock()
        user.id = 5

        # Mock unified service
        dispatcher.unified_service = MagicMock()
        dispatcher.unified_service.send_notification.return_value = {"success": True}

        with patch(
            "app.services.notification_dispatcher.record_notification_success"
        ):
            result = dispatcher.dispatch(notification, alert, user)

        # 验证使用了用户ID
        call_args = dispatcher.unified_service.send_notification.call_args
        request = call_args[0][0]
        assert request.recipient_id == 5

    def test_dispatch_raises_when_no_recipient(self):
        """测试无接收者时返回失败"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.notify_user_id = None
        notification.notify_title = "测试标题"
        notification.notify_content = "测试内容"
        notification.notify_target = "user@example.com"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1
        alert.alert_no = "ALT001"
        alert.alert_title = "预警标题"
        alert.alert_content = "预警内容"
        alert.alert_level = "WARNING"
        alert.target_type = "PROJECT"
        alert.target_name = "测试项目"

        with patch(
            "app.services.notification_dispatcher.record_notification_failure"
        ):
            result = dispatcher.dispatch(notification, alert, None)

        assert result is False
        assert notification.status == "FAILED"

    def test_dispatch_uses_default_channel_when_none(self):
        """测试通道为空时使用默认通道"""
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_db = MagicMock()
        dispatcher = NotificationDispatcher(mock_db)

        notification = MagicMock()
        notification.notify_channel = None  # 无通道
        notification.notify_user_id = 1
        notification.notify_title = "测试标题"
        notification.notify_content = "测试内容"
        notification.notify_target = "user@example.com"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1
        alert.alert_no = "ALT001"
        alert.alert_title = "预警标题"
        alert.alert_content = "预警内容"
        alert.alert_level = "WARNING"
        alert.target_type = "PROJECT"
        alert.target_name = "测试项目"

        dispatcher.unified_service = MagicMock()
        dispatcher.unified_service.send_notification.return_value = {"success": True}

        with patch(
            "app.services.notification_dispatcher.record_notification_success"
        ):
            result = dispatcher.dispatch(notification, alert, None)

        assert result is True


class TestModuleExports:
    """测试模块导出"""

    def test_exports_notification_dispatcher(self):
        """测试导出 NotificationDispatcher"""
        from app.services.notification_dispatcher import NotificationDispatcher

        assert NotificationDispatcher is not None

    def test_exports_utility_functions(self):
        """测试导出工具函数"""
        from app.services.notification_dispatcher import (
            resolve_channels,
            resolve_recipients,
            resolve_channel_target,
            channel_allowed,
            is_quiet_hours,
            next_quiet_resume,
        )

        assert resolve_channels is not None
        assert resolve_recipients is not None
        assert resolve_channel_target is not None
        assert channel_allowed is not None
        assert is_quiet_hours is not None
        assert next_quiet_resume is not None
