# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from app.services.lead_priority_scoring.opportunity_scoring import OpportunityScoringMixin


class FakeService(OpportunityScoringMixin):
    REQUIREMENT_MATURITY_SCORES = {1: 3, 2: 6, 3: 8, 4: 12, 5: 15}

    def __init__(self, db):
        self.db = db

    def _get_customer_score(self, customer):
        return 15

    def _get_amount_score(self, amount):
        return 20

    def _get_win_rate_score(self, rate):
        return 15

    def _calculate_opportunity_urgency(self, opp):
        return 7

    def _calculate_opportunity_relationship(self, opp, customer):
        return 8

    def _get_relationship_description_for_opp(self, opp, customer):
        return "良好"

    def _determine_priority_level(self, total, urgency):
        return "HIGH"

    def _determine_importance_level(self, total):
        return "HIGH"

    def _determine_urgency_level(self, urgency):
        return "MEDIUM"


class TestOpportunityScoringMixin:
    def setup_method(self):
        self.db = MagicMock()
        self.service = FakeService(self.db)

    def test_opportunity_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            self.service.calculate_opportunity_priority(999)

    def test_calculate_priority_success(self):
        opp = MagicMock()
        opp.id = 1
        opp.opp_code = "OPP001"
        opp.customer_id = 1
        opp.est_amount = Decimal("100000")
        opp.score = 80
        opp.requirement_maturity = 4
        opp.delivery_window = "2024-Q1"

        customer = MagicMock()
        customer.credit_level = "A"

        self.db.query.return_value.filter.return_value.first.side_effect = [opp, customer]
        result = self.service.calculate_opportunity_priority(1)
        assert result["total_score"] > 0
        assert result["opp_code"] == "OPP001"
        assert "scores" in result
