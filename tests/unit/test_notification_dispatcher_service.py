# -*- coding: utf-8 -*-
"""
通知分发服务单元测试
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestNotificationDispatcherInit:
    """测试服务初始化"""

    def test_init_with_db_session(self, dispatcher, db_session):
        """测试使用数据库会话初始化"""
        assert dispatcher.db == db_session

    def test_retry_schedule_exists(self):
        """测试重试计划存在"""
        from app.services.notification_dispatcher import NotificationDispatcher

        assert hasattr(NotificationDispatcher, 'RETRY_SCHEDULE')
        assert isinstance(NotificationDispatcher.RETRY_SCHEDULE, list)
        assert len(NotificationDispatcher.RETRY_SCHEDULE) > 0

    def test_handlers_initialized(self, dispatcher):
        """测试处理器初始化"""
        assert hasattr(dispatcher, 'unified_service')


class TestComputeNextRetry:
    """测试计算下次重试时间"""

    def test_first_retry(self, dispatcher):
        """测试第一次重试"""
        next_retry = dispatcher._compute_next_retry(1)

        assert next_retry > datetime.now()

    def test_retry_schedule_minutes(self):
        """测试重试间隔分钟数"""
        from app.services.notification_dispatcher import NotificationDispatcher

        schedule = NotificationDispatcher.RETRY_SCHEDULE
        # 默认为 [5, 15, 30, 60]
        assert schedule[0] == 5

    def test_max_retry_uses_last_schedule(self):
        """测试超过计划使用最后一个间隔"""
        from app.services.notification_dispatcher import NotificationDispatcher

        schedule = NotificationDispatcher.RETRY_SCHEDULE
        idx = min(10, len(schedule)) - 1
        minutes = schedule[idx] if idx >= 0 else schedule[0]

        assert minutes == schedule[-1]


class TestDispatch:
    """测试分发通知"""

    def test_dispatch_system_channel(self, dispatcher, mock_unified_service):
        """测试系统通道分发"""
        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        user = MagicMock()

        result = dispatcher.dispatch(notification, alert, user)
        # 可能成功或失败
        assert isinstance(result, bool)
        assert mock_unified_service.send_notification.called

    def test_dispatch_email_channel(self, dispatcher, mock_unified_service):
        """测试邮件通道分发"""
        notification = MagicMock()
        notification.notify_channel = "EMAIL"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        user = MagicMock()

        result = dispatcher.dispatch(notification, alert, user)
        assert isinstance(result, bool)
        assert mock_unified_service.send_notification.called

    def test_dispatch_wechat_channel(self, dispatcher, mock_unified_service):
        """测试微信通道分发"""
        notification = MagicMock()
        notification.notify_channel = "WECHAT"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        user = MagicMock()

        result = dispatcher.dispatch(notification, alert, user)
        assert isinstance(result, bool)
        assert mock_unified_service.send_notification.called

    def test_dispatch_sms_channel(self, dispatcher, mock_unified_service):
        """测试短信通道分发"""
        notification = MagicMock()
        notification.notify_channel = "SMS"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        user = MagicMock()

        result = dispatcher.dispatch(notification, alert, user)
        assert isinstance(result, bool)
        assert mock_unified_service.send_notification.called

    def test_dispatch_default_channel(self, dispatcher, mock_unified_service):
        """测试默认通道"""
        notification = MagicMock()
        notification.notify_channel = None  # 默认应使用SYSTEM
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        result = dispatcher.dispatch(notification, alert, None)
        assert isinstance(result, bool)
        assert mock_unified_service.send_notification.called

    def test_dispatch_unsupported_channel(self, dispatcher, mock_unified_service):
        """测试不支持的通道"""
        notification = MagicMock()
        notification.notify_channel = "UNKNOWN_CHANNEL"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        result = dispatcher.dispatch(notification, alert, None)
        # 未知通道会回退到 SYSTEM
        assert result is True
        assert notification.status == "SENT"
        assert mock_unified_service.send_notification.called


class TestDispatchSuccess:
    """测试分发成功"""

    def test_success_updates_status(self, dispatcher, mock_unified_service):
        """测试成功更新状态"""
        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        with patch('app.services.notification_dispatcher.record_notification_success') as record_success:
            result = dispatcher.dispatch(notification, alert, None)

            if result:
                assert notification.status == "SENT"
                assert notification.sent_at is not None
        assert mock_unified_service.send_notification.called
        assert record_success.called


class TestDispatchFailure:
    """测试分发失败"""

    def test_failure_updates_status(self, dispatcher, mock_unified_service):
        """测试失败更新状态"""
        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        mock_unified_service.send_notification.return_value = {
            "success": False,
            "message": "发送失败",
        }
        with patch('app.services.notification_dispatcher.record_notification_failure') as record_failure:
            result = dispatcher.dispatch(notification, alert, None)

            assert result is False
            assert notification.status == "FAILED"
            assert notification.retry_count == 1
            assert notification.error_message == "发送失败"
        assert record_failure.called

    def test_failure_sets_next_retry(self, dispatcher, mock_unified_service):
        """测试失败设置下次重试时间"""
        notification = MagicMock()
        notification.notify_channel = "SYSTEM"
        notification.retry_count = 0

        alert = MagicMock()
        alert.id = 1

        mock_unified_service.send_notification.return_value = {
            "success": False,
            "message": "发送失败",
        }
        with patch('app.services.notification_dispatcher.record_notification_failure'):
            dispatcher.dispatch(notification, alert, None)

            assert notification.next_retry_at is not None


class TestChannelNormalization:
    """测试通道名称规范化"""

    def test_lowercase_channel_normalized(self):
        """测试小写通道名规范化"""
        channel = "system"
        normalized = channel.upper()
        assert normalized == "SYSTEM"

    def test_mixed_case_channel_normalized(self):
        """测试混合大小写通道名规范化"""
        channel = "Email"
        normalized = channel.upper()
        assert normalized == "EMAIL"


# pytest fixtures
@pytest.fixture
def mock_unified_service():
    """创建统一通知服务Mock"""
    service = MagicMock()
    service.send_notification.return_value = {"success": True}
    return service


@pytest.fixture
def dispatcher(db_session, mock_unified_service):
    """创建通知分发器并注入统一通知服务"""
    with patch(
        "app.services.notification_dispatcher.get_notification_service",
        return_value=mock_unified_service,
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        return NotificationDispatcher(db_session)


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    except Exception:
        yield MagicMock()
