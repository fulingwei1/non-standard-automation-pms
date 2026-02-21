# -*- coding: utf-8 -*-
"""
审批处理功能单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖(db.query, db.add, db.commit等)
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, call
from datetime import datetime
from typing import List, Dict

# 显式导入以便覆盖率统计
import app.services.approval_engine.engine.approve as approve_module
from app.services.approval_engine.engine.approve import ApprovalProcessMixin
from app.services.approval_engine.engine.core import ApprovalEngineCore


class TestApprovalProcessMixin(unittest.TestCase):
    """测试审批处理功能混入类"""

    def setUp(self):
        """每个测试前的准备工作"""
        # Mock数据库会话
        self.mock_db = MagicMock()
        
        # 创建引擎实例 - 通过多重继承让ApprovalEngineCore拥有approve功能
        class TestEngine(ApprovalProcessMixin, ApprovalEngineCore):
            pass
        
        self.engine = TestEngine(self.mock_db)
        
        # Mock服务依赖
        self.engine.executor = MagicMock()
        self.engine.notify = MagicMock()
        self.engine.router = MagicMock()
        self.engine.delegate_service = MagicMock()

    def _create_mock_task(
        self, 
        task_id: int = 1,
        assignee_id: int = 100,
        status: str = "PENDING",
        node_id: int = 1,
        instance_id: int = 1,
    ):
        """创建mock任务对象"""
        task = MagicMock()
        task.id = task_id
        task.assignee_id = assignee_id
        task.status = status
        task.node_id = node_id
        task.instance_id = instance_id
        task.task_type = "APPROVAL"
        task.task_order = 1
        task.is_countersign = False
        task.due_at = None
        
        # Mock节点
        task.node = self._create_mock_node(node_id)
        
        # Mock实例
        task.instance = self._create_mock_instance(instance_id)
        
        return task

    def _create_mock_node(
        self,
        node_id: int = 1,
        flow_id: int = 1,
        node_order: int = 1,
        can_transfer: bool = True,
        can_add_approver: bool = True,
    ):
        """创建mock节点对象"""
        node = MagicMock()
        node.id = node_id
        node.flow_id = flow_id
        node.node_order = node_order
        node.can_transfer = can_transfer
        node.can_add_approver = can_add_approver
        node.notify_config = {}
        return node

    def _create_mock_instance(
        self,
        instance_id: int = 1,
        status: str = "PENDING",
        template_id: int = 1,
        initiator_id: int = 200,
    ):
        """创建mock实例对象"""
        instance = MagicMock()
        instance.id = instance_id
        instance.status = status
        instance.template_id = template_id
        instance.initiator_id = initiator_id
        instance.entity_type = "TEST"
        instance.entity_id = 1
        instance.form_data = {"amount": 5000}
        instance.completed_at = None
        return instance

    def _create_mock_user(
        self,
        user_id: int = 100,
        username: str = "testuser",
        real_name: str = "测试用户",
    ):
        """创建mock用户对象"""
        user = MagicMock()
        user.id = user_id
        user.username = username
        user.real_name = real_name
        return user

    # ========== approve() 测试 ==========

    def test_approve_success_and_advance(self):
        """测试审批通过并流转到下一节点"""
        # 准备数据
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        # Mock数据库查询
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,  # _get_and_validate_task
            approver,  # approve() 中查询审批人
        ]
        
        # Mock executor.process_approval 返回可以继续流转
        self.engine.executor.process_approval.return_value = (True, None)
        
        # 执行
        result = self.engine.approve(
            task_id=1,
            approver_id=100,
            comment="同意",
            attachments=[{"name": "file.pdf"}],
        )
        
        # 验证
        self.assertEqual(result, task)
        self.engine.executor.process_approval.assert_called_once_with(
            task=task,
            action="APPROVE",
            comment="同意",
            attachments=[{"name": "file.pdf"}],
            eval_data=None,
        )
        self.mock_db.commit.assert_called_once()

    def test_approve_success_but_cannot_proceed(self):
        """测试审批通过但不能流转（如会签未全部完成）"""
        # 准备数据
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        # Mock数据库查询
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        
        # Mock executor.process_approval 返回不能继续流转
        self.engine.executor.process_approval.return_value = (False, None)
        
        # 执行
        result = self.engine.approve(task_id=1, approver_id=100)
        
        # 验证 - 不应调用 _advance_to_next_node
        self.assertEqual(result, task)
        self.mock_db.commit.assert_called_once()

    def test_approve_with_eval_data(self):
        """测试带评估数据的审批（ECN场景）"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        self.engine.executor.process_approval.return_value = (True, None)
        
        eval_data = {"score": 95, "comment": "优秀"}
        result = self.engine.approve(
            task_id=1,
            approver_id=100,
            eval_data=eval_data,
        )
        
        self.engine.executor.process_approval.assert_called_once()
        call_kwargs = self.engine.executor.process_approval.call_args[1]
        self.assertEqual(call_kwargs["eval_data"], eval_data)

    # ========== reject() 测试 ==========

    def test_reject_to_start(self):
        """测试驳回到发起人"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        self.engine.executor.process_approval.return_value = (False, None)
        
        # 执行
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="不同意",
            reject_to="START",
        )
        
        # 验证
        self.assertEqual(result, task)
        self.assertEqual(task.instance.status, "REJECTED")
        self.assertIsNotNone(task.instance.completed_at)
        self.engine.notify.notify_rejected.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_reject_to_prev_node(self):
        """测试退回到上一节点"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        prev_node = self._create_mock_node(node_id=0, node_order=0)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        
        # Mock _get_previous_node
        with patch.object(self.engine, '_get_previous_node', return_value=prev_node):
            with patch.object(self.engine, '_return_to_node') as mock_return:
                self.engine.executor.process_approval.return_value = (False, None)
                
                result = self.engine.reject(
                    task_id=1,
                    approver_id=100,
                    comment="退回修改",
                    reject_to="PREV",
                )
                
                mock_return.assert_called_once_with(task.instance, prev_node)
                self.mock_db.commit.assert_called_once()

    def test_reject_to_prev_no_prev_node(self):
        """测试退回上一节点但不存在上一节点"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        
        # Mock _get_previous_node 返回None
        with patch.object(self.engine, '_get_previous_node', return_value=None):
            self.engine.executor.process_approval.return_value = (False, None)
            
            result = self.engine.reject(
                task_id=1,
                approver_id=100,
                comment="退回修改",
                reject_to="PREV",
            )
            
            # 应该变为REJECTED状态
            self.assertEqual(task.instance.status, "REJECTED")
            self.assertIsNotNone(task.instance.completed_at)

    def test_reject_to_specific_node(self):
        """测试退回到指定节点"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        target_node = self._create_mock_node(node_id=999)
        
        # Mock数据库查询 - 注意顺序
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.first.side_effect = [
            task,       # _get_and_validate_task
            approver,   # reject() 中查询审批人
            target_node,  # reject() 中查询目标节点
        ]
        
        self.engine.executor.process_approval.return_value = (False, None)
        
        with patch.object(self.engine, '_return_to_node') as mock_return:
            result = self.engine.reject(
                task_id=1,
                approver_id=100,
                comment="退回修改",
                reject_to="999",  # 节点ID字符串
            )
            
            mock_return.assert_called_once_with(task.instance, target_node)

    def test_reject_to_invalid_node_id(self):
        """测试退回到无效节点ID"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
            None,  # 查不到目标节点
        ]
        
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="退回",
            reject_to="999",
        )
        
        # 应该变为REJECTED状态
        self.assertEqual(task.instance.status, "REJECTED")

    def test_reject_to_non_numeric_value(self):
        """测试退回目标为非数字字符串"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="退回",
            reject_to="INVALID",  # 非数字字符串
        )
        
        # 应该变为REJECTED状态
        self.assertEqual(task.instance.status, "REJECTED")

    def test_reject_empty_comment_raises_error(self):
        """测试驳回时不填写原因抛出异常"""
        with self.assertRaises(ValueError) as context:
            self.engine.reject(task_id=1, approver_id=100, comment="")
        
        self.assertIn("驳回原因不能为空", str(context.exception))

    def test_reject_none_comment_raises_error(self):
        """测试驳回时原因为None抛出异常"""
        with self.assertRaises(ValueError) as context:
            self.engine.reject(task_id=1, approver_id=100, comment=None)
        
        self.assertIn("驳回原因不能为空", str(context.exception))

    # ========== return_to() 测试 ==========

    def test_return_to_success(self):
        """测试退回到指定节点成功"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        target_node = self._create_mock_node(node_id=999)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
            target_node,
        ]
        
        with patch.object(self.engine, '_return_to_node') as mock_return:
            result = self.engine.return_to(
                task_id=1,
                approver_id=100,
                target_node_id=999,
                comment="请重新填写",
            )
            
            self.assertEqual(result, task)
            self.assertEqual(task.action, "RETURN")
            self.assertEqual(task.comment, "请重新填写")
            self.assertEqual(task.status, "COMPLETED")
            self.assertEqual(task.return_to_node_id, 999)
            self.assertIsNotNone(task.completed_at)
            mock_return.assert_called_once_with(task.instance, target_node)
            self.mock_db.commit.assert_called_once()

    def test_return_to_node_not_found(self):
        """测试退回到不存在的节点"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
            None,  # 目标节点不存在
        ]
        
        with patch.object(self.engine, '_return_to_node') as mock_return:
            result = self.engine.return_to(
                task_id=1,
                approver_id=100,
                target_node_id=999,
                comment="退回",
            )
            
            # 不应调用 _return_to_node
            mock_return.assert_not_called()
            self.mock_db.commit.assert_called_once()

    # ========== transfer() 测试 ==========

    def test_transfer_success(self):
        """测试转审成功"""
        task = self._create_mock_task()
        from_user = self._create_mock_user(user_id=100, real_name="张三")
        to_user = self._create_mock_user(user_id=200, real_name="李四")
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            from_user,
            to_user,
        ]
        
        # Mock _log_action 以避免影响 db.add 的调用计数
        with patch.object(self.engine, '_log_action'):
            result = self.engine.transfer(
                task_id=1,
                from_user_id=100,
                to_user_id=200,
                comment="转给你处理",
            )
        
        # 验证原任务状态
        self.assertEqual(task.status, "TRANSFERRED")
        self.assertIsNotNone(task.completed_at)
        
        # 验证新任务创建 (只有1次,因为_log_action被mock了)
        self.mock_db.add.assert_called_once()
        new_task = self.mock_db.add.call_args[0][0]
        self.assertEqual(new_task.assignee_id, 200)
        self.assertEqual(new_task.assignee_name, "李四")
        self.assertEqual(new_task.assignee_type, "TRANSFERRED")
        self.assertEqual(new_task.original_assignee_id, 100)
        self.assertEqual(new_task.status, "PENDING")
        
        # 验证通知
        self.engine.notify.notify_transferred.assert_called_once()
        self.mock_db.flush.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_transfer_node_not_allow(self):
        """测试节点不允许转审"""
        task = self._create_mock_task()
        task.node.can_transfer = False
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = task
        
        with self.assertRaises(ValueError) as context:
            self.engine.transfer(
                task_id=1,
                from_user_id=100,
                to_user_id=200,
            )
        
        self.assertIn("当前节点不允许转审", str(context.exception))

    def test_transfer_to_user_not_exist(self):
        """测试转审目标用户不存在"""
        task = self._create_mock_task()
        from_user = self._create_mock_user(user_id=100)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            from_user,
            None,  # to_user不存在
        ]
        
        with self.assertRaises(ValueError) as context:
            self.engine.transfer(
                task_id=1,
                from_user_id=100,
                to_user_id=200,
            )
        
        self.assertIn("转审目标用户不存在", str(context.exception))

    # ========== add_approver() 测试 ==========

    def test_add_approver_before(self):
        """测试前加签"""
        task = self._create_mock_task()
        operator = self._create_mock_user(user_id=100, real_name="张三")
        approver1 = self._create_mock_user(user_id=201, real_name="李四")
        approver2 = self._create_mock_user(user_id=202, real_name="王五")
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            operator,
            approver1,
            approver2,
        ]
        
        # Mock _log_action 以避免影响 db.add 的调用计数
        with patch.object(self.engine, '_log_action'):
            result = self.engine.add_approver(
                task_id=1,
                operator_id=100,
                approver_ids=[201, 202],
                position="BEFORE",
                comment="请先审核",
            )
        
        # 验证返回的新任务列表
        self.assertEqual(len(result), 2)
        
        # 验证新任务创建 (2个新任务)
        self.assertEqual(self.mock_db.add.call_count, 2)
        
        # 验证原任务状态变为SKIPPED
        self.assertEqual(task.status, "SKIPPED")
        
        # 验证通知
        self.assertEqual(self.engine.notify.notify_add_approver.call_count, 2)
        self.mock_db.flush.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_add_approver_after(self):
        """测试后加签"""
        task = self._create_mock_task()
        operator = self._create_mock_user(user_id=100, real_name="张三")
        approver1 = self._create_mock_user(user_id=201, real_name="李四")
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            operator,
            approver1,
        ]
        
        result = self.engine.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201],
            position="AFTER",
            comment="加签",
        )
        
        # 验证
        self.assertEqual(len(result), 1)
        new_task = result[0]
        
        # 后加签的任务状态应该是SKIPPED（等待当前审批人完成后才激活）
        self.assertEqual(new_task.status, "SKIPPED")
        self.assertEqual(new_task.assignee_type, "ADDED_AFTER")
        
        # 原任务状态不变
        self.assertNotEqual(task.status, "SKIPPED")
        
        # 后加签不应该立即通知
        self.engine.notify.notify_add_approver.assert_not_called()

    def test_add_approver_node_not_allow(self):
        """测试节点不允许加签"""
        task = self._create_mock_task()
        task.node.can_add_approver = False
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = task
        
        with self.assertRaises(ValueError) as context:
            self.engine.add_approver(
                task_id=1,
                operator_id=100,
                approver_ids=[201],
            )
        
        self.assertIn("当前节点不允许加签", str(context.exception))

    def test_add_approver_skip_non_exist_users(self):
        """测试加签时跳过不存在的用户"""
        task = self._create_mock_task()
        operator = self._create_mock_user(user_id=100)
        approver1 = self._create_mock_user(user_id=201)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            operator,
            approver1,
            None,  # 第二个用户不存在
        ]
        
        # Mock _log_action 以避免影响 db.add 的调用计数
        with patch.object(self.engine, '_log_action'):
            result = self.engine.add_approver(
                task_id=1,
                operator_id=100,
                approver_ids=[201, 202],  # 202不存在
                position="BEFORE",
            )
        
        # 应该只创建一个任务
        self.assertEqual(len(result), 1)
        self.assertEqual(self.mock_db.add.call_count, 1)

    # ========== _get_and_validate_task() 边界测试 ==========

    def test_get_and_validate_task_not_exist(self):
        """测试任务不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.engine._get_and_validate_task(task_id=999, user_id=100)
        
        self.assertIn("任务不存在", str(context.exception))

    def test_get_and_validate_task_not_authorized(self):
        """测试无权操作任务"""
        task = self._create_mock_task(assignee_id=999)
        self.mock_db.query.return_value.filter.return_value.first.return_value = task
        
        with self.assertRaises(ValueError) as context:
            self.engine._get_and_validate_task(task_id=1, user_id=100)
        
        self.assertIn("无权操作此任务", str(context.exception))

    def test_get_and_validate_task_wrong_status(self):
        """测试任务状态不正确"""
        task = self._create_mock_task(status="COMPLETED")
        self.mock_db.query.return_value.filter.return_value.first.return_value = task
        
        with self.assertRaises(ValueError) as context:
            self.engine._get_and_validate_task(task_id=1, user_id=100)
        
        self.assertIn("任务状态不正确", str(context.exception))

    # ========== 集成场景测试 ==========

    def test_approve_workflow_integration(self):
        """测试完整审批流程（模拟真实场景）"""
        # 场景：张三审批通过 -> 调用_advance_to_next_node -> 流转成功
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100, real_name="张三")
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        
        self.engine.executor.process_approval.return_value = (True, None)
        
        # Mock _advance_to_next_node
        with patch.object(self.engine, '_advance_to_next_node') as mock_advance:
            result = self.engine.approve(
                task_id=1,
                approver_id=100,
                comment="通过",
            )
            
            mock_advance.assert_called_once_with(task.instance, task)
            self.mock_db.commit.assert_called_once()

    def test_reject_and_callback_integration(self):
        """测试驳回并触发适配器回调"""
        task = self._create_mock_task()
        approver = self._create_mock_user(user_id=100)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        
        self.engine.executor.process_approval.return_value = (False, None)
        
        # Mock _call_adapter_callback
        with patch.object(self.engine, '_call_adapter_callback') as mock_callback:
            result = self.engine.reject(
                task_id=1,
                approver_id=100,
                comment="不符合要求",
                reject_to="START",
            )
            
            mock_callback.assert_called_once_with(task.instance, "on_rejected")


class TestApprovalProcessLogging(unittest.TestCase):
    """测试审批操作日志记录"""

    def setUp(self):
        self.mock_db = MagicMock()
        
        class TestEngine(ApprovalProcessMixin, ApprovalEngineCore):
            pass
        
        self.engine = TestEngine(self.mock_db)
        self.engine.executor = MagicMock()
        self.engine.notify = MagicMock()
        self.engine.router = MagicMock()

    def test_approve_logs_action(self):
        """测试审批通过记录日志"""
        task = MagicMock()
        task.id = 1
        task.node_id = 10
        task.assignee_id = 100
        task.status = "PENDING"
        task.instance = MagicMock()
        task.instance.id = 1
        task.instance.status = "PENDING"
        task.node = MagicMock()
        
        approver = MagicMock()
        approver.real_name = "张三"
        approver.username = "zhangsan"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            task,
            approver,
        ]
        
        self.engine.executor.process_approval.return_value = (False, None)
        
        # Mock _log_action
        with patch.object(self.engine, '_log_action') as mock_log:
            self.engine.approve(
                task_id=1,
                approver_id=100,
                comment="同意",
                attachments=[{"name": "file.pdf"}],
            )
            
            mock_log.assert_called_once()
            call_kwargs = mock_log.call_args[1]
            self.assertEqual(call_kwargs["action"], "APPROVE")
            self.assertEqual(call_kwargs["comment"], "同意")
            self.assertEqual(call_kwargs["operator_id"], 100)


if __name__ == "__main__":
    unittest.main()
