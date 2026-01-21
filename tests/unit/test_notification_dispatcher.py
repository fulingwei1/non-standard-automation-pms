# -*- coding: utf-8 -*-
"""
Tests for notification_dispatcher service
Covers: app/services/notification_dispatcher.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 309 lines
Batch: 6
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, Mock
from sqlalchemy.orm import Session

from app.services.notification_dispatcher import NotificationDispatcher
from app.models.alert import AlertNotification, AlertRecord
from app.models.user import User
from tests.conftest import _ensure_login_user


@pytest.fixture
def notification_dispatcher(db_session: Session):
    """创建 NotificationDispatcher 实例"""
    return NotificationDispatcher(db_session)


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    from tests.conftest import _ensure_login_user
    
    return _ensure_login_user(
        db_session,
        username="notif_test_user",
        password="test123",
        real_name="通知测试用户",
        department="技术部",
        employee_role="ENGINEER",
        is_superuser=False
    )


@pytest.fixture
def test_alert_rule(db_session: Session):
    """创建测试预警规则"""
    from app.models.alert import AlertRule
    
    rule = AlertRule(
        rule_code="RULE-001",
        rule_name="测试规则",
        rule_type="DELAY",
        target_type="PROJECT",
        condition_type="THRESHOLD",
        alert_level="HIGH",
        is_enabled=True
    )
    db_session.add(rule)
    db_session.flush()
    db_session.refresh(rule)
    return rule


@pytest.fixture
def test_alert(db_session: Session, test_alert_rule):
    """创建测试预警记录"""
    # 注意：AlertRecord.id 是 BigInteger，SQLite 可能不支持自动递增
    # 使用 MagicMock 来模拟 AlertRecord，避免数据库约束问题
    alert = MagicMock(spec=AlertRecord)
    alert.id = 1
    alert.alert_no = "ALERT-001"
    alert.rule_id = test_alert_rule.id
    alert.target_type = "PROJECT"
    alert.target_id = 1
    alert.alert_level = "HIGH"
    alert.alert_title = "测试预警"
    alert.alert_content = "这是一个测试预警"
    alert.status = "PENDING"
    alert.notify_channel = "SYSTEM"
    alert.notify_target = "user:1"
    alert.retry_count = 0
    alert.error_message = None
    alert.sent_at = None
    alert.next_retry_at = None
    return alert


# 移除 test_notification fixture，改为在测试中直接创建


class TestNotificationDispatcher:
    """Test suite for NotificationDispatcher."""

    def test_init(self, db_session: Session):
        """测试初始化"""
        dispatcher = NotificationDispatcher(db_session)
        assert dispatcher.db == db_session
        assert dispatcher.system_handler is not None
        assert dispatcher.email_handler is not None
        assert dispatcher.wechat_handler is not None
        assert dispatcher.sms_handler is not None

    def test_compute_next_retry_first_retry(self, notification_dispatcher):
        """测试计算下次重试时间 - 第一次重试"""
        retry_time = notification_dispatcher._compute_next_retry(1)
        assert retry_time > datetime.now()
        # 应该在5分钟后（RETRY_SCHEDULE[0] = 5）

    def test_compute_next_retry_second_retry(self, notification_dispatcher):
        """测试计算下次重试时间 - 第二次重试"""
        retry_time = notification_dispatcher._compute_next_retry(2)
        assert retry_time > datetime.now()
        # 应该在15分钟后（RETRY_SCHEDULE[1] = 15）

    def test_compute_next_retry_max_retry(self, notification_dispatcher):
        """测试计算下次重试时间 - 超过最大重试次数"""
        retry_time = notification_dispatcher._compute_next_retry(10)
        assert retry_time > datetime.now()
        # 应该使用最后一个重试间隔（60分钟）

    def test_dispatch_system_channel_success(self, notification_dispatcher, test_alert, test_user):
        """测试分发系统通知 - 成功场景"""
        # 创建真实的 AlertNotification 对象
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel="SYSTEM",
            notify_target="user:1",
            status="PENDING"
        )
        
        with patch.object(notification_dispatcher.system_handler, 'send') as mock_send:
            mock_send.return_value = None
            
            result = notification_dispatcher.dispatch(notification, test_alert, test_user)
            
            assert result is True
            assert notification.status == "SENT"
            assert notification.sent_at is not None
            assert notification.error_message is None
            mock_send.assert_called_once_with(notification, test_alert, test_user)

    def test_dispatch_email_channel_success(self, notification_dispatcher, test_alert, test_user):
        """测试分发邮件通知 - 成功场景"""
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel="EMAIL",
            notify_target="user:1",
            status="PENDING"
        )
        
        with patch.object(notification_dispatcher.email_handler, 'send') as mock_send:
            mock_send.return_value = None
            
            result = notification_dispatcher.dispatch(notification, test_alert, test_user)
            
            assert result is True
            assert notification.status == "SENT"
            mock_send.assert_called_once_with(notification, test_alert, test_user)

    def test_dispatch_wechat_channel_success(self, notification_dispatcher, test_alert, test_user):
        """测试分发微信通知 - 成功场景"""
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel="WECHAT",
            notify_target="user:1",
            status="PENDING"
        )
        
        with patch.object(notification_dispatcher.wechat_handler, 'send') as mock_send:
            mock_send.return_value = None
            
            result = notification_dispatcher.dispatch(notification, test_alert, test_user)
            
            assert result is True
            assert notification.status == "SENT"
            mock_send.assert_called_once_with(notification, test_alert, test_user)

    def test_dispatch_sms_channel_success(self, notification_dispatcher, test_alert, test_user):
        """测试分发短信通知 - 成功场景"""
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel="SMS",
            notify_target="user:1",
            status="PENDING"
        )
        
        with patch.object(notification_dispatcher.sms_handler, 'send') as mock_send:
            mock_send.return_value = None
            
            result = notification_dispatcher.dispatch(notification, test_alert, test_user)
            
            assert result is True
            assert notification.status == "SENT"
            mock_send.assert_called_once_with(notification, test_alert, test_user)

    def test_dispatch_unsupported_channel(self, notification_dispatcher, test_alert, test_user):
        """测试分发不支持的通知渠道"""
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel="INVALID_CHANNEL",
            notify_target="user:1",
            status="PENDING"
        )
        
        result = notification_dispatcher.dispatch(notification, test_alert, test_user)
        
        assert result is False
        assert notification.status == "FAILED"
        assert notification.error_message is not None
        assert "Unsupported notify channel" in notification.error_message
        assert notification.retry_count == 1
        assert notification.next_retry_at is not None

    def test_dispatch_system_channel_failure(self, notification_dispatcher, test_alert, test_user):
        """测试分发系统通知 - 失败场景"""
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel="SYSTEM",
            notify_target="user:1",
            status="PENDING"
        )
        
        with patch.object(notification_dispatcher.system_handler, 'send') as mock_send:
            mock_send.side_effect = Exception("发送失败")
            
            result = notification_dispatcher.dispatch(notification, test_alert, test_user)
            
            assert result is False
            assert notification.status == "FAILED"
            assert notification.error_message == "发送失败"
            assert notification.retry_count == 1
            assert notification.next_retry_at is not None

    def test_dispatch_default_channel(self, notification_dispatcher, test_alert, test_user):
        """测试默认通知渠道（SYSTEM）"""
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel=None,
            notify_target="user:1",
            status="PENDING"
        )
        
        with patch.object(notification_dispatcher.system_handler, 'send') as mock_send:
            mock_send.return_value = None
            
            result = notification_dispatcher.dispatch(notification, test_alert, test_user)
            
            assert result is True
            assert notification.status == "SENT"
            mock_send.assert_called_once()

    def test_dispatch_retry_count_increment(self, notification_dispatcher, test_alert, test_user):
        """测试重试次数递增"""
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel="SYSTEM",
            notify_target="user:1",
            status="PENDING",
            retry_count=2
        )
        
        with patch.object(notification_dispatcher.system_handler, 'send') as mock_send:
            mock_send.side_effect = Exception("发送失败")
            
            notification_dispatcher.dispatch(notification, test_alert, test_user)
            
            assert notification.retry_count == 3

    def test_dispatch_no_user(self, notification_dispatcher, test_alert):
        """测试无用户的分发"""
        notification = AlertNotification(
            alert_id=test_alert.id,
            notify_channel="SYSTEM",
            notify_target="user:1",
            status="PENDING"
        )
        
        with patch.object(notification_dispatcher.system_handler, 'send') as mock_send:
            mock_send.return_value = None
            
            result = notification_dispatcher.dispatch(notification, test_alert, None)
            
            assert result is True
            mock_send.assert_called_once_with(notification, test_alert, None)
