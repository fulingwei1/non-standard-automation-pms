# -*- coding: utf-8 -*-
"""
审批代理人服务单元测试

测试策略：
1. 只mock外部依赖（db.query, db.add等）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from datetime import date, datetime, timedelta

from app.services.approval_engine.delegate import ApprovalDelegateService
from app.models.approval import (
    ApprovalDelegate,
    ApprovalDelegateLog,
    ApprovalTask,
)


class TestApprovalDelegateService(unittest.TestCase):
    """测试审批代理人服务"""

    def setUp(self):
        """测试前准备"""
        self.db = MagicMock()
        self.service = ApprovalDelegateService(self.db)

    # ========== get_active_delegate() 测试 ==========

    def test_get_active_delegate_with_all_scope(self):
        """测试获取ALL范围的代理配置"""
        today = date.today()
        
        # Mock代理配置
        delegate = Mock()
        delegate.scope = "ALL"
        delegate.user_id = 1
        delegate.delegate_id = 2
        delegate.is_active = True
        delegate.start_date = today - timedelta(days=1)
        delegate.end_date = today + timedelta(days=7)
        
        # Mock数据库查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [delegate]
        
        result = self.service.get_active_delegate(user_id=1)
        
        self.assertEqual(result, delegate)
        self.db.query.assert_called_once()

    def test_get_active_delegate_with_template_scope(self):
        """测试获取TEMPLATE范围的代理配置"""
        today = date.today()
        
        delegate = Mock()
        delegate.scope = "TEMPLATE"
        delegate.template_ids = [100, 200, 300]
        delegate.is_active = True
        delegate.start_date = today - timedelta(days=1)
        delegate.end_date = today + timedelta(days=7)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [delegate]
        
        # 测试匹配的模板
        result = self.service.get_active_delegate(user_id=1, template_id=200)
        self.assertEqual(result, delegate)
        
        # 测试不匹配的模板
        result = self.service.get_active_delegate(user_id=1, template_id=999)
        self.assertIsNone(result)

    def test_get_active_delegate_with_category_scope(self):
        """测试获取CATEGORY范围的代理配置"""
        today = date.today()
        
        delegate = Mock()
        delegate.scope = "CATEGORY"
        delegate.categories = ["EXPENSE", "LEAVE"]
        delegate.is_active = True
        delegate.start_date = today
        delegate.end_date = today + timedelta(days=7)
        
        # Mock模板查询
        mock_template = Mock()
        mock_template.id = 100
        mock_template.category = "EXPENSE"
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # 第一次调用返回delegate，第二次调用返回template
        mock_query.all.return_value = [delegate]
        mock_query.first.return_value = mock_template
        
        result = self.service.get_active_delegate(user_id=1, template_id=100)
        self.assertEqual(result, delegate)

    def test_get_active_delegate_no_active_config(self):
        """测试无生效的代理配置"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.get_active_delegate(user_id=1)
        self.assertIsNone(result)

    def test_get_active_delegate_with_custom_date(self):
        """测试使用自定义日期"""
        check_date = date(2024, 6, 15)
        
        delegate = Mock()
        delegate.scope = "ALL"
        delegate.start_date = date(2024, 6, 10)
        delegate.end_date = date(2024, 6, 20)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [delegate]
        
        result = self.service.get_active_delegate(user_id=1, check_date=check_date)
        self.assertEqual(result, delegate)

    # ========== apply_delegation() 测试 ==========

    def test_apply_delegation_success(self):
        """测试成功应用代理"""
        # Mock任务
        mock_task = Mock()
        mock_instance = Mock()
        mock_instance.template_id = 100
        mock_instance.id = 1
        mock_task.instance = mock_instance
        mock_task.id = 10
        
        # Mock代理配置
        mock_delegate = Mock()
        mock_delegate.id = 5
        mock_delegate.delegate_id = 2
        
        # Mock用户
        mock_user = Mock()
        mock_user.id = 2
        mock_user.real_name = "李四"
        mock_user.username = "lisi"
        
        # Mock get_active_delegate方法
        with patch.object(self.service, 'get_active_delegate', return_value=mock_delegate):
            # Mock用户查询
            mock_query = MagicMock()
            self.db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_user
            
            result = self.service.apply_delegation(mock_task, original_assignee_id=1)
            
            self.assertEqual(result, mock_task)
            self.assertEqual(mock_task.original_assignee_id, 1)
            self.assertEqual(mock_task.assignee_type, "DELEGATED")
            self.assertEqual(mock_task.assignee_id, 2)
            self.assertEqual(mock_task.assignee_name, "李四")
            self.db.add.assert_called_once()

    def test_apply_delegation_no_delegate_config(self):
        """测试无代理配置时不应用"""
        mock_task = Mock()
        mock_instance = Mock()
        mock_instance.template_id = 100
        mock_task.instance = mock_instance
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        result = self.service.apply_delegation(mock_task, original_assignee_id=1)
        
        self.assertIsNone(result)
        self.db.add.assert_not_called()

    def test_apply_delegation_without_real_name(self):
        """测试代理人无真实姓名时使用用户名"""
        mock_task = Mock()
        mock_instance = Mock()
        mock_instance.template_id = 100
        mock_instance.id = 1
        mock_task.instance = mock_instance
        mock_task.id = 10
        
        mock_delegate = Mock()
        mock_delegate.id = 5
        mock_delegate.delegate_id = 2
        
        mock_user = Mock()
        mock_user.id = 2
        mock_user.real_name = None
        mock_user.username = "delegate_user"
        
        with patch.object(self.service, 'get_active_delegate', return_value=mock_delegate):
            mock_query = MagicMock()
            self.db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = mock_user
            
            result = self.service.apply_delegation(mock_task, original_assignee_id=1)
            
            self.assertEqual(mock_task.assignee_name, "delegate_user")

    # ========== create_delegate() 测试 ==========

    def test_create_delegate_success(self):
        """测试成功创建代理配置"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        # Mock查询，无重叠配置
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=start_date,
            end_date=end_date,
            scope="ALL",
            reason="出差",
            created_by=1,
        )
        
        self.assertIsNotNone(result)
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()

    def test_create_delegate_with_template_scope(self):
        """测试创建指定模板的代理配置"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=start_date,
            end_date=end_date,
            scope="TEMPLATE",
            template_ids=[100, 200],
        )
        
        self.db.add.assert_called_once()

    def test_create_delegate_with_category_scope(self):
        """测试创建指定分类的代理配置"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=start_date,
            end_date=end_date,
            scope="CATEGORY",
            categories=["EXPENSE", "LEAVE"],
        )
        
        self.db.add.assert_called_once()

    def test_create_delegate_with_overlapping_config(self):
        """测试创建重叠的代理配置应抛出异常"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        # Mock已存在的重叠配置
        existing = Mock()
        existing.id = 1
        existing.start_date = start_date
        existing.end_date = end_date
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing
        
        with self.assertRaises(ValueError) as context:
            self.service.create_delegate(
                user_id=1,
                delegate_id=2,
                start_date=start_date,
                end_date=end_date,
            )
        
        self.assertIn("重叠", str(context.exception))
        self.db.add.assert_not_called()

    def test_create_delegate_default_created_by(self):
        """测试默认created_by为user_id"""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 不传created_by
        self.service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=start_date,
            end_date=end_date,
        )
        
        # 获取调用add的参数
        call_args = self.db.add.call_args[0][0]
        self.assertEqual(call_args.created_by, 1)

    # ========== update_delegate() 测试 ==========

    def test_update_delegate_success(self):
        """测试成功更新代理配置"""
        mock_delegate = Mock()
        mock_delegate.id = 1
        mock_delegate.delegate_id = 2
        mock_delegate.reason = "出差"
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_delegate
        
        result = self.service.update_delegate(
            delegate_id=1,
            reason="休假",
            is_active=False,
        )
        
        self.assertEqual(result, mock_delegate)
        self.assertEqual(mock_delegate.reason, "休假")
        self.assertEqual(mock_delegate.is_active, False)

    def test_update_delegate_not_found(self):
        """测试更新不存在的代理配置"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.update_delegate(delegate_id=999, reason="新原因")
        
        self.assertIsNone(result)

    def test_update_delegate_only_allowed_fields(self):
        """测试只能更新允许的字段"""
        mock_delegate = Mock()
        mock_delegate.id = 1
        mock_delegate.user_id = 1
        mock_delegate.created_by = 1
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_delegate
        
        # 尝试更新不允许的字段
        result = self.service.update_delegate(
            delegate_id=1,
            user_id=999,  # 不在允许列表中
            reason="新原因",  # 允许
        )
        
        # user_id不应该被更新
        self.assertEqual(mock_delegate.user_id, 1)
        # reason应该被更新
        self.assertEqual(mock_delegate.reason, "新原因")

    # ========== cancel_delegate() 测试 ==========

    def test_cancel_delegate_success(self):
        """测试成功取消代理配置"""
        mock_delegate = Mock()
        mock_delegate.id = 1
        mock_delegate.is_active = True
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_delegate
        
        result = self.service.cancel_delegate(delegate_id=1)
        
        self.assertTrue(result)
        self.assertFalse(mock_delegate.is_active)

    def test_cancel_delegate_not_found(self):
        """测试取消不存在的代理配置"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        result = self.service.cancel_delegate(delegate_id=999)
        
        self.assertFalse(result)

    # ========== get_user_delegates() 测试 ==========

    def test_get_user_delegates_active_only(self):
        """测试获取用户的活跃代理配置"""
        mock_delegates = [Mock(), Mock()]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_delegates
        
        result = self.service.get_user_delegates(user_id=1, include_inactive=False)
        
        self.assertEqual(result, mock_delegates)
        self.assertEqual(len(result), 2)

    def test_get_user_delegates_include_inactive(self):
        """测试获取用户的所有代理配置（包含失效）"""
        mock_delegates = [Mock(), Mock(), Mock()]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_delegates
        
        result = self.service.get_user_delegates(user_id=1, include_inactive=True)
        
        self.assertEqual(len(result), 3)

    # ========== get_delegated_to_user() 测试 ==========

    def test_get_delegated_to_user(self):
        """测试获取作为代理人的配置"""
        mock_delegates = [Mock(), Mock()]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_delegates
        
        result = self.service.get_delegated_to_user(delegate_id=2)
        
        self.assertEqual(result, mock_delegates)

    # ========== record_delegate_action() 测试 ==========

    def test_record_delegate_action_success(self):
        """测试记录代理操作"""
        mock_log = Mock()
        mock_log.id = 1
        mock_log.action = None
        mock_log.action_at = None
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_log
        
        self.service.record_delegate_action(delegate_log_id=1, action="APPROVE")
        
        self.assertEqual(mock_log.action, "APPROVE")
        self.assertIsNotNone(mock_log.action_at)

    def test_record_delegate_action_log_not_found(self):
        """测试记录操作时日志不存在"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 不应该抛出异常
        self.service.record_delegate_action(delegate_log_id=999, action="APPROVE")

    # ========== notify_original_user() 测试 ==========

    def test_notify_original_user_success(self):
        """测试通知原审批人"""
        mock_log = Mock()
        mock_log.id = 1
        mock_log.delegate_config_id = 5
        mock_log.task_id = 10
        mock_log.action = "APPROVED"
        mock_log.original_notified = False
        
        mock_config = Mock()
        mock_config.id = 5
        mock_config.notify_original = True
        mock_config.user_id = 1
        
        # 创建两个不同的query对象
        mock_query_log = MagicMock()
        mock_query_config = MagicMock()
        
        # 配置query返回不同的对象
        def query_side_effect(model):
            if model == ApprovalDelegateLog:
                return mock_query_log
            elif model == ApprovalDelegate:
                return mock_query_config
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        mock_query_log.filter.return_value = mock_query_log
        mock_query_log.first.return_value = mock_log
        
        mock_query_config.filter.return_value = mock_query_config
        mock_query_config.first.return_value = mock_config
        
        with patch.object(self.service, '_send_delegate_notification') as mock_send:
            self.service.notify_original_user(delegate_log_id=1)
            
            self.assertTrue(mock_log.original_notified)
            self.assertIsNotNone(mock_log.original_notified_at)
            mock_send.assert_called_once_with(mock_log, mock_config)

    def test_notify_original_user_notify_disabled(self):
        """测试关闭通知时不发送"""
        mock_log = Mock()
        mock_log.id = 1
        mock_log.delegate_config_id = 5
        
        mock_config = Mock()
        mock_config.id = 5
        mock_config.notify_original = False
        
        mock_query_log = MagicMock()
        mock_query_config = MagicMock()
        
        def query_side_effect(model):
            if model == ApprovalDelegateLog:
                return mock_query_log
            elif model == ApprovalDelegate:
                return mock_query_config
            return MagicMock()
        
        self.db.query.side_effect = query_side_effect
        
        mock_query_log.filter.return_value = mock_query_log
        mock_query_log.first.return_value = mock_log
        
        mock_query_config.filter.return_value = mock_query_config
        mock_query_config.first.return_value = mock_config
        
        with patch.object(self.service, '_send_delegate_notification') as mock_send:
            self.service.notify_original_user(delegate_log_id=1)
            
            # 不应该调用发送通知
            mock_send.assert_not_called()

    def test_notify_original_user_log_not_found(self):
        """测试日志不存在时不通知"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        # 不应该抛出异常
        self.service.notify_original_user(delegate_log_id=999)

    # ========== cleanup_expired_delegates() 测试 ==========

    def test_cleanup_expired_delegates(self):
        """测试清理过期代理配置"""
        mock_query = MagicMock()
        mock_update_query = MagicMock()
        
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_update_query
        mock_update_query.update.return_value = 3  # 更新了3条记录
        
        self.service.cleanup_expired_delegates()
        
        mock_update_query.update.assert_called_once_with(
            {"is_active": False}, 
            synchronize_session=False
        )

    # ========== _send_delegate_notification() 测试 ==========

    def test_send_delegate_notification_success(self):
        """测试发送通知成功"""
        mock_log = Mock()
        mock_log.task_id = 10
        mock_log.action = "APPROVED"
        
        mock_config = Mock()
        mock_config.user_id = 1
        
        mock_instance = Mock()
        mock_instance.id = 100
        mock_instance.title = "测试审批"
        
        mock_task = Mock()
        mock_task.id = 10
        mock_task.instance = mock_instance
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_task
        
        with patch('app.services.approval_engine.notify.ApprovalNotifyService') as mock_notify_class:
            mock_notify_instance = MagicMock()
            mock_notify_class.return_value = mock_notify_instance
            
            self.service._send_delegate_notification(mock_log, mock_config)
            
            mock_notify_class.assert_called_once_with(self.db)
            mock_notify_instance._send_notification.assert_called_once()
            
            # 验证通知内容
            call_args = mock_notify_instance._send_notification.call_args[0][0]
            self.assertEqual(call_args['type'], 'APPROVAL_DELEGATED_RESULT')
            self.assertEqual(call_args['receiver_id'], 1)
            self.assertIn('通过', call_args['title'])

    def test_send_delegate_notification_task_not_found(self):
        """测试任务不存在时不发送通知"""
        mock_log = Mock()
        mock_log.task_id = 999
        
        mock_config = Mock()
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        with patch('app.services.approval_engine.notify.ApprovalNotifyService') as mock_notify_class:
            self.service._send_delegate_notification(mock_log, mock_config)
            
            # 任务不存在，直接return，不会创建通知服务
            mock_notify_class.assert_not_called()

    def test_send_delegate_notification_exception_handled(self):
        """测试发送通知异常被捕获"""
        mock_log = Mock()
        mock_log.task_id = 10
        
        mock_config = Mock()
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = Exception("Database error")
        
        # 不应该抛出异常
        self.service._send_delegate_notification(mock_log, mock_config)

    # ========== 边界情况测试 ==========

    def test_get_active_delegate_with_multiple_configs_priority(self):
        """测试多个配置时优先级（ALL > TEMPLATE > CATEGORY）"""
        today = date.today()
        
        delegate_template = Mock()
        delegate_template.scope = "TEMPLATE"
        delegate_template.template_ids = [100]
        
        delegate_all = Mock()
        delegate_all.scope = "ALL"
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        # 返回多个配置，ALL在后面
        mock_query.all.return_value = [delegate_template, delegate_all]
        
        result = self.service.get_active_delegate(user_id=1, template_id=100)
        
        # 应该返回第一个匹配的，即TEMPLATE
        self.assertEqual(result, delegate_template)

    def test_apply_delegation_delegate_user_not_found(self):
        """测试代理人用户不存在时的处理"""
        mock_task = Mock()
        mock_instance = Mock()
        mock_instance.template_id = 100
        mock_instance.id = 1
        mock_task.instance = mock_instance
        
        mock_delegate = Mock()
        mock_delegate.id = 5
        mock_delegate.delegate_id = 2
        
        with patch.object(self.service, 'get_active_delegate', return_value=mock_delegate):
            mock_query = MagicMock()
            self.db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.first.return_value = None  # 用户不存在
            
            result = self.service.apply_delegation(mock_task, original_assignee_id=1)
            
            # 应该仍然应用代理，只是没有设置assignee_name
            self.assertEqual(result, mock_task)
            self.assertEqual(mock_task.assignee_id, 2)

    def test_get_active_delegate_category_template_not_found(self):
        """测试CATEGORY范围但模板不存在"""
        today = date.today()
        
        delegate = Mock()
        delegate.scope = "CATEGORY"
        delegate.categories = ["EXPENSE"]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [delegate]
        mock_query.first.return_value = None  # 模板不存在
        
        result = self.service.get_active_delegate(user_id=1, template_id=999)
        
        self.assertIsNone(result)

    def test_get_active_delegate_category_mismatch(self):
        """测试CATEGORY范围但分类不匹配"""
        today = date.today()
        
        delegate = Mock()
        delegate.scope = "CATEGORY"
        delegate.categories = ["EXPENSE"]
        
        mock_template = Mock()
        mock_template.category = "LEAVE"  # 不匹配
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [delegate]
        mock_query.first.return_value = mock_template
        
        result = self.service.get_active_delegate(user_id=1, template_id=100)
        
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
