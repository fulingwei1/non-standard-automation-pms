# -*- coding: utf-8 -*-
"""
审批引擎核心类单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率

核心方法：
- _generate_instance_no(): 生成审批单号
- _get_first_node(): 获取流程的第一个节点
- _get_previous_node(): 获取上一个审批节点
- _create_node_tasks(): 为节点创建审批任务
- _advance_to_next_node(): 流转到下一节点
- _call_adapter_callback(): 调用适配器回调
- _return_to_node(): 退回到指定节点
- _get_and_validate_task(): 获取并验证任务
- _get_affected_user_ids(): 获取受影响的用户ID
- _log_action(): 记录操作日志
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from app.models.approval import (
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalActionLog,
)
from app.services.approval_engine.engine.core import ApprovalEngineCore


class TestGenerateInstanceNo(unittest.TestCase):
    """测试 _generate_instance_no() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)

    @patch('app.services.approval_engine.engine.core.apply_like_filter')
    @patch('app.services.approval_engine.engine.core.datetime')
    def test_generate_instance_no_first_today(self, mock_datetime, mock_apply_like_filter):
        """测试当天第一个单号"""
        # Mock当前时间
        mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 30, 0)
        
        # Mock查询链
        mock_scalar_query = MagicMock()
        mock_scalar_query.with_for_update.return_value.scalar.return_value = None
        
        # Mock apply_like_filter返回查询对象
        mock_apply_like_filter.return_value = mock_scalar_query
        
        result = self.engine._generate_instance_no("CONTRACT")
        
        # 验证格式：AP260221XXXX
        self.assertEqual(result, "AP2602210001")
        
        # 验证使用了FOR UPDATE锁
        mock_scalar_query.with_for_update.assert_called_once()

    @patch('app.services.approval_engine.engine.core.apply_like_filter')
    @patch('app.services.approval_engine.engine.core.datetime')
    def test_generate_instance_no_increment(self, mock_datetime, mock_apply_like_filter):
        """测试单号递增"""
        mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 30, 0)
        
        # Mock查询返回已有的最大单号
        mock_scalar_query = MagicMock()
        mock_scalar_query.with_for_update.return_value.scalar.return_value = "AP2602210005"
        mock_apply_like_filter.return_value = mock_scalar_query
        
        result = self.engine._generate_instance_no("CONTRACT")
        
        # 验证递增
        self.assertEqual(result, "AP2602210006")

    @patch('app.services.approval_engine.engine.core.apply_like_filter')
    @patch('app.services.approval_engine.engine.core.datetime')
    def test_generate_instance_no_large_sequence(self, mock_datetime, mock_apply_like_filter):
        """测试大序号"""
        mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 30, 0)
        
        mock_scalar_query = MagicMock()
        mock_scalar_query.with_for_update.return_value.scalar.return_value = "AP2602210099"
        mock_apply_like_filter.return_value = mock_scalar_query
        
        result = self.engine._generate_instance_no("CONTRACT")
        
        self.assertEqual(result, "AP2602210100")

    @patch('app.services.approval_engine.engine.core.apply_like_filter')
    @patch('app.services.approval_engine.engine.core.datetime')
    def test_generate_instance_no_invalid_format(self, mock_datetime, mock_apply_like_filter):
        """测试无效格式的单号（异常恢复）"""
        mock_datetime.now.return_value = datetime(2026, 2, 21, 10, 30, 0)
        
        # Mock返回格式错误的单号
        mock_scalar_query = MagicMock()
        mock_scalar_query.with_for_update.return_value.scalar.return_value = "INVALID"
        mock_apply_like_filter.return_value = mock_scalar_query
        
        result = self.engine._generate_instance_no("CONTRACT")
        
        # 应该重置为0001
        self.assertEqual(result, "AP2602210001")

    @patch('app.services.approval_engine.engine.core.apply_like_filter')
    @patch('app.services.approval_engine.engine.core.datetime')
    def test_generate_instance_no_different_dates(self, mock_datetime, mock_apply_like_filter):
        """测试不同日期的单号"""
        # 测试不同日期生成不同前缀
        mock_datetime.now.return_value = datetime(2026, 3, 15, 10, 30, 0)
        
        mock_scalar_query = MagicMock()
        mock_scalar_query.with_for_update.return_value.scalar.return_value = None
        mock_apply_like_filter.return_value = mock_scalar_query
        
        result = self.engine._generate_instance_no("CONTRACT")
        
        self.assertEqual(result, "AP2603150001")


