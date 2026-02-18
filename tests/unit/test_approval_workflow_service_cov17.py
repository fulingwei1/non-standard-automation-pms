# -*- coding: utf-8 -*-
"""第十七批 - 审批工作流服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

pytest.importorskip("app.services.approval_workflow_service")


def _make_db():
    return MagicMock()


def _make_service(db=None):
    from app.services.approval_workflow_service import ApprovalWorkflowService
    return ApprovalWorkflowService(db or _make_db())


class TestApprovalWorkflowService:

    def test_start_approval_returns_existing_if_pending(self):
        """已存在 PENDING 审批时直接返回"""
        from app.models.enums import ApprovalRecordStatusEnum
        existing = MagicMock()
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = existing

        svc = _make_service(db)
        with patch("app.services.approval_workflow_service.ApprovalWorkflowService.start_approval",
                   wraps=svc.start_approval):
            with patch("app.models.sales.workflow.ApprovalRecord", MagicMock()):
                result = svc.start_approval("QUOTE", 1, 10)
        # 现有记录被返回
        assert result is existing

    def test_start_approval_creates_new_record(self):
        """无现有审批时创建新记录"""
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None

        mock_record = MagicMock()
        with patch.dict("sys.modules", {"app.models.sales.workflow": MagicMock()}):
            import app.models.sales.workflow as wf_mod
            wf_mod.ApprovalRecord = MagicMock(return_value=mock_record)
            svc = _make_service(db)
            result = svc.start_approval("QUOTE", 42, 5)

        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_approve_step_raises_when_record_not_found(self):
        """记录不存在时 approve_step 抛出 ValueError"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        svc = _make_service(db)
        with patch.dict("sys.modules", {"app.models.sales.workflow": MagicMock()}):
            with pytest.raises(ValueError, match="审批记录不存在"):
                svc.approve_step(999, 1)

    def test_approve_step_sets_status_approved(self):
        """approve_step 成功后状态变为 APPROVED"""
        from app.models.enums import ApprovalRecordStatusEnum
        record = MagicMock()
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = record

        svc = _make_service(db)
        with patch.dict("sys.modules", {"app.models.sales.workflow": MagicMock()}):
            result = svc.approve_step(1, 10, "LGTM")

        assert record.status == ApprovalRecordStatusEnum.APPROVED
        db.commit.assert_called_once()

    def test_reject_step_sets_status_rejected(self):
        """reject_step 成功后状态变为 REJECTED"""
        from app.models.enums import ApprovalRecordStatusEnum
        record = MagicMock()
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = record

        svc = _make_service(db)
        with patch.dict("sys.modules", {"app.models.sales.workflow": MagicMock()}):
            svc.reject_step(1, 10, "质量不达标")

        assert record.status == ApprovalRecordStatusEnum.REJECTED

    def test_reject_step_raises_when_not_found(self):
        """记录不存在时 reject_step 抛出 ValueError"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        svc = _make_service(db)
        with patch.dict("sys.modules", {"app.models.sales.workflow": MagicMock()}):
            with pytest.raises(ValueError):
                svc.reject_step(999, 1)

    def test_withdraw_approval_sets_cancelled(self):
        """withdraw_approval 成功后状态变为 CANCELLED"""
        from app.models.enums import ApprovalRecordStatusEnum
        record = MagicMock()
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = record

        svc = _make_service(db)
        with patch.dict("sys.modules", {"app.models.sales.workflow": MagicMock()}):
            svc.withdraw_approval(1, 99, "取消原因")

        assert record.status == ApprovalRecordStatusEnum.CANCELLED

    def test_validate_approver_always_true(self):
        """_validate_approver 默认返回 True"""
        svc = _make_service()
        assert svc._validate_approver(1, 2) is True

    def test_select_workflow_returns_none_when_no_workflows(self):
        """无工作流时返回 None"""
        db = _make_db()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        svc = _make_service(db)
        with patch.dict("sys.modules", {"app.models.sales.workflow": MagicMock()}):
            result = svc._select_workflow_by_routing("QUOTE")
        assert result is None
