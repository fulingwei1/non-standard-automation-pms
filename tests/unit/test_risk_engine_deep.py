# -*- coding: utf-8 -*-
"""risk_engine 深度测试"""

from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.sales.engines.base import RecommendationPriority, RecommendationType
from app.services.sales.engines.risk_engine import RiskEngine


class FakeQuery:
    def __init__(self, all_value=None):
        self._all_value = all_value or []

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value


class TestRiskEngineDeep:
    def test_get_recommendations_collects_contract_and_invoice_alerts(self):
        engine = RiskEngine(Mock())
        engine._get_expiring_contract_alerts = Mock(return_value=[SimpleNamespace(type=RecommendationType.RISK)])
        engine._get_overdue_invoice_alerts = Mock(return_value=[SimpleNamespace(type=RecommendationType.RISK), SimpleNamespace(type=RecommendationType.RISK)])

        recs = engine.get_recommendations(1)

        assert len(recs) == 3
        assert all(r.type == RecommendationType.RISK for r in recs)

    def test_get_recommendations_swallows_errors(self):
        engine = RiskEngine(Mock())
        engine._get_expiring_contract_alerts = Mock(side_effect=RuntimeError("boom"))

        recs = engine.get_recommendations(1)

        assert recs == []

    def test_get_expiring_contract_alerts_priority_split(self):
        today = date.today()
        contracts = [
            SimpleNamespace(id=1, contract_code="C1", expiry_date=today + timedelta(days=5)),
            SimpleNamespace(id=2, contract_code="C2", expiry_date=today + timedelta(days=20)),
        ]
        db = Mock()
        db.query.return_value = FakeQuery(all_value=contracts)
        engine = RiskEngine(db)

        recs = engine._get_expiring_contract_alerts(8)

        assert len(recs) == 2
        assert recs[0].priority == RecommendationPriority.HIGH
        assert recs[1].priority == RecommendationPriority.MEDIUM
        assert recs[0].data["days_to_expiry"] == 5

    def test_get_overdue_invoice_alerts_groups_by_contract_and_filters_owner(self):
        today = date.today()
        contract1 = SimpleNamespace(id=11, contract_code="CT1", sales_owner_id=9)
        contract2 = SimpleNamespace(id=12, contract_code="CT2", sales_owner_id=9)
        other = SimpleNamespace(id=13, contract_code="CT3", sales_owner_id=99)
        invoices = [
            SimpleNamespace(contract=contract1, contract_id=11, amount=100, due_date=today - timedelta(days=10)),
            SimpleNamespace(contract=contract1, contract_id=11, amount=50, due_date=today - timedelta(days=40)),
            SimpleNamespace(contract=contract2, contract_id=12, amount=80, due_date=today - timedelta(days=3)),
            SimpleNamespace(contract=other, contract_id=13, amount=999, due_date=today - timedelta(days=60)),
            SimpleNamespace(contract=None, contract_id=14, amount=20, due_date=today - timedelta(days=5)),
        ]
        db = Mock()
        db.query.return_value = FakeQuery(all_value=invoices)
        engine = RiskEngine(db)

        recs = engine._get_overdue_invoice_alerts(9)

        assert len(recs) == 2
        by_code = {r.title: r for r in recs}
        assert by_code["发票逾期: CT1"].priority == RecommendationPriority.CRITICAL
        assert by_code["发票逾期: CT1"].data["overdue_count"] == 2
        assert by_code["发票逾期: CT1"].data["total_overdue"] == 150.0
        assert by_code["发票逾期: CT1"].data["max_overdue_days"] == 40
        assert by_code["发票逾期: CT2"].priority == RecommendationPriority.HIGH