class TestGetFirstNode(unittest.TestCase):
    """测试 _get_first_node() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)

    def test_get_first_node_found(self):
        """测试获取到第一个节点"""
        mock_node = MagicMock(spec=ApprovalNodeDefinition)
        mock_node.id = 1
        mock_node.node_order = 1
        mock_node.node_type = "APPROVAL"
        
        # Mock查询链
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = mock_node
        self.mock_db.query.return_value = mock_query
        
        result = self.engine._get_first_node(flow_id=10)
        
        self.assertEqual(result, mock_node)
        self.mock_db.query.assert_called_once_with(ApprovalNodeDefinition)

    def test_get_first_node_not_found(self):
        """测试没有找到节点"""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = self.engine._get_first_node(flow_id=10)
        
        self.assertIsNone(result)


class TestGetPreviousNode(unittest.TestCase):
    """测试 _get_previous_node() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)

    def test_get_previous_node_found(self):
        """测试获取到上一节点"""
        current_node = MagicMock(spec=ApprovalNodeDefinition)
        current_node.flow_id = 10
        current_node.node_order = 3
        
        prev_node = MagicMock(spec=ApprovalNodeDefinition)
        prev_node.id = 2
        prev_node.node_order = 2
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = prev_node
        self.mock_db.query.return_value = mock_query
        
        result = self.engine._get_previous_node(current_node)
        
        self.assertEqual(result, prev_node)

    def test_get_previous_node_first_node(self):
        """测试第一个节点没有上一节点"""
        current_node = MagicMock(spec=ApprovalNodeDefinition)
        current_node.flow_id = 10
        current_node.node_order = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = self.engine._get_previous_node(current_node)
        
        self.assertIsNone(result)


