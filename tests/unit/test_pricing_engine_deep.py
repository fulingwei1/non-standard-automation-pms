# -*- coding: utf-8 -*-
"""pricing_engine 深度测试"""

from types import SimpleNamespace
from unittest.mock import Mock

from app.services.sales.engines.base import RecommendationPriority, RecommendationType
from app.services.sales.engines.pricing_engine import PricingEngine


class FakeQuery:
    def __init__(self, all_value=None):
        self._all_value = all_value or []

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value


class TestPricingEngineDeep:
    def test_get_recommendations_uses_current_or_latest_version(self):
        q1 = SimpleNamespace(
            id=1,
            quote_code="Q1",
            current_version=SimpleNamespace(margin_rate=10),
            versions=[],
        )
        q2 = SimpleNamespace(
            id=2,
            quote_code="Q2",
            current_version=None,
            versions=[SimpleNamespace(version_number=1, margin_rate=30), SimpleNamespace(version_number=3, margin_rate=12)],
        )
        q3 = SimpleNamespace(
            id=3,
            quote_code="Q3",
            current_version=None,
            versions=[],
        )
        db = Mock()
        db.query.return_value = FakeQuery(all_value=[q1, q2, q3])
        engine = PricingEngine(db)

        recs = engine.get_recommendations(5)

        assert len(recs) == 2
        assert all(r.type == RecommendationType.PRICING for r in recs)
        by_title = {r.title: r for r in recs}
        assert by_title["报价毛利率过低: Q1"].priority == RecommendationPriority.HIGH
        assert by_title["报价毛利率过低: Q1"].data["margin_rate"] == 10.0
        assert by_title["报价毛利率过低: Q2"].data["margin_rate"] == 12.0

    def test_get_recommendations_swallows_errors(self):
        db = Mock()
        db.query.side_effect = RuntimeError("boom")
        engine = PricingEngine(db)

        assert engine.get_recommendations(1) == []

    def test_get_latest_version_and_low_margin_boundary(self):
        engine = PricingEngine(Mock())
        quote_with_current = SimpleNamespace(current_version=SimpleNamespace(version_number=2), versions=[SimpleNamespace(version_number=9)])
        quote_with_versions = SimpleNamespace(current_version=None, versions=[SimpleNamespace(version_number=1), SimpleNamespace(version_number=4)])
        quote_empty = SimpleNamespace(current_version=None, versions=[])
        quote = SimpleNamespace(id=8, quote_code="Q8")

        assert engine._get_latest_version(quote_with_current).version_number == 2
        assert engine._get_latest_version(quote_with_versions).version_number == 4
        assert engine._get_latest_version(quote_empty) is None

        low = engine._check_low_margin(quote, SimpleNamespace(margin_rate=14.9))
        ok = engine._check_low_margin(quote, SimpleNamespace(margin_rate=15))
        none_margin = engine._check_low_margin(quote, SimpleNamespace(margin_rate=None))

        assert len(low) == 1
        assert low[0].priority == RecommendationPriority.HIGH
        assert ok == []
        assert len(none_margin) == 1
        assert none_margin[0].data["margin_rate"] == 0.0
