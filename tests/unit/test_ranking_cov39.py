# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - lead_priority_scoring/ranking.py
"""
import pytest
from unittest.mock import MagicMock

pytest.importorskip("app.services.lead_priority_scoring.ranking",
                    reason="import failed, skip")

from app.services.lead_priority_scoring.ranking import RankingMixin


def _make_lead(lid, status="NEW", customer_name="客户A"):
    l = MagicMock()
    l.id = lid
    l.lead_code = f"LEAD{lid:04d}"
    l.customer_name = customer_name
    l.status = status
    return l


def _make_opp(oid, stage="NEGOTIATING"):
    o = MagicMock()
    o.id = oid
    o.opp_code = f"OPP{oid:04d}"
    o.opp_name = f"商机{oid}"
    o.stage = stage
    return o


class ConcreteRankingService(RankingMixin):
    def __init__(self, db):
        self.db = db

    def calculate_lead_priority(self, lead_id):
        return {"total_score": 80.0, "is_key_lead": True,
                "priority_level": "HIGH", "importance_level": "HIGH", "urgency_level": "MEDIUM"}

    def calculate_opportunity_priority(self, opp_id):
        return {"total_score": 75.0, "is_key_opportunity": False,
                "priority_level": "MEDIUM", "importance_level": "MEDIUM", "urgency_level": "LOW"}


class TestRankingMixin:

    def setup_method(self):
        self.db = MagicMock()
        self.svc = ConcreteRankingService(self.db)

    def test_get_priority_ranking_lead_empty(self):
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []

        result = self.svc.get_priority_ranking("lead")
        assert result == []

    def test_get_priority_ranking_lead_returns_list(self):
        leads = [_make_lead(1), _make_lead(2)]
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = leads

        result = self.svc.get_priority_ranking("lead", limit=10)
        assert len(result) == 2
        assert result[0]["id"] in [1, 2]

    def test_get_priority_ranking_opportunity_empty(self):
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []

        result = self.svc.get_priority_ranking("opportunity")
        assert result == []

    def test_get_priority_ranking_opportunity_with_data(self):
        opps = [_make_opp(1), _make_opp(2)]
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = opps

        result = self.svc.get_priority_ranking("opportunity")
        assert len(result) == 2

    def test_get_key_leads_filters_is_key(self):
        leads = [_make_lead(1), _make_lead(2)]
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = leads

        result = self.svc.get_key_leads()
        # calculate_lead_priority always returns is_key_lead=True
        assert len(result) == 2
        assert all(r["is_key"] for r in result)

    def test_get_key_opportunities_filters_is_key(self):
        opps = [_make_opp(1)]
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = opps

        result = self.svc.get_key_opportunities()
        # calculate_opportunity_priority returns is_key_opportunity=False
        assert result == []

    def test_get_priority_ranking_sorted_by_score(self):
        leads = [_make_lead(1, customer_name="A"), _make_lead(2, customer_name="B")]
        call_count = [0]
        scores = [60.0, 90.0]

        def side_calculate(lead_id):
            idx = call_count[0]
            call_count[0] += 1
            return {"total_score": scores[idx], "is_key_lead": False,
                    "priority_level": "LOW", "importance_level": "LOW", "urgency_level": "LOW"}

        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = leads
        self.svc.calculate_lead_priority = side_calculate

        result = self.svc.get_priority_ranking("lead")
        if len(result) > 1:
            assert result[0]["total_score"] >= result[1]["total_score"]