class TestCreateNodeTasks(unittest.TestCase):
    """测试 _create_node_tasks() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)
        
        # 重新mock依赖（因为__init__会创建真实对象）
        self.engine.router = MagicMock()
        self.engine.executor = MagicMock()
        self.engine.notify = MagicMock()
        self.engine.delegate_service = MagicMock()

    def test_create_node_tasks_with_approvers(self):
        """测试创建任务（有审批人）"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        instance.template_id = 100
        
        node = MagicMock(spec=ApprovalNodeDefinition)
        node.id = 10
        node.notify_config = {}
        
        context = {
            "form_data": {},
            "initiator": {"id": 1, "dept_id": 5},
        }
        
        # Mock router解析出审批人
        self.engine.router.resolve_approvers = MagicMock(return_value=[201, 202])
        
        # Mock delegate_service返回无代理
        self.engine.delegate_service.get_active_delegate = MagicMock(return_value=None)
        
        # Mock executor创建任务
        task1 = MagicMock(status="PENDING")
        task2 = MagicMock(status="PENDING")
        self.engine.executor.create_tasks_for_node = MagicMock(return_value=[task1, task2])
        
        self.engine._create_node_tasks(instance, node, context)
        
        # 验证调用router解析审批人
        self.engine.router.resolve_approvers.assert_called_once_with(node, context)
        
        # 验证调用executor创建任务
        self.engine.executor.create_tasks_for_node.assert_called_once()
        call_kwargs = self.engine.executor.create_tasks_for_node.call_args[1]
        self.assertEqual(call_kwargs['instance'], instance)
        self.assertEqual(call_kwargs['node'], node)
        self.assertEqual(call_kwargs['approver_ids'], [201, 202])
        
        # 验证通知了2个审批人
        self.assertEqual(self.engine.notify.notify_pending.call_count, 2)

    def test_create_node_tasks_no_approvers(self):
        """测试无审批人时跳过节点"""
        instance = MagicMock(spec=ApprovalInstance)
        node = MagicMock(spec=ApprovalNodeDefinition)
        context = {}
        
        # Mock返回空审批人列表
        self.engine.router.resolve_approvers = MagicMock(return_value=[])
        
        # Mock _advance_to_next_node
        self.engine._advance_to_next_node = MagicMock()
        
        self.engine._create_node_tasks(instance, node, context)
        
        # 应该调用流转到下一节点
        self.engine._advance_to_next_node.assert_called_once_with(instance, None)
        
        # 不应创建任务
        self.engine.executor.create_tasks_for_node.assert_not_called()

    def test_create_node_tasks_with_delegate(self):
        """测试有代理人时替换审批人"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.template_id = 100
        
        node = MagicMock(spec=ApprovalNodeDefinition)
        node.notify_config = {}
        
        context = {}
        
        # Mock原审批人
        self.engine.router.resolve_approvers = MagicMock(return_value=[201, 202])
        
        # Mock第一个人有代理，第二个没有
        delegate_config = MagicMock()
        delegate_config.delegate_id = 301
        
        def mock_get_delegate(user_id, template_id):
            if user_id == 201:
                return delegate_config
            return None
        
        self.engine.delegate_service.get_active_delegate = MagicMock(side_effect=mock_get_delegate)
        
        task1 = MagicMock(status="PENDING")
        task2 = MagicMock(status="PENDING")
        self.engine.executor.create_tasks_for_node = MagicMock(return_value=[task1, task2])
        
        self.engine._create_node_tasks(instance, node, context)
        
        # 验证传递的审批人：第一个被替换为代理人301
        call_kwargs = self.engine.executor.create_tasks_for_node.call_args[1]
        self.assertEqual(call_kwargs['approver_ids'], [301, 202])

    def test_create_node_tasks_with_cc(self):
        """测试创建任务时处理抄送"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.template_id = 100
        
        node = MagicMock(spec=ApprovalNodeDefinition)
        node.id = 10
        node.notify_config = {
            "cc_user_ids": [401, 402, 403],
        }
        
        context = {}
        
        self.engine.router.resolve_approvers = MagicMock(return_value=[201])
        self.engine.delegate_service.get_active_delegate = MagicMock(return_value=None)
        
        task = MagicMock(status="PENDING")
        self.engine.executor.create_tasks_for_node = MagicMock(return_value=[task])
        
        self.engine._create_node_tasks(instance, node, context)
        
        # 验证创建了抄送记录
        self.engine.executor.create_cc_records.assert_called_once()
        call_kwargs = self.engine.executor.create_cc_records.call_args[1]
        self.assertEqual(call_kwargs['instance'], instance)
        self.assertEqual(call_kwargs['node_id'], 10)
        self.assertEqual(call_kwargs['cc_user_ids'], [401, 402, 403])
        self.assertEqual(call_kwargs['cc_source'], "FLOW")

    def test_create_node_tasks_skip_completed_tasks(self):
        """测试跳过已完成的任务通知"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.template_id = 100
        
        node = MagicMock(spec=ApprovalNodeDefinition)
        node.notify_config = {}
        
        context = {}
        
        self.engine.router.resolve_approvers = MagicMock(return_value=[201, 202])
        self.engine.delegate_service.get_active_delegate = MagicMock(return_value=None)
        
        # 一个PENDING，一个COMPLETED
        task1 = MagicMock(status="PENDING")
        task2 = MagicMock(status="COMPLETED")
        self.engine.executor.create_tasks_for_node = MagicMock(return_value=[task1, task2])
        
        self.engine._create_node_tasks(instance, node, context)
        
        # 只应通知一次（PENDING的任务）
        self.assertEqual(self.engine.notify.notify_pending.call_count, 1)
        self.engine.notify.notify_pending.assert_called_with(task1)


class TestAdvanceToNextNode(unittest.TestCase):
    """测试 _advance_to_next_node() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)
        
        # 重新mock依赖
        self.engine.router = MagicMock()
        self.engine.executor = MagicMock()
        self.engine.notify = MagicMock()
        self.engine.delegate_service = MagicMock()

    def test_advance_with_task(self):
        """测试通过任务流转"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        instance.form_data = {"amount": 10000}
        instance.initiator_id = 100
        instance.initiator_dept_id = 5
        
        current_node = MagicMock(spec=ApprovalNodeDefinition)
        current_node.id = 10
        
        task = MagicMock(spec=ApprovalTask)
        task.node = current_node
        
        next_node = MagicMock(spec=ApprovalNodeDefinition)
        next_node.id = 11
        
        # Mock router返回下一节点
        self.engine.router.get_next_nodes = MagicMock(return_value=[next_node])
        
        # Mock创建任务
        self.engine._create_node_tasks = MagicMock()
        
        self.engine._advance_to_next_node(instance, task)
        
        # 验证更新了当前节点
        self.assertEqual(instance.current_node_id, 11)
        
        # 验证调用创建任务
        self.engine._create_node_tasks.assert_called_once()
        call_args = self.engine._create_node_tasks.call_args[0]
        self.assertEqual(call_args[0], instance)
        self.assertEqual(call_args[1], next_node)
        
        # 验证传递的context
        context = call_args[2]
        self.assertEqual(context['form_data'], {"amount": 10000})
        self.assertEqual(context['initiator']['id'], 100)
        self.assertEqual(context['initiator']['dept_id'], 5)

    def test_advance_without_task(self):
        """测试无任务时从实例获取当前节点"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        instance.current_node_id = 10
        instance.form_data = {}
        instance.initiator_id = 100
        instance.initiator_dept_id = 5
        
        current_node = MagicMock(spec=ApprovalNodeDefinition)
        current_node.id = 10
        
        # Mock查询当前节点
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = current_node
        self.mock_db.query.return_value = mock_query
        
        next_node = MagicMock(spec=ApprovalNodeDefinition)
        next_node.id = 11
        
        self.engine.router.get_next_nodes = MagicMock(return_value=[next_node])
        self.engine._create_node_tasks = MagicMock()
        
        self.engine._advance_to_next_node(instance, None)
        
        # 验证查询了当前节点
        self.mock_db.query.assert_called_with(ApprovalNodeDefinition)
        
        # 验证流转
        self.assertEqual(instance.current_node_id, 11)

    def test_advance_no_next_node_approved(self):
        """测试无下一节点时审批完成"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        instance.status = "IN_PROGRESS"
        instance.completed_at = None
        instance.entity_type = "CONTRACT"
        instance.entity_id = 123
        instance.form_data = {}
        instance.initiator_id = 100
        instance.initiator_dept_id = 5
        
        current_node = MagicMock(spec=ApprovalNodeDefinition)
        
        task = MagicMock()
        task.node = current_node
        
        # Mock无下一节点
        self.engine.router.get_next_nodes = MagicMock(return_value=[])
        
        # Mock适配器回调
        self.engine._call_adapter_callback = MagicMock()
        
        self.engine._advance_to_next_node(instance, task)
        
        # 验证状态变为APPROVED
        self.assertEqual(instance.status, "APPROVED")
        self.assertIsNotNone(instance.completed_at)
        
        # 验证调用了适配器回调
        self.engine._call_adapter_callback.assert_called_once_with(instance, "on_approved")
        
        # 验证通知
        self.engine.notify.notify_approved.assert_called_once_with(instance)

    def test_advance_no_current_node(self):
        """测试当前节点不存在时直接返回"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.current_node_id = 10
        
        # Mock查询返回None
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        self.engine.router.get_next_nodes = MagicMock()
        
        self.engine._advance_to_next_node(instance, None)
        
        # 不应调用router
        self.engine.router.get_next_nodes.assert_not_called()


