# -*- coding: utf-8 -*-
"""
approval_engine/approve.py 增强单元测试

测试审批处理功能混入类的所有核心方法
覆盖：approve, reject, return_to, transfer, add_approver
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.models.approval import (
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
)
from app.models.user import User
from app.services.approval_engine.engine import ApprovalEngineService


@pytest.mark.unit
class TestApprove:
    """测试 approve 方法"""

    def setup_method(self):
        """每个测试前的设置"""
        self.mock_db = MagicMock()
        self.service = ApprovalEngineService(self.mock_db)

    def _create_mock_task(self, task_id=1, assignee_id=100, node_id=10):
        """创建模拟任务对象"""
        task = ApprovalTask(
            id=task_id,
            instance_id=1,
            node_id=node_id,
            assignee_id=assignee_id,
            status="PENDING",
            task_type="APPROVAL",
            task_order=1,
        )
        
        # 创建关联的实例
        instance = ApprovalInstance(
            id=1,
            instance_no="AP2602210001",
            template_id=1,
            flow_id=1,
            status="IN_PROGRESS",
            initiator_id=99,
        )
        task.instance = instance
        
        # 创建关联的节点
        node = ApprovalNodeDefinition(
            id=node_id,
            flow_id=1,
            node_name="审批节点",
            node_order=1,
        )
        task.node = node
        
        return task

    def _create_mock_user(self, user_id=100, username="testuser", real_name="测试用户"):
        """创建模拟用户对象"""
        user = User(
            id=user_id,
            username=username,
            real_name=real_name,
        password_hash="test_hash_123"
    )
        return user

    def test_approve_success_with_next_node(self):
        """测试成功审批并流转到下一节点"""
        task = self._create_mock_task()
        approver = self._create_mock_user()

        # Mock 数据库查询
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        # Mock 内部方法
        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._advance_to_next_node = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(True, None))

        result = self.service.approve(
            task_id=1,
            approver_id=100,
            comment="同意",
        )

        assert result == task
        self.service._get_and_validate_task.assert_called_once_with(1, 100)
        self.service.executor.process_approval.assert_called_once()
        self.service._advance_to_next_node.assert_called_once_with(task.instance, task)
        self.mock_db.commit.assert_called_once()

    def test_approve_success_without_next_node(self):
        """测试成功审批但不流转（最后节点）"""
        task = self._create_mock_task()
        approver = self._create_mock_user()

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._advance_to_next_node = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(False, None))

        result = self.service.approve(
            task_id=1,
            approver_id=100,
            comment="同意",
        )

        assert result == task
        self.service._advance_to_next_node.assert_not_called()
        self.mock_db.commit.assert_called_once()

    def test_approve_with_attachments(self):
        """测试带附件的审批"""
        task = self._create_mock_task()
        approver = self._create_mock_user()
        attachments = [
            {"name": "file1.pdf", "url": "http://example.com/file1.pdf"},
            {"name": "file2.docx", "url": "http://example.com/file2.docx"},
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._advance_to_next_node = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(True, None))

        result = self.service.approve(
            task_id=1,
            approver_id=100,
            comment="同意",
            attachments=attachments,
        )

        # 验证附件被传递
        call_args = self.service.executor.process_approval.call_args
        assert call_args[1]["attachments"] == attachments

    def test_approve_with_eval_data(self):
        """测试带评估数据的审批（ECN场景）"""
        task = self._create_mock_task()
        approver = self._create_mock_user()
        eval_data = {
            "score": 85,
            "level": "A",
            "remarks": "表现优秀",
        }

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._advance_to_next_node = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(True, None))

        result = self.service.approve(
            task_id=1,
            approver_id=100,
            eval_data=eval_data,
        )

        call_args = self.service.executor.process_approval.call_args
        assert call_args[1]["eval_data"] == eval_data

    def test_approve_logs_action_correctly(self):
        """测试审批正确记录日志"""
        task = self._create_mock_task()
        approver = self._create_mock_user(real_name="张三")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._advance_to_next_node = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(True, None))

        self.service.approve(
            task_id=1,
            approver_id=100,
            comment="审批通过",
        )

        self.service._log_action.assert_called_once()
        call_args = self.service._log_action.call_args
        assert call_args[1]["action"] == "APPROVE"
        assert call_args[1]["operator_id"] == 100
        assert call_args[1]["operator_name"] == "张三"
        assert call_args[1]["comment"] == "审批通过"

    def test_approve_without_user_real_name(self):
        """测试审批人没有真实姓名时使用用户名"""
        task = self._create_mock_task()
        approver = self._create_mock_user(real_name=None, username="testuser")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._advance_to_next_node = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(True, None))

        self.service.approve(task_id=1, approver_id=100)

        call_args = self.service._log_action.call_args
        assert call_args[1]["operator_name"] == "testuser"


@pytest.mark.unit
class TestReject:
    """测试 reject 方法"""

    def setup_method(self):
        """每个测试前的设置"""
        self.mock_db = MagicMock()
        self.service = ApprovalEngineService(self.mock_db)

    def _create_mock_task(self):
        """创建模拟任务对象"""
        task = ApprovalTask(
            id=1,
            instance_id=1,
            node_id=10,
            assignee_id=100,
            status="PENDING",
        )
        
        instance = ApprovalInstance(
            id=1,
            instance_no="AP2602210001",
            status="IN_PROGRESS",
        )
        task.instance = instance
        
        node = ApprovalNodeDefinition(
            id=10,
            flow_id=1,
            node_name="审批节点",
        )
        task.node = node
        
        return task

    def test_reject_to_start_success(self):
        """测试驳回到发起人"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "张三"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._call_adapter_callback = MagicMock()
        self.service.notify.notify_rejected = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(False, None))

        result = self.service.reject(
            task_id=1,
            approver_id=100,
            comment="不符合要求",
            reject_to="START",
        )

        assert task.instance.status == "REJECTED"
        assert task.instance.completed_at is not None
        self.service._call_adapter_callback.assert_called_once_with(task.instance, "on_rejected")
        self.service.notify.notify_rejected.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_reject_requires_comment(self):
        """测试驳回必须提供原因"""
        with pytest.raises(ValueError, match="驳回原因不能为空"):
            self.service.reject(
                task_id=1,
                approver_id=100,
                comment="",
                reject_to="START",
            )

    def test_reject_to_previous_node(self):
        """测试驳回到上一节点"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "李四"

        prev_node = ApprovalNodeDefinition(
            id=9,
            flow_id=1,
            node_name="上一节点",
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._get_previous_node = MagicMock(return_value=prev_node)
        self.service._return_to_node = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(False, None))

        result = self.service.reject(
            task_id=1,
            approver_id=100,
            comment="需要修改",
            reject_to="PREV",
        )

        self.service._get_previous_node.assert_called_once()
        self.service._return_to_node.assert_called_once_with(task.instance, prev_node)

    def test_reject_to_previous_node_not_found(self):
        """测试驳回到上一节点但节点不存在"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "王五"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._get_previous_node = MagicMock(return_value=None)
        self.service.executor.process_approval = MagicMock(return_value=(False, None))

        result = self.service.reject(
            task_id=1,
            approver_id=100,
            comment="需要修改",
            reject_to="PREV",
        )

        assert task.instance.status == "REJECTED"
        assert task.instance.completed_at is not None

    def test_reject_to_specific_node_by_id(self):
        """测试驳回到指定节点ID"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "赵六"

        target_node = ApprovalNodeDefinition(
            id=8,
            flow_id=1,
            node_name="目标节点",
        )

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = approver

        mock_node_query = MagicMock()
        mock_node_query.filter.return_value.first.return_value = target_node

        self.mock_db.query.side_effect = [mock_user_query, mock_node_query]

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._return_to_node = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(False, None))

        result = self.service.reject(
            task_id=1,
            approver_id=100,
            comment="需要返工",
            reject_to="8",
        )

        self.service._return_to_node.assert_called_once_with(task.instance, target_node)

    def test_reject_to_specific_node_not_found(self):
        """测试驳回到指定节点但节点不存在"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "孙七"

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = approver

        mock_node_query = MagicMock()
        mock_node_query.filter.return_value.first.return_value = None

        self.mock_db.query.side_effect = [mock_user_query, mock_node_query]

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(False, None))

        result = self.service.reject(
            task_id=1,
            approver_id=100,
            comment="节点不存在",
            reject_to="999",
        )

        assert task.instance.status == "REJECTED"

    def test_reject_with_invalid_node_id(self):
        """测试驳回时提供无效的节点ID"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "周八"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(False, None))

        result = self.service.reject(
            task_id=1,
            approver_id=100,
            comment="无效节点",
            reject_to="INVALID",
        )

        assert task.instance.status == "REJECTED"

    def test_reject_logs_action_with_detail(self):
        """测试驳回记录日志包含详细信息"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "吴九"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = approver
        self.mock_db.query.return_value = mock_query

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._call_adapter_callback = MagicMock()
        self.service.notify.notify_rejected = MagicMock()
        self.service.executor.process_approval = MagicMock(return_value=(False, None))

        self.service.reject(
            task_id=1,
            approver_id=100,
            comment="不符合标准",
            reject_to="START",
        )

        call_args = self.service._log_action.call_args
        assert call_args[1]["action"] == "REJECT"
        assert call_args[1]["action_detail"]["reject_to"] == "START"


