# -*- coding: utf-8 -*-
"""relationship_engine 深度测试"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.sales.engines.base import RecommendationPriority, RecommendationType
from app.services.sales.engines.relationship_engine import RelationshipEngine


class FakeQuery:
    def __init__(self, all_value=None):
        self._all_value = all_value or []

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value


class TestRelationshipEngineDeep:
    def test_get_recommendations_groups_latest_contract_by_customer(self):
        old = datetime.now() - timedelta(days=220)
        recent = datetime.now() - timedelta(days=20)
        customer1 = SimpleNamespace(id=1, customer_name="客户A")
        customer2 = SimpleNamespace(id=2, customer_name="客户B")
        contracts = [
            SimpleNamespace(customer_id=1, customer=customer1, created_at=old),
            SimpleNamespace(customer_id=1, customer=customer1, created_at=recent),
            SimpleNamespace(customer_id=2, customer=customer2, created_at=old),
            SimpleNamespace(customer_id=None, customer=customer2, created_at=old),
        ]
        db = Mock()
        db.query.return_value = FakeQuery(all_value=contracts)
        engine = RelationshipEngine(db)

        recs = engine.get_recommendations(3)

        assert len(recs) == 2
        assert all(r.type == RecommendationType.RELATIONSHIP for r in recs)
        titles = [r.title for r in recs]
        assert "客户关系需维护: 客户A" in titles
        assert "客户关系需维护: 客户B" in titles

    def test_get_recommendations_swallows_errors(self):
        db = Mock()
        db.query.side_effect = RuntimeError("boom")
        engine = RelationshipEngine(db)

        assert engine.get_recommendations(1) == []

    def test_check_customer_activity_boundaries(self):
        engine = RelationshipEngine(Mock())
        silent_customer = SimpleNamespace(id=9, customer_name="沉默客户")
        active_customer = SimpleNamespace(id=10, customer_name="活跃客户")
        silent = SimpleNamespace(customer=silent_customer, created_at=datetime.now() - timedelta(days=181))
        active = SimpleNamespace(customer=active_customer, created_at=datetime.now() - timedelta(days=180))
        missing_customer = SimpleNamespace(customer=None, created_at=datetime.now() - timedelta(days=500))
        missing_date = SimpleNamespace(customer=silent_customer, created_at=None)

        recs1 = engine._check_customer_activity(silent)
        recs2 = engine._check_customer_activity(active)
        recs3 = engine._check_customer_activity(missing_customer)
        recs4 = engine._check_customer_activity(missing_date)

        assert len(recs1) == 1
        assert recs1[0].priority == RecommendationPriority.MEDIUM
        assert recs1[0].data["days_since_last_contract"] >= 181
        assert recs2 == []
        assert recs3 == []
        assert recs4 == []