class TestCallAdapterCallback(unittest.TestCase):
    """测试 _call_adapter_callback() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)

    @patch('app.services.approval_engine.adapters.get_adapter')
    def test_call_adapter_callback_success(self, mock_get_adapter):
        """测试成功调用适配器回调"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.entity_type = "CONTRACT"
        instance.entity_id = 123
        
        # Mock适配器
        mock_adapter = MagicMock()
        mock_callback = MagicMock()
        mock_adapter.on_approved = mock_callback
        mock_get_adapter.return_value = mock_adapter
        
        self.engine._call_adapter_callback(instance, "on_approved")
        
        # 验证调用了适配器
        mock_get_adapter.assert_called_once_with("CONTRACT", self.mock_db)
        mock_callback.assert_called_once_with(123, instance)

    @patch('app.services.approval_engine.adapters.get_adapter')
    def test_call_adapter_callback_no_method(self, mock_get_adapter):
        """测试适配器没有对应方法"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.entity_type = "CONTRACT"
        instance.entity_id = 123
        
        # Mock适配器没有on_rejected方法
        mock_adapter = MagicMock(spec=[])
        mock_get_adapter.return_value = mock_adapter
        
        # 不应抛出异常
        self.engine._call_adapter_callback(instance, "on_rejected")
        
        # 应该调用了get_adapter
        mock_get_adapter.assert_called_once()

    @patch('app.services.approval_engine.adapters.get_adapter')
    def test_call_adapter_callback_no_adapter(self, mock_get_adapter):
        """测试未配置适配器"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.entity_type = "UNKNOWN_TYPE"
        instance.entity_id = 123
        
        # Mock抛出ValueError
        mock_get_adapter.side_effect = ValueError("未配置适配器")
        
        # 不应抛出异常（应该被捕获）
        self.engine._call_adapter_callback(instance, "on_approved")
        
        mock_get_adapter.assert_called_once_with("UNKNOWN_TYPE", self.mock_db)


