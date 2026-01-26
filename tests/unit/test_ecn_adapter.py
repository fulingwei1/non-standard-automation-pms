# -*- coding: utf-8 -*-
"""
approval_engine/adapters/ecn.py 单元测试 - 简化版

测试ECN审批适配器的核心方法
"""

import pytest
from unittest.mock import MagicMock

from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter


class TestEcnApprovalAdapter(EcnApprovalAdapter):
    def __init__(self, db):
        self.db = db


@pytest.mark.unit
class TestGetEntity:
    def test_get_entity_found(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

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
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_entity(entity_id=1)

        assert result is None


@pytest.mark.unit
class TestValidateSubmit:
    def test_validate_success(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.status = "DRAFT"
        mock_ecn.change_reason = "需求变更"
        mock_ecn.change_description = "详细描述"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result, message = adapter.validate_submit(entity_id=1)

        assert result is True
        assert message == ""

    def test_validate_invalid_status(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.status = "EVALUATING"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result, message = adapter.validate_submit(entity_id=1)

        assert result is False
        assert "当前状态" in message

    def test_validate_no_reason(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.status = "DRAFT"
        mock_ecn.change_reason = None
        mock_ecn.change_description = "描述"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result, message = adapter.validate_submit(entity_id=1)

        assert result is False
        assert "请填写变更原因" in message


@pytest.mark.unit
class TestOnSubmit:
    def test_on_submit_starts_evaluation(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

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
        adapter = TestEcnApprovalAdapter(db=mock_db)

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
        adapter = TestEcnApprovalAdapter(db=mock_db)

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
        adapter = TestEcnApprovalAdapter(db=mock_db)

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
        adapter = TestEcnApprovalAdapter(db=mock_db)

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
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_title(entity_id=999)

        assert result == "ECN审批 - #999"


@pytest.mark.unit
class TestGetSummary:
    def test_get_summary_returns_string(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_summary(entity_id=1)

        assert isinstance(result, str)
        assert result == ""


@pytest.mark.unit
class TestGetRequiredEvaluators:
    def test_get_evaluators_with_ecn(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_type = "MATERIAL"
        mock_ecn.cost_impact = 5000

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result = adapter.get_required_evaluators(entity_id=1)

        assert len(result) > 0

    def test_get_evaluators_no_ecn(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = adapter.get_required_evaluators(entity_id=1)

        assert result == []


@pytest.mark.unit
class TestCreateEvaluationTasks:
    def test_create_evaluation_tasks(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_ecn = MagicMock()
        mock_ecn.id = 1
        mock_ecn.ecn_type = "MATERIAL"

        mock_instance = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn
        mock_db.query.return_value = mock_query

        result = adapter.create_evaluation_tasks(entity_id=1, instance=mock_instance)

        assert len(result) >= 1
        mock_db.add.assert_called()
        mock_db.flush.assert_called()


@pytest.mark.unit
class TestCheckEvaluationComplete:
    def test_check_all_completed(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_eval1 = MagicMock()
        mock_eval1.status = "COMPLETED"

        mock_eval2 = MagicMock()
        mock_eval2.status = "COMPLETED"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_eval1, mock_eval2]
        mock_db.query.return_value = mock_query

        result, summary = adapter.check_evaluation_complete(entity_id=1)

        assert result is True
        assert summary["total"] == 2

    def test_check_with_pending(self):
        mock_db = MagicMock()
        adapter = TestEcnApprovalAdapter(db=mock_db)

        mock_eval1 = MagicMock()
        mock_eval1.status = "COMPLETED"

        mock_eval2 = MagicMock()
        mock_eval2.status = "PENDING"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_eval1, mock_eval2]
        mock_db.query.return_value = mock_query

        result, summary = adapter.check_evaluation_complete(entity_id=1)

        assert result is False
        assert summary["pending"] == 1
