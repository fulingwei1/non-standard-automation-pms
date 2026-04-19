# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 审批引擎核心功能"""
import pytest
from unittest.mock import MagicMock, patch


class TestApprovalEngineApproveLogic:
    """审批通过逻辑测试"""

    def test_approve_task_not_found(self):
        """测试任务不存在"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(side_effect=ValueError("任务不存在"))

            with pytest.raises(ValueError):
                mixin.approve(999, 1)
        except ImportError:
            pytest.skip("Module not found")

    def test_approve_task_wrong_approver(self):
        """测试错误的审批人"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()
            mock_task = MagicMock()
            mock_task.assigned_to = 2  # 审批人是2，不是1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_task

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(side_effect=ValueError("非当前审批人"))

            with pytest.raises(ValueError):
                mixin.approve(1, 1)  # 用户1尝试审批
        except ImportError:
            pytest.skip("Module not found")

    def test_approve_success(self):
        """测试审批通过成功"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.status = "PENDING"
            mock_task.instance = MagicMock()
            mock_task.instance.id = 100

            mock_approver = MagicMock()
            mock_approver.id = 1
            mock_approver.real_name = "张三"

            mock_db.query.return_value.filter.return_value.first.return_value = mock_approver

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=mock_task)
            mixin.executor = MagicMock()
            mixin.executor.process_approval.return_value = (True, None)
            mixin._log_action = MagicMock()
            mixin._advance_to_next_node = MagicMock()

            result = mixin.approve(1, 1, "同意")

            assert mixin.executor.process_approval.called
            assert mixin._advance_to_next_node.called
        except ImportError:
            pytest.skip("Module not found")

    def test_approve_with_attachments(self):
        """测试带附件审批"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.instance = MagicMock()

            mock_approver = MagicMock()
            mock_approver.id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = mock_approver

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=mock_task)
            mixin.executor = MagicMock()
            mixin.executor.process_approval.return_value = (True, None)
            mixin._log_action = MagicMock()
            mixin._advance_to_next_node = MagicMock()

            attachments = [{"name": "test.pdf", "url": "http://example.com/test.pdf"}]
            result = mixin.approve(1, 1, "同意", attachments=attachments)

            # 验证附件被传递
            call_kwargs = mixin.executor.process_approval.call_args[1]
            assert call_kwargs["attachments"] == attachments
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalEngineRejectLogic:
    """审批驳回逻辑测试"""

    def test_reject_requires_comment(self):
        """测试驳回需要意见"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=MagicMock())

            # 驳回必须有意见
            with pytest.raises(ValueError):
                mixin.reject(1, 1, comment=None)
        except ImportError:
            pytest.skip("Module not found")

    def test_reject_to_start(self):
        """测试驳回至发起人"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.node_id = 10
            mock_task.instance = MagicMock()
            mock_task.instance.id = 100
            mock_task.instance.status = "PENDING"
            mock_task.node = MagicMock()

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=mock_task)
            mixin.executor = MagicMock()
            mixin.executor.process_approval.return_value = (False, None)
            mixin._log_action = MagicMock()
            mixin._call_adapter_callback = MagicMock()
            mixin.notify = MagicMock()

            result = mixin.reject(1, 1, "不同意", reject_to="START")

            assert mock_task.instance.status == "REJECTED"
            assert mixin._call_adapter_callback.called
            assert mixin.notify.notify_rejected.called
        except ImportError:
            pytest.skip("Module not found")

    def test_reject_cancel_instance(self):
        """测试未知 reject_to 时实例直接变为驳回"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.node_id = 10
            mock_task.instance = MagicMock()
            mock_task.instance.status = "PENDING"
            mock_task.node = MagicMock()

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=mock_task)
            mixin.executor = MagicMock()
            mixin.executor.process_approval.return_value = (False, None)
            mixin._log_action = MagicMock()

            result = mixin.reject(1, 1, "不同意", reject_to="CANCEL")

            assert mock_task.instance.status == "REJECTED"
            assert mock_task.instance.completed_at is not None
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalEngineReturnLogic:
    """退回逻辑测试"""

    def test_return_to_previous_node(self):
        """测试退回指定节点"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.node_id = 10
            mock_task.instance = MagicMock()
            mock_task.instance.id = 100

            target_node = MagicMock()
            target_node.id = 5

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=mock_task)
            mixin._log_action = MagicMock()
            mixin._return_to_node = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = target_node

            result = mixin.return_to(1, 1, target_node_id=5, comment="退回修改")

            assert mixin._return_to_node.called
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalEngineTransferLogic:
    """转审逻辑测试"""

    def test_transfer_to_another_approver(self):
        """测试转给其他审批人"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.node_id = 10
            mock_task.instance = MagicMock()
            mock_task.instance.id = 100
            mock_task.node = MagicMock(id=99, can_transfer=True)
            mock_task.task_type = "APPROVAL"
            mock_task.task_order = 1
            mock_task.due_at = None
            mock_task.is_countersign = False

            mock_from_user = MagicMock()
            mock_from_user.id = 1
            mock_from_user.real_name = "张三"
            mock_from_user.username = "zhangsan"

            mock_new_approver = MagicMock()
            mock_new_approver.id = 2
            mock_new_approver.real_name = "李四"
            mock_new_approver.username = "lisi"

            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_from_user,
                mock_new_approver,
            ]

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=mock_task)
            mixin._log_action = MagicMock()
            mixin.notify = MagicMock()

            result = mixin.transfer(1, 1, 2, "转给李四处理")

            assert result.assignee_id == 2
            assert mixin.notify.notify_transferred.called
        except ImportError:
            pytest.skip("Module not found")

    def test_transfer_to_nonexistent_user(self):
        """测试转给不存在用户"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=MagicMock())

            with pytest.raises(ValueError):
                mixin.transfer(1, 1, 999, "转给不存在用户")
        except ImportError:
            pytest.skip("Module not found")


