# -*- coding: utf-8 -*-
"""
EcnApprovalAdapter 深度覆盖测试（N3组）

覆盖：
- get_entity / get_entity_data
- on_submit / on_approved / on_rejected / on_withdrawn
- get_title / get_summary
- submit_for_approval
- sync_from_approval_instance
- create_ecn_approval_records
- get_ecn_approvers / _determine_approval_level
- update_ecn_approval_from_action
- get_required_evaluators / create_evaluation_tasks
- check_evaluation_complete
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def adapter(mock_db):
    from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
    return EcnApprovalAdapter(db=mock_db)


def _make_ecn(**kwargs):
    """Helper: build a mock ECN object."""
    ecn = MagicMock()
    ecn.id = kwargs.get("id", 1)
    ecn.ecn_no = kwargs.get("ecn_no", "ECN-2024-001")
    ecn.ecn_title = kwargs.get("ecn_title", "测试ECN")
    ecn.ecn_type = kwargs.get("ecn_type", "DESIGN")
    ecn.status = kwargs.get("status", "DRAFT")
    ecn.project_id = kwargs.get("project_id", 10)
    ecn.machine_id = kwargs.get("machine_id", None)
    ecn.source_type = kwargs.get("source_type", None)
    ecn.source_no = kwargs.get("source_no", None)
    ecn.priority = kwargs.get("priority", "NORMAL")
    ecn.urgency = kwargs.get("urgency", "NORMAL")
    ecn.cost_impact = kwargs.get("cost_impact", Decimal("0"))
    ecn.schedule_impact_days = kwargs.get("schedule_impact_days", 0)
    ecn.quality_impact = kwargs.get("quality_impact", None)
    ecn.applicant_id = kwargs.get("applicant_id", 1)
    ecn.applicant_dept = kwargs.get("applicant_dept", "工程部")
    ecn.root_cause = kwargs.get("root_cause", None)
    ecn.root_cause_category = kwargs.get("root_cause_category", None)
    ecn.approval_instance_id = kwargs.get("approval_instance_id", None)
    ecn.approval_status = kwargs.get("approval_status", None)
    ecn.approval_result = kwargs.get("approval_result", None)
    ecn.current_step = kwargs.get("current_step", None)
    ecn.impact_analysis = kwargs.get("impact_analysis", "")
    ecn.applicant_name = kwargs.get("applicant_name", "张三")
    ecn.tasks = kwargs.get("tasks", [])
    # project relation
    proj = MagicMock()
    proj.project_code = "PROJ-001"
    proj.project_name = "测试项目"
    ecn.project = proj
    # applicant relation
    applicant = MagicMock()
    applicant.name = "张三"
    ecn.applicant = applicant
    return ecn


# ---------------------------------------------------------------------------
# get_entity
# ---------------------------------------------------------------------------

class TestGetEntity:
    def test_returns_ecn_when_found(self, adapter, mock_db):
        ecn = _make_ecn()
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        result = adapter.get_entity(1)
        assert result is ecn

    def test_returns_none_when_not_found(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = adapter.get_entity(999)
        assert result is None


# ---------------------------------------------------------------------------
# get_entity_data
# ---------------------------------------------------------------------------

class TestGetEntityData:
    def test_returns_empty_dict_when_ecn_not_found(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = adapter.get_entity_data(999)
        assert result == {}

    def test_returns_full_data_dict(self, adapter, mock_db):
        ecn = _make_ecn(cost_impact=Decimal("5000"), schedule_impact_days=3)
        # First call returns ecn, second call returns evaluations
        eval1 = MagicMock()
        eval1.status = "COMPLETED"
        eval1.cost_estimate = Decimal("1000")
        eval1.schedule_estimate = 2
        eval1.eval_dept = "工程部"
        eval2 = MagicMock()
        eval2.status = "PENDING"
        eval2.cost_estimate = None
        eval2.schedule_estimate = None
        eval2.eval_dept = "质量部"

        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        mock_db.query.return_value.filter.return_value.all.return_value = [eval1, eval2]

        result = adapter.get_entity_data(1)
        assert result["ecn_no"] == "ECN-2024-001"
        assert result["cost_impact"] == 5000.0
        assert result["schedule_impact_days"] == 3
        assert result["evaluation_summary"]["total_evaluations"] == 2
        assert result["evaluation_summary"]["completed_evaluations"] == 1

    def test_cost_impact_zero_returns_zero(self, adapter, mock_db):
        ecn = _make_ecn(cost_impact=None)
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = adapter.get_entity_data(1)
        assert result["cost_impact"] == 0

    def test_no_project_returns_none_for_project_fields(self, adapter, mock_db):
        ecn = _make_ecn()
        ecn.project = None
        ecn.applicant = None
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = adapter.get_entity_data(1)
        assert result["project_code"] is None
        assert result["project_name"] is None
        assert result["applicant_name"] is None


# ---------------------------------------------------------------------------
# Lifecycle callbacks
# ---------------------------------------------------------------------------

class TestLifecycleCallbacks:
    def test_on_submit_sets_status_evaluating(self, adapter, mock_db):
        ecn = _make_ecn()
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        instance = MagicMock()
        adapter.on_submit(1, instance)
        assert ecn.status == "EVALUATING"
        assert ecn.current_step == "EVALUATION"
        mock_db.flush.assert_called_once()

    def test_on_submit_no_op_when_ecn_not_found(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        adapter.on_submit(999, MagicMock())  # should not raise

    def test_on_approved_sets_status_approved(self, adapter, mock_db):
        ecn = _make_ecn()
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        adapter.on_approved(1, MagicMock())
        assert ecn.status == "APPROVED"
        assert ecn.approval_result == "APPROVED"
        assert ecn.current_step == "EXECUTION"

    def test_on_rejected_sets_status_rejected(self, adapter, mock_db):
        ecn = _make_ecn()
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        adapter.on_rejected(1, MagicMock())
        assert ecn.status == "REJECTED"
        assert ecn.approval_result == "REJECTED"

    def test_on_withdrawn_resets_to_draft(self, adapter, mock_db):
        ecn = _make_ecn(status="SUBMITTED", current_step="REVIEW")
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        adapter.on_withdrawn(1, MagicMock())
        assert ecn.status == "DRAFT"
        assert ecn.current_step is None

    def test_on_approved_when_ecn_not_found(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        adapter.on_approved(999, MagicMock())  # should not raise


# ---------------------------------------------------------------------------
# get_title / get_summary
# ---------------------------------------------------------------------------

class TestGetTitleAndSummary:
    def test_get_title_when_ecn_exists(self, adapter, mock_db):
        ecn = _make_ecn(ecn_no="ECN-001", ecn_title="变更设计")
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        title = adapter.get_title(1)
        assert "ECN-001" in title
        assert "变更设计" in title

    def test_get_title_fallback_when_not_found(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        title = adapter.get_title(42)
        assert "42" in title

    def test_get_summary_with_all_fields(self, adapter, mock_db):
        ecn = _make_ecn(cost_impact=Decimal("8000"), schedule_impact_days=5, priority="HIGH")
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        mock_db.query.return_value.filter.return_value.all.return_value = []
        summary = adapter.get_summary(1)
        assert "8,000.00" in summary or "8000" in summary
        assert "5" in summary
        assert "HIGH" in summary

    def test_get_summary_returns_empty_when_not_found(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        summary = adapter.get_summary(999)
        assert summary == ""


# ---------------------------------------------------------------------------
# submit_for_approval
# ---------------------------------------------------------------------------

class TestSubmitForApproval:
    def test_returns_existing_instance_when_already_submitted(self, adapter, mock_db):
        ecn = _make_ecn(approval_instance_id=7)
        existing_instance = MagicMock()
        existing_instance.id = 7
        mock_db.query.return_value.filter.return_value.first.return_value = existing_instance
        result = adapter.submit_for_approval(ecn, initiator_id=1)
        assert result is existing_instance

    def test_creates_new_instance_when_not_submitted(self, adapter, mock_db):
        ecn = _make_ecn(approval_instance_id=None)
        new_instance = MagicMock()
        new_instance.id = 10
        new_instance.status = "PENDING"

        # evaluations query returns empty
        eval_query = MagicMock()
        eval_query.all.return_value = []

        with patch(
            "app.services.approval_engine.adapters.ecn.WorkflowEngine"
        ) as MockWorkflowEngine:
            engine_instance = MockWorkflowEngine.return_value
            engine_instance.create_instance.return_value = new_instance
            mock_db.query.return_value.filter.return_value.all.return_value = []
            result = adapter.submit_for_approval(ecn, initiator_id=1)
            assert result is new_instance
            assert ecn.approval_instance_id == 10

    def test_submit_with_evaluations_included(self, adapter, mock_db):
        ecn = _make_ecn(approval_instance_id=None)
        eval1 = MagicMock()
        eval1.eval_dept = "工程部"
        eval1.evaluator_id = 2
        eval1.evaluator_name = "李工"
        eval1.impact_analysis = "影响分析"
        eval1.cost_estimate = Decimal("500")
        eval1.schedule_estimate = 2
        eval1.resource_requirement = "资源"
        eval1.risk_assessment = "低风险"
        eval1.eval_result = "APPROVE"
        eval1.eval_opinion = "同意"
        eval1.status = "COMPLETED"
        new_instance = MagicMock()
        new_instance.id = 11
        new_instance.status = "PENDING"

        with patch(
            "app.services.approval_engine.adapters.ecn.WorkflowEngine"
        ) as MockWorkflowEngine:
            engine_instance = MockWorkflowEngine.return_value
            engine_instance.create_instance.return_value = new_instance
            mock_db.query.return_value.filter.return_value.all.return_value = [eval1]
            result = adapter.submit_for_approval(ecn, initiator_id=1)
            assert result is new_instance


# ---------------------------------------------------------------------------
# sync_from_approval_instance
# ---------------------------------------------------------------------------

class TestSyncFromApprovalInstance:
    def _make_instance(self, status, completed_at=None, final_comment=None, final_approver_id=None):
        inst = MagicMock()
        inst.status = status
        inst.completed_at = completed_at
        inst.final_comment = final_comment
        inst.final_approver_id = final_approver_id
        return inst

    def test_sync_approved_status(self, adapter, mock_db):
        ecn = _make_ecn(approval_status="PENDING")
        instance = self._make_instance("APPROVED", completed_at=datetime.now())
        adapter.sync_from_approval_instance(instance, ecn)
        assert ecn.status == "APPROVED"
        assert ecn.approval_result == "APPROVED"

    def test_sync_rejected_status(self, adapter, mock_db):
        ecn = _make_ecn(approval_status="PENDING")
        instance = self._make_instance("REJECTED", completed_at=datetime.now())
        adapter.sync_from_approval_instance(instance, ecn)
        assert ecn.status == "REJECTED"
        assert ecn.approval_result == "REJECTED"

    def test_sync_cancelled_status(self, adapter, mock_db):
        ecn = _make_ecn()
        instance = self._make_instance("CANCELLED")
        adapter.sync_from_approval_instance(instance, ecn)
        assert ecn.status == "CANCELLED"
        assert ecn.approval_result == "CANCELLED"

    def test_sync_terminated_status(self, adapter, mock_db):
        ecn = _make_ecn()
        instance = self._make_instance("TERMINATED")
        adapter.sync_from_approval_instance(instance, ecn)
        assert ecn.status == "TERMINATED"

    def test_sync_sets_final_comment(self, adapter, mock_db):
        ecn = _make_ecn()
        instance = self._make_instance("APPROVED", final_comment="审批通过，请执行")
        adapter.sync_from_approval_instance(instance, ecn)
        assert ecn.approval_note == "审批通过，请执行"

    def test_sync_no_comment_when_none(self, adapter, mock_db):
        ecn = _make_ecn()
        ecn.approval_note = "old_note"
        instance = self._make_instance("APPROVED", final_comment=None)
        adapter.sync_from_approval_instance(instance, ecn)
        # approval_note should remain unchanged
        assert ecn.approval_note == "old_note"


# ---------------------------------------------------------------------------
# get_required_evaluators
# ---------------------------------------------------------------------------

class TestGetRequiredEvaluators:
    def test_returns_empty_when_ecn_not_found(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = adapter.get_required_evaluators(999)
        assert result == []

    def test_material_type_includes_purchase_and_production(self, adapter, mock_db):
        ecn = _make_ecn(ecn_type="MATERIAL", cost_impact=Decimal("0"))
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        result = adapter.get_required_evaluators(1)
        depts = [r["dept"] for r in result]
        assert "工程部" in depts
        assert "采购部" in depts
        assert "生产部" in depts

    def test_design_type_includes_quality(self, adapter, mock_db):
        ecn = _make_ecn(ecn_type="DESIGN", cost_impact=Decimal("0"))
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        result = adapter.get_required_evaluators(1)
        depts = [r["dept"] for r in result]
        assert "质量部" in depts

    def test_high_cost_impact_includes_finance(self, adapter, mock_db):
        ecn = _make_ecn(ecn_type="DESIGN", cost_impact=Decimal("50000"))
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        result = adapter.get_required_evaluators(1)
        depts = [r["dept"] for r in result]
        assert "财务部" in depts

    def test_low_cost_impact_excludes_finance(self, adapter, mock_db):
        ecn = _make_ecn(ecn_type="PROCESS", cost_impact=Decimal("500"))
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        result = adapter.get_required_evaluators(1)
        depts = [r["dept"] for r in result]
        assert "财务部" not in depts

    def test_basic_ecn_includes_engineering(self, adapter, mock_db):
        ecn = _make_ecn(ecn_type="OTHER", cost_impact=Decimal("0"))
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        result = adapter.get_required_evaluators(1)
        assert result[0]["dept"] == "工程部"
        assert result[0]["required"] is True


# ---------------------------------------------------------------------------
# check_evaluation_complete
# ---------------------------------------------------------------------------

class TestCheckEvaluationComplete:
    def test_returns_false_when_no_evaluations(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        is_done, summary = adapter.check_evaluation_complete(1)
        assert is_done is False
        assert summary == {}

    def test_returns_true_when_all_completed(self, adapter, mock_db):
        e1 = MagicMock(status="COMPLETED", cost_estimate=Decimal("100"), schedule_estimate=2, eval_result="APPROVE", eval_dept="工程部")
        e2 = MagicMock(status="COMPLETED", cost_estimate=Decimal("200"), schedule_estimate=1, eval_result="APPROVE", eval_dept="质量部")
        mock_db.query.return_value.filter.return_value.all.return_value = [e1, e2]
        is_done, summary = adapter.check_evaluation_complete(1)
        assert is_done is True
        assert summary["total"] == 2
        assert summary["pending"] == 0
        assert summary["all_approved"] is True

    def test_returns_false_when_pending_exist(self, adapter, mock_db):
        e1 = MagicMock(status="COMPLETED", cost_estimate=Decimal("100"), schedule_estimate=2, eval_result="APPROVE", eval_dept="工程部")
        e2 = MagicMock(status="PENDING", cost_estimate=None, schedule_estimate=None, eval_result=None, eval_dept="质量部")
        mock_db.query.return_value.filter.return_value.all.return_value = [e1, e2]
        is_done, summary = adapter.check_evaluation_complete(1)
        assert is_done is False
        assert summary["pending"] == 1
        assert "质量部" in summary["pending_depts"]

    def test_all_approved_false_when_one_rejected(self, adapter, mock_db):
        e1 = MagicMock(status="COMPLETED", cost_estimate=None, schedule_estimate=0, eval_result="REJECT", eval_dept="采购部")
        mock_db.query.return_value.filter.return_value.all.return_value = [e1]
        is_done, summary = adapter.check_evaluation_complete(1)
        assert is_done is True
        assert summary["all_approved"] is False


# ---------------------------------------------------------------------------
# create_evaluation_tasks
# ---------------------------------------------------------------------------

class TestCreateEvaluationTasks:
    def test_creates_tasks_for_each_evaluator(self, adapter, mock_db):
        ecn = _make_ecn(ecn_type="MATERIAL", cost_impact=Decimal("0"))
        mock_db.query.return_value.filter.return_value.first.return_value = ecn

        # Patch get_required_evaluators to return 2 depts
        with patch.object(adapter, "get_required_evaluators", return_value=[
            {"dept": "工程部", "required": True},
            {"dept": "采购部", "required": True},
        ]):
            tasks = adapter.create_evaluation_tasks(1, MagicMock())
        assert len(tasks) == 2
        mock_db.flush.assert_called()

    def test_creates_no_tasks_when_evaluators_empty(self, adapter, mock_db):
        ecn = _make_ecn(ecn_type="PROCESS")
        mock_db.query.return_value.filter.return_value.first.return_value = ecn
        with patch.object(adapter, "get_required_evaluators", return_value=[]):
            tasks = adapter.create_evaluation_tasks(1, MagicMock())
        assert tasks == []


# ---------------------------------------------------------------------------
# _determine_approval_level
# ---------------------------------------------------------------------------

class TestDetermineApprovalLevel:
    def test_returns_node_order_when_found(self, adapter, mock_db):
        node = MagicMock()
        node.node_order = 3
        mock_db.query.return_value.filter.return_value.first.return_value = node
        level = adapter._determine_approval_level(5, MagicMock())
        assert level == 3

    def test_returns_1_when_node_not_found(self, adapter, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        level = adapter._determine_approval_level(999, MagicMock())
        assert level == 1


# ---------------------------------------------------------------------------
# update_ecn_approval_from_action
# ---------------------------------------------------------------------------

class TestUpdateEcnApprovalFromAction:
    def _make_task(self, node_id=1, instance_entity_id=1):
        task = MagicMock()
        task.node_id = node_id
        task.instance = MagicMock()
        task.instance.entity_id = instance_entity_id
        task.instance.entity = MagicMock()
        return task

    def test_returns_none_when_approval_not_found(self, adapter, mock_db):
        task = self._make_task()
        node = MagicMock()
        node.node_order = 1
        # node query returns node, approval query returns None
        mock_db.query.return_value.filter.return_value.first.side_effect = [node, None]
        result = adapter.update_ecn_approval_from_action(task, "APPROVE")
        assert result is None

    def test_approve_action_sets_correct_fields(self, adapter, mock_db):
        task = self._make_task()
        node = MagicMock()
        node.node_order = 1
        approval = MagicMock()
        approval.ecn_id = 1
        approval.approval_level = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [node, approval]
        result = adapter.update_ecn_approval_from_action(task, "APPROVE", comment="同意")
        assert approval.approval_result == "APPROVED"
        assert approval.status == "APPROVED"
        assert approval.approval_opinion == "同意"

    def test_reject_action_sets_rejected(self, adapter, mock_db):
        task = self._make_task()
        node = MagicMock()
        node.node_order = 1
        approval = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [node, approval]
        adapter.update_ecn_approval_from_action(task, "REJECT", comment="不同意")
        assert approval.approval_result == "REJECTED"
        assert approval.status == "REJECTED"

    def test_withdraw_action_sets_cancelled(self, adapter, mock_db):
        task = self._make_task()
        node = MagicMock()
        node.node_order = 1
        approval = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [node, approval]
        adapter.update_ecn_approval_from_action(task, "WITHDRAW")
        assert approval.approval_result == "WITHDRAWN"
        assert approval.status == "CANCELLED"
