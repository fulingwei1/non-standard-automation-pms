# -*- coding: utf-8 -*-
"""
审批处理功能单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库、日志服务、通知服务）
2. 测试核心业务逻辑真正执行
3. 达到70%+覆盖率

核心方法：
- approve(): 审批通过
- reject(): 审批驳回
- return_to(): 退回到指定节点
- transfer(): 转审
- add_approver(): 加签
"""

import unittest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta

from app.models.approval import (
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
)
from app.models.user import User
from app.services.approval_engine.engine.approve import ApprovalProcessMixin
from app.services.approval_engine.engine.core import ApprovalEngineCore


class MockApprovalEngine(ApprovalProcessMixin, ApprovalEngineCore):
    """测试用的混入类实例"""
    
    def __init__(self, db):
        self.db = db
        self.executor = MagicMock()
        self.notify = MagicMock()
        self.logger = MagicMock()


class TestApprove(unittest.TestCase):
    """测试 approve() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = MockApprovalEngine(self.mock_db)

    def _create_task(self, task_id=1, approver_id=100, status="PENDING"):
        """创建测试用任务对象"""
        task = MagicMock(spec=ApprovalTask)
        task.id = task_id
        task.node_id = 10
        task.status = status
        
        # 关联实例
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        instance.status = "IN_PROGRESS"
        task.instance = instance
        
        # 关联节点
        node = MagicMock(spec=ApprovalNodeDefinition)
        node.id = 10
        node.node_name = "审批节点"
        task.node = node
        
        return task

    def _create_user(self, user_id=100, real_name="测试用户", username="testuser"):
        """创建测试用户"""
        user = MagicMock(spec=User)
        user.id = user_id
        user.real_name = real_name
        user.username = username
        return user

    def test_approve_success_can_proceed(self):
        """测试审批通过并流转到下一节点"""
        task = self._create_task()
        approver = self._create_user()
        
        # Mock数据库查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        
        # Mock内部方法
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._advance_to_next_node = MagicMock()
        
        # Mock executor返回可以流转
        self.engine.executor.process_approval.return_value = (True, None)
        
        # 执行
        result = self.engine.approve(
            task_id=1,
            approver_id=100,
            comment="同意",
        )
        
        # 验证
        self.assertEqual(result, task)
        self.engine._get_and_validate_task.assert_called_once_with(1, 100)
        self.engine.executor.process_approval.assert_called_once()
        
        # 验证process_approval的调用参数
        call_kwargs = self.engine.executor.process_approval.call_args[1]
        self.assertEqual(call_kwargs['task'], task)
        self.assertEqual(call_kwargs['action'], 'APPROVE')
        self.assertEqual(call_kwargs['comment'], '同意')
        
        # 验证流转到下一节点
        self.engine._advance_to_next_node.assert_called_once_with(task.instance, task)
        
        # 验证记录日志
        self.engine._log_action.assert_called_once()
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['action'], 'APPROVE')
        self.assertEqual(log_kwargs['operator_id'], 100)
        self.assertEqual(log_kwargs['operator_name'], '测试用户')
        self.assertEqual(log_kwargs['comment'], '同意')
        
        # 验证提交
        self.mock_db.commit.assert_called_once()

    def test_approve_success_cannot_proceed(self):
        """测试审批通过但不流转（最后节点）"""
        task = self._create_task()
        approver = self._create_user()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._advance_to_next_node = MagicMock()
        
        # 不能流转
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.approve(task_id=1, approver_id=100)
        
        # 不应调用流转
        self.engine._advance_to_next_node.assert_not_called()
        self.mock_db.commit.assert_called_once()

    def test_approve_with_attachments(self):
        """测试带附件的审批"""
        task = self._create_task()
        approver = self._create_user()
        
        attachments = [
            {"name": "file1.pdf", "url": "http://example.com/file1.pdf"},
            {"name": "file2.docx", "url": "http://example.com/file2.docx"},
        ]
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._advance_to_next_node = MagicMock()
        self.engine.executor.process_approval.return_value = (True, None)
        
        result = self.engine.approve(
            task_id=1,
            approver_id=100,
            attachments=attachments,
        )
        
        # 验证附件被传递
        call_kwargs = self.engine.executor.process_approval.call_args[1]
        self.assertEqual(call_kwargs['attachments'], attachments)
        
        # 验证日志包含附件
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['attachments'], attachments)

    def test_approve_with_eval_data(self):
        """测试带评估数据的审批（ECN场景）"""
        task = self._create_task()
        approver = self._create_user()
        
        eval_data = {
            "score": 85,
            "level": "A",
            "remarks": "表现优秀",
        }
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._advance_to_next_node = MagicMock()
        self.engine.executor.process_approval.return_value = (True, None)
        
        result = self.engine.approve(
            task_id=1,
            approver_id=100,
            eval_data=eval_data,
        )
        
        # 验证eval_data被传递
        call_kwargs = self.engine.executor.process_approval.call_args[1]
        self.assertEqual(call_kwargs['eval_data'], eval_data)

    def test_approve_user_without_real_name(self):
        """测试审批人没有真实姓名时使用用户名"""
        task = self._create_task()
        approver = self._create_user(real_name=None, username="john_doe")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._advance_to_next_node = MagicMock()
        self.engine.executor.process_approval.return_value = (True, None)
        
        self.engine.approve(task_id=1, approver_id=100)
        
        # 验证使用用户名
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['operator_name'], 'john_doe')

    def test_approve_user_not_found(self):
        """测试审批人不存在时（处理None）"""
        task = self._create_task()
        
        # 用户不存在
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._advance_to_next_node = MagicMock()
        self.engine.executor.process_approval.return_value = (True, None)
        
        self.engine.approve(task_id=1, approver_id=100)
        
        # 验证operator_name为None
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertIsNone(log_kwargs['operator_name'])


class TestReject(unittest.TestCase):
    """测试 reject() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = MockApprovalEngine(self.mock_db)

    def _create_task(self):
        """创建测试任务"""
        task = MagicMock(spec=ApprovalTask)
        task.id = 1
        task.node_id = 10
        
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        instance.status = "IN_PROGRESS"
        instance.completed_at = None
        task.instance = instance
        
        node = MagicMock(spec=ApprovalNodeDefinition)
        node.id = 10
        task.node = node
        
        return task

    def _create_user(self, user_id=100, real_name="测试用户"):
        """创建测试用户"""
        user = MagicMock(spec=User)
        user.id = user_id
        user.real_name = real_name
        user.username = "testuser"
        return user

    def test_reject_requires_comment(self):
        """测试驳回必须提供原因"""
        with self.assertRaises(ValueError) as cm:
            self.engine.reject(
                task_id=1,
                approver_id=100,
                comment="",
                reject_to="START",
            )
        self.assertIn("驳回原因不能为空", str(cm.exception))

    def test_reject_to_start_success(self):
        """测试驳回到发起人"""
        task = self._create_task()
        approver = self._create_user(real_name="张三")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._call_adapter_callback = MagicMock()
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="不符合要求",
            reject_to="START",
        )
        
        # 验证实例状态
        self.assertEqual(task.instance.status, "REJECTED")
        self.assertIsNotNone(task.instance.completed_at)
        
        # 验证调用适配器回调
        self.engine._call_adapter_callback.assert_called_once_with(
            task.instance, "on_rejected"
        )
        
        # 验证通知发起人
        self.engine.notify.notify_rejected.assert_called_once()
        notify_kwargs = self.engine.notify.notify_rejected.call_args[0]
        self.assertEqual(notify_kwargs[0], task.instance)
        
        # 验证日志
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['action'], 'REJECT')
        self.assertEqual(log_kwargs['action_detail']['reject_to'], 'START')
        
        self.mock_db.commit.assert_called_once()

    def test_reject_to_prev_with_node(self):
        """测试驳回到上一节点（节点存在）"""
        task = self._create_task()
        approver = self._create_user()
        
        prev_node = MagicMock(spec=ApprovalNodeDefinition)
        prev_node.id = 9
        prev_node.node_name = "上一节点"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._get_previous_node = MagicMock(return_value=prev_node)
        self.engine._return_to_node = MagicMock()
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="需要修改",
            reject_to="PREV",
        )
        
        # 验证调用了退回方法
        self.engine._get_previous_node.assert_called_once_with(task.node)
        self.engine._return_to_node.assert_called_once_with(task.instance, prev_node)
        
        # 实例状态应该不变（由_return_to_node处理）
        self.assertNotEqual(task.instance.status, "REJECTED")

    def test_reject_to_prev_without_node(self):
        """测试驳回到上一节点（节点不存在）"""
        task = self._create_task()
        approver = self._create_user()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._get_previous_node = MagicMock(return_value=None)
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="无上一节点",
            reject_to="PREV",
        )
        
        # 应该变为REJECTED
        self.assertEqual(task.instance.status, "REJECTED")
        self.assertIsNotNone(task.instance.completed_at)

    def test_reject_to_specific_node_by_id(self):
        """测试驳回到指定节点ID"""
        task = self._create_task()
        approver = self._create_user()
        
        target_node = MagicMock(spec=ApprovalNodeDefinition)
        target_node.id = 8
        
        # 第一次查询用户，第二次查询节点
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=target_node)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._return_to_node = MagicMock()
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="退回到节点8",
            reject_to="8",
        )
        
        # 验证退回到指定节点
        self.engine._return_to_node.assert_called_once_with(task.instance, target_node)

    def test_reject_to_specific_node_not_found(self):
        """测试驳回到指定节点但节点不存在"""
        task = self._create_task()
        approver = self._create_user()
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="节点不存在",
            reject_to="999",
        )
        
        # 应该变为REJECTED
        self.assertEqual(task.instance.status, "REJECTED")

    def test_reject_with_invalid_node_id(self):
        """测试驳回时提供非数字的节点ID"""
        task = self._create_task()
        approver = self._create_user()
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="无效节点ID",
            reject_to="INVALID_ID",
        )
        
        # 应该变为REJECTED
        self.assertEqual(task.instance.status, "REJECTED")

    def test_reject_with_attachments(self):
        """测试带附件的驳回"""
        task = self._create_task()
        approver = self._create_user()
        
        attachments = [{"name": "proof.pdf", "url": "http://example.com/proof.pdf"}]
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = approver
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._call_adapter_callback = MagicMock()
        self.engine.executor.process_approval.return_value = (False, None)
        
        result = self.engine.reject(
            task_id=1,
            approver_id=100,
            comment="不符合标准，见附件",
            reject_to="START",
            attachments=attachments,
        )
        
        # 验证附件被传递
        call_kwargs = self.engine.executor.process_approval.call_args[1]
        self.assertEqual(call_kwargs['attachments'], attachments)
        
        # 验证日志包含附件
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['attachments'], attachments)