@pytest.mark.unit
class TestReturnTo:
    """测试 return_to 方法"""

    def setup_method(self):
        """每个测试前的设置"""
        self.mock_db = MagicMock()
        self.service = ApprovalEngineService(self.mock_db)

    def _create_mock_task(self):
        """创建模拟任务对象"""
        task = ApprovalTask(
            id=1,
            instance_id=1,
            node_id=10,
            assignee_id=100,
            status="PENDING",
        )
        
        instance = ApprovalInstance(
            id=1,
            instance_no="AP2602210001",
            status="IN_PROGRESS",
        )
        task.instance = instance
        
        return task

    def test_return_to_success(self):
        """测试成功退回到指定节点"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "陈十"

        target_node = ApprovalNodeDefinition(
            id=8,
            flow_id=1,
            node_name="目标节点",
        )

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = approver

        mock_node_query = MagicMock()
        mock_node_query.filter.return_value.first.return_value = target_node

        self.mock_db.query.side_effect = [mock_user_query, mock_node_query]

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._return_to_node = MagicMock()

        result = self.service.return_to(
            task_id=1,
            approver_id=100,
            target_node_id=8,
            comment="需要重新审核",
        )

        assert task.action == "RETURN"
        assert task.comment == "需要重新审核"
        assert task.status == "COMPLETED"
        assert task.completed_at is not None
        assert task.return_to_node_id == 8
        self.service._return_to_node.assert_called_once_with(task.instance, target_node)
        self.mock_db.commit.assert_called_once()

    def test_return_to_target_node_not_found(self):
        """测试退回时目标节点不存在"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "褚十一"

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = approver

        mock_node_query = MagicMock()
        mock_node_query.filter.return_value.first.return_value = None

        self.mock_db.query.side_effect = [mock_user_query, mock_node_query]

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._return_to_node = MagicMock()

        result = self.service.return_to(
            task_id=1,
            approver_id=100,
            target_node_id=999,
            comment="节点不存在",
        )

        # 即使节点不存在，任务状态也应该更新
        assert task.status == "COMPLETED"
        self.service._return_to_node.assert_not_called()

    def test_return_to_logs_action_detail(self):
        """测试退回记录日志包含详细信息"""
        task = self._create_mock_task()
        approver = MagicMock()
        approver.real_name = "卫十二"

        target_node = ApprovalNodeDefinition(id=8, flow_id=1)

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = approver

        mock_node_query = MagicMock()
        mock_node_query.filter.return_value.first.return_value = target_node

        self.mock_db.query.side_effect = [mock_user_query, mock_node_query]

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service._return_to_node = MagicMock()

        self.service.return_to(
            task_id=1,
            approver_id=100,
            target_node_id=8,
            comment="退回修改",
        )

        call_args = self.service._log_action.call_args
        assert call_args[1]["action"] == "RETURN"
        assert call_args[1]["action_detail"]["return_to_node_id"] == 8


