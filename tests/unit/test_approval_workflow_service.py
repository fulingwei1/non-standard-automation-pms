# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

import pytest


class TestApprovalWorkflowService:
    def setup_method(self):
        self.db = MagicMock()
        from app.services.approval_workflow_service import ApprovalWorkflowService

        self.service = ApprovalWorkflowService(self.db)

    def test_start_approval_returns_existing(self):
        existing = MagicMock()
        self.db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = (
            existing
        )
        result = self.service.start_approval("QUOTE", 1, 10)
        assert result == existing

    def test_start_approval_creates_new(self):
        self.db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = (
            None
        )
        instance = MagicMock()
        instance.status = "PENDING"

        with patch("app.services.approval_workflow_service.ApprovalEngineService") as MockEngine:
            MockEngine.return_value.submit.return_value = instance
            result = self.service.start_approval("QUOTE", 1, 10)

        assert result == instance
        MockEngine.return_value.submit.assert_called_once()

    def test_approve_step_success(self):
        record = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = record
        result = self.service.approve_step(1, 10, "ok")
        assert result.status == "APPROVED"
        self.db.commit.assert_called()

    def test_approve_step_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            self.service.approve_step(999, 10)

    def test_reject_step_success(self):
        record = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = record
        result = self.service.reject_step(1, 10, "no")
        assert result.status == "REJECTED"

    def test_reject_step_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            self.service.reject_step(999, 10)

    def test_withdraw_approval_success(self):
        record = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = record
        result = self.service.withdraw_approval(1, 10)
        assert result.status == "CANCELLED"

    def test_withdraw_not_found(self):
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
        wf.is_default = True
        self.db.query.return_value.filter.return_value.filter.return_value.all.return_value = [wf]
        result = self.service._select_workflow_by_routing("QUOTE")
        assert result == wf
