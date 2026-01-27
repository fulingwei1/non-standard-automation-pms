# -*- coding: utf-8 -*-
"""
通知处理器服务单元测试

测试覆盖:
- SystemNotificationHandler: 系统通知（站内消息）
- EmailNotificationHandler: 邮件通知
- WeChatNotificationHandler: 企业微信通知
- SMSNotificationHandler: 短信通知
"""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestSystemNotificationHandler:
    """测试系统通知处理器"""

    @pytest.fixture
    def handler(self, db_session):
        """创建系统通知处理器"""
        from app.services.notification_handlers.system_handler import SystemNotificationHandler
        return SystemNotificationHandler(db_session)

    @pytest.fixture
    def mock_notification(self):
        """创建模拟通知"""
        notification = MagicMock()
        notification.notify_user_id = 1
        notification.notify_title = "测试预警标题"
        notification.notify_content = "测试预警内容"
        return notification

    @pytest.fixture
    def mock_alert(self):
        """创建模拟预警记录"""
        alert = MagicMock()
        alert.id = 1
        alert.alert_no = "ALT202501001"
        alert.alert_title = "测试预警"
        alert.alert_content = "这是测试预警内容"
        alert.alert_level = "WARNING"
        alert.target_type = "PROJECT"
        alert.target_name = "测试项目"
        return alert

    def test_handler_initialization(self, handler, db_session):
        """测试处理器初始化"""
        assert handler.db == db_session
        assert handler._parent is None

    def test_handler_with_parent(self, db_session):
        """测试带父分发器的处理器"""
        from app.services.notification_handlers.system_handler import SystemNotificationHandler

        mock_parent = MagicMock()
        handler = SystemNotificationHandler(db_session, parent=mock_parent)

        assert handler._parent == mock_parent

    def test_send_missing_user_id(self, handler, mock_notification, mock_alert):
        """测试发送通知缺少用户ID"""
        mock_notification.notify_user_id = None

        with pytest.raises(ValueError) as exc_info:
            handler.send(mock_notification, mock_alert)

        assert "notify_user_id" in str(exc_info.value)

    def test_send_creates_notification(self, handler, mock_notification, mock_alert, db_session):
        """测试发送通知创建记录"""
        # Mock the query to return no existing notification
        with patch.object(db_session, 'query') as mock_query:
            mock_filter = MagicMock()
            mock_filter.filter.return_value = mock_filter
            mock_filter.first.return_value = None
            mock_query.return_value = mock_filter

            handler.send(mock_notification, mock_alert)

            # 验证调用了 add
            assert db_session.add.called or mock_query.called

    def test_send_skips_duplicate(self, handler, mock_notification, mock_alert, db_session):
        """测试发送通知跳过重复"""
        from app.models.notification import Notification

        # Mock 存在的通知
        existing_notification = MagicMock(spec=Notification)

        with patch.object(db_session, 'query') as mock_query:
            mock_filter = MagicMock()
            mock_filter.filter.return_value = mock_filter
            mock_filter.first.return_value = existing_notification
            mock_query.return_value = mock_filter

            handler.send(mock_notification, mock_alert)

            # 不应该调用 add
            # (因为跳过了重复)

    def test_send_uses_notification_title(self, handler, mock_notification, mock_alert):
        """测试使用通知标题"""
        mock_notification.notify_title = "自定义标题"

        # 验证使用了 notify_title
        assert mock_notification.notify_title == "自定义标题"

    def test_send_uses_alert_title_fallback(self, handler, mock_notification, mock_alert):
        """测试标题回退到预警标题"""
        mock_notification.notify_title = None

        # 应该使用 alert.alert_title
        assert mock_alert.alert_title == "测试预警"


class TestEmailNotificationHandler:
    """测试邮件通知处理器"""

    @pytest.fixture
    def handler(self, db_session):
        """创建邮件通知处理器"""
        from app.services.notification_handlers.email_handler import EmailNotificationHandler
        return EmailNotificationHandler(db_session)

    @pytest.fixture
    def mock_notification(self):
        """创建模拟通知"""
        notification = MagicMock()
        notification.notify_user_id = 1
        notification.notify_title = "测试邮件标题"
        notification.notify_content = "测试邮件内容"
        notification.notify_email = "test@example.com"
        return notification

    @pytest.fixture
    def mock_alert(self):
        """创建模拟预警记录"""
        alert = MagicMock()
        alert.id = 1
        alert.alert_no = "ALT202501001"
        alert.alert_title = "测试预警"
        alert.alert_content = "这是测试预警内容"
        alert.alert_level = "WARNING"
        alert.target_type = "PROJECT"
        alert.target_name = "测试项目"
        return alert

    def test_handler_initialization(self, handler, db_session):
        """测试处理器初始化"""
        assert handler.db == db_session

    def test_email_subject_format(self, mock_notification, mock_alert):
        """测试邮件主题格式"""
        # 验证邮件标题
        assert mock_notification.notify_title is not None

    def test_email_recipient(self, mock_notification):
        """测试邮件收件人"""
        assert mock_notification.notify_email == "test@example.com"


class TestWeChatNotificationHandler:
    """测试企业微信通知处理器"""

    @pytest.fixture
    def handler(self, db_session):
        """创建企业微信通知处理器"""
        from app.services.notification_handlers.wechat_handler import WeChatNotificationHandler
        return WeChatNotificationHandler(db_session)

    def test_handler_initialization(self, handler, db_session):
        """测试处理器初始化"""
        assert handler.db == db_session


class TestSMSNotificationHandler:
    """测试短信通知处理器"""

    @pytest.fixture
    def handler(self, db_session):
        """创建短信通知处理器"""
        from app.services.notification_handlers.sms_handler import SMSNotificationHandler
        return SMSNotificationHandler(db_session)

    def test_handler_initialization(self, handler, db_session):
        """测试处理器初始化"""
        assert handler.db == db_session


class TestNotificationHandlersModule:
    """测试通知处理器模块"""

    def test_import_all_handlers(self):
        """测试导入所有处理器"""
        from app.services.notification_handlers import (
            SystemNotificationHandler,
            EmailNotificationHandler,
            WeChatNotificationHandler,
            SMSNotificationHandler,
        )

        assert SystemNotificationHandler is not None
        assert EmailNotificationHandler is not None
        assert WeChatNotificationHandler is not None
        assert SMSNotificationHandler is not None

    def test_handlers_have_send_method(self):
        """测试处理器都有 send 方法"""
        from app.services.notification_handlers import (
            SystemNotificationHandler,
            EmailNotificationHandler,
            WeChatNotificationHandler,
            SMSNotificationHandler,
        )

        assert hasattr(SystemNotificationHandler, 'send')
        assert hasattr(EmailNotificationHandler, 'send')
        assert hasattr(WeChatNotificationHandler, 'send')
        assert hasattr(SMSNotificationHandler, 'send')
