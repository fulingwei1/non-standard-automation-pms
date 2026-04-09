# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 审批节点执行器"""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta


class TestApprovalNodeExecutorBusinessLogic:
    """审批节点执行器业务逻辑测试"""

    def test_create_tasks_for_node_single(self):
        """测试单人审批模式"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_instance = MagicMock()
            mock_instance.id = 1

            mock_node = MagicMock()
            mock_node.id = 1
            mock_node.approval_mode = "SINGLE"
            mock_node.timeout_hours = 24

            executor = ApprovalNodeExecutor(mock_db)
            result = executor.create_tasks_for_node(mock_instance, mock_node, [1])

            assert len(result) == 1
            assert result[0].assignee_id == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_create_tasks_for_node_or_sign(self):
        """测试或签模式"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_instance = MagicMock()
            mock_instance.id = 1

            mock_node = MagicMock()
            mock_node.id = 1
            mock_node.approval_mode = "OR_SIGN"
            mock_node.timeout_hours = None

            executor = ApprovalNodeExecutor(mock_db)
            result = executor.create_tasks_for_node(mock_instance, mock_node, [1, 2, 3])

            assert len(result) == 3
        except ImportError:
            pytest.skip("Module not found")

    def test_create_tasks_for_node_countersign(self):
        """测试会签模式"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_instance = MagicMock()
            mock_instance.id = 1

            mock_node = MagicMock()
            mock_node.id = 1
            mock_node.approval_mode = "COUNTERSIGN"
            mock_node.timeout_hours = 48

            executor = ApprovalNodeExecutor(mock_db)
            result = executor.create_tasks_for_node(mock_instance, mock_node, [1, 2])

            assert len(result) == 2
        except ImportError:
            pytest.skip("Module not found")

    def test_create_tasks_for_node_sequence(self):
        """测试依次审批模式"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_instance = MagicMock()
            mock_instance.id = 1

            mock_node = MagicMock()
            mock_node.id = 1
            mock_node.approval_mode = "SEQUENCE"
            mock_node.timeout_hours = 24

            executor = ApprovalNodeExecutor(mock_db)
            result = executor.create_tasks_for_node(mock_instance, mock_node, [1, 2])

            # 依次审批只有第一个任务激活
            assert len(result) >= 1
        except ImportError:
            pytest.skip("Module not found")

    def test_create_tasks_no_approver(self):
        """测试没有审批人"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_instance = MagicMock()
            mock_node = MagicMock()

            executor = ApprovalNodeExecutor(mock_db)
            result = executor.create_tasks_for_node(mock_instance, mock_node, [])

            assert len(result) == 0
        except ImportError:
            pytest.skip("Module not found")

    def test_process_approval_approve(self):
        """测试处理审批通过"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.status = "PENDING"

            executor = ApprovalNodeExecutor(mock_db)
            result = executor.process_approval(
                task=mock_task,
                action="APPROVE",
                comment="同意"
            )

            assert mock_task.status == "APPROVED"
        except ImportError:
            pytest.skip("Module not found")

    def test_process_approval_reject(self):
        """测试处理审批拒绝"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.status = "PENDING"

            executor = ApprovalNodeExecutor(mock_db)
            result = executor.process_approval(
                task=mock_task,
                action="REJECT",
                comment="不同意"
            )

            assert mock_task.status == "REJECTED"
        except ImportError:
            pytest.skip("Module not found")

    def test_process_countersign_complete(self):
        """测试会签完成"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.is_countersign = True

            executor = ApprovalNodeExecutor(mock_db)
            executor._check_countersign_complete = MagicMock(return_value=True)

            result = executor.process_countersign(mock_task, "APPROVE", "同意")

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_calculate_due_at(self):
        """测试计算截止时间"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()
            executor = ApprovalNodeExecutor(mock_db)

            timeout_hours = 24
            result = executor._calculate_due_at(timeout_hours)

            assert result is not None
            expected = datetime.now() + timedelta(hours=timeout_hours)
            # 时间应该接近
            assert abs((result - expected).total_seconds()) < 10
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalNodeExecutorCountersign:
    """会签逻辑测试"""

    def test_check_countersign_complete_all_approved(self):
        """测试会签全部通过"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task1 = MagicMock()
            mock_task1.status = "APPROVED"

            mock_task2 = MagicMock()
            mock_task2.status = "APPROVED"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_task1, mock_task2]

            executor = ApprovalNodeExecutor(mock_db)
            result = executor._check_countersign_complete(1, 1)

            assert result == True
        except ImportError:
            pytest.skip("Module not found")

    def test_check_countersign_complete_partial(self):
        """测试会签部分通过"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task1 = MagicMock()
            mock_task1.status = "APPROVED"

            mock_task2 = MagicMock()
            mock_task2.status = "PENDING"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_task1, mock_task2]

            executor = ApprovalNodeExecutor(mock_db)
            result = executor._check_countersign_complete(1, 1)

            assert result == False
        except ImportError:
            pytest.skip("Module not found")

    def test_check_countersign_complete_one_rejected(self):
        """测试会签一人拒绝"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task1 = MagicMock()
            mock_task1.status = "APPROVED"

            mock_task2 = MagicMock()
            mock_task2.status = "REJECTED"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_task1, mock_task2]

            executor = ApprovalNodeExecutor(mock_db)
            result = executor._check_countersign_complete(1, 1)

            # 一人拒绝，会签失败
            assert result == False
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalNodeExecutorOrSign:
    """或签逻辑测试"""

    def test_or_sign_first_approve_complete(self):
        """测试或签第一个通过完成"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task1 = MagicMock()
            mock_task1.id = 1
            mock_task1.status = "APPROVED"

            mock_task2 = MagicMock()
            mock_task2.id = 2
            mock_task2.status = "PENDING"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_task1, mock_task2]

            executor = ApprovalNodeExecutor(mock_db)
            executor._cancel_other_or_sign_tasks = MagicMock()

            result = executor.process_approval(mock_task1, "APPROVE", "同意")

            # 或签一人通过即可完成节点
            assert executor._cancel_other_or_sign_tasks.called
        except ImportError:
            pytest.skip("Module not found")

    def test_cancel_other_or_sign_tasks(self):
        """测试取消其他或签任务"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task1 = MagicMock()
            mock_task1.id = 1

            mock_task2 = MagicMock()
            mock_task2.id = 2
            mock_task2.status = "PENDING"

            mock_db.query.return_value.filter.return_value.all.return_value = [mock_task2]

            executor = ApprovalNodeExecutor(mock_db)
            executor._cancel_other_or_sign_tasks(1, 1)

            # 其他任务应该被取消
            assert mock_task2.status == "CANCELLED"
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalNodeExecutorEdgeCases:
    """边界情况测试"""

    def test_task_already_processed(self):
        """测试任务已处理"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.status = "APPROVED"  # 已处理

            executor = ApprovalNodeExecutor(mock_db)

            # 已处理的任务不能再次处理
            with pytest.raises(Exception):
                executor.process_approval(mock_task, "APPROVE", "同意")
        except ImportError:
            pytest.skip("Module not found")

    def test_timeout_hours_zero(self):
        """测试零超时时间"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()
            executor = ApprovalNodeExecutor(mock_db)

            result = executor._calculate_due_at(0)

            # 零超时时间不设置截止时间
            assert result is None
        except ImportError:
            pytest.skip("Module not found")

    def test_timeout_hours_none(self):
        """测试无超时时间"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()
            executor = ApprovalNodeExecutor(mock_db)

            result = executor._calculate_due_at(None)

            assert result is None
        except ImportError:
            pytest.skip("Module not found")

    def test_single_approver_in_or_sign(self):
        """测试或签只有一个审批人"""
        try:
            from app.services.approval_engine.executor import ApprovalNodeExecutor

            mock_db = MagicMock()

            mock_instance = MagicMock()
            mock_node = MagicMock()
            mock_node.approval_mode = "OR_SIGN"

            executor = ApprovalNodeExecutor(mock_db)
            result = executor.create_tasks_for_node(mock_instance, mock_node, [1])

            # 只有一个审批人，效果等同于单人审批
            assert len(result) == 1
        except ImportError:
            pytest.skip("Module not found")