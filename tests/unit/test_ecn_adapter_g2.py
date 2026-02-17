# -*- coding: utf-8 -*-
"""
EcnApprovalAdapter 单元测试 - G2组覆盖率提升

覆盖:
- EcnApprovalAdapter.__init__ / entity_type
- get_entity
- get_entity_data (ECN存在/不存在)
- on_submit (状态变更)
- on_approved
- on_rejected
- on_withdrawn
- get_title
- get_summary
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestEcnApprovalAdapterInit:
    """初始化测试"""

    def test_init_stores_db(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        db = MagicMock()
        adapter = EcnApprovalAdapter(db)
        assert adapter.db is db

    def test_entity_type_is_ecn(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        assert EcnApprovalAdapter.entity_type == "ECN"


class TestGetEntity:
    """测试 get_entity"""

    def setup_method(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)

    def test_returns_ecn_when_found(self):
        mock_ecn = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_ecn
        result = self.adapter.get_entity(1)
        assert result == mock_ecn

    def test_returns_none_when_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.adapter.get_entity(999)
        assert result is None


class TestGetEntityData:
    """测试 get_entity_data"""

    def setup_method(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)

    def test_returns_empty_dict_when_ecn_not_found(self):
        self.adapter.get_entity = MagicMock(return_value=None)
        result = self.adapter.get_entity_data(999)
        assert result == {}

    def test_returns_data_dict_with_required_keys(self):
        mock_ecn = MagicMock()
        mock_ecn.ecn_no = "ECN-20260101-001"
        mock_ecn.ecn_title = "测试变更"
        mock_ecn.ecn_type = "DESIGN"
        mock_ecn.status = "DRAFT"
        mock_ecn.project_id = 1
        mock_ecn.project = MagicMock()
        mock_ecn.project.project_code = "PROJ-001"
        mock_ecn.project.project_name = "测试项目"
        mock_ecn.machine_id = 2
        mock_ecn.source_type = "QUALITY"
        mock_ecn.source_no = "QI-001"
        mock_ecn.priority = "HIGH"
        mock_ecn.urgency = "NORMAL"
        mock_ecn.cost_impact = Decimal("5000")
        mock_ecn.schedule_impact_days = 3
        mock_ecn.quality_impact = "medium"
        mock_ecn.applicant_id = 5
        mock_ecn.applicant = MagicMock()
        mock_ecn.applicant.name = "测试人员"
        mock_ecn.applicant_dept = "工程部"
        mock_ecn.root_cause = "设计缺陷"
        mock_ecn.root_cause_category = "DESIGN"

        self.adapter.get_entity = MagicMock(return_value=mock_ecn)

        # Mock evaluations query
        self.db.query.return_value.filter.return_value.all.return_value = []

        result = self.adapter.get_entity_data(1)

        assert "ecn_no" in result
        assert "ecn_type" in result
        assert "cost_impact" in result
        assert "evaluation_summary" in result
        assert result["ecn_no"] == "ECN-20260101-001"

    def test_evaluation_summary_counts(self):
        mock_ecn = MagicMock()
        mock_ecn.cost_impact = Decimal("0")
        mock_ecn.project = None
        mock_ecn.applicant = None

        self.adapter.get_entity = MagicMock(return_value=mock_ecn)

        eval1 = MagicMock()
        eval1.status = "COMPLETED"
        eval1.cost_estimate = Decimal("1000")
        eval1.schedule_estimate = 2
        eval1.eval_dept = "工程部"

        eval2 = MagicMock()
        eval2.status = "PENDING"
        eval2.cost_estimate = Decimal("500")
        eval2.schedule_estimate = 1
        eval2.eval_dept = "采购部"

        self.db.query.return_value.filter.return_value.all.return_value = [eval1, eval2]

        result = self.adapter.get_entity_data(1)

        assert result["evaluation_summary"]["total_evaluations"] == 2
        assert result["evaluation_summary"]["completed_evaluations"] == 1
        assert result["evaluation_summary"]["pending_evaluations"] == 1


class TestOnSubmit:
    """测试 on_submit 回调"""

    def setup_method(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)

    def test_sets_status_evaluating(self):
        mock_ecn = MagicMock()
        self.adapter.get_entity = MagicMock(return_value=mock_ecn)

        instance = MagicMock()
        self.adapter.on_submit(entity_id=1, instance=instance)

        assert mock_ecn.status == "EVALUATING"
        assert mock_ecn.current_step == "EVALUATION"
        self.db.flush.assert_called_once()

    def test_skips_when_ecn_not_found(self):
        self.adapter.get_entity = MagicMock(return_value=None)
        # Should not raise
        self.adapter.on_submit(entity_id=999, instance=MagicMock())
        self.db.flush.assert_not_called()


class TestOnApproved:
    """测试 on_approved 回调"""

    def setup_method(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)

    def test_sets_status_approved(self):
        mock_ecn = MagicMock()
        self.adapter.get_entity = MagicMock(return_value=mock_ecn)

        self.adapter.on_approved(entity_id=1, instance=MagicMock())

        assert mock_ecn.status == "APPROVED"
        assert mock_ecn.approval_result == "APPROVED"
        assert mock_ecn.current_step == "EXECUTION"
        self.db.flush.assert_called_once()


class TestOnRejected:
    """测试 on_rejected 回调"""

    def setup_method(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)

    def test_sets_status_rejected(self):
        mock_ecn = MagicMock()
        self.adapter.get_entity = MagicMock(return_value=mock_ecn)

        self.adapter.on_rejected(entity_id=1, instance=MagicMock())

        assert mock_ecn.status == "REJECTED"
        assert mock_ecn.approval_result == "REJECTED"
        self.db.flush.assert_called_once()


class TestOnWithdrawn:
    """测试 on_withdrawn 回调"""

    def setup_method(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)

    def test_resets_to_draft(self):
        mock_ecn = MagicMock()
        self.adapter.get_entity = MagicMock(return_value=mock_ecn)

        self.adapter.on_withdrawn(entity_id=1, instance=MagicMock())

        assert mock_ecn.status == "DRAFT"
        assert mock_ecn.current_step is None
        self.db.flush.assert_called_once()


class TestGetTitle:
    """测试 get_title"""

    def setup_method(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)

    def test_returns_title_with_ecn_info(self):
        mock_ecn = MagicMock()
        mock_ecn.ecn_no = "ECN-001"
        mock_ecn.ecn_title = "测试标题"
        self.adapter.get_entity = MagicMock(return_value=mock_ecn)

        title = self.adapter.get_title(1)
        assert "ECN-001" in title
        assert "测试标题" in title

    def test_returns_fallback_when_not_found(self):
        self.adapter.get_entity = MagicMock(return_value=None)
        title = self.adapter.get_title(999)
        assert "999" in title


class TestGetSummary:
    """测试 get_summary"""

    def setup_method(self):
        from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
        self.db = MagicMock()
        self.adapter = EcnApprovalAdapter(self.db)

    def test_returns_empty_when_no_data(self):
        self.adapter.get_entity_data = MagicMock(return_value={})
        summary = self.adapter.get_summary(999)
        assert summary == ""

    def test_includes_cost_impact_in_summary(self):
        self.adapter.get_entity_data = MagicMock(return_value={
            "ecn_type": "DESIGN",
            "project_name": "测试项目",
            "cost_impact": 5000.0,
            "schedule_impact_days": 3,
            "priority": "HIGH",
        })
        summary = self.adapter.get_summary(1)
        assert "5,000.00" in summary or "5000" in summary

    def test_summary_uses_pipe_separator(self):
        self.adapter.get_entity_data = MagicMock(return_value={
            "ecn_type": "DESIGN",
            "project_name": "项目A",
            "cost_impact": 1000.0,
            "schedule_impact_days": 0,
            "priority": "NORMAL",
        })
        summary = self.adapter.get_summary(1)
        assert "|" in summary