@pytest.mark.unit
class TestTransfer:
    """测试 transfer 方法"""

    def setup_method(self):
        """每个测试前的设置"""
        self.mock_db = MagicMock()
        self.service = ApprovalEngineService(self.mock_db)

    def _create_mock_task(self, can_transfer=True):
        """创建模拟任务对象"""
        task = ApprovalTask(
            id=1,
            instance_id=1,
            node_id=10,
            assignee_id=100,
            status="PENDING",
            task_type="APPROVAL",
            task_order=1,
            due_at=datetime.now() + timedelta(days=3),
        )
        
        instance = ApprovalInstance(
            id=1,
            instance_no="AP2602210001",
            status="IN_PROGRESS",
        )
        task.instance = instance
        
        node = ApprovalNodeDefinition(
            id=10,
            flow_id=1,
            node_name="审批节点",
            can_transfer=can_transfer,
        )
        task.node = node
        
        return task

    def test_transfer_success(self):
        """测试成功转审"""
        task = self._create_mock_task()
        from_user = MagicMock()
        from_user.id = 100
        from_user.real_name = "张三"
        from_user.username = "zhangsan"

        to_user = MagicMock()
        to_user.id = 200
        to_user.real_name = "李四"
        to_user.username = "lisi"

        mock_queries = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=from_user)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=to_user)))),
        ]
        self.mock_db.query.side_effect = mock_queries

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.notify.notify_transferred = MagicMock()

        # 捕获新创建的任务
        added_tasks = []
        def mock_add(obj):
            added_tasks.append(obj)
        self.mock_db.add.side_effect = mock_add

        result = self.service.transfer(
            task_id=1,
            from_user_id=100,
            to_user_id=200,
            comment="转给李四处理",
        )

        # 原任务应标记为已转审
        assert task.status == "TRANSFERRED"
        assert task.completed_at is not None

        # 应创建新任务
        assert len(added_tasks) == 1
        new_task = added_tasks[0]
        assert new_task.assignee_id == 200
        assert new_task.assignee_name == "李四"
        assert new_task.assignee_type == "TRANSFERRED"
        assert new_task.original_assignee_id == 100
        assert new_task.status == "PENDING"

        self.service.notify.notify_transferred.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_transfer_node_not_allow_transfer(self):
        """测试节点不允许转审"""
        task = self._create_mock_task(can_transfer=False)

        self.service._get_and_validate_task = MagicMock(return_value=task)

        with pytest.raises(ValueError, match="当前节点不允许转审"):
            self.service.transfer(
                task_id=1,
                from_user_id=100,
                to_user_id=200,
            )

    def test_transfer_to_user_not_found(self):
        """测试转审目标用户不存在"""
        task = self._create_mock_task()
        from_user = MagicMock()
        from_user.real_name = "王五"

        mock_from_user_query = MagicMock()
        mock_from_user_query.filter.return_value.first.return_value = from_user

        mock_to_user_query = MagicMock()
        mock_to_user_query.filter.return_value.first.return_value = None

        self.mock_db.query.side_effect = [mock_from_user_query, mock_to_user_query]

        self.service._get_and_validate_task = MagicMock(return_value=task)

        with pytest.raises(ValueError, match="转审目标用户不存在: 200"):
            self.service.transfer(
                task_id=1,
                from_user_id=100,
                to_user_id=200,
            )

    def test_transfer_preserves_task_properties(self):
        """测试转审保留任务属性"""
        due_time = datetime.now() + timedelta(days=5)
        task = self._create_mock_task()
        task.due_at = due_time
        task.is_countersign = True

        from_user = MagicMock()
        from_user.real_name = "赵六"
        from_user.username = "zhaoliu"

        to_user = MagicMock()
        to_user.real_name = "孙七"
        to_user.username = "sunqi"

        mock_queries = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=from_user)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=to_user)))),
        ]
        self.mock_db.query.side_effect = mock_queries

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.notify.notify_transferred = MagicMock()

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        self.service.transfer(
            task_id=1,
            from_user_id=100,
            to_user_id=200,
        )

        new_task = added_tasks[0]
        assert new_task.due_at == due_time
        assert new_task.is_countersign == True
        assert new_task.task_type == task.task_type
        assert new_task.task_order == task.task_order

    def test_transfer_uses_username_when_no_real_name(self):
        """测试转审人没有真实姓名时使用用户名"""
        task = self._create_mock_task()
        from_user = MagicMock()
        from_user.real_name = None
        from_user.username = "user1"

        to_user = MagicMock()
        to_user.real_name = None
        to_user.username = "user2"

        mock_queries = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=from_user)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=to_user)))),
        ]
        self.mock_db.query.side_effect = mock_queries

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.notify.notify_transferred = MagicMock()

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        self.service.transfer(
            task_id=1,
            from_user_id=100,
            to_user_id=200,
        )

        new_task = added_tasks[0]
        assert new_task.assignee_name == "user2"


