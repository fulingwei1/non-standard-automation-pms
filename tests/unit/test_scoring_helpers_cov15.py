# -*- coding: utf-8 -*-
"""第十五批: lead_priority_scoring/scoring_helpers 单元测试"""
import pytest

pytest.importorskip("app.services.lead_priority_scoring.scoring_helpers")

from unittest.mock import MagicMock
from app.services.lead_priority_scoring.scoring_helpers import ScoringHelpersMixin
from app.services.lead_priority_scoring.constants import ScoringConstants


class ConcreteScoringService(ScoringConstants, ScoringHelpersMixin):
    def __init__(self, db):
        self.db = db


def make_svc():
    return ConcreteScoringService(MagicMock())


def test_get_customer_score_a_level():
    svc = make_svc()
    customer = MagicMock()
    customer.credit_level = "A"
    assert svc._get_customer_score(customer) == 20


def test_get_customer_score_c_level():
    svc = make_svc()
    customer = MagicMock()
    customer.credit_level = "c"  # lowercase should be uppercased
    assert svc._get_customer_score(customer) == 10


def test_get_customer_score_no_customer():
    svc = make_svc()
    assert svc._get_customer_score(None) == 5


def test_get_amount_score_large():
    svc = make_svc()
    score = svc._get_amount_score(1_500_000)
    assert score == 25


def test_get_amount_score_medium():
    svc = make_svc()
    score = svc._get_amount_score(300_000)
    assert score == 15


def test_get_amount_score_small():
    svc = make_svc()
    score = svc._get_amount_score(50_000)
    assert score == 5


def test_get_win_rate_score_high():
    svc = make_svc()
    score = svc._get_win_rate_score(0.85)
    assert score == 20


def test_get_win_rate_score_low():
    svc = make_svc()
    score = svc._get_win_rate_score(0.2)
    assert score == 5


def test_calculate_customer_importance_no_opportunity_no_name():
    svc = make_svc()
    lead = MagicMock()
    lead.opportunities = []
    lead.customer_name = None
    score = svc._calculate_customer_importance(lead)
    assert score == 5


def test_calculate_contract_amount_score_no_opportunity():
    svc = make_svc()
    lead = MagicMock()
    lead.opportunities = []
    score = svc._calculate_contract_amount_score(lead)
    assert score == 5