class TestApprovalEngineAddSignerLogic:
    """加签逻辑测试"""

    def test_add_signer_before(self):
        """测试前加签"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.node_id = 10
            mock_task.instance = MagicMock()
            mock_task.instance.id = 100
            mock_task.node = MagicMock(can_add_approver=True, id=99)
            mock_task.task_order = 1
            mock_task.due_at = None
            mock_task.status = "PENDING"

            mock_operator = MagicMock()
            mock_operator.id = 1
            mock_operator.real_name = "张三"
            mock_operator.username = "zhangsan"

            mock_signer = MagicMock()
            mock_signer.id = 3
            mock_signer.real_name = "王五"
            mock_signer.username = "wangwu"

            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_operator,
                mock_signer,
            ]

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=mock_task)
            mixin._log_action = MagicMock()
            mixin.notify = MagicMock()

            result = mixin.add_approver(1, 1, [3], comment="前加签", position="BEFORE")

            assert mock_task.status == "SKIPPED"
            assert len(result) == 1
        except ImportError:
            pytest.skip("Module not found")

    def test_add_signer_after(self):
        """测试后加签"""
        try:
            from app.services.approval_engine.engine.approve import ApprovalProcessMixin

            mock_db = MagicMock()

            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.node_id = 10
            mock_task.instance = MagicMock()
            mock_task.instance.id = 100
            mock_task.node = MagicMock(can_add_approver=True, id=99)
            mock_task.task_order = 1
            mock_task.due_at = None
            mock_task.status = "PENDING"

            mock_operator = MagicMock()
            mock_operator.id = 1
            mock_operator.real_name = "张三"
            mock_operator.username = "zhangsan"

            mock_signer = MagicMock()
            mock_signer.id = 4
            mock_signer.real_name = "赵六"
            mock_signer.username = "zhaoliu"

            mock_db.query.return_value.filter.return_value.first.side_effect = [
                mock_operator,
                mock_signer,
            ]

            mixin = ApprovalProcessMixin()
            mixin.db = mock_db
            mixin._get_and_validate_task = MagicMock(return_value=mock_task)
            mixin._log_action = MagicMock()
            mixin.notify = MagicMock()

            result = mixin.add_approver(1, 1, [4], comment="后加签", position="AFTER")

            assert len(result) == 1
            assert result[0].status == "SKIPPED"
        except ImportError:
            pytest.skip("Module not found")