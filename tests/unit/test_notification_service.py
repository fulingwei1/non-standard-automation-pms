# -*- coding: utf-8 -*-
"""
通知服务单元测试

测试策略：
1. 只mock外部依赖（db操作、外部服务调用）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率：70%+
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime
from app.services.notification_service import (
    NotificationService,
    AlertNotificationService,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
)


class TestNotificationServiceCore(unittest.TestCase):
    """测试 NotificationService 核心功能"""

    def setUp(self):
        """每个测试前的设置"""
        self.mock_db = MagicMock()
        self.service = NotificationService(db=self.mock_db)

    # ========== __init__ 和配置测试 ==========

    def test_init_with_db(self):
        """测试带db参数的初始化"""
        service = NotificationService(db=self.mock_db)
        self.assertEqual(service._db, self.mock_db)
        self.assertIsNotNone(service.enabled_channels)

    def test_init_without_db(self):
        """测试不带db参数的初始化"""
        service = NotificationService()
        self.assertIsNone(service._db)
        self.assertIsNotNone(service.enabled_channels)

    @patch('app.services.notification_service.settings')
    def test_get_enabled_channels_all_enabled(self, mock_settings):
        """测试所有渠道都启用"""
        mock_settings.EMAIL_ENABLED = True
        mock_settings.SMS_ENABLED = True
        mock_settings.WECHAT_ENABLED = True
        mock_settings.WECHAT_WEBHOOK_URL = "http://webhook.example.com"

        service = NotificationService()
        channels = service._get_enabled_channels()

        self.assertIn(NotificationChannel.WEB, channels)
        self.assertIn(NotificationChannel.EMAIL, channels)
        self.assertIn(NotificationChannel.SMS, channels)
        self.assertIn(NotificationChannel.WECHAT, channels)
        self.assertIn(NotificationChannel.WEBHOOK, channels)

    @patch('app.services.notification_service.settings')
    def test_get_enabled_channels_only_web(self, mock_settings):
        """测试只启用站内通知"""
        mock_settings.EMAIL_ENABLED = False
        mock_settings.SMS_ENABLED = False
        mock_settings.WECHAT_ENABLED = False
        mock_settings.WECHAT_WEBHOOK_URL = None

        service = NotificationService()
        channels = service._get_enabled_channels()

        self.assertEqual(len(channels), 1)
        self.assertIn(NotificationChannel.WEB, channels)

    # ========== 渠道和优先级映射测试 ==========

    def test_map_old_channel_to_new(self):
        """测试渠道映射"""
        self.assertEqual(
            self.service._map_old_channel_to_new(NotificationChannel.WEB),
            "system"
        )
        self.assertEqual(
            self.service._map_old_channel_to_new(NotificationChannel.EMAIL),
            "email"
        )
        self.assertEqual(
            self.service._map_old_channel_to_new(NotificationChannel.WECHAT),
            "wechat"
        )

    def test_map_old_priority_to_new_enum(self):
        """测试优先级映射（枚举类型）"""
        result = self.service._map_old_priority_to_new(NotificationPriority.HIGH)
        self.assertEqual(result, "high")

    def test_map_old_priority_to_new_string(self):
        """测试优先级映射（字符串类型）"""
        result = self.service._map_old_priority_to_new("urgent")
        self.assertEqual(result, "urgent")

    def test_map_old_priority_to_new_other(self):
        """测试优先级映射（其他类型）"""
        result = self.service._map_old_priority_to_new(123)
        self.assertEqual(result, "123")

    # ========== _infer_category 测试 ==========

    def test_infer_category_task(self):
        """测试推断task分类"""
        result = self.service._infer_category(NotificationType.TASK_ASSIGNED)
        self.assertEqual(result, "task")

    def test_infer_category_project(self):
        """测试推断project分类"""
        result = self.service._infer_category(NotificationType.PROJECT_UPDATE)
        self.assertEqual(result, "project")

    def test_infer_category_general(self):
        """测试推断general分类"""
        result = self.service._infer_category(NotificationType.SYSTEM_ANNOUNCEMENT)
        self.assertEqual(result, "general")

    # ========== send_notification 主方法测试 ==========

    @patch('app.services.notification_service.get_notification_service')
    def test_send_notification_success(self, mock_get_service):
        """测试发送通知成功"""
        # Mock统一服务
        mock_unified_service = MagicMock()
        mock_unified_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_unified_service

        # 调用
        result = self.service.send_notification(
            db=self.mock_db,
            recipient_id=1,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="测试通知",
            content="这是测试内容",
            priority=NotificationPriority.NORMAL,
            channels=[NotificationChannel.EMAIL],
            data={"task_id": 123},
            link="http://example.com/task/123"
        )

        # 验证
        self.assertTrue(result)
        mock_get_service.assert_called_once_with(self.mock_db)
        mock_unified_service.send_notification.assert_called_once()

    @patch('app.services.notification_service.get_notification_service')
    def test_send_notification_without_channels(self, mock_get_service):
        """测试发送通知（不指定渠道）"""
        mock_unified_service = MagicMock()
        mock_unified_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_unified_service

        result = self.service.send_notification(
            db=self.mock_db,
            recipient_id=1,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="测试通知",
            content="测试内容"
        )

        self.assertTrue(result)

    def test_send_notification_no_db(self):
        """测试发送通知时没有db"""
        result = self.service.send_notification(
            db=None,
            recipient_id=1,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="测试通知",
            content="测试内容"
        )

        self.assertFalse(result)

    @patch('app.services.notification_service.get_notification_service')
    def test_send_notification_fail(self, mock_get_service):
        """测试发送通知失败"""
        mock_unified_service = MagicMock()
        mock_unified_service.send_notification.return_value = {"success": False}
        mock_get_service.return_value = mock_unified_service

        result = self.service.send_notification(
            db=self.mock_db,
            recipient_id=1,
            notification_type=NotificationType.TASK_ASSIGNED,
            title="测试通知",
            content="测试内容"
        )

        self.assertFalse(result)

    # ========== 具体通知方法测试 ==========

    @patch('app.services.notification_service.get_notification_service')
    def test_send_task_assigned_notification(self, mock_get_service):
        """测试发送任务分配通知"""
        mock_unified_service = MagicMock()
        mock_unified_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_unified_service

        result = self.service.send_task_assigned_notification(
            db=self.mock_db,
            assignee_id=1,
            task_name="开发新功能",
            project_name="项目A",
            task_id=123,
            due_date=datetime(2026, 3, 1)
        )

        self.assertTrue(result)
        call_args = mock_unified_service.send_notification.call_args[0][0]
        self.assertIn("开发新功能", call_args.title)
        self.assertIn("2026-03-01", call_args.content)

    @patch('app.services.notification_service.get_notification_service')
    def test_send_task_assigned_notification_without_due_date(self, mock_get_service):
        """测试发送任务分配通知（无截止日期）"""
        mock_unified_service = MagicMock()
        mock_unified_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_unified_service

        result = self.service.send_task_assigned_notification(
            db=self.mock_db,
            assignee_id=1,
            task_name="开发新功能",
            project_name="项目A",
            task_id=123
        )

        self.assertTrue(result)

    @patch('app.services.notification_service.get_notification_service')
    def test_send_task_completed_notification(self, mock_get_service):
        """测试发送任务完成通知"""
        mock_unified_service = MagicMock()
        mock_unified_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_unified_service

        result = self.service.send_task_completed_notification(
            db=self.mock_db,
            task_owner_id=1,
            task_name="开发新功能",
            project_name="项目A"
        )

        self.assertTrue(result)
        call_args = mock_unified_service.send_notification.call_args[0][0]
        self.assertIn("开发新功能", call_args.title)
        self.assertIn("已完成", call_args.title)

    @patch('app.services.notification_service.get_notification_service')
    def test_send_deadline_reminder_urgent(self, mock_get_service):
        """测试发送紧急截止日期提醒"""
        mock_unified_service = MagicMock()
        mock_unified_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_unified_service

        result = self.service.send_deadline_reminder(
            db=self.mock_db,
            recipient_id=1,
            task_name="开发新功能",
            due_date=datetime(2026, 3, 1),
            days_remaining=1
        )

        self.assertTrue(result)
        call_args = mock_unified_service.send_notification.call_args[0][0]
        self.assertIn("紧急", call_args.title)

    @patch('app.services.notification_service.get_notification_service')
    def test_send_deadline_reminder_normal(self, mock_get_service):
        """测试发送普通截止日期提醒"""
        mock_unified_service = MagicMock()
        mock_unified_service.send_notification.return_value = {"success": True}
        mock_get_service.return_value = mock_unified_service

        result = self.service.send_deadline_reminder(
            db=self.mock_db,
            recipient_id=1,
            task_name="开发新功能",
            due_date=datetime(2026, 3, 1),
            days_remaining=5
        )

        self.assertTrue(result)
        call_args = mock_unified_service.send_notification.call_args[0][0]
        self.assertNotIn("紧急", call_args.title)


class TestAlertNotificationService(unittest.TestCase):
    """测试 AlertNotificationService 功能"""

    def setUp(self):
        """每个测试前的设置"""
        self.mock_db = MagicMock()
        self.service = AlertNotificationService(db=self.mock_db)

    # ========== __init__ 测试 ==========

    @patch('app.services.notification_service.get_notification_service')
    def test_init(self, mock_get_service):
        """测试初始化"""
        service = AlertNotificationService(db=self.mock_db)
        self.assertEqual(service.db, self.mock_db)
        mock_get_service.assert_called_once_with(self.mock_db)

    # ========== create_alert_notification 测试 ==========

    @patch('app.models.alert.AlertNotification')
    def test_create_alert_notification_with_alert_record(self, mock_alert_notification_model):
        """测试创建预警通知记录（AlertRecord类型）"""
        # Mock AlertRecord
        mock_alert = MagicMock()
        mock_alert.__class__.__name__ = "AlertRecord"
        mock_alert.id = 123
        mock_alert.assignee_id = 456

        # Mock AlertNotification实例
        mock_notification_instance = MagicMock()
        mock_alert_notification_model.return_value = mock_notification_instance

        # 调用
        result = AlertNotificationService.create_alert_notification(
            db=self.mock_db,
            alert=mock_alert,
            notify_channel="EMAIL",
            status="pending"
        )

        # 验证
        self.mock_db.add.assert_called_once_with(mock_notification_instance)
        self.mock_db.commit.assert_called_once()
        self.assertEqual(result, mock_notification_instance)

    @patch('app.models.alert.AlertNotification')
    def test_create_alert_notification_with_other_type(self, mock_alert_notification_model):
        """测试创建预警通知记录（其他类型）"""
        # Mock 其他类型的alert
        mock_alert = MagicMock()
        mock_alert.__class__.__name__ = "OtherAlert"
        mock_alert.id = 789
        mock_alert.assignee_id = 101

        mock_notification_instance = MagicMock()
        mock_alert_notification_model.return_value = mock_notification_instance

        result = AlertNotificationService.create_alert_notification(
            db=self.mock_db,
            alert=mock_alert,
            notify_channel="SMS"
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    # ========== send_alert_notification 测试 ==========

    @patch('app.services.notification_dispatcher.NotificationDispatcher')
    def test_send_alert_notification_with_user_ids(self, mock_dispatcher_class):
        """测试发送预警通知（指定用户ID列表）"""
        # Mock alert
        mock_alert = MagicMock()
        mock_alert.alert_title = "测试预警"
        mock_alert.alert_content = "这是测试预警内容"

        # Mock dispatcher
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch_alert_notifications.return_value = {"queued": 1}
        mock_dispatcher_class.return_value = mock_dispatcher

        # 调用
        result = self.service.send_alert_notification(
            alert=mock_alert,
            user_ids=[1, 2, 3],
            channels=["EMAIL", "WECHAT"]
        )

        # 验证
        self.assertTrue(result)
        mock_dispatcher.dispatch_alert_notifications.assert_called_once()
        call_kwargs = mock_dispatcher.dispatch_alert_notifications.call_args[1]
        self.assertEqual(call_kwargs["user_ids"], [1, 2, 3])
        self.assertIn("EMAIL", call_kwargs["channels"])

    @patch('app.services.notification_dispatcher.NotificationDispatcher')
    def test_send_alert_notification_with_single_user(self, mock_dispatcher_class):
        """测试发送预警通知（单个用户）"""
        mock_alert = MagicMock()
        mock_alert.alert_title = "测试预警"
        mock_alert.alert_content = "测试内容"

        mock_user = MagicMock()
        mock_user.id = 123

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch_alert_notifications.return_value = {"sent": 1}
        mock_dispatcher_class.return_value = mock_dispatcher

        result = self.service.send_alert_notification(
            alert=mock_alert,
            user=mock_user
        )

        self.assertTrue(result)

    @patch('app.services.notification_dispatcher.NotificationDispatcher')
    def test_send_alert_notification_from_alert_assignee(self, mock_dispatcher_class):
        """测试发送预警通知（从alert获取接收者）"""
        # Mock AlertRecord
        from app.models.alert import AlertRecord
        mock_alert = MagicMock(spec=AlertRecord)
        mock_alert.assignee_id = 999
        mock_alert.alert_title = "测试预警"
        mock_alert.alert_content = "测试内容"

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch_alert_notifications.return_value = {"created": 1}
        mock_dispatcher_class.return_value = mock_dispatcher

        result = self.service.send_alert_notification(alert=mock_alert)

        self.assertTrue(result)
        call_kwargs = mock_dispatcher.dispatch_alert_notifications.call_args[1]
        self.assertIn(999, call_kwargs["user_ids"])

    @patch('app.services.notification_dispatcher.NotificationDispatcher')
    def test_send_alert_notification_no_recipients(self, mock_dispatcher_class):
        """测试发送预警通知（无接收者）"""
        mock_alert = MagicMock()
        mock_alert.assignee_id = None
        mock_alert.handler_id = None
        mock_alert.alert_title = "测试预警"

        result = self.service.send_alert_notification(alert=mock_alert)

        self.assertFalse(result)
        mock_dispatcher_class.assert_not_called()

    @patch('app.services.notification_dispatcher.NotificationDispatcher')
    def test_send_alert_notification_with_exception(self, mock_dispatcher_class):
        """测试发送预警通知异常处理"""
        mock_alert = MagicMock()
        mock_alert.alert_title = "测试预警"
        mock_alert.alert_content = "测试内容"

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch_alert_notifications.side_effect = Exception("测试异常")
        mock_dispatcher_class.return_value = mock_dispatcher

        result = self.service.send_alert_notification(
            alert=mock_alert,
            user_ids=[1]
        )

        self.assertFalse(result)

    @patch('app.services.notification_dispatcher.NotificationDispatcher')
    def test_send_alert_notification_channel_normalization(self, mock_dispatcher_class):
        """测试渠道名称规范化"""
        mock_alert = MagicMock()
        mock_alert.alert_title = "测试"
        mock_alert.alert_content = "内容"

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch_alert_notifications.return_value = {"sent": 1}
        mock_dispatcher_class.return_value = mock_dispatcher

        # 测试各种渠道名称格式
        result = self.service.send_alert_notification(
            alert=mock_alert,
            user_ids=[1],
            channels=["web", "EMAIL", "WeChaT", None, ""]
        )

        self.assertTrue(result)
        call_kwargs = mock_dispatcher.dispatch_alert_notifications.call_args[1]
        # 验证渠道被正确规范化
        self.assertIn("SYSTEM", call_kwargs["channels"])
        self.assertIn("EMAIL", call_kwargs["channels"])
        self.assertIn("WECHAT", call_kwargs["channels"])

    # ========== get_user_notifications 测试 ==========

    @patch('app.models.alert.AlertNotification')
    @patch('app.models.alert.AlertRecord')
    def test_get_user_notifications_success(self, mock_alert_record, mock_alert_notification):
        """测试获取用户通知列表成功"""
        # Mock query结果
        mock_notification1 = MagicMock()
        mock_notification1.id = 1
        mock_notification1.alert_id = 10
        mock_notification1.notify_channel = "EMAIL"
        mock_notification1.status = "SENT"
        mock_notification1.created_at = datetime(2026, 2, 20)
        mock_notification1.sent_at = datetime(2026, 2, 20, 10, 0)
        mock_notification1.notify_title = "通知1"

        mock_alert1 = MagicMock()
        mock_alert1.alert_title = "预警1"
        mock_alert1.alert_level = "HIGH"

        # Mock数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.all.return_value = [mock_notification1]
        mock_query.first.return_value = mock_alert1

        self.mock_db.query.return_value = mock_query

        # 调用
        result = self.service.get_user_notifications(user_id=123, limit=10, offset=0)

        # 验证
        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["id"], 1)
        self.assertEqual(result["items"][0]["alert_title"], "预警1")

    @patch('app.models.alert.AlertNotification')
    def test_get_user_notifications_filter_read(self, mock_alert_notification):
        """测试筛选已读通知"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.all.return_value = []

        self.mock_db.query.return_value = mock_query

        result = self.service.get_user_notifications(
            user_id=123,
            is_read=True,
            limit=10
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["total"], 0)

    def test_get_user_notifications_exception(self):
        """测试获取通知列表异常"""
        self.mock_db.query.side_effect = Exception("数据库错误")

        result = self.service.get_user_notifications(user_id=123)

        self.assertFalse(result["success"])
        self.assertEqual(result["total"], 0)

    # ========== mark_notification_read 测试 ==========

    @patch('app.models.alert.AlertNotification')
    def test_mark_notification_read_success(self, mock_alert_notification):
        """测试标记通知为已读成功"""
        mock_notification = MagicMock()
        mock_notification.status = "PENDING"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_notification

        self.mock_db.query.return_value = mock_query

        result = self.service.mark_notification_read(
            notification_id=1,
            user_id=123
        )

        self.assertTrue(result)
        self.assertEqual(mock_notification.status, "SENT")
        self.mock_db.commit.assert_called_once()

    @patch('app.models.alert.AlertNotification')
    def test_mark_notification_read_not_found(self, mock_alert_notification):
        """测试标记不存在的通知"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        self.mock_db.query.return_value = mock_query

        result = self.service.mark_notification_read(
            notification_id=999,
            user_id=123
        )

        self.assertFalse(result)

    @patch('app.models.alert.AlertNotification')
    def test_mark_notification_read_exception(self, mock_alert_notification):
        """测试标记通知异常"""
        mock_notification = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_notification

        self.mock_db.query.return_value = mock_query
        self.mock_db.commit.side_effect = Exception("数据库错误")

        result = self.service.mark_notification_read(
            notification_id=1,
            user_id=123
        )

        self.assertFalse(result)
        self.mock_db.rollback.assert_called_once()

    # ========== get_unread_count 测试 ==========

    @patch('app.models.alert.AlertNotification')
    def test_get_unread_count_success(self, mock_alert_notification):
        """测试获取未读数量成功"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5

        self.mock_db.query.return_value = mock_query

        result = self.service.get_unread_count(user_id=123)

        self.assertEqual(result, 5)

    @patch('app.models.alert.AlertNotification')
    def test_get_unread_count_exception(self, mock_alert_notification):
        """测试获取未读数量异常"""
        self.mock_db.query.side_effect = Exception("数据库错误")

        result = self.service.get_unread_count(user_id=123)

        self.assertEqual(result, 0)

    # ========== batch_mark_read 测试 ==========

    @patch('app.models.alert.AlertNotification')
    def test_batch_mark_read_success(self, mock_alert_notification):
        """测试批量标记已读成功"""
        mock_notif1 = MagicMock()
        mock_notif1.status = "PENDING"
        mock_notif2 = MagicMock()
        mock_notif2.status = "PENDING"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_notif1, mock_notif2]

        self.mock_db.query.return_value = mock_query

        result = self.service.batch_mark_read(
            notification_ids=[1, 2],
            user_id=123
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["total_count"], 2)
        self.mock_db.commit.assert_called_once()

    @patch('app.models.alert.AlertNotification')
    def test_batch_mark_read_partial(self, mock_alert_notification):
        """测试批量标记部分成功"""
        mock_notif = MagicMock()
        mock_notif.status = "PENDING"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_notif]  # 只找到一个

        self.mock_db.query.return_value = mock_query

        result = self.service.batch_mark_read(
            notification_ids=[1, 2, 3],
            user_id=123
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["total_count"], 3)

    @patch('app.models.alert.AlertNotification')
    def test_batch_mark_read_exception(self, mock_alert_notification):
        """测试批量标记异常"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = Exception("数据库错误")

        self.mock_db.query.return_value = mock_query

        result = self.service.batch_mark_read(
            notification_ids=[1, 2],
            user_id=123
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["success_count"], 0)
        self.mock_db.rollback.assert_called_once()


class TestEnums(unittest.TestCase):
    """测试枚举类型"""

    def test_notification_channel_values(self):
        """测试通知渠道枚举值"""
        self.assertEqual(NotificationChannel.SYSTEM.value, "system")
        self.assertEqual(NotificationChannel.EMAIL.value, "email")
        self.assertEqual(NotificationChannel.SMS.value, "sms")
        self.assertEqual(NotificationChannel.WECHAT.value, "wechat")
        self.assertEqual(NotificationChannel.WEB.value, "web")
        self.assertEqual(NotificationChannel.WEBHOOK.value, "webhook")

    def test_notification_priority_values(self):
        """测试通知优先级枚举值"""
        self.assertEqual(NotificationPriority.LOW.value, "low")
        self.assertEqual(NotificationPriority.NORMAL.value, "normal")
        self.assertEqual(NotificationPriority.HIGH.value, "high")
        self.assertEqual(NotificationPriority.URGENT.value, "urgent")

    def test_notification_type_values(self):
        """测试通知类型枚举值"""
        self.assertEqual(NotificationType.TASK_ASSIGNED.value, "task_assigned")
        self.assertEqual(NotificationType.TASK_UPDATED.value, "task_updated")
        self.assertEqual(NotificationType.TASK_COMPLETED.value, "task_completed")
        self.assertEqual(NotificationType.PROJECT_UPDATE.value, "project_update")
        self.assertEqual(NotificationType.DEADLINE_REMINDER.value, "deadline_reminder")


class TestHelperFunctions(unittest.TestCase):
    """测试辅助函数"""

    def test_get_notification_service_instance(self):
        """测试获取通知服务实例"""
        from app.services.notification_service import get_notification_service_instance

        mock_db = MagicMock()
        service = get_notification_service_instance(db=mock_db)

        self.assertIsInstance(service, NotificationService)
        self.assertEqual(service._db, mock_db)

    def test_get_notification_service_instance_without_db(self):
        """测试获取通知服务实例（无db）"""
        from app.services.notification_service import get_notification_service_instance

        service = get_notification_service_instance()

        self.assertIsInstance(service, NotificationService)


if __name__ == "__main__":
    unittest.main()