class TestReturnToNode(unittest.TestCase):
    """测试 _return_to_node() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)
        
        # 重新mock依赖
        self.engine.router = MagicMock()
        self.engine.executor = MagicMock()
        self.engine.notify = MagicMock()
        self.engine.delegate_service = MagicMock()

    def test_return_to_node_success(self):
        """测试成功退回到节点"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        instance.form_data = {"amount": 5000}
        instance.initiator_id = 100
        instance.initiator_dept_id = 5
        
        target_node = MagicMock(spec=ApprovalNodeDefinition)
        target_node.id = 8
        
        # Mock查询待处理任务
        mock_update = MagicMock()
        self.mock_db.query.return_value.filter.return_value.update = mock_update
        
        # Mock创建任务
        self.engine._create_node_tasks = MagicMock()
        
        self.engine._return_to_node(instance, target_node)
        
        # 验证取消了待处理任务
        mock_update.assert_called_once_with(
            {"status": "CANCELLED"},
            synchronize_session=False
        )
        
        # 验证更新了当前节点
        self.assertEqual(instance.current_node_id, 8)
        
        # 验证创建了新任务
        self.engine._create_node_tasks.assert_called_once()
        call_args = self.engine._create_node_tasks.call_args[0]
        self.assertEqual(call_args[0], instance)
        self.assertEqual(call_args[1], target_node)
        
        # 验证context
        context = call_args[2]
        self.assertEqual(context['form_data'], {"amount": 5000})
        self.assertEqual(context['initiator']['id'], 100)


class TestGetAndValidateTask(unittest.TestCase):
    """测试 _get_and_validate_task() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)

    def test_get_and_validate_task_success(self):
        """测试成功获取并验证任务"""
        task = MagicMock(spec=ApprovalTask)
        task.id = 1
        task.assignee_id = 100
        task.status = "PENDING"
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = task
        self.mock_db.query.return_value = mock_query
        
        result = self.engine._get_and_validate_task(task_id=1, user_id=100)
        
        self.assertEqual(result, task)

    def test_get_and_validate_task_not_found(self):
        """测试任务不存在"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as cm:
            self.engine._get_and_validate_task(task_id=1, user_id=100)
        
        self.assertIn("任务不存在: 1", str(cm.exception))

    def test_get_and_validate_task_wrong_user(self):
        """测试无权操作任务"""
        task = MagicMock(spec=ApprovalTask)
        task.id = 1
        task.assignee_id = 200  # 不是当前用户
        task.status = "PENDING"
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = task
        self.mock_db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as cm:
            self.engine._get_and_validate_task(task_id=1, user_id=100)
        
        self.assertIn("无权操作此任务", str(cm.exception))

    def test_get_and_validate_task_wrong_status(self):
        """测试任务状态不正确"""
        task = MagicMock(spec=ApprovalTask)
        task.id = 1
        task.assignee_id = 100
        task.status = "COMPLETED"
        
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = task
        self.mock_db.query.return_value = mock_query
        
        with self.assertRaises(ValueError) as cm:
            self.engine._get_and_validate_task(task_id=1, user_id=100)
        
        self.assertIn("任务状态不正确: COMPLETED", str(cm.exception))


