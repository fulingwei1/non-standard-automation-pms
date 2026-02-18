# -*- coding: utf-8 -*-
"""第十五批: lead_priority_scoring/opportunity_scoring 单元测试"""
import pytest

pytest.importorskip("app.services.lead_priority_scoring.opportunity_scoring")

from unittest.mock import MagicMock
from decimal import Decimal
from app.services.lead_priority_scoring.opportunity_scoring import OpportunityScoringMixin
from app.services.lead_priority_scoring.constants import ScoringConstants
from app.services.lead_priority_scoring.scoring_helpers import ScoringHelpersMixin
from app.services.lead_priority_scoring.level_determination import LevelDeterminationMixin
from app.services.lead_priority_scoring.descriptions import DescriptionsMixin


class ConcreteOpportunityService(
    ScoringConstants,
    ScoringHelpersMixin,
    LevelDeterminationMixin,
    DescriptionsMixin,
    OpportunityScoringMixin,
):
    def __init__(self, db):
        self.db = db


def test_calculate_opportunity_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    svc = ConcreteOpportunityService(db)
    with pytest.raises(ValueError, match="不存在"):
        svc.calculate_opportunity_priority(99)


def _make_opp_db(opp, customer=None):
    """Build a mock DB that handles Opportunity, Customer, and count() calls."""
    db = MagicMock()

    def mock_query(model):
        from app.models.sales import Opportunity
        from app.models.project import Customer, Project
        q = MagicMock()
        # Always return 0 for count() to avoid MagicMock comparison issues
        q.filter.return_value.count.return_value = 0
        q.filter.return_value.filter.return_value.count.return_value = 0
        if model is Opportunity:
            q.filter.return_value.first.return_value = opp
        elif model is Customer:
            q.filter.return_value.first.return_value = customer
        else:
            q.filter.return_value.first.return_value = None
        return q

    db.query.side_effect = mock_query
    return db


def test_calculate_opportunity_basic():
    opp = MagicMock()
    opp.customer_id = 1
    opp.est_amount = Decimal("800000")
    opp.score = 80
    opp.requirement_maturity = 4
    opp.delivery_window = "Q1"
    customer = MagicMock()
    customer.credit_level = "A"
    customer.is_strategic = False
    db = _make_opp_db(opp, customer)
    svc = ConcreteOpportunityService(db)
    result = svc.calculate_opportunity_priority(1)
    assert "customer_importance" in result["scores"]
    assert "contract_amount" in result["scores"]
    assert "win_rate" in result["scores"]
    assert result["total_score"] > 0


def test_calculate_opportunity_no_customer():
    opp = MagicMock()
    opp.customer_id = 999
    opp.est_amount = Decimal("100000")
    opp.score = 50
    opp.requirement_maturity = 3
    opp.delivery_window = None
    db = _make_opp_db(opp, customer=None)
    svc = ConcreteOpportunityService(db)
    result = svc.calculate_opportunity_priority(1)
    assert result["scores"]["customer_importance"]["score"] == 5


def test_calculate_opportunity_zero_score():
    opp = MagicMock()
    opp.customer_id = 1
    opp.est_amount = Decimal("0")
    opp.score = None
    opp.requirement_maturity = None
    opp.delivery_window = None
    db = _make_opp_db(opp, customer=None)
    svc = ConcreteOpportunityService(db)
    result = svc.calculate_opportunity_priority(1)
    assert isinstance(result["total_score"], (int, float))