@pytest.mark.unit
class TestAddApprover:
    """测试 add_approver 方法"""

    def setup_method(self):
        """每个测试前的设置"""
        self.mock_db = MagicMock()
        self.service = ApprovalEngineService(self.mock_db)

    def _create_mock_task(self, can_add_approver=True):
        """创建模拟任务对象"""
        task = ApprovalTask(
            id=1,
            instance_id=1,
            node_id=10,
            assignee_id=100,
            status="PENDING",
            task_order=1,
            due_at=datetime.now() + timedelta(days=3),
        )
        
        instance = ApprovalInstance(
            id=1,
            instance_no="AP2602210001",
            status="IN_PROGRESS",
        )
        task.instance = instance
        
        node = ApprovalNodeDefinition(
            id=10,
            flow_id=1,
            node_name="审批节点",
            can_add_approver=can_add_approver,
        )
        task.node = node
        
        return task

    def test_add_approver_after_success(self):
        """测试后加签成功"""
        task = self._create_mock_task()
        operator = MagicMock()
        operator.id = 100
        operator.real_name = "张三"

        approver1 = MagicMock()
        approver1.id = 201
        approver1.real_name = "李四"
        approver1.username = "lisi"

        approver2 = MagicMock()
        approver2.id = 202
        approver2.real_name = "王五"
        approver2.username = "wangwu"

        mock_queries = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver1)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver2)))),
        ]
        self.mock_db.query.side_effect = mock_queries

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.notify.notify_add_approver = MagicMock()

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        result = self.service.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201, 202],
            position="AFTER",
            comment="请帮忙审核",
        )

        # 应创建2个新任务
        assert len(added_tasks) == 2
        assert len(result) == 2

        # 后加签的任务初始状态应为SKIPPED
        assert added_tasks[0].status == "SKIPPED"
        assert added_tasks[1].status == "SKIPPED"
        assert added_tasks[0].assignee_type == "ADDED_AFTER"
        assert added_tasks[1].assignee_type == "ADDED_AFTER"

        # 原任务状态不变
        assert task.status == "PENDING"

        # 后加签不应通知（状态为SKIPPED）
        assert self.service.notify.notify_add_approver.call_count == 0

    def test_add_approver_before_success(self):
        """测试前加签成功"""
        task = self._create_mock_task()
        operator = MagicMock()
        operator.real_name = "赵六"

        approver = MagicMock()
        approver.id = 201
        approver.real_name = "孙七"
        approver.username = "sunqi"

        mock_queries = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver)))),
        ]
        self.mock_db.query.side_effect = mock_queries

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.notify.notify_add_approver = MagicMock()

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        result = self.service.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201],
            position="BEFORE",
            comment="请先审核",
        )

        assert len(added_tasks) == 1
        
        # 前加签的任务应为PENDING
        new_task = added_tasks[0]
        assert new_task.status == "PENDING"
        assert new_task.assignee_type == "ADDED_BEFORE"
        assert new_task.assignee_id == 201

        # 原任务应变为SKIPPED
        assert task.status == "SKIPPED"

        # 应通知新审批人
        self.service.notify.notify_add_approver.assert_called_once()

    def test_add_approver_node_not_allow(self):
        """测试节点不允许加签"""
        task = self._create_mock_task(can_add_approver=False)

        self.service._get_and_validate_task = MagicMock(return_value=task)

        with pytest.raises(ValueError, match="当前节点不允许加签"):
            self.service.add_approver(
                task_id=1,
                operator_id=100,
                approver_ids=[201],
            )

    def test_add_approver_skip_nonexistent_users(self):
        """测试加签时跳过不存在的用户"""
        task = self._create_mock_task()
        operator = MagicMock()
        operator.real_name = "周八"

        approver1 = MagicMock()
        approver1.id = 201
        approver1.real_name = "吴九"
        approver1.username = "wujiu"

        # 第二个用户不存在
        mock_queries = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver1)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
        ]
        self.mock_db.query.side_effect = mock_queries

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.notify.notify_add_approver = MagicMock()

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        result = self.service.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201, 999],  # 999不存在
            position="AFTER",
        )

        # 只应创建1个任务
        assert len(added_tasks) == 1
        assert added_tasks[0].assignee_id == 201

    def test_add_approver_logs_action_detail(self):
        """测试加签记录日志包含详细信息"""
        task = self._create_mock_task()
        operator = MagicMock()
        operator.real_name = "郑十"

        approver = MagicMock()
        approver.id = 201
        approver.real_name = "冯十一"
        approver.username = "feng11"

        mock_queries = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver)))),
        ]
        self.mock_db.query.side_effect = mock_queries

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.notify.notify_add_approver = MagicMock()

        self.mock_db.add.side_effect = lambda obj: None

        self.service.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201],
            position="BEFORE",
        )

        call_args = self.service._log_action.call_args
        assert call_args[1]["action"] == "ADD_APPROVER_BEFORE"
        assert call_args[1]["action_detail"]["approver_ids"] == [201]
        assert call_args[1]["action_detail"]["position"] == "BEFORE"

    def test_add_approver_multiple_preserves_task_properties(self):
        """测试批量加签保留任务属性"""
        due_time = datetime.now() + timedelta(days=7)
        task = self._create_mock_task()
        task.due_at = due_time

        operator = MagicMock()
        operator.real_name = "陈十二"

        approver1 = MagicMock()
        approver1.id = 201
        approver1.real_name = "褚十三"
        approver1.username = "chu13"

        approver2 = MagicMock()
        approver2.id = 202
        approver2.real_name = "卫十四"
        approver2.username = "wei14"

        mock_queries = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver1)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=approver2)))),
        ]
        self.mock_db.query.side_effect = mock_queries

        self.service._get_and_validate_task = MagicMock(return_value=task)
        self.service._log_action = MagicMock()
        self.service.notify.notify_add_approver = MagicMock()

        added_tasks = []
        self.mock_db.add.side_effect = lambda obj: added_tasks.append(obj)

        self.service.add_approver(
            task_id=1,
            operator_id=100,
            approver_ids=[201, 202],
            position="BEFORE",
        )

        # 所有新任务都应保留截止时间
        for new_task in added_tasks:
            assert new_task.due_at == due_time
            assert new_task.node_id == task.node_id
            assert new_task.instance_id == task.instance_id
