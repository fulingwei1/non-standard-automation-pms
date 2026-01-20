# -*- coding: utf-8 -*-
"""
Tests for approval_workflow_service
Covers: app/services/approval_workflow_service.py
Coverage Target: 0% -> 50%+
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


class TestApprovalWorkflowService:
    """审批工作流服务测试"""

    @pytest.fixture
    def service(self, db_session: Session):
        from app.services.approval_workflow_service import ApprovalWorkflowService
        return ApprovalWorkflowService(db_session)

    @pytest.fixture
    def mock_workflow(self):
        """模拟审批工作流"""
        mock = MagicMock()
        mock.id = 1
        mock.task_id = 1
        mock.workflow_type = "PROJECT_APPROVAL"
        mock.current_approver_id = 1
        mock.current_step = 1
        mock.total_steps = 3
        mock.status = "PENDING"
        mock.created_at = datetime.now()
        return mock

    @pytest.fixture
    def mock_approver(self):
        """模拟审批人"""
        mock = MagicMock()
        mock.id = 1
        mock.username = "approver"
        mock.real_name = "审批人"
        return mock

    def test_init_service(self, service, db_session: Session):
        """测试服务初始化"""
        from app.services.approval_workflow_service import ApprovalWorkflowService
        svc = ApprovalWorkflowService(db_session)
        assert svc.db == db_session

    def test_create_workflow(self, service, db_session: Session, mock_approver):
        """测试创建审批工作流"""
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.add.return_value = None

        result = service.create_workflow(
            task_id=1,
            workflow_type="PROJECT_APPROVAL",
            approver_ids=[1, 2, 3]
        )

        assert result is not None
        assert result.workflow_type == "PROJECT_APPROVAL"

    def test_submit_for_approval(self, service, db_session: Session, mock_workflow):
        """测试提交审批"""
        db_session.query.return_value.filter.return_value.first.return_value = mock_workflow

        result = service.submit_for_approval(workflow_id=1, submitted_by=1)

        assert result is not None
        assert result.status == "IN_PROGRESS"

    def test_approve_step(self, service, db_session: Session, mock_workflow, mock_approver):
        """测试审批步骤"""
        mock_workflow.status = "IN_PROGRESS"
        mock_workflow.current_step = 1
        mock_workflow.total_steps = 3

        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_workflow, mock_approver
        ]

        result = service.approve_step(
            workflow_id=1,
            approver_id=1,
            comment="审批通过"
        )

        assert result is not None
        assert result.status == "IN_PROGRESS"

    def test_reject_step(self, service, db_session: Session, mock_workflow, mock_approver):
        """测试拒绝步骤"""
        mock_workflow.status = "IN_PROGRESS"
        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_workflow, mock_approver
        ]

        result = service.reject_step(
            workflow_id=1,
            approver_id=1,
            reason="不符合要求"
        )

        assert result is not None
        assert result.status == "REJECTED"

    def test_get_pending_approvals(self, service, db_session: Session, mock_workflow):
        """测试获取待审批列表"""
        mock_workflow.status = "PENDING"
        db_session.query.return_value.filter.return_value.all.return_value = [mock_workflow]

        result = service.get_pending_approvals(approver_id=1)

        assert result == [mock_workflow]

    def test_get_workflow_history(self, service, db_session: Session):
        """测试获取工作流历史"""
        mock_history = [MagicMock(), MagicMock()]
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_history

        result = service.get_workflow_history(workflow_id=1)

        assert result == mock_history

    def test_cancel_workflow(self, service, db_session: Session, mock_workflow):
        """测试取消工作流"""
        db_session.query.return_value.filter.return_value.first.return_value = mock_workflow

        result = service.cancel_workflow(workflow_id=1, cancelled_by=1)

        assert result is True
        assert mock_workflow.status == "CANCELLED"

    def test_cancel_workflow_not_found(self, service, db_session: Session):
        """测试取消不存在的工作流"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = service.cancel_workflow(workflow_id=999, cancelled_by=1)

        assert result is False

    def test_check_workflow_complete(self, service, db_session: Session, mock_workflow):
        """测试检查工作流是否完成"""
        mock_workflow.status = "IN_PROGRESS"
        mock_workflow.current_step = 3
        mock_workflow.total_steps = 3

        db_session.query.return_value.filter.return_value.first.return_value = mock_workflow

        result = service.check_workflow_complete(workflow_id=1)

        assert result is True
        assert mock_workflow.status == "COMPLETED"

    def test_get_workflow_status(self, service, db_session: Session, mock_workflow):
        """测试获取工作流状态"""
        db_session.query.return_value.filter.return_value.first.return_value = mock_workflow

        result = service.get_workflow_status(workflow_id=1)

        assert result == mock_workflow


class TestApprovalWorkflowServiceNotifications:
    """审批工作流通知测试"""

    @pytest.fixture
    def service(self, db_session: Session):
        from app.services.approval_workflow_service import ApprovalWorkflowService
        return ApprovalWorkflowService(db_session)

    def test_notify_next_approver(self, service, db_session: Session, mock_workflow, mock_approver):
        """测试通知下一审批人"""
        mock_workflow.status = "IN_PROGRESS"
        mock_workflow.current_step = 1
        mock_workflow.total_steps = 3

        db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_workflow, mock_approver
        ]

        with patch('app.services.approval_workflow_service.NotificationService') as mock_ns:
            mock_ns.return_value.send_notification.return_value = True

            result = service.notify_next_approver(workflow_id=1)

            assert result is True

    def test_notify_submitter_approved(self, service, db_session: Session, mock_workflow):
        """测试通知提交人审批通过"""
        mock_workflow.status = "COMPLETED"

        with patch('app.services.approval_workflow_service.NotificationService') as mock_ns:
            mock_ns.return_value.send_notification.return_value = True

            result = service.notify_submitter(workflow_id=1, approved=True)

            assert result is True

    def test_notify_submitter_rejected(self, service, db_session: Session, mock_workflow):
        """测试通知提交人审批拒绝"""
        mock_workflow.status = "REJECTED"

        with patch('app.services.approval_workflow_service.NotificationService') as mock_ns:
            mock_ns.return_value.send_notification.return_value = True

            result = service.notify_submitter(workflow_id=1, approved=False, reason="不符合要求")

            assert result is True
