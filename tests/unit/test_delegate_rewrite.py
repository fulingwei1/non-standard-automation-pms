# -*- coding: utf-8 -*-
"""
审批代理人服务单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库、模型）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime

from app.services.approval_engine.delegate import ApprovalDelegateService


class TestApprovalDelegateServiceCore(unittest.TestCase):
    """测试核心服务方法"""

    def setUp(self):
        """准备mock的数据库session"""
        self.db = MagicMock()
        self.service = ApprovalDelegateService(db=self.db)

    # ========== get_active_delegate() 测试 ==========
    
    def test_get_active_delegate_all_scope(self):
        """测试获取ALL范围的代理配置"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "ALL"
        mock_delegate.user_id = 1
        mock_delegate.delegate_id = 2
        
        # Mock查询链
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        result = self.service.get_active_delegate(user_id=1)
        
        self.assertEqual(result, mock_delegate)
        self.db.query.assert_called_once()

    def test_get_active_delegate_template_scope_match(self):
        """测试TEMPLATE范围匹配"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "TEMPLATE"
        mock_delegate.template_ids = [1, 2, 3]
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        result = self.service.get_active_delegate(user_id=1, template_id=2)
        
        self.assertEqual(result, mock_delegate)

    def test_get_active_delegate_template_scope_no_match(self):
        """测试TEMPLATE范围不匹配"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "TEMPLATE"
        mock_delegate.template_ids = [1, 2, 3]
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        result = self.service.get_active_delegate(user_id=1, template_id=99)
        
        self.assertIsNone(result)

    def test_get_active_delegate_template_scope_no_template_id(self):
        """测试TEMPLATE范围但未提供template_id"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "TEMPLATE"
        mock_delegate.template_ids = [1, 2]
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        result = self.service.get_active_delegate(user_id=1, template_id=None)
        
        self.assertIsNone(result)

    def test_get_active_delegate_category_scope_match(self):
        """测试CATEGORY范围匹配"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "CATEGORY"
        mock_delegate.categories = ["财务", "人事"]
        
        mock_template = MagicMock()
        mock_template.category = "财务"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        # Mock模板查询
        with patch.object(self.db, 'query') as mock_query:
            # 第一次调用：查询delegate
            # 第二次调用：查询template
            mock_query.return_value.filter.return_value.all.return_value = [mock_delegate]
            mock_query.return_value.filter.return_value.first.return_value = mock_template
            
            result = self.service.get_active_delegate(user_id=1, template_id=10)
            
            self.assertEqual(result, mock_delegate)

    def test_get_active_delegate_category_scope_no_match(self):
        """测试CATEGORY范围不匹配"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "CATEGORY"
        mock_delegate.categories = ["财务", "人事"]
        
        mock_template = MagicMock()
        mock_template.category = "采购"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        with patch.object(self.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = [mock_delegate]
            mock_query.return_value.filter.return_value.first.return_value = mock_template
            
            result = self.service.get_active_delegate(user_id=1, template_id=10)
            
            self.assertIsNone(result)

    def test_get_active_delegate_no_delegates(self):
        """测试没有代理配置"""
        self.db.query.return_value.filter.return_value.all.return_value = []
        
        result = self.service.get_active_delegate(user_id=1)
        
        self.assertIsNone(result)

    def test_get_active_delegate_custom_check_date(self):
        """测试自定义检查日期"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "ALL"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        check_date = date(2025, 6, 15)
        result = self.service.get_active_delegate(user_id=1, check_date=check_date)
        
        self.assertEqual(result, mock_delegate)

    # ========== apply_delegation() 测试 ==========
    
    def test_apply_delegation_success(self):
        """测试成功应用代理"""
        mock_task = MagicMock()
        mock_instance = MagicMock()
        mock_instance.template_id = 1
        mock_task.instance = mock_instance
        
        mock_delegate = MagicMock()
        mock_delegate.id = 100
        mock_delegate.delegate_id = 2
        
        mock_user = MagicMock()
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        
        # Mock get_active_delegate
        with patch.object(self.service, 'get_active_delegate', return_value=mock_delegate):
            with patch.object(self.db, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = mock_user
                
                result = self.service.apply_delegation(task=mock_task, original_assignee_id=1)
                
                self.assertEqual(result, mock_task)
                self.assertEqual(mock_task.original_assignee_id, 1)
                self.assertEqual(mock_task.assignee_type, "DELEGATED")
                self.assertEqual(mock_task.assignee_id, 2)
                self.assertEqual(mock_task.assignee_name, "张三")
                self.db.add.assert_called_once()

    def test_apply_delegation_no_delegate(self):
        """测试无代理配置"""
        mock_task = MagicMock()
        mock_instance = MagicMock()
        mock_task.instance = mock_instance
        
        with patch.object(self.service, 'get_active_delegate', return_value=None):
            result = self.service.apply_delegation(task=mock_task, original_assignee_id=1)
            
            self.assertIsNone(result)

    def test_apply_delegation_user_no_real_name(self):
        """测试代理人无真实姓名（使用username）"""
        mock_task = MagicMock()
        mock_instance = MagicMock()
        mock_instance.template_id = 1
        mock_task.instance = mock_instance
        
        mock_delegate = MagicMock()
        mock_delegate.id = 100
        mock_delegate.delegate_id = 2
        
        mock_user = MagicMock()
        mock_user.real_name = None
        mock_user.username = "lisi"
        
        with patch.object(self.service, 'get_active_delegate', return_value=mock_delegate):
            with patch.object(self.db, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = mock_user
                
                result = self.service.apply_delegation(task=mock_task, original_assignee_id=1)
                
                self.assertEqual(mock_task.assignee_name, "lisi")

    # ========== create_delegate() 测试 ==========
    
    def test_create_delegate_success(self):
        """测试成功创建代理配置"""
        # Mock查询无重叠配置
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            scope="ALL",
            reason="出差"
        )
        
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()
        
        # 检查创建的对象属性
        call_args = self.db.add.call_args[0][0]
        self.assertEqual(call_args.user_id, 1)
        self.assertEqual(call_args.delegate_id, 2)
        self.assertEqual(call_args.scope, "ALL")
        self.assertTrue(call_args.is_active)

    def test_create_delegate_with_template_scope(self):
        """测试创建TEMPLATE范围的代理"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            scope="TEMPLATE",
            template_ids=[1, 2, 3],
            created_by=10
        )
        
        call_args = self.db.add.call_args[0][0]
        self.assertEqual(call_args.scope, "TEMPLATE")
        self.assertEqual(call_args.template_ids, [1, 2, 3])
        self.assertEqual(call_args.created_by, 10)

    def test_create_delegate_overlapping_config(self):
        """测试创建重叠的代理配置（应抛出异常）"""
        # Mock存在重叠配置
        mock_existing = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_existing
        
        with self.assertRaises(ValueError) as context:
            self.service.create_delegate(
                user_id=1,
                delegate_id=2,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31)
            )
        
        self.assertIn("重叠", str(context.exception))

    def test_create_delegate_with_categories(self):
        """测试创建CATEGORY范围的代理"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            scope="CATEGORY",
            categories=["财务", "人事"]
        )
        
        call_args = self.db.add.call_args[0][0]
        self.assertEqual(call_args.categories, ["财务", "人事"])

    # ========== update_delegate() 测试 ==========
    
    def test_update_delegate_success(self):
        """测试成功更新代理配置"""
        mock_delegate = MagicMock()
        mock_delegate.id = 1
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_delegate
        
        result = self.service.update_delegate(
            delegate_id=1,
            reason="延长出差时间",
            end_date=date(2026, 12, 31)
        )
        
        self.assertEqual(result, mock_delegate)
        self.assertEqual(mock_delegate.reason, "延长出差时间")
        self.assertEqual(mock_delegate.end_date, date(2026, 12, 31))

    def test_update_delegate_not_found(self):
        """测试更新不存在的代理配置"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.update_delegate(delegate_id=999, reason="test")
        
        self.assertIsNone(result)

    def test_update_delegate_allowed_fields(self):
        """测试只允许更新特定字段"""
        mock_delegate = MagicMock()
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_delegate
        
        # 尝试更新允许的字段
        result = self.service.update_delegate(
            delegate_id=1,
            scope="TEMPLATE",  # 允许
            is_active=False  # 允许
        )
        
        self.assertEqual(mock_delegate.scope, "TEMPLATE")
        self.assertEqual(mock_delegate.is_active, False)

    def test_update_delegate_ignore_invalid_fields(self):
        """测试忽略不允许的字段"""
        mock_delegate = MagicMock()
        mock_delegate.id = 1
        mock_delegate.user_id = 1
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_delegate
        
        # 尝试更新不允许的字段
        result = self.service.update_delegate(
            delegate_id=1,
            user_id=999,  # 不允许
            id=888  # 不允许
        )
        
        # 这些字段不应该被更新
        self.assertEqual(mock_delegate.user_id, 1)
        self.assertEqual(mock_delegate.id, 1)

    # ========== cancel_delegate() 测试 ==========
    
    def test_cancel_delegate_success(self):
        """测试成功取消代理配置"""
        mock_delegate = MagicMock()
        mock_delegate.is_active = True
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_delegate
        
        result = self.service.cancel_delegate(delegate_id=1)
        
        self.assertTrue(result)
        self.assertFalse(mock_delegate.is_active)

    def test_cancel_delegate_not_found(self):
        """测试取消不存在的代理配置"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        result = self.service.cancel_delegate(delegate_id=999)
        
        self.assertFalse(result)

    # ========== get_user_delegates() 测试 ==========
    
    def test_get_user_delegates_active_only(self):
        """测试获取用户的活跃代理配置"""
        mock_delegates = [MagicMock(), MagicMock()]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_delegates
        
        result = self.service.get_user_delegates(user_id=1, include_inactive=False)
        
        self.assertEqual(result, mock_delegates)
        # 验证过滤了is_active
        self.assertEqual(mock_query.filter.call_count, 2)  # user_id + is_active

    def test_get_user_delegates_include_inactive(self):
        """测试获取用户所有代理配置（包括已失效）"""
        mock_delegates = [MagicMock(), MagicMock(), MagicMock()]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_delegates
        
        result = self.service.get_user_delegates(user_id=1, include_inactive=True)
        
        self.assertEqual(result, mock_delegates)
        # 只过滤user_id，不过滤is_active
        self.assertEqual(mock_query.filter.call_count, 1)

    # ========== get_delegated_to_user() 测试 ==========
    
    def test_get_delegated_to_user_active_only(self):
        """测试获取作为代理人的活跃配置"""
        mock_delegates = [MagicMock()]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_delegates
        
        result = self.service.get_delegated_to_user(delegate_id=2, include_inactive=False)
        
        self.assertEqual(result, mock_delegates)
        self.assertEqual(mock_query.filter.call_count, 2)

    def test_get_delegated_to_user_include_inactive(self):
        """测试获取作为代理人的所有配置"""
        mock_delegates = [MagicMock(), MagicMock()]
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_delegates
        
        result = self.service.get_delegated_to_user(delegate_id=2, include_inactive=True)
        
        self.assertEqual(result, mock_delegates)
        self.assertEqual(mock_query.filter.call_count, 1)

    # ========== record_delegate_action() 测试 ==========
    
    def test_record_delegate_action_success(self):
        """测试记录代理人操作"""
        mock_log = MagicMock()
        mock_log.action = None
        mock_log.action_at = None
        
        self.db.query.return_value.filter.return_value.first.return_value = mock_log
        
        self.service.record_delegate_action(delegate_log_id=1, action="APPROVED")
        
        self.assertEqual(mock_log.action, "APPROVED")
        self.assertIsNotNone(mock_log.action_at)
        self.assertIsInstance(mock_log.action_at, datetime)

    def test_record_delegate_action_log_not_found(self):
        """测试记录操作时日志不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # 不应抛出异常
        self.service.record_delegate_action(delegate_log_id=999, action="APPROVED")

    # ========== notify_original_user() 测试 ==========
    
    def test_notify_original_user_success(self):
        """测试通知原审批人"""
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.delegate_config_id = 100
        mock_log.task_id = 200
        mock_log.action = "APPROVED"
        mock_log.original_notified = False
        
        mock_config = MagicMock()
        mock_config.notify_original = True
        mock_config.user_id = 1
        
        with patch.object(self.db, 'query') as mock_query:
            # 第一次：查log，第二次：查config
            mock_query.return_value.filter.return_value.first.side_effect = [
                mock_log,
                mock_config
            ]
            
            # 这里只测试标记字段被设置，不测试具体通知发送
            self.service.notify_original_user(delegate_log_id=1)
            
            self.assertTrue(mock_log.original_notified)
            self.assertIsNotNone(mock_log.original_notified_at)

    def test_notify_original_user_log_not_found(self):
        """测试通知时日志不存在"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # 不应抛出异常
        self.service.notify_original_user(delegate_log_id=999)

    def test_notify_original_user_config_notify_disabled(self):
        """测试配置禁用了通知"""
        mock_log = MagicMock()
        mock_log.original_notified = False
        mock_config = MagicMock()
        mock_config.notify_original = False
        
        with patch.object(self.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.side_effect = [
                mock_log,
                mock_config
            ]
            
            self.service.notify_original_user(delegate_log_id=1)
            
            # 标记字段应该被设置
            self.assertTrue(mock_log.original_notified)

    # ========== cleanup_expired_delegates() 测试 ==========
    
    def test_cleanup_expired_delegates(self):
        """测试清理过期代理配置"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value.update.return_value = 3
        
        self.service.cleanup_expired_delegates()
        
        mock_query.filter.return_value.update.assert_called_once_with(
            {"is_active": False},
            synchronize_session=False
        )

    # ========== _send_delegate_notification() 测试（简化版） ==========
    
    def test_send_delegate_notification_exception_handling(self):
        """测试通知异常处理（不会向外抛出异常）"""
        mock_log = MagicMock()
        mock_config = MagicMock()
        
        # Mock抛出异常
        self.db.query.side_effect = Exception("数据库错误")
        
        # 不应抛出异常到外部，应该被内部捕获
        try:
            self.service._send_delegate_notification(mock_log, mock_config)
        except Exception:
            self.fail("_send_delegate_notification should not raise exceptions")


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        self.db = MagicMock()
        self.service = ApprovalDelegateService(db=self.db)

    def test_get_active_delegate_category_no_template(self):
        """测试CATEGORY范围但模板不存在"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "CATEGORY"
        mock_delegate.categories = ["财务"]
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        with patch.object(self.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = [mock_delegate]
            mock_query.return_value.filter.return_value.first.return_value = None  # 模板不存在
            
            result = self.service.get_active_delegate(user_id=1, template_id=99)
            
            self.assertIsNone(result)

    def test_get_active_delegate_category_no_categories(self):
        """测试CATEGORY范围但categories为None"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "CATEGORY"
        mock_delegate.categories = None
        
        mock_template = MagicMock()
        mock_template.category = "财务"
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        with patch.object(self.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.all.return_value = [mock_delegate]
            mock_query.return_value.filter.return_value.first.return_value = mock_template
            
            result = self.service.get_active_delegate(user_id=1, template_id=10)
            
            self.assertIsNone(result)

    def test_get_active_delegate_template_no_template_ids(self):
        """测试TEMPLATE范围但template_ids为None"""
        mock_delegate = MagicMock()
        mock_delegate.scope = "TEMPLATE"
        mock_delegate.template_ids = None
        
        self.db.query.return_value.filter.return_value.all.return_value = [mock_delegate]
        
        result = self.service.get_active_delegate(user_id=1, template_id=5)
        
        self.assertIsNone(result)

    def test_apply_delegation_no_user_found(self):
        """测试应用代理时找不到用户"""
        mock_task = MagicMock()
        mock_instance = MagicMock()
        mock_instance.template_id = 1
        mock_task.instance = mock_instance
        
        mock_delegate = MagicMock()
        mock_delegate.id = 100
        mock_delegate.delegate_id = 2
        
        with patch.object(self.service, 'get_active_delegate', return_value=mock_delegate):
            with patch.object(self.db, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = None  # 用户不存在
                
                result = self.service.apply_delegation(task=mock_task, original_assignee_id=1)
                
                # 仍然返回task，但assignee_name未设置
                self.assertEqual(result, mock_task)

    def test_create_delegate_default_created_by(self):
        """测试创建代理配置时默认created_by为user_id"""
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        self.service.create_delegate(
            user_id=5,
            delegate_id=2,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            # 不传created_by
        )
        
        call_args = self.db.add.call_args[0][0]
        self.assertEqual(call_args.created_by, 5)  # 应该默认为user_id


if __name__ == "__main__":
    unittest.main()
