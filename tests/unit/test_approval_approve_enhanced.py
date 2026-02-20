# -*- coding: utf-8 -*-
"""
审批处理功能完整测试（approve.py）
覆盖所有核心方法和边界条件
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.approval_engine.engine.approve import ApprovalProcessMixin
from app.services.approval_engine.engine.core import ApprovalEngineCore


class TestApprovalProcessMixin(unittest.TestCase):
    """测试审批处理混入类"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.executor = MagicMock()
        self.notify = MagicMock()
        
        # 创建混入实例
        self.mixin = ApprovalProcessMixin()
        self.mixin.db = self.db
        self.mixin.executor = self.executor
        self.mixin.notify = self.notify
        
        # Mock辅助方法
        self.mixin._get_and_validate_task = MagicMock()
        self.mixin._log_action = MagicMock()
        self.mixin._advance_to_next_node = MagicMock()
        self.mixin._get_previous_node = MagicMock()
        self.mixin._return_to_node = MagicMock()
        self.mixin._call_adapter_callback = MagicMock()

    # ==================== approve 方法测试 ====================

    def test_approve_success_basic(self):
        """测试基本审批通过"""
        # 准备数据
        task = MagicMock()
        task.id = 1
        task.node_id = 10
        instance = MagicMock()
        instance.id = 100
        instance.status = "PENDING"
        task.instance = instance
        
        approver = MagicMock()
        approver.id = 5
        approver.real_name = "张三"
        approver.username = "zhangsan"
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        self.executor.process_approval.return_value = (True, None)
        
        # 执行
        result = self.mixin.approve(task_id=1, approver_id=5)
        
        # 验证
        self.assertEqual(result, task)
        self.mixin._get_and_validate_task.assert_called_once_with(1, 5)
        self.executor.process_approval.assert_called_once()
        self.mixin._log_action.assert_called_once()
        self.mixin._advance_to_next_node.assert_called_once_with(instance, task)
        self.db.commit.assert_called_once()

    def test_approve_with_comment(self):
        """测试带审批意见的审批"""
        task = MagicMock()
        task.instance = MagicMock(id=100, status="PENDING")
        approver = MagicMock(id=5, real_name="李四")
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        self.executor.process_approval.return_value = (True, None)
        
        result = self.mixin.approve(task_id=1, approver_id=5, comment="同意")
        
        call_args = self.executor.process_approval.call_args
        self.assertEqual(call_args[1]['comment'], "同意")

    def test_approve_with_attachments(self):
        """测试带附件的审批"""
        task = MagicMock()
        task.instance = MagicMock(id=100, status="PENDING")
        approver = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        self.executor.process_approval.return_value = (True, None)
        
        attachments = [{"name": "file1.pdf", "url": "http://..."}]
        result = self.mixin.approve(task_id=1, approver_id=5, attachments=attachments)
        
        call_args = self.executor.process_approval.call_args
        self.assertEqual(call_args[1]['attachments'], attachments)

    def test_approve_with_eval_data(self):
        """测试带评估数据的审批（ECN场景）"""
        task = MagicMock()
        task.instance = MagicMock(id=100, status="PENDING")
        approver = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        self.executor.process_approval.return_value = (True, None)
        
        eval_data = {"score": 90, "level": "A"}
        result = self.mixin.approve(task_id=1, approver_id=5, eval_data=eval_data)
        
        call_args = self.executor.process_approval.call_args
        self.assertEqual(call_args[1]['eval_data'], eval_data)

    def test_approve_cannot_proceed(self):
        """测试审批后不能继续流转"""
        task = MagicMock()
        task.instance = MagicMock(id=100, status="PENDING")
        approver = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        self.executor.process_approval.return_value = (False, "等待其他审批人")
        
        result = self.mixin.approve(task_id=1, approver_id=5)
        
        # 不应该调用_advance_to_next_node
        self.mixin._advance_to_next_node.assert_not_called()

    def test_approve_no_approver_info(self):
        """测试审批人信息不存在"""
        task = MagicMock()
        task.instance = MagicMock(id=100, status="PENDING")
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = None
        self.executor.process_approval.return_value = (True, None)
        
        result = self.mixin.approve(task_id=1, approver_id=5)
        
        # 应该记录日志，operator_name为None
        log_call = self.mixin._log_action.call_args
        self.assertIsNone(log_call[1]['operator_name'])

    # ==================== reject 方法测试 ====================

    def test_reject_to_start(self):
        """测试驳回到发起人"""
        task = MagicMock()
        task.id = 1
        task.node_id = 10
        instance = MagicMock()
        instance.id = 100
        instance.status = "PENDING"
        task.instance = instance
        node = MagicMock()
        task.node = node
        
        approver = MagicMock(id=5, real_name="王五")
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        
        result = self.mixin.reject(
            task_id=1, 
            approver_id=5, 
            comment="不符合要求", 
            reject_to="START"
        )
        
        # 验证状态更新
        self.assertEqual(instance.status, "REJECTED")
        self.assertIsNotNone(instance.completed_at)
        self.mixin._call_adapter_callback.assert_called_once_with(instance, "on_rejected")
        self.notify.notify_rejected.assert_called_once()
        self.db.commit.assert_called_once()

    def test_reject_to_previous(self):
        """测试退回到上一节点"""
        task = MagicMock()
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        node = MagicMock()
        task.node = node
        
        prev_node = MagicMock()
        approver = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        self.mixin._get_previous_node.return_value = prev_node
        
        result = self.mixin.reject(
            task_id=1, 
            approver_id=5, 
            comment="请修改", 
            reject_to="PREV"
        )
        
        self.mixin._return_to_node.assert_called_once_with(instance, prev_node)
        self.assertNotEqual(instance.status, "REJECTED")

    def test_reject_to_previous_no_prev_node(self):
        """测试退回到上一节点但没有上一节点"""
        task = MagicMock()
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        node = MagicMock()
        task.node = node
        
        approver = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        self.mixin._get_previous_node.return_value = None
        
        result = self.mixin.reject(
            task_id=1, 
            approver_id=5, 
            comment="退回", 
            reject_to="PREV"
        )
        
        # 应该设置为REJECTED
        self.assertEqual(instance.status, "REJECTED")

    def test_reject_to_specific_node(self):
        """测试退回到指定节点"""
        task = MagicMock()
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        node = MagicMock()
        task.node = node
        
        target_node = MagicMock()
        approver = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.side_effect = [approver, target_node]
        
        result = self.mixin.reject(
            task_id=1, 
            approver_id=5, 
            comment="退回", 
            reject_to="20"
        )
        
        self.mixin._return_to_node.assert_called_once_with(instance, target_node)

    def test_reject_to_invalid_node_id(self):
        """测试退回到无效节点ID"""
        task = MagicMock()
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        node = MagicMock()
        task.node = node
        
        approver = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        
        result = self.mixin.reject(
            task_id=1, 
            approver_id=5, 
            comment="退回", 
            reject_to="invalid"
        )
        
        # 应该设置为REJECTED
        self.assertEqual(instance.status, "REJECTED")

    def test_reject_empty_comment(self):
        """测试空驳回原因"""
        task = MagicMock()
        
        with self.assertRaises(ValueError) as context:
            self.mixin.reject(task_id=1, approver_id=5, comment="")
        
        self.assertIn("驳回原因不能为空", str(context.exception))

    def test_reject_none_comment(self):
        """测试None驳回原因"""
        with self.assertRaises(ValueError) as context:
            self.mixin.reject(task_id=1, approver_id=5, comment=None)
        
        self.assertIn("驳回原因不能为空", str(context.exception))

    # ==================== return_to 方法测试 ====================

    def test_return_to_success(self):
        """测试退回到指定节点成功"""
        task = MagicMock()
        task.id = 1
        task.node_id = 10
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        
        target_node = MagicMock()
        approver = MagicMock(id=5, real_name="赵六")
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.return_value = approver
        
        with patch.object(self.db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.side_effect = [approver, target_node]
            
            result = self.mixin.return_to(
                task_id=1, 
                approver_id=5, 
                target_node_id=8, 
                comment="请重新填写"
            )
        
        # 验证任务状态更新
        self.assertEqual(task.action, "RETURN")
        self.assertEqual(task.comment, "请重新填写")
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.return_to_node_id, 8)

    def test_return_to_node_not_found(self):
        """测试退回节点不存在"""
        task = MagicMock()
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        
        approver = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.side_effect = [approver, None]
        
        result = self.mixin.return_to(
            task_id=1, 
            approver_id=5, 
            target_node_id=999, 
            comment="退回"
        )
        
        # _return_to_node不应该被调用
        self.mixin._return_to_node.assert_not_called()

    # ==================== transfer 方法测试 ====================

    def test_transfer_success(self):
        """测试转审成功"""
        task = MagicMock()
        task.id = 1
        task.node_id = 10
        task.task_type = "APPROVAL"
        task.task_order = 1
        task.due_at = None
        task.is_countersign = False
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        node = MagicMock()
        node.can_transfer = True
        task.node = node
        
        from_user = MagicMock(id=5, real_name="用户A", username="userA")
        to_user = MagicMock(id=6, real_name="用户B", username="userB")
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.side_effect = [from_user, to_user]
        
        from app.models.approval import ApprovalTask
        with patch('app.services.approval_engine.engine.approve.ApprovalTask') as mock_task_class:
            new_task = MagicMock()
            mock_task_class.return_value = new_task
            
            result = self.mixin.transfer(
                task_id=1, 
                from_user_id=5, 
                to_user_id=6, 
                comment="请帮忙审批"
            )
        
        # 验证原任务状态
        self.assertEqual(task.status, "TRANSFERRED")
        self.assertIsNotNone(task.completed_at)
        
        # 验证新任务创建
        self.db.add.assert_called_once()
        self.db.flush.assert_called_once()
        
        # 验证通知
        self.notify.notify_transferred.assert_called_once()

    def test_transfer_node_cannot_transfer(self):
        """测试节点不允许转审"""
        task = MagicMock()
        node = MagicMock()
        node.can_transfer = False
        task.node = node
        
        self.mixin._get_and_validate_task.return_value = task
        
        with self.assertRaises(ValueError) as context:
            self.mixin.transfer(task_id=1, from_user_id=5, to_user_id=6)
        
        self.assertIn("不允许转审", str(context.exception))

    def test_transfer_to_user_not_found(self):
        """测试转审目标用户不存在"""
        task = MagicMock()
        node = MagicMock()
        node.can_transfer = True
        task.node = node
        
        from_user = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.side_effect = [from_user, None]
        
        with self.assertRaises(ValueError) as context:
            self.mixin.transfer(task_id=1, from_user_id=5, to_user_id=999)
        
        self.assertIn("转审目标用户不存在", str(context.exception))

    # ==================== add_approver 方法测试 ====================

    def test_add_approver_before(self):
        """测试前加签"""
        task = MagicMock()
        task.id = 1
        task.node_id = 10
        task.task_order = 1
        task.due_at = None
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        node = MagicMock()
        node.id = 10
        node.can_add_approver = True
        task.node = node
        
        operator = MagicMock(id=5, real_name="操作人")
        approver1 = MagicMock(id=6, real_name="新审批人1", username="new1")
        approver2 = MagicMock(id=7, real_name="新审批人2", username="new2")
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.side_effect = [
            operator, approver1, approver2
        ]
        
        from app.models.approval import ApprovalTask
        with patch('app.services.approval_engine.engine.approve.ApprovalTask') as mock_task_class:
            new_task1 = MagicMock()
            new_task2 = MagicMock()
            mock_task_class.side_effect = [new_task1, new_task2]
            
            result = self.mixin.add_approver(
                task_id=1, 
                operator_id=5, 
                approver_ids=[6, 7], 
                position="BEFORE"
            )
        
        # 验证返回的新任务列表
        self.assertEqual(len(result), 2)
        
        # 验证原任务状态
        self.assertEqual(task.status, "SKIPPED")
        
        # 验证数据库操作
        self.assertEqual(self.db.add.call_count, 2)
        self.db.flush.assert_called_once()

    def test_add_approver_after(self):
        """测试后加签"""
        task = MagicMock()
        instance = MagicMock(id=100, status="PENDING")
        task.instance = instance
        node = MagicMock()
        node.can_add_approver = True
        task.node = node
        
        operator = MagicMock(id=5)
        approver = MagicMock(id=6, real_name="新审批人", username="new")
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.side_effect = [operator, approver]
        
        from app.models.approval import ApprovalTask
        with patch('app.services.approval_engine.engine.approve.ApprovalTask') as mock_task_class:
            new_task = MagicMock()
            mock_task_class.return_value = new_task
            
            result = self.mixin.add_approver(
                task_id=1, 
                operator_id=5, 
                approver_ids=[6], 
                position="AFTER"
            )
        
        # 验证原任务状态不变
        self.assertNotEqual(task.status, "SKIPPED")

    def test_add_approver_node_cannot_add(self):
        """测试节点不允许加签"""
        task = MagicMock()
        node = MagicMock()
        node.can_add_approver = False
        task.node = node
        
        self.mixin._get_and_validate_task.return_value = task
        
        with self.assertRaises(ValueError) as context:
            self.mixin.add_approver(task_id=1, operator_id=5, approver_ids=[6])
        
        self.assertIn("不允许加签", str(context.exception))

    def test_add_approver_user_not_found(self):
        """测试加签用户不存在"""
        task = MagicMock()
        node = MagicMock()
        node.can_add_approver = True
        task.node = node
        instance = MagicMock(id=100)
        task.instance = instance
        
        operator = MagicMock(id=5)
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.side_effect = [operator, None]
        
        from app.models.approval import ApprovalTask
        with patch('app.services.approval_engine.engine.approve.ApprovalTask'):
            result = self.mixin.add_approver(
                task_id=1, 
                operator_id=5, 
                approver_ids=[999]
            )
        
        # 应该返回空列表
        self.assertEqual(len(result), 0)

    def test_add_approver_notify_pending_only(self):
        """测试只通知PENDING状态的新任务"""
        task = MagicMock()
        node = MagicMock()
        node.can_add_approver = True
        task.node = node
        instance = MagicMock(id=100)
        task.instance = instance
        
        operator = MagicMock(id=5, real_name="操作人")
        approver1 = MagicMock(id=6, real_name="审批人1", username="app1")
        approver2 = MagicMock(id=7, real_name="审批人2", username="app2")
        
        self.mixin._get_and_validate_task.return_value = task
        self.db.query.return_value.filter.return_value.first.side_effect = [
            operator, approver1, approver2
        ]
        
        from app.models.approval import ApprovalTask
        with patch('app.services.approval_engine.engine.approve.ApprovalTask') as mock_task_class:
            new_task1 = MagicMock()
            new_task1.status = "PENDING"
            new_task2 = MagicMock()
            new_task2.status = "SKIPPED"
            mock_task_class.side_effect = [new_task1, new_task2]
            
            result = self.mixin.add_approver(
                task_id=1, 
                operator_id=5, 
                approver_ids=[6, 7], 
                position="BEFORE"
            )
        
        # 只应该通知一次（PENDING的任务）
        self.assertEqual(self.notify.notify_add_approver.call_count, 1)


if __name__ == "__main__":
    unittest.main()
