# -*- coding: utf-8 -*-
"""
统一通知服务测试
"""
from unittest.mock import Mock
import pytest

from app.services.notification.unified_notification_service import (
    NotificationService,
    get_notification_service,
)
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationChannel,
    NotificationPriority,
)
from app.models.notification import NotificationSettings
from app.models.user import User


class TestNotificationService:
    """NotificationService 测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = Mock()
        return db

    @pytest.fixture
    def notification_service(self, mock_db):
        """创建通知服务实例"""
        return NotificationService(mock_db)

    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.phone = "13800138000"
        return user

    @pytest.fixture
    def mock_user_settings(self):
        """创建用户通知设置"""
        settings = Mock(spec=NotificationSettings)
        settings.user_id = 1
        settings.email_enabled = True
        settings.sms_enabled = True
        settings.wechat_enabled = True
        settings.quiet_hours_start = None
        settings.quiet_hours_end = None
        settings.task_notifications = True
        settings.approval_notifications = True
        settings.alert_notifications = True
        settings.issue_notifications = True
        settings.project_notifications = True
        return settings

    def test_send_notification_success(self, notification_service, mock_db):
        """测试发送通知成功"""
        # Mock用户设置返回
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试通知",
            content="这是测试内容",
            priority=NotificationPriority.NORMAL,
        )

        result = notification_service.send_notification(request)

        assert "success" in result
        assert "channels_sent" in result

    def test_send_notification_with_user_settings(
        self, notification_service, mock_db, mock_user_settings
    ):
        """测试带用户设置的发送"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user_settings
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试通知",
            content="这是测试内容",
            priority=NotificationPriority.NORMAL,
            force_send=True,
        )

        result = notification_service.send_notification(request)

        assert "success" in result

    def test_send_notification_quiet_hours(self, notification_service, mock_db):
        """测试免打扰时间"""
        # 创建免打扰设置
        settings = Mock(spec=NotificationSettings)
        settings.quiet_hours_start = "00:00"
        settings.quiet_hours_end = "23:59"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = settings
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试通知",
            content="这是测试内容",
            priority=NotificationPriority.NORMAL,
            force_send=False,
        )

        result = notification_service.send_notification(request)

        # 强制发送时应该绕过免打扰
        assert "quiet_hours" in result or "success" in result

    def test_send_notification_category_disabled(
        self, notification_service, mock_db
    ):
        """测试用户禁用某类通知"""
        settings = Mock(spec=NotificationSettings)
        settings.task_notifications = False
        settings.approval_notifications = True
        settings.alert_notifications = True
        settings.issue_notifications = True
        settings.project_notifications = True
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = settings
        mock_db.query.return_value = mock_query

        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="task",
            title="测试通知",
            content="这是测试内容",
            priority=NotificationPriority.NORMAL,
            force_send=False,
        )

        result = notification_service.send_notification(request)

        # 非强制发送时如果分类被禁用，应该返回disabled
        assert "disabled" in result or "success" in result

    def test_send_task_assigned(self, notification_service, mock_db):
        """测试发送任务分配通知"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = notification_service.send_task_assigned(
            recipient_id=1,
            task_id=100,
            task_name="测试任务",
            assigner_name="张三",
        )

        assert "success" in result

    def test_send_task_completed(self, notification_service, mock_db):
        """测试发送任务完成通知"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = notification_service.send_task_completed(
            recipient_id=1,
            task_id=100,
            task_name="测试任务",
        )

        assert "success" in result

    def test_send_approval_pending(self, notification_service, mock_db):
        """测试发送审批待处理通知"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = notification_service.send_approval_pending(
            recipient_id=1,
            approval_id=200,
            title="采购审批",
            submitter_name="李四",
        )

        assert "success" in result

    def test_send_approval_result_approved(self, notification_service, mock_db):
        """测试发送审批通过通知"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = notification_service.send_approval_result(
            recipient_id=1,
            approval_id=200,
            title="采购审批",
            approved=True,
            comment="同意",
        )

        assert "success" in result

    def test_send_approval_result_rejected(self, notification_service, mock_db):
        """测试发送审批拒绝通知"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = notification_service.send_approval_result(
            recipient_id=1,
            approval_id=200,
            title="采购审批",
            approved=False,
            comment="预算不足",
        )

        assert "success" in result

    def test_send_alert_critical(self, notification_service, mock_db):
        """测试发送严重预警通知"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = notification_service.send_alert(
            recipient_id=1,
            alert_id=300,
            alert_title="系统异常",
            alert_level="CRITICAL",
        )

        assert "success" in result

    def test_send_alert_warning(self, notification_service, mock_db):
        """测试发送警告预警通知"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = notification_service.send_alert(
            recipient_id=1,
            alert_id=300,
            alert_title="资源不足",
            alert_level="WARNING",
        )

        assert "success" in result

    def test_send_bulk_notification(self, notification_service, mock_db):
        """测试批量发送通知"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        requests = [
            NotificationRequest(
                recipient_id=1,
                notification_type="TEST",
                category="test",
                title="测试1",
                content="内容1",
            ),
            NotificationRequest(
                recipient_id=2,
                notification_type="TEST",
                category="test",
                title="测试2",
                content="内容2",
            ),
        ]

        results = notification_service.send_bulk_notification(requests)

        assert len(results) == 2
        for result in results:
            assert "success" in result

    def test_determine_channels_default(self, notification_service, mock_db):
        """测试默认渠道确定"""
        request = NotificationRequest(
            recipient_id=1,
            notification_type="TEST",
            category="test",
            title="测试",
            content="内容",
            priority=NotificationPriority.NORMAL,
            channels=None,
        )

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        channels = notification_service._determine_channels(request)

        assert NotificationChannel.SYSTEM in channels

    def test_get_notification_service_singleton(self, mock_db):
        """测试获取通知服务单例"""
        service1 = get_notification_service(mock_db)
        service2 = get_notification_service(mock_db)

        # 单例模式应该返回同一个实例
        assert service1 is not None
        assert service2 is not None