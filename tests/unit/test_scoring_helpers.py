# -*- coding: utf-8 -*-
"""ScoringHelpersMixin 单元测试"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, PropertyMock
import pytest

from app.services.lead_priority_scoring.scoring_helpers import ScoringHelpersMixin


class ConcreteScoringHelpers(ScoringHelpersMixin):
    CUSTOMER_IMPORTANCE_SCORES = {"A": 20, "B": 15, "C": 10}
    CONTRACT_AMOUNT_SCORES = [(1000000, 20), (500000, 15), (100000, 10)]
    WIN_RATE_SCORES = [(0.8, 20), (0.5, 15), (0.3, 10)]

    def __init__(self, db):
        self.db = db


class TestScoringHelpers:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = ConcreteScoringHelpers(self.db)

    def test_get_customer_score_none(self):
        assert self.svc._get_customer_score(None) == 5

    def test_get_customer_score_level_a(self):
        customer = MagicMock()
        customer.credit_level = "A"
        assert self.svc._get_customer_score(customer) == 20

    def test_get_amount_score(self):
        assert self.svc._get_amount_score(2000000) == 20
        assert self.svc._get_amount_score(600000) == 15
        assert self.svc._get_amount_score(50) == 5

    def test_get_win_rate_score(self):
        assert self.svc._get_win_rate_score(0.9) == 20
        assert self.svc._get_win_rate_score(0.6) == 15
        assert self.svc._get_win_rate_score(0.1) == 5

    def test_calculate_requirement_maturity_score(self):
        lead = MagicMock()
        lead.completeness = 90
        assert self.svc._calculate_requirement_maturity_score(lead) == 15
        lead.completeness = 0
        assert self.svc._calculate_requirement_maturity_score(lead) == 3

    def test_calculate_urgency_score(self):
        lead = MagicMock()
        lead.next_action_at = MagicMock()
        lead.next_action_at.date.return_value = date.today() + timedelta(days=1)
        assert self.svc._calculate_urgency_score(lead) == 10

    def test_calculate_urgency_score_no_date(self):
        lead = MagicMock()
        lead.next_action_at = None
        assert self.svc._calculate_urgency_score(lead) == 7

    def test_calculate_opportunity_urgency(self):
        opp = MagicMock()
        opp.delivery_window = "紧急交付"
        assert self.svc._calculate_opportunity_urgency(opp) == 10
        opp.delivery_window = "正常排期"
        assert self.svc._calculate_opportunity_urgency(opp) == 7
        opp.delivery_window = None
        assert self.svc._calculate_opportunity_urgency(opp) == 7

    def test_calculate_relationship_score_no_customer(self):
        lead = MagicMock()
        lead.customer_name = None
        assert self.svc._calculate_relationship_score(lead) == 5
