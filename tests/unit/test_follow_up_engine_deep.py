# -*- coding: utf-8 -*-
"""follow_up_engine 深度测试"""

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.sales.engines.base import RecommendationPriority, RecommendationType
from app.services.sales.engines.follow_up_engine import FollowUpEngine


class FakeQuery:
    def __init__(self, all_value=None):
        self._all_value = all_value or []

    def options(self, *args, **kwargs):
        return self

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value


class TestFollowUpEngineDeep:
    def test_get_recommendations_collects_all_rules(self):
        today = date.today()
        opps = [
            SimpleNamespace(
                id=1,
                opp_name="A",
                expected_close_date=today + timedelta(days=3),
                updated_at=datetime.now() - timedelta(days=20),
                est_amount=800000,
                stage="DISCOVERY",
            ),
            SimpleNamespace(
                id=2,
                opp_name="B",
                expected_close_date=today + timedelta(days=10),
                updated_at=datetime.now() - timedelta(days=2),
                est_amount=100000,
                stage="NEGOTIATION",
            ),
        ]
        db = Mock()
        db.query.return_value = FakeQuery(all_value=opps)
        engine = FollowUpEngine(db)

        recs = engine.get_recommendations(7)

        assert len(recs) == 3
        titles = [r.title for r in recs]
        assert any("商机即将到期: A" in t for t in titles)
        assert any("商机停滞: A" in t for t in titles)
        assert any("高价值商机需加速: A" in t for t in titles)
        assert all(r.type == RecommendationType.FOLLOW_UP for r in recs)

    def test_get_recommendations_swallows_query_error(self):
        db = Mock()
        db.query.side_effect = RuntimeError("boom")
        engine = FollowUpEngine(db)

        recs = engine.get_recommendations(1)

        assert recs == []

    def test_close_date_rule_only_within_seven_days(self):
        engine = FollowUpEngine(Mock())
        today = date.today()
        opp = SimpleNamespace(id=3, opp_name="C", expected_close_date=today + timedelta(days=7))

        recs = engine._check_close_date_approaching(opp, today)

        assert len(recs) == 1
        assert recs[0].priority == RecommendationPriority.HIGH
        assert recs[0].data["days_to_close"] == 7

    def test_stagnant_and_high_value_rules_boundaries(self):
        engine = FollowUpEngine(Mock())
        stagnant = SimpleNamespace(id=4, opp_name="D", updated_at=datetime.now() - timedelta(days=15))
        active = SimpleNamespace(id=5, opp_name="E", updated_at=datetime.now() - timedelta(days=14))
        high_value = SimpleNamespace(id=6, opp_name="F", est_amount=500001, stage="QUALIFICATION")
        not_high = SimpleNamespace(id=7, opp_name="G", est_amount=500000, stage="DISCOVERY")

        recs1 = engine._check_stagnant_opportunity(stagnant)
        recs2 = engine._check_stagnant_opportunity(active)
        recs3 = engine._check_high_value_opportunity(high_value)
        recs4 = engine._check_high_value_opportunity(not_high)

        assert len(recs1) == 1 and recs1[0].priority == RecommendationPriority.MEDIUM
        assert recs2 == []
        assert len(recs3) == 1 and recs3[0].data["est_amount"] == 500001.0
        assert recs4 == []
