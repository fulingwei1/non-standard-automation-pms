# -*- coding: utf-8 -*-
"""
通知分发器单元测试 - 重写版本

目标：
1. 只mock外部通知渠道（邮件、短信、企业微信API）
2. 让分发逻辑真正执行
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.notification_dispatcher import NotificationDispatcher
from app.models.alert import AlertNotification, AlertRecord
from app.models.notification import Notification, NotificationSettings
from app.models.user import User
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationChannel,
    NotificationPriority,
)


class TestNotificationDispatcherCore(unittest.TestCase):
    """测试核心分发方法"""

    def setUp(self):
        """初始化测试环境"""
        self.db = MagicMock(spec=Session)
        self.dispatcher = NotificationDispatcher(self.db)

    # ========== create_system_notification() 测试 ==========
    
    def test_create_system_notification_basic(self):
        """测试创建基本站内通知"""
        notification = self.dispatcher.create_system_notification(
            recipient_id=1,
            notification_type="ALERT",
            title="测试通知",
            content="这是一条测试通知",
        )
        
        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.user_id, 1)
        self.assertEqual(notification.notification_type, "ALERT")
        self.assertEqual(notification.title, "测试通知")
        self.assertEqual(notification.content, "这是一条测试通知")
        self.assertEqual(notification.priority, "NORMAL")
        self.db.add.assert_called_once_with(notification)

    def test_create_system_notification_with_all_params(self):
        """测试创建完整参数的站内通知"""
        extra_data = {"key": "value"}
        notification = self.dispatcher.create_system_notification(
            recipient_id=2,
            notification_type="TASK",
            title="任务通知",
            content="任务已分配",
            source_type="task",
            source_id=100,
            link_url="/tasks/100",
            priority="HIGH",
            extra_data=extra_data,
        )
        
        self.assertEqual(notification.source_type, "task")
        self.assertEqual(notification.source_id, 100)
        self.assertEqual(notification.link_url, "/tasks/100")
        self.assertEqual(notification.priority, "HIGH")
        self.assertEqual(notification.extra_data, extra_data)

    # ========== send_notification_request() 测试 ==========
    
    @patch('app.services.notification_dispatcher.get_notification_service')
    def test_send_notification_request(self, mock_get_service):
        """测试发送通知请求"""
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_service
        
        # 重新初始化dispatcher以使用mock service
        dispatcher = NotificationDispatcher(self.db)
        
        request = NotificationRequest(
            recipient_id=1,
            notification_type="ALERT",
            category="alert",
            title="测试",
            content="内容",
            channels=["SYSTEM"],
        )
        
        result = dispatcher.send_notification_request(request)
        
        self.assertEqual(result, {"success": True})
        mock_service.send_notification.assert_called_once_with(request)

    # ========== _resolve_recipients_by_ids() 测试 ==========
    
    def test_resolve_recipients_by_ids_success(self):
        """测试解析用户ID成功"""
        user1 = User(id=1, username="user1", email="user1@test.com", is_active=True)
        user2 = User(id=2, username="user2", email="user2@test.com", is_active=True)
        setting1 = NotificationSettings(user_id=1, email_enabled=True)
        
        # Mock数据库查询
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.filter.return_value.all.return_value = [user1, user2]
        
        mock_settings_query = MagicMock()
        mock_settings_query.filter.return_value.all.return_value = [setting1]
        
        self.db.query.side_effect = [mock_user_query, mock_settings_query]
        
        result = self.dispatcher._resolve_recipients_by_ids([1, 2])
        
        self.assertEqual(len(result), 2)
        self.assertIn(1, result)
        self.assertIn(2, result)
        self.assertEqual(result[1]["user"], user1)
        self.assertEqual(result[1]["settings"], setting1)
        self.assertEqual(result[2]["user"], user2)
        self.assertIsNone(result[2]["settings"])

    def test_resolve_recipients_by_ids_empty(self):
        """测试空用户ID列表"""
        result = self.dispatcher._resolve_recipients_by_ids([])
        self.assertEqual(result, {})

    def test_resolve_recipients_by_ids_no_users(self):
        """测试查询不到用户"""
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value = mock_query
        
        result = self.dispatcher._resolve_recipients_by_ids([999])
        self.assertEqual(result, {})

    def test_resolve_recipients_by_ids_invalid_types(self):
        """测试过滤无效类型的ID"""
        # Mock数据库查询
        user1 = User(id=1, username="user1", is_active=True)
        user2 = User(id=2, username="user2", is_active=True)
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.filter.return_value.all.return_value = [user1, user2]
        
        mock_settings_query = MagicMock()
        mock_settings_query.filter.return_value.all.return_value = []
        
        self.db.query.side_effect = [mock_user_query, mock_settings_query]
        
        result = self.dispatcher._resolve_recipients_by_ids([1, "invalid", None, 2])
        # 应该只保留有效的整数ID (1 和 2)
        self.assertEqual(len(result), 2)
        self.assertIn(1, result)
        self.assertIn(2, result)

    # ========== _compute_next_retry() 测试 ==========
    
    def test_compute_next_retry_first_attempt(self):
        """测试第一次重试（5分钟）"""
        before = datetime.now()
        next_retry = self.dispatcher._compute_next_retry(1)
        after = datetime.now()
        
        # 应该是当前时间 + 5分钟
        expected_min = before + timedelta(minutes=5)
        expected_max = after + timedelta(minutes=5)
        
        self.assertGreaterEqual(next_retry, expected_min)
        self.assertLessEqual(next_retry, expected_max)

    def test_compute_next_retry_second_attempt(self):
        """测试第二次重试（15分钟）"""
        before = datetime.now()
        next_retry = self.dispatcher._compute_next_retry(2)
        after = datetime.now()
        
        expected_min = before + timedelta(minutes=15)
        expected_max = after + timedelta(minutes=15)
        
        self.assertGreaterEqual(next_retry, expected_min)
        self.assertLessEqual(next_retry, expected_max)

    def test_compute_next_retry_max_attempts(self):
        """测试超过最大重试次数（使用最后一个值60分钟）"""
        before = datetime.now()
        next_retry = self.dispatcher._compute_next_retry(10)
        after = datetime.now()
        
        expected_min = before + timedelta(minutes=60)
        expected_max = after + timedelta(minutes=60)
        
        self.assertGreaterEqual(next_retry, expected_min)
        self.assertLessEqual(next_retry, expected_max)

    # ========== _map_channel_to_unified() 测试 ==========
    
    def test_map_channel_system(self):
        """测试映射SYSTEM渠道"""
        result = self.dispatcher._map_channel_to_unified("SYSTEM")
        self.assertEqual(result, NotificationChannel.SYSTEM)
        
        result = self.dispatcher._map_channel_to_unified("system")
        self.assertEqual(result, NotificationChannel.SYSTEM)

    def test_map_channel_email(self):
        """测试映射EMAIL渠道"""
        result = self.dispatcher._map_channel_to_unified("EMAIL")
        self.assertEqual(result, NotificationChannel.EMAIL)

    def test_map_channel_wechat(self):
        """测试映射WECHAT渠道"""
        result = self.dispatcher._map_channel_to_unified("WECHAT")
        self.assertEqual(result, NotificationChannel.WECHAT)

    def test_map_channel_sms(self):
        """测试映射SMS渠道"""
        result = self.dispatcher._map_channel_to_unified("SMS")
        self.assertEqual(result, NotificationChannel.SMS)

    def test_map_channel_webhook(self):
        """测试映射WEBHOOK渠道"""
        result = self.dispatcher._map_channel_to_unified("WEBHOOK")
        self.assertEqual(result, NotificationChannel.WEBHOOK)

    def test_map_channel_unknown(self):
        """测试映射未知渠道（默认SYSTEM）"""
        result = self.dispatcher._map_channel_to_unified("UNKNOWN")
        self.assertEqual(result, NotificationChannel.SYSTEM)

    # ========== _map_alert_level_to_priority() 测试 ==========
    
    def test_map_alert_level_urgent(self):
        """测试映射URGENT级别"""
        result = self.dispatcher._map_alert_level_to_priority("URGENT")
        self.assertEqual(result, NotificationPriority.URGENT)

    def test_map_alert_level_critical(self):
        """测试映射CRITICAL级别（也映射为URGENT）"""
        result = self.dispatcher._map_alert_level_to_priority("CRITICAL")
        self.assertEqual(result, NotificationPriority.URGENT)

    def test_map_alert_level_warning(self):
        """测试映射WARNING级别"""
        result = self.dispatcher._map_alert_level_to_priority("WARNING")
        self.assertEqual(result, NotificationPriority.HIGH)

    def test_map_alert_level_info(self):
        """测试映射INFO级别"""
        result = self.dispatcher._map_alert_level_to_priority("INFO")
        self.assertEqual(result, NotificationPriority.NORMAL)

    def test_map_alert_level_unknown(self):
        """测试映射未知级别（默认NORMAL）"""
        result = self.dispatcher._map_alert_level_to_priority("UNKNOWN")
        self.assertEqual(result, NotificationPriority.NORMAL)

    def test_map_alert_level_none(self):
        """测试映射None级别"""
        result = self.dispatcher._map_alert_level_to_priority(None)
        self.assertEqual(result, NotificationPriority.NORMAL)

    # ========== _resolve_recipient_id() 测试 ==========
    
    def test_resolve_recipient_id_from_notification(self):
        """测试从通知对象获取接收者ID"""
        notification = AlertNotification(notify_user_id=123)
        result = self.dispatcher._resolve_recipient_id(notification, None)
        self.assertEqual(result, 123)

    def test_resolve_recipient_id_from_user(self):
        """测试从用户对象获取接收者ID"""
        notification = AlertNotification(notify_user_id=None)
        user = User(id=456)
        result = self.dispatcher._resolve_recipient_id(notification, user)
        self.assertEqual(result, 456)

    def test_resolve_recipient_id_missing(self):
        """测试缺少接收者ID时抛出异常"""
        notification = AlertNotification(notify_user_id=None)
        with self.assertRaises(ValueError) as context:
            self.dispatcher._resolve_recipient_id(notification, None)
        self.assertIn("recipient_id", str(context.exception))

    # ========== _build_request() 测试 ==========
    
    def test_build_request_basic(self):
        """测试构建基本通知请求"""
        alert = AlertRecord(
            id=1,
            alert_no="AL001",
            alert_title="成本超支",
            alert_content="项目成本超过预算20%",
            alert_level="WARNING",
            target_type="project",
            target_name="项目A",
        )
        notification = AlertNotification(
            notify_title="预警通知",
            notify_content="请关注成本",
        )
        
        request = self.dispatcher._build_request(
            notification=notification,
            alert=alert,
            recipient_id=100,
            unified_channel=NotificationChannel.EMAIL,
        )
        
        self.assertIsInstance(request, NotificationRequest)
        self.assertEqual(request.recipient_id, 100)
        self.assertEqual(request.notification_type, "ALERT")
        self.assertEqual(request.category, "alert")
        self.assertEqual(request.title, "预警通知")
        self.assertEqual(request.content, "请关注成本")
        self.assertEqual(request.priority, NotificationPriority.HIGH)
        self.assertEqual(request.channels, [NotificationChannel.EMAIL])
        self.assertEqual(request.source_type, "alert")
        self.assertEqual(request.source_id, 1)
        self.assertEqual(request.link_url, "/alerts/1")
        self.assertEqual(request.extra_data["alert_no"], "AL001")

    def test_build_request_with_force_send(self):
        """测试构建强制发送的请求"""
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification()
        
        request = self.dispatcher._build_request(
            notification=notification,
            alert=alert,
            recipient_id=100,
            unified_channel=NotificationChannel.SYSTEM,
            force_send=True,
        )
        
        self.assertTrue(request.force_send)

    # ========== build_notification_request() 测试 ==========
    
    def test_build_notification_request_with_user(self):
        """测试使用用户对象构建请求"""
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification(
            notify_channel="EMAIL",
            notify_user_id=None,
        )
        user = User(id=200)
        
        request = self.dispatcher.build_notification_request(
            notification=notification,
            alert=alert,
            user=user,
        )
        
        self.assertEqual(request.recipient_id, 200)
        self.assertIn(NotificationChannel.EMAIL, request.channels)

    def test_build_notification_request_default_channel(self):
        """测试默认渠道（SYSTEM）"""
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification(
            notify_channel=None,
            notify_user_id=100,
        )
        
        request = self.dispatcher.build_notification_request(
            notification=notification,
            alert=alert,
            user=None,
        )
        
        self.assertIn(NotificationChannel.SYSTEM, request.channels)

    # ========== dispatch() 测试 ==========
    
    @patch('app.services.notification_dispatcher.get_notification_service')
    @patch('app.services.notification_dispatcher.record_notification_success')
    @patch('app.services.notification_dispatcher.record_notification_failure')
    def test_dispatch_success(self, mock_failure, mock_success, mock_get_service):
        """测试成功分发通知"""
        # Mock统一服务
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_service
        
        # 重新初始化dispatcher
        dispatcher = NotificationDispatcher(self.db)
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification(
            notify_channel="EMAIL",
            notify_user_id=100,
        )
        user = User(id=100)
        
        result = dispatcher.dispatch(notification, alert, user)
        
        self.assertTrue(result)
        self.assertEqual(notification.status, "SENT")
        self.assertIsNotNone(notification.sent_at)
        self.assertIsNone(notification.error_message)
        mock_success.assert_called_once_with("EMAIL")
        mock_failure.assert_not_called()

    @patch('app.services.notification_dispatcher.get_notification_service')
    @patch('app.services.notification_dispatcher.record_notification_success')
    @patch('app.services.notification_dispatcher.record_notification_failure')
    def test_dispatch_failure(self, mock_failure, mock_success, mock_get_service):
        """测试分发失败"""
        # Mock统一服务返回失败
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {
            "success": False,
            "message": "发送失败"
        }
        mock_get_service.return_value = mock_service
        
        dispatcher = NotificationDispatcher(self.db)
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification(
            notify_channel="EMAIL",
            notify_user_id=100,
            retry_count=0,
        )
        user = User(id=100)
        
        result = dispatcher.dispatch(notification, alert, user)
        
        self.assertFalse(result)
        self.assertEqual(notification.status, "FAILED")
        self.assertEqual(notification.error_message, "发送失败")
        self.assertEqual(notification.retry_count, 1)
        self.assertIsNotNone(notification.next_retry_at)
        mock_failure.assert_called_once_with("EMAIL")
        mock_success.assert_not_called()

    @patch('app.services.notification_dispatcher.get_notification_service')
    @patch('app.services.notification_dispatcher.record_notification_failure')
    def test_dispatch_exception(self, mock_failure, mock_get_service):
        """测试分发时发生异常"""
        # Mock统一服务抛出异常
        mock_service = MagicMock()
        mock_service.send_notification.side_effect = Exception("网络错误")
        mock_get_service.return_value = mock_service
        
        dispatcher = NotificationDispatcher(self.db)
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification(
            notify_channel="EMAIL",
            notify_user_id=100,
            retry_count=0,
        )
        user = User(id=100)
        
        result = dispatcher.dispatch(notification, alert, user)
        
        self.assertFalse(result)
        self.assertEqual(notification.status, "FAILED")
        self.assertIn("网络错误", notification.error_message)
        self.assertEqual(notification.retry_count, 1)
        mock_failure.assert_called_once()

    @patch('app.services.notification_dispatcher.get_notification_service')
    @patch('app.services.notification_dispatcher.is_quiet_hours')
    @patch('app.services.notification_dispatcher.next_quiet_resume')
    def test_dispatch_quiet_hours(self, mock_next_resume, mock_is_quiet, mock_get_service):
        """测试免打扰时段延迟发送"""
        # Mock免打扰判断
        mock_is_quiet.return_value = True
        mock_next_resume.return_value = datetime.now() + timedelta(hours=2)
        
        # Mock数据库查询settings
        settings = NotificationSettings(
            user_id=100,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
        )
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = settings
        self.db.query.return_value = mock_query
        
        dispatcher = NotificationDispatcher(self.db)
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification(
            notify_channel="EMAIL",
            notify_user_id=100,
            retry_count=0,
        )
        user = User(id=100)
        
        result = dispatcher.dispatch(notification, alert, user, force_send=False)
        
        self.assertTrue(result)  # 返回True但状态为PENDING
        self.assertEqual(notification.status, "PENDING")
        self.assertIn("quiet hours", notification.error_message)
        self.assertIsNotNone(notification.next_retry_at)

    @patch('app.services.notification_dispatcher.get_notification_service')
    @patch('app.services.notification_dispatcher.is_quiet_hours')
    def test_dispatch_quiet_hours_force_send(self, mock_is_quiet, mock_get_service):
        """测试强制发送忽略免打扰"""
        mock_is_quiet.return_value = True
        
        # Mock统一服务
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_service
        
        dispatcher = NotificationDispatcher(self.db)
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification(
            notify_channel="EMAIL",
            notify_user_id=100,
        )
        user = User(id=100)
        
        result = dispatcher.dispatch(notification, alert, user, force_send=True)
        
        # 强制发送应该成功，不受免打扰影响
        self.assertTrue(result)
        self.assertEqual(notification.status, "SENT")
        mock_is_quiet.assert_not_called()  # 不应该检查免打扰

    @patch('app.services.notification_dispatcher.get_notification_service')
    def test_dispatch_with_request(self, mock_get_service):
        """测试使用预构建的request分发"""
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_service
        
        dispatcher = NotificationDispatcher(self.db)
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        notification = AlertNotification(
            notify_channel="EMAIL",
            notify_user_id=100,
        )
        user = User(id=100)
        
        # 预构建request
        request = NotificationRequest(
            recipient_id=100,
            notification_type="ALERT",
            category="alert",
            title="测试",
            content="内容",
            channels=[NotificationChannel.EMAIL],
        )
        
        result = dispatcher.dispatch(notification, alert, user, request=request)
        
        self.assertTrue(result)
        mock_service.send_notification.assert_called_once_with(request)

    # ========== dispatch_alert_notifications() 测试 ==========
    
    @patch('app.services.notification_queue.enqueue_notification')
    @patch('app.services.notification_dispatcher.resolve_recipients')
    @patch('app.services.notification_dispatcher.resolve_channels')
    @patch('app.services.notification_dispatcher.resolve_channel_target')
    @patch('app.services.notification_dispatcher.channel_allowed')
    def test_dispatch_alert_notifications_success(
        self,
        mock_channel_allowed,
        mock_resolve_target,
        mock_resolve_channels,
        mock_resolve_recipients,
        mock_enqueue,
    ):
        """测试批量分发预警通知成功"""
        # Mock解析接收者
        user1 = User(id=1, username="user1", email="user1@test.com")
        user2 = User(id=2, username="user2", email="user2@test.com")
        mock_resolve_recipients.return_value = {
            1: {"user": user1, "settings": None},
            2: {"user": user2, "settings": None},
        }
        
        # Mock解析渠道
        mock_resolve_channels.return_value = ["SYSTEM", "EMAIL"]
        
        # Mock解析目标
        mock_resolve_target.side_effect = lambda channel, user: (
            f"{user.username}@system" if channel == "SYSTEM" else user.email
        )
        
        # Mock渠道允许
        mock_channel_allowed.return_value = True
        
        # Mock入队成功
        mock_enqueue.return_value = True
        
        # Mock数据库查询不存在重复通知
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query
        
        alert = AlertRecord(
            id=1,
            alert_no="AL001",
            alert_title="成本预警",
            alert_content="成本超支",
            alert_level="WARNING",
        )
        
        result = self.dispatcher.dispatch_alert_notifications(alert)
        
        self.assertEqual(result["created"], 4)  # 2用户 x 2渠道
        self.assertEqual(result["queued"], 4)
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["failed"], 0)

    @patch('app.services.notification_queue.enqueue_notification')
    @patch('app.services.notification_dispatcher.get_notification_service')
    @patch('app.services.notification_dispatcher.record_notification_success')
    def test_dispatch_alert_notifications_fallback_to_direct(
        self,
        mock_success,
        mock_get_service,
        mock_enqueue,
    ):
        """测试队列失败时直接分发"""
        # Mock统一服务
        mock_service = MagicMock()
        mock_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_service
        
        # Mock入队失败
        mock_enqueue.return_value = False
        
        # Mock数据库查询（使用 return_value 而不是 side_effect）
        user = User(id=1, username="user1", email="user1@test.com")
        
        # 创建一个根据参数返回不同结果的函数
        def query_mock(model):
            if model == User:
                mock_q = MagicMock()
                mock_q.filter.return_value.filter.return_value.all.return_value = [user]
                return mock_q
            elif model == NotificationSettings:
                mock_q = MagicMock()
                mock_q.filter.return_value.all.return_value = []
                return mock_q
            else:  # AlertNotification
                mock_q = MagicMock()
                mock_q.filter.return_value.first.return_value = None
                return mock_q
        
        self.db.query.side_effect = query_mock
        
        # 重新初始化dispatcher
        dispatcher = NotificationDispatcher(self.db)
        
        alert = AlertRecord(
            id=1,
            alert_title="测试",
            alert_level="INFO",
        )
        
        with patch('app.services.notification_dispatcher.resolve_recipients') as mock_resolve_recipients, \
             patch('app.services.notification_dispatcher.resolve_channels') as mock_resolve_channels, \
             patch('app.services.notification_dispatcher.resolve_channel_target') as mock_resolve_target, \
             patch('app.services.notification_dispatcher.channel_allowed') as mock_channel_allowed:
            
            mock_resolve_recipients.return_value = {1: {"user": user, "settings": None}}
            mock_resolve_channels.return_value = ["SYSTEM"]
            mock_resolve_target.return_value = "user1@system"
            mock_channel_allowed.return_value = True
            
            result = dispatcher.dispatch_alert_notifications(alert)
        
        self.assertEqual(result["created"], 1)
        self.assertEqual(result["queued"], 0)
        self.assertEqual(result["sent"], 1)
        self.assertEqual(result["failed"], 0)

    @patch('app.services.notification_dispatcher.resolve_recipients')
    def test_dispatch_alert_notifications_no_recipients(self, mock_resolve_recipients):
        """测试无接收者时不创建通知"""
        mock_resolve_recipients.return_value = {}
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        
        result = self.dispatcher.dispatch_alert_notifications(alert)
        
        self.assertEqual(result["created"], 0)
        self.assertEqual(result["queued"], 0)
        self.assertEqual(result["sent"], 0)
        self.assertEqual(result["failed"], 0)

    @patch('app.services.notification_queue.enqueue_notification')
    def test_dispatch_alert_notifications_with_user_ids(self, mock_enqueue):
        """测试指定用户ID列表"""
        mock_enqueue.return_value = True
        
        # Mock数据库查询
        user = User(id=1, username="user1", email="user1@test.com")
        
        def query_mock(model):
            if model == User:
                mock_q = MagicMock()
                mock_q.filter.return_value.filter.return_value.all.return_value = [user]
                return mock_q
            elif model == NotificationSettings:
                mock_q = MagicMock()
                mock_q.filter.return_value.all.return_value = []
                return mock_q
            else:  # AlertNotification
                mock_q = MagicMock()
                mock_q.filter.return_value.first.return_value = None
                return mock_q
        
        self.db.query.side_effect = query_mock
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        
        with patch('app.services.notification_dispatcher.resolve_channels') as mock_resolve_channels, \
             patch('app.services.notification_dispatcher.resolve_channel_target') as mock_resolve_target, \
             patch('app.services.notification_dispatcher.channel_allowed') as mock_channel_allowed:
            
            mock_resolve_channels.return_value = ["SYSTEM"]
            mock_resolve_target.return_value = "user1@system"
            mock_channel_allowed.return_value = True
            
            result = self.dispatcher.dispatch_alert_notifications(
                alert,
                user_ids=[1],
            )
        
        self.assertEqual(result["created"], 1)

    @patch('app.services.notification_queue.enqueue_notification')
    def test_dispatch_alert_notifications_with_channels(self, mock_enqueue):
        """测试指定渠道列表"""
        mock_enqueue.return_value = True
        
        # Mock数据库查询
        user = User(id=1, username="user1", email="user1@test.com")
        
        def query_mock(model):
            if model == AlertNotification:
                mock_q = MagicMock()
                mock_q.filter.return_value.first.return_value = None
                return mock_q
            return MagicMock()
        
        self.db.query.side_effect = query_mock
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        
        with patch('app.services.notification_dispatcher.resolve_recipients') as mock_resolve_recipients, \
             patch('app.services.notification_dispatcher.resolve_channel_target') as mock_resolve_target, \
             patch('app.services.notification_dispatcher.channel_allowed') as mock_channel_allowed:
            
            mock_resolve_recipients.return_value = {1: {"user": user, "settings": None}}
            mock_resolve_target.return_value = user.email
            mock_channel_allowed.return_value = True
            
            result = self.dispatcher.dispatch_alert_notifications(
                alert,
                channels=["EMAIL"],
            )
        
        self.assertEqual(result["created"], 1)

    @patch('app.services.notification_queue.enqueue_notification')
    def test_dispatch_alert_notifications_skip_existing(self, mock_enqueue):
        """测试跳过已存在的通知"""
        # Mock已存在的通知
        existing_notification = AlertNotification(
            alert_id=1,
            notify_channel="EMAIL",
            notify_target="user1@test.com",
        )
        mock_notification_query = MagicMock()
        mock_notification_query.filter.return_value.first.return_value = existing_notification
        
        # Mock其他查询
        user = User(id=1, username="user1", email="user1@test.com")
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.filter.return_value.all.return_value = [user]
        
        mock_settings_query = MagicMock()
        mock_settings_query.filter.return_value.all.return_value = []
        
        self.db.query.side_effect = [
            mock_user_query,
            mock_settings_query,
            mock_notification_query,
        ]
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        
        with patch('app.services.notification_dispatcher.resolve_recipients') as mock_resolve_recipients, \
             patch('app.services.notification_dispatcher.resolve_channels') as mock_resolve_channels, \
             patch('app.services.notification_dispatcher.resolve_channel_target') as mock_resolve_target, \
             patch('app.services.notification_dispatcher.channel_allowed') as mock_channel_allowed:
            
            mock_resolve_recipients.return_value = {1: {"user": user, "settings": None}}
            mock_resolve_channels.return_value = ["EMAIL"]
            mock_resolve_target.return_value = user.email
            mock_channel_allowed.return_value = True
            
            result = self.dispatcher.dispatch_alert_notifications(alert)
        
        # 应该跳过已存在的通知
        self.assertEqual(result["created"], 0)

    @patch('app.services.notification_queue.enqueue_notification')
    def test_dispatch_alert_notifications_channel_not_allowed(self, mock_enqueue):
        """测试渠道不允许时跳过"""
        # Mock数据库查询
        user = User(id=1, username="user1", email="user1@test.com")
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.filter.return_value.all.return_value = [user]
        
        mock_settings_query = MagicMock()
        mock_settings_query.filter.return_value.all.return_value = []
        
        self.db.query.side_effect = [mock_user_query, mock_settings_query]
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        
        with patch('app.services.notification_dispatcher.resolve_recipients') as mock_resolve_recipients, \
             patch('app.services.notification_dispatcher.resolve_channels') as mock_resolve_channels, \
             patch('app.services.notification_dispatcher.channel_allowed') as mock_channel_allowed:
            
            mock_resolve_recipients.return_value = {1: {"user": user, "settings": None}}
            mock_resolve_channels.return_value = ["EMAIL"]
            mock_channel_allowed.return_value = False  # 渠道不允许
            
            result = self.dispatcher.dispatch_alert_notifications(alert)
        
        # 渠道不允许，不创建通知
        self.assertEqual(result["created"], 0)

    @patch('app.services.notification_queue.enqueue_notification')
    def test_dispatch_alert_notifications_no_target(self, mock_enqueue):
        """测试无法解析目标时跳过"""
        # Mock数据库查询
        user = User(id=1, username="user1", email=None)  # 无邮箱
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.filter.return_value.all.return_value = [user]
        
        mock_settings_query = MagicMock()
        mock_settings_query.filter.return_value.all.return_value = []
        
        self.db.query.side_effect = [mock_user_query, mock_settings_query]
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        
        with patch('app.services.notification_dispatcher.resolve_recipients') as mock_resolve_recipients, \
             patch('app.services.notification_dispatcher.resolve_channels') as mock_resolve_channels, \
             patch('app.services.notification_dispatcher.resolve_channel_target') as mock_resolve_target, \
             patch('app.services.notification_dispatcher.channel_allowed') as mock_channel_allowed:
            
            mock_resolve_recipients.return_value = {1: {"user": user, "settings": None}}
            mock_resolve_channels.return_value = ["EMAIL"]
            mock_resolve_target.return_value = None  # 无法解析目标
            mock_channel_allowed.return_value = True
            
            result = self.dispatcher.dispatch_alert_notifications(alert)
        
        # 无目标，不创建通知
        self.assertEqual(result["created"], 0)

    def test_dispatch_alert_notifications_exception_in_resolve_recipients(self):
        """测试解析接收者时异常"""
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        
        with patch('app.services.notification_dispatcher.resolve_recipients') as mock_resolve:
            mock_resolve.side_effect = Exception("解析失败")
            
            result = self.dispatcher.dispatch_alert_notifications(alert)
        
        # 异常时返回空结果
        self.assertEqual(result["created"], 0)

    def test_dispatch_alert_notifications_exception_in_resolve_channels(self):
        """测试解析渠道时异常"""
        user = User(id=1, username="user1", email="user1@test.com")
        
        alert = AlertRecord(id=1, alert_title="测试", alert_level="INFO")
        
        # Mock数据库查询
        def query_mock(model):
            if model == AlertNotification:
                mock_q = MagicMock()
                mock_q.filter.return_value.first.return_value = None
                return mock_q
            return MagicMock()
        
        self.db.query.side_effect = query_mock
        
        with patch('app.services.notification_dispatcher.resolve_recipients') as mock_resolve_recipients, \
             patch('app.services.notification_dispatcher.resolve_channels') as mock_resolve_channels:
            
            mock_resolve_recipients.return_value = {1: {"user": user, "settings": None}}
            mock_resolve_channels.side_effect = Exception("解析失败")
            
            with patch('app.services.notification_queue.enqueue_notification') as mock_enqueue, \
                 patch('app.services.notification_dispatcher.resolve_channel_target') as mock_resolve_target, \
                 patch('app.services.notification_dispatcher.channel_allowed') as mock_channel_allowed:
                
                mock_enqueue.return_value = True
                mock_resolve_target.return_value = "user1@system"
                mock_channel_allowed.return_value = True
                
                result = self.dispatcher.dispatch_alert_notifications(alert)
            
            # 应该使用默认SYSTEM渠道创建通知
            self.assertEqual(result["created"], 1)


class TestNotificationDispatcherEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.dispatcher = NotificationDispatcher(self.db)

    def test_create_system_notification_empty_extra_data(self):
        """测试空额外数据"""
        notification = self.dispatcher.create_system_notification(
            recipient_id=1,
            notification_type="ALERT",
            title="测试",
            content="内容",
            extra_data=None,
        )
        self.assertEqual(notification.extra_data, {})

    def test_resolve_recipients_by_ids_with_duplicates(self):
        """测试重复的用户ID"""
        user = User(id=1, username="user1", is_active=True)
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.filter.return_value.all.return_value = [user]
        
        mock_settings_query = MagicMock()
        mock_settings_query.filter.return_value.all.return_value = []
        
        self.db.query.side_effect = [mock_user_query, mock_settings_query]
        
        # 传入重复ID
        result = self.dispatcher._resolve_recipients_by_ids([1, 1, 1])
        
        # 应该去重
        self.assertEqual(len(result), 1)

    def test_build_request_missing_alert_fields(self):
        """测试alert缺少部分字段"""
        alert = AlertRecord(id=1)  # 只有id
        notification = AlertNotification()
        
        request = self.dispatcher._build_request(
            notification=notification,
            alert=alert,
            recipient_id=100,
            unified_channel=NotificationChannel.SYSTEM,
        )
        
        # 应该使用默认值
        self.assertEqual(request.title, "预警通知")
        self.assertEqual(request.content, "")
        self.assertEqual(request.priority, NotificationPriority.NORMAL)


if __name__ == "__main__":
    unittest.main()
