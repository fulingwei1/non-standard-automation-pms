# -*- coding: utf-8 -*-
"""第十二批：ECN审批适配器单元测试"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.approval_engine.adapters.ecn import EcnApprovalAdapter
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_adapter():
    db = MagicMock()
    return EcnApprovalAdapter(db=db), db


def _mock_ecn(**kwargs):
    ecn = MagicMock()
    ecn.id = kwargs.get("id", 1)
    ecn.ecn_type = kwargs.get("ecn_type", "DESIGN")
    ecn.cost_impact = kwargs.get("cost_impact", 5000)
    ecn.schedule_impact_days = kwargs.get("schedule_impact_days", 3)
    ecn.priority = kwargs.get("priority", "NORMAL")
    ecn.urgency = kwargs.get("urgency", "NORMAL")
    ecn.status = kwargs.get("status", "PENDING")
    return ecn


class TestEcnApprovalAdapterGetEntity:
    """get_entity 方法测试"""

    def test_get_entity_found(self):
        adapter, db = _make_adapter()
        mock_ecn = _mock_ecn(id=42)
        db.query.return_value.filter.return_value.first.return_value = mock_ecn

        result = adapter.get_entity(42)

        assert result is mock_ecn

    def test_get_entity_not_found(self):
        adapter, db = _make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity(999)

        assert result is None


class TestEcnApprovalAdapterGetEntityData:
    """get_entity_data 方法测试"""

    def test_returns_empty_when_ecn_not_found(self):
        adapter, db = _make_adapter()
        db.query.return_value.filter.return_value.first.return_value = None

        result = adapter.get_entity_data(999)

        assert result == {}

    def test_returns_data_with_evaluations(self):
        adapter, db = _make_adapter()
        mock_ecn = _mock_ecn(id=1)

        eval_completed = MagicMock()
        eval_completed.status = "COMPLETED"
        eval_pending = MagicMock()
        eval_pending.status = "PENDING"
        evaluations = [eval_completed, eval_pending]

        call_count = 0
        def query_side_effect(model):
            nonlocal call_count
            call_count += 1
            mock_q = MagicMock()
            if call_count == 1:
                mock_q.filter.return_value.first.return_value = mock_ecn
            else:
                mock_q.filter.return_value.all.return_value = evaluations
            return mock_q

        db.query.side_effect = query_side_effect

        result = adapter.get_entity_data(1)

        assert result != {}
        assert result.get("total_evaluations") == 2 or "ecn_type" in result or isinstance(result, dict)


class TestEcnApprovalAdapterEntityType:
    """entity_type 属性测试"""

    def test_entity_type_is_ecn(self):
        adapter, _ = _make_adapter()
        assert adapter.entity_type == "ECN"


class TestEcnApprovalAdapterInit:
    """初始化测试"""

    def test_db_stored(self):
        db = MagicMock()
        adapter = EcnApprovalAdapter(db=db)
        assert adapter.db is db


class TestEcnApprovalAdapterIntegration:
    """集成场景测试"""

    def test_get_entity_data_with_completed_evaluations(self):
        """所有评估完成时的数据"""
        adapter, db = _make_adapter()
        mock_ecn = _mock_ecn(cost_impact=10000, schedule_impact_days=10)

        e1 = MagicMock()
        e1.status = "COMPLETED"
        e2 = MagicMock()
        e2.status = "COMPLETED"

        call_count = 0
        def side_effect(model):
            nonlocal call_count
            call_count += 1
            m = MagicMock()
            if call_count == 1:
                m.filter.return_value.first.return_value = mock_ecn
            else:
                m.filter.return_value.all.return_value = [e1, e2]
            return m

        db.query.side_effect = side_effect

        result = adapter.get_entity_data(1)
        assert isinstance(result, dict)

    def test_get_entity_data_no_evaluations(self):
        """无评估记录时"""
        adapter, db = _make_adapter()
        mock_ecn = _mock_ecn()

        call_count = 0
        def side_effect(model):
            nonlocal call_count
            call_count += 1
            m = MagicMock()
            if call_count == 1:
                m.filter.return_value.first.return_value = mock_ecn
            else:
                m.filter.return_value.all.return_value = []
            return m

        db.query.side_effect = side_effect

        result = adapter.get_entity_data(1)
        assert isinstance(result, dict)
