# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch


class TestApprovalWorkflowService:
    def setup_method(self):
        self.db = MagicMock()
        from app.services.approval_workflow_service import ApprovalWorkflowService
        self.service = ApprovalWorkflowService(self.db)

    @patch("app.services.approval_workflow_service.ApprovalRecordStatusEnum")
    def test_start_approval_returns_existing(self, mock_enum):
        mock_enum.PENDING = "PENDING"
        existing = MagicMock()
        self.db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = existing
        result = self.service.start_approval("QUOTE", 1, 10)
        assert result == existing

    @patch("app.services.approval_workflow_service.ApprovalRecordStatusEnum")
    def test_start_approval_creates_new(self, mock_enum):
        mock_enum.PENDING = "PENDING"
        self.db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None

        with patch("app.models.sales.workflow.ApprovalRecord") as MockRecord:
            instance = MagicMock()
            MockRecord.return_value = instance
            result = self.service.start_approval("QUOTE", 1, 10)

        self.db.add.assert_called()
        self.db.flush.assert_called()

    @patch("app.services.approval_workflow_service.ApprovalRecordStatusEnum")
    def test_approve_step_success(self, mock_enum):
        mock_enum.APPROVED = "APPROVED"
        record = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = record
        result = self.service.approve_step(1, 10, "ok")
        assert result.status == "APPROVED"
        self.db.commit.assert_called()

    @patch("app.services.approval_workflow_service.ApprovalRecordStatusEnum")
    def test_approve_step_not_found(self, mock_enum):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            self.service.approve_step(999, 10)

    @patch("app.services.approval_workflow_service.ApprovalRecordStatusEnum")
    def test_reject_step_success(self, mock_enum):
        mock_enum.REJECTED = "REJECTED"
        record = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = record
        result = self.service.reject_step(1, 10, "no")
        assert result.status == "REJECTED"

    @patch("app.services.approval_workflow_service.ApprovalRecordStatusEnum")
    def test_reject_step_not_found(self, mock_enum):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            self.service.reject_step(999, 10)

    @patch("app.services.approval_workflow_service.ApprovalRecordStatusEnum")
    def test_withdraw_approval_success(self, mock_enum):
        mock_enum.CANCELLED = "CANCELLED"
        record = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = record
        result = self.service.withdraw_approval(1, 10)
        assert result.status == "CANCELLED"

    @patch("app.services.approval_workflow_service.ApprovalRecordStatusEnum")
    def test_withdraw_not_found(self, mock_enum):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            self.service.withdraw_approval(999, 10)

    def test_validate_approver_always_true(self):
        assert self.service._validate_approver(1, 1) is True

    def test_select_workflow_no_workflows(self):
        self.db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = self.service._select_workflow_by_routing("QUOTE")
        assert result is None

    def test_select_workflow_returns_default(self):
        wf = MagicMock()
        wf.routing_rules = {"default": True}
        self.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [wf]
        result = self.service._select_workflow_by_routing("QUOTE")
        assert result == wf
