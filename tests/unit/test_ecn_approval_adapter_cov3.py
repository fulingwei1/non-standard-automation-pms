# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - approval_engine/adapters/ecn"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.approval_engine.adapters.ecn")

from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter


def make_db():
    return MagicMock()


def make_ecn(**kw):
    e = MagicMock()
    e.id = kw.get("id", 1)
    e.ecn_no = kw.get("ecn_no", "ECN-001")
    e.ecn_title = kw.get("ecn_title", "Test ECN")
    e.ecn_type = kw.get("ecn_type", "DESIGN")
    e.status = kw.get("status", "DRAFT")
    e.project_id = kw.get("project_id", 1)
    e.project = None
    e.applicant = None
    e.cost_impact = kw.get("cost_impact", None)
    e.schedule_impact_days = kw.get("schedule_impact_days", 0)
    e.quality_impact = kw.get("quality_impact", None)
    e.applicant_id = kw.get("applicant_id", 1)
    e.applicant_dept = kw.get("applicant_dept", "Engineering")
    e.priority = kw.get("priority", "NORMAL")
    e.urgency = kw.get("urgency", "NORMAL")
    e.source_type = kw.get("source_type", "MANUAL")
    e.source_no = kw.get("source_no", None)
    e.machine_id = kw.get("machine_id", None)
    e.root_cause = kw.get("root_cause", None)
    e.root_cause_category = kw.get("root_cause_category", None)
    e.current_step = kw.get("current_step", "DRAFT")
    e.approval_result = kw.get("approval_result", None)
    return e


class TestGetEntity:
    def test_get_entity_found(self):
        db = make_db()
        ecn = make_ecn()
        db.query.return_value.filter.return_value.first.return_value = ecn
        svc = EcnApprovalAdapter(db)
        result = svc.get_entity(1)
        assert result is ecn

    def test_get_entity_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = EcnApprovalAdapter(db)
        result = svc.get_entity(999)
        assert result is None


class TestGetEntityData:
    def test_returns_empty_when_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = EcnApprovalAdapter(db)
        result = svc.get_entity_data(999)
        assert result == {}

    def test_returns_data_dict(self):
        db = make_db()
        ecn = make_ecn()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = ecn
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        svc = EcnApprovalAdapter(db)
        result = svc.get_entity_data(1)
        assert "ecn_no" in result
        assert "ecn_type" in result


class TestCallbacks:
    def test_on_submit_sets_evaluating(self):
        db = make_db()
        ecn = make_ecn(status="DRAFT")
        db.query.return_value.filter.return_value.first.return_value = ecn
        svc = EcnApprovalAdapter(db)
        instance = MagicMock()
        svc.on_submit(1, instance)
        assert ecn.status == "EVALUATING"

    def test_on_approved_sets_approved(self):
        db = make_db()
        ecn = make_ecn(status="REVIEWING")
        db.query.return_value.filter.return_value.first.return_value = ecn
        svc = EcnApprovalAdapter(db)
        instance = MagicMock()
        svc.on_approved(1, instance)
        assert ecn.status == "APPROVED"

    def test_on_rejected_sets_rejected(self):
        db = make_db()
        ecn = make_ecn(status="REVIEWING")
        db.query.return_value.filter.return_value.first.return_value = ecn
        svc = EcnApprovalAdapter(db)
        instance = MagicMock()
        svc.on_rejected(1, instance)
        assert ecn.status == "REJECTED"

    def test_on_withdrawn_updates_status(self):
        db = make_db()
        ecn = make_ecn(status="REVIEWING")
        db.query.return_value.filter.return_value.first.return_value = ecn
        svc = EcnApprovalAdapter(db)
        instance = MagicMock()
        svc.on_withdrawn(1, instance)
        # status should be updated
        db.flush.assert_called()


class TestGetTitle:
    def test_get_title(self):
        db = make_db()
        ecn = make_ecn(ecn_no="ECN-001", ecn_title="Test Title")
        db.query.return_value.filter.return_value.first.return_value = ecn
        svc = EcnApprovalAdapter(db)
        title = svc.get_title(1)
        assert "ECN-001" in title or "Test Title" in title

    def test_get_title_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = EcnApprovalAdapter(db)
        title = svc.get_title(999)
        assert isinstance(title, str)


class TestDetermineApprovalLevel:
    def test_node_not_found_returns_1(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = EcnApprovalAdapter(db)
        level = svc._determine_approval_level(999, MagicMock())
        assert level == 1

    def test_node_found_returns_order(self):
        db = make_db()
        node = MagicMock()
        node.node_order = 3
        db.query.return_value.filter.return_value.first.return_value = node
        svc = EcnApprovalAdapter(db)
        level = svc._determine_approval_level(1, MagicMock())
        assert level == 3


class TestCheckEvaluationComplete:
    def test_no_evaluations_returns_false(self):
        """When no evaluations found, returns False and empty dict"""
        db = make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = EcnApprovalAdapter(db)
        complete, summary = svc.check_evaluation_complete(999)
        assert complete is False
        assert summary == {}

    def test_all_evaluations_complete(self):
        db = make_db()
        eval1 = MagicMock(status="COMPLETED", cost_estimate=5000, schedule_estimate=3, eval_dept="Engineering", eval_result="APPROVE")
        eval2 = MagicMock(status="COMPLETED", cost_estimate=3000, schedule_estimate=2, eval_dept="Quality", eval_result="APPROVE")
        
        db.query.return_value.filter.return_value.all.return_value = [eval1, eval2]

        svc = EcnApprovalAdapter(db)
        complete, summary = svc.check_evaluation_complete(1)
        assert complete is True
        assert summary["completed"] == 2

    def test_pending_evaluations_returns_false(self):
        db = make_db()
        eval1 = MagicMock(status="PENDING", cost_estimate=None, schedule_estimate=None, eval_dept="Engineering", eval_result=None)
        
        db.query.return_value.filter.return_value.all.return_value = [eval1]

        svc = EcnApprovalAdapter(db)
        complete, summary = svc.check_evaluation_complete(1)
        assert complete is False
