# -*- coding: utf-8 -*-
"""
approval_engine/adapters/ecn.py 单元测试 - 简化版

测试ECN审批适配器的核心方法
"""

import pytest
from unittest.mock import MagicMock

from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter


class MockEcnApprovalAdapter(EcnApprovalAdapter):
    """测试用适配器子类"""
    def __init__(self, db):
        self.db = db


@pytest.mark.unit
class TestGetEntity:
    def test_get_entity_found(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result = adapter.get_entity(entity_id=1)

        assert result == mock_ecn

    def test_get_entity_not_found(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_entity(entity_id=1)

        assert result is None


@pytest.mark.unit
class TestValidateSubmit:
    """测试validate_submit - 使用基类默认实现"""

    def test_validate_submit_default(self):
        """基类默认实现返回(True, None)"""
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        result, message = adapter.validate_submit(entity_id=1)

        assert result is True
        assert message is None


@pytest.mark.unit
class TestOnSubmit:
    def test_on_submit_starts_evaluation(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1

        mock_instance = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        adapter.on_submit(entity_id=1, instance=mock_instance)

        assert mock_ecn.status == "EVALUATING"
        assert mock_ecn.current_step == "EVALUATION"
        mock_db.flush.assert_called()


@pytest.mark.unit
class TestOnApproved:
    def test_on_approved_updates_status(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1

        mock_instance = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        adapter.on_approved(entity_id=1, instance=mock_instance)

        assert mock_ecn.status == "APPROVED"
        assert mock_ecn.approval_result == "APPROVED"
        assert mock_ecn.current_step == "EXECUTION"
        mock_db.flush.assert_called()


@pytest.mark.unit
class TestOnRejected:
    def test_on_rejected_updates_status(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1

        mock_instance = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        adapter.on_rejected(entity_id=1, instance=mock_instance)

        assert mock_ecn.status == "REJECTED"
        assert mock_ecn.approval_result == "REJECTED"
        mock_db.flush.assert_called()


@pytest.mark.unit
class TestOnWithdrawn:
    def test_on_withdrawn_resets_to_draft(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1

        mock_instance = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        adapter.on_withdrawn(entity_id=1, instance=mock_instance)

        assert mock_ecn.status == "DRAFT"
        assert mock_ecn.current_step is None
        mock_db.flush.assert_called()


@pytest.mark.unit
class TestGetTitle:
    def test_get_title_with_ecn(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_no = "ECN001"
        mock_ecn.ecn_title = "测试标题"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result = adapter.get_title(entity_id=1)

        assert result == "ECN审批 - ECN001: 测试标题"

    def test_get_title_without_ecn(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_title(entity_id=999)

        assert result == "ECN审批 - #999"


@pytest.mark.unit
class TestGetSummary:
    def test_get_summary_returns_empty_when_no_ecn(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_summary(entity_id=1)

        assert isinstance(result, str)
        assert result == ""

    def test_get_summary_with_ecn_data(self):
        """测试有ECN数据时生成摘要"""
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.ecn_no = "ECN001"
        mock_ecn.ecn_title = "测试ECN"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.status = "DRAFT"
        mock_ecn.project_id = 1
        mock_ecn.project = MagicMock()
        mock_ecn.project.project_code = "PJ001"
        mock_ecn.project.project_name = "测试项目"
        mock_ecn.machine_id = None
        mock_ecn.source_type = None
        mock_ecn.source_no = None
        mock_ecn.priority = "HIGH"
        mock_ecn.urgency = "NORMAL"
        mock_ecn.cost_impact = 5000
        mock_ecn.schedule_impact_days = 3
        mock_ecn.quality_impact = None
        mock_ecn.applicant_id = 1
        mock_ecn.applicant = MagicMock()
        mock_ecn.applicant.name = "张三"
        mock_ecn.applicant_dept = "工程部"
        mock_ecn.root_cause = None
        mock_ecn.root_cause_category = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_query.all.return_value = []  # No evaluations
        mock_db.query.return_value = mock_query

        result = adapter.get_summary(entity_id=1)

        assert "DESIGN" in result
        assert "测试项目" in result
        assert "5,000" in result or "5000" in result
        assert "3" in result
        assert "HIGH" in result


@pytest.mark.unit
class TestGetRequiredEvaluators:
    def test_get_evaluators_material_type(self):
        """测试MATERIAL类型需要采购部和生产部评估"""
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_type = "MATERIAL"
        mock_ecn.cost_impact = 5000  # 低于10000，不需要财务

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result = adapter.get_required_evaluators(entity_id=1)

        depts = [e["dept"] for e in result]
        assert "工程部" in depts
        assert "采购部" in depts
        assert "生产部" in depts

    def test_get_evaluators_high_cost_needs_finance(self):
        """测试高成本影响需要财务部评估"""
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.cost_impact = 50000  # 高于10000

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result = adapter.get_required_evaluators(entity_id=1)

        depts = [e["dept"] for e in result]
        assert "财务部" in depts

    def test_get_evaluators_no_ecn(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_required_evaluators(entity_id=1)

        assert result == []


@pytest.mark.unit
class TestCreateEvaluationTasks:
    def test_create_evaluation_tasks_for_material(self):
        """测试为MATERIAL类型创建评估任务"""
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_type = "MATERIAL"
        mock_ecn.cost_impact = 5000  # 设置为数值，不是MagicMock

        mock_instance = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result = adapter.create_evaluation_tasks(entity_id=1, instance=mock_instance)

        # MATERIAL类型至少需要工程部、采购部、生产部
        assert len(result) >= 3
        mock_db.add.assert_called()
        mock_db.flush.assert_called()


@pytest.mark.unit
class TestCheckEvaluationComplete:
    def test_check_all_completed(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_eval1 = MagicMock()
        mock_eval1.status = "COMPLETED"
        mock_eval1.eval_dept = "工程部"
        mock_eval1.cost_estimate = 1000
        mock_eval1.schedule_estimate = 2
        mock_eval1.eval_result = "APPROVE"

        mock_eval2 = MagicMock()
        mock_eval2.status = "COMPLETED"
        mock_eval2.eval_dept = "采购部"
        mock_eval2.cost_estimate = 2000
        mock_eval2.schedule_estimate = 3
        mock_eval2.eval_result = "APPROVE"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_eval1, mock_eval2]
        mock_db.query.return_value = mock_query

        result, summary = adapter.check_evaluation_complete(entity_id=1)

        assert result is True
        assert summary["total"] == 2
        assert summary["completed"] == 2
        assert summary["pending"] == 0

    def test_check_with_pending(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_eval1 = MagicMock()
        mock_eval1.status = "COMPLETED"
        mock_eval1.eval_dept = "工程部"
        mock_eval1.cost_estimate = 1000
        mock_eval1.schedule_estimate = 2
        mock_eval1.eval_result = "APPROVE"

        mock_eval2 = MagicMock()
        mock_eval2.status = "PENDING"
        mock_eval2.eval_dept = "采购部"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_eval1, mock_eval2]
        mock_db.query.return_value = mock_query

        result, summary = adapter.check_evaluation_complete(entity_id=1)

        assert result is False
        assert summary["pending"] == 1
        assert "采购部" in summary["pending_depts"]

    def test_check_no_evaluations(self):
        """测试没有评估记录时返回False"""
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        result, summary = adapter.check_evaluation_complete(entity_id=1)

        assert result is False
        assert summary == {}


@pytest.mark.unit
class TestGetEntityData:
    """测试get_entity_data方法"""

    def test_get_entity_data_with_ecn(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        # 创建mock ECN
        mock_ecn = MagicMock()
        mock_ecn.ecn_no = "ECN001"
        mock_ecn.ecn_title = "测试ECN"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.status = "DRAFT"
        mock_ecn.project_id = 1
        mock_ecn.project = MagicMock()
        mock_ecn.project.project_code = "PJ001"
        mock_ecn.project.project_name = "测试项目"
        mock_ecn.machine_id = None
        mock_ecn.source_type = "CUSTOMER"
        mock_ecn.source_no = "REQ001"
        mock_ecn.priority = "HIGH"
        mock_ecn.urgency = "NORMAL"
        mock_ecn.cost_impact = 5000
        mock_ecn.schedule_impact_days = 3
        mock_ecn.quality_impact = "LOW"
        mock_ecn.applicant_id = 1
        mock_ecn.applicant = MagicMock()
        mock_ecn.applicant.name = "张三"
        mock_ecn.applicant_dept = "工程部"
        mock_ecn.root_cause = "设计缺陷"
        mock_ecn.root_cause_category = "DESIGN"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_query.all.return_value = []  # No evaluations
        mock_db.query.return_value = mock_query

        result = adapter.get_entity_data(entity_id=1)

        assert result["ecn_no"] == "ECN001"
        assert result["ecn_type"] == "DESIGN"
        assert result["priority"] == "HIGH"
        assert result["cost_impact"] == 5000
        assert result["project_name"] == "测试项目"

    def test_get_entity_data_no_ecn(self):
        mock_db = MagicMock()
        adapter = MockEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_entity_data(entity_id=999)

        assert result == {}