class TestReturnTo(unittest.TestCase):
    """测试 return_to() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = MockApprovalEngine(self.mock_db)

    def _create_task(self):
        """创建测试任务"""
        task = MagicMock(spec=ApprovalTask)
        task.id = 1
        task.node_id = 10
        task.action = None
        task.comment = None
        task.status = "PENDING"
        task.completed_at = None
        task.return_to_node_id = None
        
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        task.instance = instance
        
        return task

    def test_return_to_success(self):
        """测试成功退回到指定节点"""
        task = self._create_task()
        approver = MagicMock(spec=User)
        approver.real_name = "张三"
        approver.username = "zhangsan"
        
        target_node = MagicMock(spec=ApprovalNodeDefinition)
        target_node.id = 8
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=target_node)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._return_to_node = MagicMock()
        
        result = self.engine.return_to(
            task_id=1,
            approver_id=100,
            target_node_id=8,
            comment="需要重新审核",
        )
        
        # 验证任务属性更新
        self.assertEqual(task.action, "RETURN")
        self.assertEqual(task.comment, "需要重新审核")
        self.assertEqual(task.status, "COMPLETED")
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.return_to_node_id, 8)
        
        # 验证退回到目标节点
        self.engine._return_to_node.assert_called_once_with(task.instance, target_node)
        
        # 验证日志
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['action'], 'RETURN')
        self.assertEqual(log_kwargs['comment'], '需要重新审核')
        self.assertEqual(log_kwargs['action_detail']['return_to_node_id'], 8)
        
        self.mock_db.commit.assert_called_once()

    def test_return_to_node_not_found(self):
        """测试退回时目标节点不存在"""
        task = self._create_task()
        approver = MagicMock(spec=User)
        approver.real_name = "李四"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        self.engine._return_to_node = MagicMock()
        
        result = self.engine.return_to(
            task_id=1,
            approver_id=100,
            target_node_id=999,
            comment="节点不存在",
        )
        
        # 任务状态应该更新
        self.assertEqual(task.status, "COMPLETED")
        
        # 不应调用_return_to_node
        self.engine._return_to_node.assert_not_called()


class TestTransfer(unittest.TestCase):
    """测试 transfer() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = MockApprovalEngine(self.mock_db)

    def _create_task(self, can_transfer=True):
        """创建测试任务"""
        task = MagicMock(spec=ApprovalTask)
        task.id = 1
        task.instance_id = 1
        task.node_id = 10
        task.task_type = "APPROVAL"
        task.task_order = 1
        task.status = "PENDING"
        task.completed_at = None
        task.due_at = datetime.now() + timedelta(days=3)
        task.is_countersign = False
        
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        task.instance = instance
        
        node = MagicMock(spec=ApprovalNodeDefinition)
        node.id = 10
        node.can_transfer = can_transfer
        task.node = node
        
        return task

    def test_transfer_not_allowed(self):
        """测试节点不允许转审"""
        task = self._create_task(can_transfer=False)
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        
        with self.assertRaises(ValueError) as cm:
            self.engine.transfer(
                task_id=1,
                from_user_id=100,
                to_user_id=200,
            )
        self.assertIn("当前节点不允许转审", str(cm.exception))

    def test_transfer_to_user_not_found(self):
        """测试转审目标用户不存在"""
        task = self._create_task()
        from_user = MagicMock(spec=User)
        from_user.real_name = "张三"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=from_user)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        
        with self.assertRaises(ValueError) as cm:
            self.engine.transfer(
                task_id=1,
                from_user_id=100,
                to_user_id=200,
            )
        self.assertIn("转审目标用户不存在: 200", str(cm.exception))

    def test_transfer_success(self):
        """测试成功转审"""
        task = self._create_task()
        from_user = MagicMock(spec=User)
        from_user.id = 100
        from_user.real_name = "张三"
        from_user.username = "zhangsan"
        
        to_user = MagicMock(spec=User)
        to_user.id = 200
        to_user.real_name = "李四"
        to_user.username = "lisi"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=from_user)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=to_user)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        
        # 捕获添加的新任务
        added_tasks = []
        def mock_add(obj):
            added_tasks.append(obj)
        self.mock_db.add.side_effect = mock_add
        
        result = self.engine.transfer(
            task_id=1,
            from_user_id=100,
            to_user_id=200,
            comment="转给李四处理",
        )
        
        # 验证原任务状态
        self.assertEqual(task.status, "TRANSFERRED")
        self.assertIsNotNone(task.completed_at)
        
        # 验证创建了新任务
        self.assertEqual(len(added_tasks), 1)
        new_task = added_tasks[0]
        self.assertEqual(new_task.assignee_id, 200)
        self.assertEqual(new_task.assignee_name, "李四")
        self.assertEqual(new_task.assignee_type, "TRANSFERRED")
        self.assertEqual(new_task.original_assignee_id, 100)
        self.assertEqual(new_task.status, "PENDING")
        self.assertEqual(new_task.instance_id, task.instance_id)
        self.assertEqual(new_task.node_id, task.node_id)
        
        # 验证通知
        self.engine.notify.notify_transferred.assert_called_once()
        
        # 验证日志
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['action'], 'TRANSFER')
        self.assertEqual(log_kwargs['action_detail']['from_user_id'], 100)
        self.assertEqual(log_kwargs['action_detail']['to_user_id'], 200)
        
        self.mock_db.commit.assert_called_once()

    def test_transfer_preserves_task_properties(self):
        """测试转审保留任务属性"""
        due_time = datetime.now() + timedelta(days=5)
        task = self._create_task()
        task.due_at = due_time
        task.is_countersign = True
        
        from_user = MagicMock(spec=User)
        from_user.real_name = "王五"
        from_user.username = "wangwu"
        
        to_user = MagicMock(spec=User)
        to_user.real_name = "赵六"
        to_user.username = "zhaoliu"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=from_user)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=to_user)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        
        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)
        
        self.engine.transfer(task_id=1, from_user_id=100, to_user_id=200)
        
        # 验证新任务保留属性
        new_task = added_tasks[0]
        self.assertEqual(new_task.due_at, due_time)
        self.assertEqual(new_task.is_countersign, True)
        self.assertEqual(new_task.task_type, task.task_type)
        self.assertEqual(new_task.task_order, task.task_order)

    def test_transfer_user_without_real_name(self):
        """测试转审人没有真实姓名时使用用户名"""
        task = self._create_task()
        from_user = MagicMock(spec=User)
        from_user.real_name = None
        from_user.username = "user1"
        
        to_user = MagicMock(spec=User)
        to_user.real_name = None
        to_user.username = "user2"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=from_user)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=to_user)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        
        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)
        
        self.engine.transfer(task_id=1, from_user_id=100, to_user_id=200)
        
        # 验证使用用户名
        new_task = added_tasks[0]
        self.assertEqual(new_task.assignee_name, "user2")