class TestGetAffectedUserIds(unittest.TestCase):
    """测试 _get_affected_user_ids() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)

    def test_get_affected_user_ids(self):
        """测试获取受影响的用户ID"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        
        # Mock任务
        task1 = MagicMock(spec=ApprovalTask)
        task1.assignee_id = 201
        
        task2 = MagicMock(spec=ApprovalTask)
        task2.assignee_id = 202
        
        task3 = MagicMock(spec=ApprovalTask)
        task3.assignee_id = 203
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [task1, task2, task3]
        self.mock_db.query.return_value = mock_query
        
        result = self.engine._get_affected_user_ids(instance)
        
        self.assertEqual(result, [201, 202, 203])

    def test_get_affected_user_ids_empty(self):
        """测试无待处理任务"""
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        result = self.engine._get_affected_user_ids(instance)
        
        self.assertEqual(result, [])


class TestLogAction(unittest.TestCase):
    """测试 _log_action() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineCore(self.mock_db)

    @patch('app.services.approval_engine.engine.core.datetime')
    def test_log_action_minimal(self, mock_datetime):
        """测试记录最小日志"""
        now = datetime(2026, 2, 21, 10, 30, 0)
        mock_datetime.now.return_value = now
        
        added_logs = []
        self.mock_db.add.side_effect = lambda obj: added_logs.append(obj)
        
        self.engine._log_action(
            instance_id=1,
            operator_id=100,
            action="APPROVE",
        )
        
        # 验证创建了日志
        self.assertEqual(len(added_logs), 1)
        log = added_logs[0]
        
        self.assertEqual(log.instance_id, 1)
        self.assertEqual(log.operator_id, 100)
        self.assertEqual(log.action, "APPROVE")
        self.assertEqual(log.action_at, now)
        self.assertIsNone(log.task_id)
        self.assertIsNone(log.node_id)
        self.assertIsNone(log.comment)

    @patch('app.services.approval_engine.engine.core.datetime')
    def test_log_action_full(self, mock_datetime):
        """测试记录完整日志"""
        now = datetime(2026, 2, 21, 10, 30, 0)
        mock_datetime.now.return_value = now
        
        added_logs = []
        self.mock_db.add.side_effect = lambda obj: added_logs.append(obj)
        
        attachments = [{"name": "file.pdf", "url": "http://example.com/file.pdf"}]
        action_detail = {"reject_to": "START"}
        
        self.engine._log_action(
            instance_id=1,
            operator_id=100,
            action="REJECT",
            task_id=10,
            node_id=5,
            operator_name="张三",
            comment="不符合要求",
            attachments=attachments,
            action_detail=action_detail,
            before_status="IN_PROGRESS",
            after_status="REJECTED",
        )
        
        log = added_logs[0]
        
        self.assertEqual(log.instance_id, 1)
        self.assertEqual(log.task_id, 10)
        self.assertEqual(log.node_id, 5)
        self.assertEqual(log.operator_id, 100)
        self.assertEqual(log.operator_name, "张三")
        self.assertEqual(log.action, "REJECT")
        self.assertEqual(log.comment, "不符合要求")
        self.assertEqual(log.attachments, attachments)
        self.assertEqual(log.action_detail, action_detail)
        self.assertEqual(log.before_status, "IN_PROGRESS")
        self.assertEqual(log.after_status, "REJECTED")
        self.assertEqual(log.action_at, now)


if __name__ == "__main__":
    unittest.main()
