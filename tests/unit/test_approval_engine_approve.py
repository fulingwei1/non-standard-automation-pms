# -*- coding: utf-8 -*-
"""
approval_engine/engine/approve.py 单元测试

测试审批处理功能（通过、驳回、转审、加签）
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.engine.approve import ApprovalProcessMixin


@pytest.mark.unit
class TestApprovalProcessMixinInit:
    """测试 ApprovalProcessMixin 初始化"""

    def test_init_with_core(self):
        """测试使用ApprovalEngineCore初始化"""
        mock_db = MagicMock()
        mock_core = MagicMock()

        mixin = ApprovalProcessMixin(mock_core)

        assert mixin.core is not None
        assert hasattr(mixin, "approve")
        assert hasattr(mixin, "reject")


@pytest.mark.unit
class TestApprove:
    """测试 approve 方法"""

    def test_approve_success(self):
        """测试审批通过成功"""
        mock_db = MagicMock()
        mock_core = MagicMock()

        mixin = ApprovalProcessMixin(mock_core)

        # Mock task and instance
        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.status = "PENDING"
        mock_task.instance = MagicMock()
        mock_task.instance.id = 100
        mock_task.instance.current_node_id = 5

        # Mock approver
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "Test User"

        # Mock query and update
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_query.filter.return_value.update.return_value = MagicMock()

        mock_db.query.return_value = mock_query

        # Mock process_approval to return True
        with patch.object(mixin, "process_approval") as mock_process:
            mock_process.return_value = True

            result = mixin.approve(
            task_id=10,
            approver_id=1,
            comment="Approved",
            )

            assert result.id == 10
            assert result.status == "APPROVED"
            mock_process.assert_called_once()
            mock_db.flush.assert_called_once()

    def test_approve_with_comment(self):
        """测试带评论的审批通过"""
        mock_db = MagicMock()
        mock_core = MagicMock()

        mixin = ApprovalProcessMixin(mock_core)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.status = "PENDING"
        mock_task.instance = MagicMock()
        mock_task.instance.id = 100
        mock_task.instance.current_node_id = 5

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_query.filter.return_value.update.return_value = MagicMock()
        mock_db.query.return_value = mock_query

        with patch.object(mixin, "process_approval") as mock_process:
            mock_process.return_value = True

            result = mixin.approve(
            task_id=10,
            approver_id=1,
            comment="Good work!",
            )

            assert result.status == "APPROVED"
            assert result.approved_at is not None

    def test_approve_with_attachments(self):
        """测试带附件的审批通过"""
        mock_db = MagicMock()
        mock_core = MagicMock()

        mixin = ApprovalProcessMixin(mock_core)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.status = "PENDING"
        mock_task.instance = MagicMock()
        mock_task.instance.id = 100
        mock_task.instance.current_node_id = 5

        attachments = [{"name": "file.pdf", "url": "http://example.com/file.pdf"}]

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_query.filter.return_value.update.return_value = MagicMock()
        mock_db.query.return_value = mock_query

        with patch.object(mixin, "process_approval") as mock_process:
            mock_process.return_value = True

            result = mixin.approve(
            task_id=10,
            approver_id=1,
            attachments=attachments,
            )

            assert result.status == "APPROVED"
            # Check attachments were passed to process_approval
        assert mock_process.call_args[0][1].get("attachments") == attachments


@pytest.mark.unit
class TestReject:
    """测试 reject 方法"""

    def test_reject_success(self):
        """测试驳回成功"""
        mock_db = MagicMock()
        mock_core = MagicMock()

        mixin = ApprovalProcessMixin(mock_core)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.status = "PENDING"
        mock_task.instance = MagicMock()
        mock_task.instance.id = 100
        mock_task.instance.current_node_id = 5

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.name = "Test User"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_query.filter.return_value.update.return_value = MagicMock()
        mock_db.query.return_value = mock_query

        with patch.object(mixin, "process_approval") as mock_process:
            mock_process.return_value = True

            result = mixin.reject(
            task_id=10,
            approver_id=1,
            comment="Needs revision",
            reject_to="START",
            )

            assert result.status == "REJECTED"
            assert result.rejected_at is not None

    def test_reject_with_attachments(self):
        """测试带附件的驳回"""
        mock_db = MagicMock()
        mock_core = MagicMock()

        mixin = ApprovalProcessMixin(mock_core)

        mock_task = MagicMock()
        mock_task.id = 10
        mock_task.instance_id = 100
        mock_task.node_id = 5
        mock_task.status = "PENDING"

        attachments = [{"name": "error.pdf", "url": "http://example.com/error.pdf"}]

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_query.filter.return_value.update.return_value = MagicMock()
        mock_db.query.return_value = mock_query

        with patch.object(mixin, "process_approval") as mock_process:
            mock_process.return_value = True

            result = mixin.reject(
            task_id=10,
            approver_id=1,
            attachments=attachments,
            comment="Error in attachment",
            )

            assert result.status == "REJECTED"
            mock_process.call_args[0][1].get("attachments") == attachments


@pytest.mark.unit
class TestApprovalProcessIntegration:
    """集成测试"""

    def test_approve_and_reject_callable(self):
        """测试approve和reject方法可调用"""
        mock_db = MagicMock()
        mock_core = MagicMock()
        mixin = ApprovalProcessMixin(mock_core)

        assert hasattr(mixin, "approve")
        assert hasattr(mixin, "reject")