class TestAddApprover(unittest.TestCase):
    """测试 add_approver() 方法"""

    def setUp(self):
        """测试前设置"""
        self.mock_db = MagicMock()
        self.engine = MockApprovalEngine(self.mock_db)

    def _create_task(self, can_add_approver=True):
        """创建测试任务"""
        task = MagicMock(spec=ApprovalTask)
        task.id = 1
        task.instance_id = 1
        task.node_id = 10
        task.task_order = 1
        task.status = "PENDING"
        task.due_at = datetime.now() + timedelta(days=3)
        
        instance = MagicMock(spec=ApprovalInstance)
        instance.id = 1
        task.instance = instance
        
        node = MagicMock(spec=ApprovalNodeDefinition)
        node.id = 10
        node.can_add_approver = can_add_approver
        task.node = node
        
        return task

    def test_add_approver_not_allowed(self):
        """测试节点不允许加签"""
        task = self._create_task(can_add_approver=False)
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        
        with self.assertRaises(ValueError) as cm:
            self.engine.add_approver(
                task_id=1,
                operator_id=100,
                approver_ids=[201],
            )
        self.assertIn("当前节点不允许加签", str(cm.exception))

    def test_add_approver_after_success(self):
        """测试后加签成功"""
        task = self._create_task()
        operator = MagicMock(spec=User)
        operator.id = 100
        operator.real_name = "张三"
        operator.username = "zhangsan"
        
        approver1 = MagicMock(spec=User)
        approver1.id = 201
        approver1.real_name = "李四"
        approver1.username = "lisi"
        
        approver2 = MagicMock(spec=User)
        approver2.id = 202
        approver2.real_name = "王五"
        approver2.username = "wangwu"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver1)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver2)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        
        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)
        
        result = self.engine.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201, 202],
            position="AFTER",
            comment="请帮忙审核",
        )
        
        # 验证创建了2个新任务
        self.assertEqual(len(added_tasks), 2)
        self.assertEqual(len(result), 2)
        
        # 后加签任务初始状态为SKIPPED
        self.assertEqual(added_tasks[0].status, "SKIPPED")
        self.assertEqual(added_tasks[1].status, "SKIPPED")
        self.assertEqual(added_tasks[0].assignee_type, "ADDED_AFTER")
        self.assertEqual(added_tasks[1].assignee_type, "ADDED_AFTER")
        
        # 原任务状态不变
        self.assertEqual(task.status, "PENDING")
        
        # 后加签不应通知（状态为SKIPPED）
        self.engine.notify.notify_add_approver.assert_not_called()
        
        # 验证日志
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['action'], 'ADD_APPROVER_AFTER')
        self.assertEqual(log_kwargs['action_detail']['approver_ids'], [201, 202])
        self.assertEqual(log_kwargs['action_detail']['position'], 'AFTER')

    def test_add_approver_before_success(self):
        """测试前加签成功"""
        task = self._create_task()
        operator = MagicMock(spec=User)
        operator.real_name = "赵六"
        operator.username = "zhaoliu"
        
        approver = MagicMock(spec=User)
        approver.id = 201
        approver.real_name = "孙七"
        approver.username = "sunqi"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        
        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)
        
        result = self.engine.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201],
            position="BEFORE",
            comment="请先审核",
        )
        
        # 验证创建了1个新任务
        self.assertEqual(len(added_tasks), 1)
        
        # 前加签任务状态为PENDING
        new_task = added_tasks[0]
        self.assertEqual(new_task.status, "PENDING")
        self.assertEqual(new_task.assignee_type, "ADDED_BEFORE")
        self.assertEqual(new_task.assignee_id, 201)
        
        # 原任务应变为SKIPPED
        self.assertEqual(task.status, "SKIPPED")
        
        # 应通知新审批人
        self.engine.notify.notify_add_approver.assert_called_once()
        
        # 验证日志
        log_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(log_kwargs['action'], 'ADD_APPROVER_BEFORE')

    def test_add_approver_skip_nonexistent_users(self):
        """测试加签时跳过不存在的用户"""
        task = self._create_task()
        operator = MagicMock(spec=User)
        operator.real_name = "周八"
        
        approver1 = MagicMock(spec=User)
        approver1.id = 201
        approver1.real_name = "吴九"
        approver1.username = "wujiu"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver1)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),  # 不存在
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        
        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)
        
        result = self.engine.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201, 999],  # 999不存在
            position="AFTER",
        )
        
        # 只创建1个任务
        self.assertEqual(len(added_tasks), 1)
        self.assertEqual(added_tasks[0].assignee_id, 201)

    def test_add_approver_preserves_task_properties(self):
        """测试加签保留任务属性"""
        due_time = datetime.now() + timedelta(days=7)
        task = self._create_task()
        task.due_at = due_time
        
        operator = MagicMock(spec=User)
        operator.real_name = "郑十"
        
        approver = MagicMock(spec=User)
        approver.id = 201
        approver.real_name = "冯十一"
        approver.username = "feng11"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        
        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)
        
        self.engine.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201],
            position="BEFORE",
        )
        
        # 验证新任务保留属性
        new_task = added_tasks[0]
        self.assertEqual(new_task.due_at, due_time)
        self.assertEqual(new_task.node_id, task.node_id)
        self.assertEqual(new_task.instance_id, task.instance_id)
        self.assertEqual(new_task.task_order, task.task_order)

    def test_add_approver_multiple_before(self):
        """测试批量前加签"""
        task = self._create_task()
        operator = MagicMock(spec=User)
        operator.real_name = "陈十二"
        
        approver1 = MagicMock(spec=User)
        approver1.id = 201
        approver1.real_name = "褚十三"
        approver1.username = "chu13"
        
        approver2 = MagicMock(spec=User)
        approver2.id = 202
        approver2.real_name = "卫十四"
        approver2.username = "wei14"
        
        self.mock_db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver1)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver2)))),
        ]
        
        self.engine._get_and_validate_task = MagicMock(return_value=task)
        self.engine._log_action = MagicMock()
        
        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)
        
        result = self.engine.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201, 202],
            position="BEFORE",
        )
        
        # 验证创建了2个前加签任务
        self.assertEqual(len(added_tasks), 2)
        self.assertTrue(all(t.status == "PENDING" for t in added_tasks))
        self.assertTrue(all(t.assignee_type == "ADDED_BEFORE" for t in added_tasks))
        
        # 应通知2次
        self.assertEqual(self.engine.notify.notify_add_approver.call_count, 2)


if __name__ == "__main__":
    unittest.main()
