# -*- coding: utf-8 -*-
"""cross_sell_engine 深度测试"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.sales.engines.base import RecommendationPriority, RecommendationType
from app.services.sales.engines.cross_sell_engine import CrossSellEngine


class FakeQuery:
    def __init__(self, all_value=None):
        self._all_value = all_value or []

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value


class TestCrossSellEngineDeep:
    def test_get_recommendations_dedupes_customer_and_skips_missing_customer(self):
        customer1 = SimpleNamespace(id=1, customer_name="客户A")
        customer2 = SimpleNamespace(id=2, customer_name="客户B")
        contracts = [
            SimpleNamespace(id=11, customer_id=1, customer=customer1, created_at=datetime.now() - timedelta(days=10)),
            SimpleNamespace(id=12, customer_id=1, customer=customer1, created_at=datetime.now() - timedelta(days=20)),
            SimpleNamespace(id=13, customer_id=2, customer=customer2, created_at=datetime.now() - timedelta(days=30)),
            SimpleNamespace(id=14, customer_id=3, customer=None, created_at=datetime.now() - timedelta(days=5)),
        ]
        db = Mock()
        db.query.return_value = FakeQuery(all_value=contracts)
        engine = CrossSellEngine(db)

        recs = engine.get_recommendations(7)

        assert len(recs) == 2
        assert all(r.type == RecommendationType.CROSS_SELL for r in recs)
        titles = [r.title for r in recs]
        assert "交叉销售机会: 客户A" in titles
        assert "交叉销售机会: 客户B" in titles

    def test_get_recommendations_swallows_errors(self):
        db = Mock()
        db.query.side_effect = RuntimeError("boom")
        engine = CrossSellEngine(db)

        assert engine.get_recommendations(1) == []

    def test_generate_cross_sell_for_customer(self):
        engine = CrossSellEngine(Mock())
        customer = SimpleNamespace(id=9, customer_name="客户C")
        contract = SimpleNamespace(id=21)

        recs = engine._generate_cross_sell_for_customer(customer, contract)

        assert len(recs) == 1
        assert recs[0].priority == RecommendationPriority.LOW
        assert recs[0].entity_type == "customer"
        assert recs[0].data["recent_contract_id"] == 21
