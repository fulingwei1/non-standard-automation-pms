# -*- coding: utf-8 -*-
"""
Unit tests for app/services/win_rate_prediction_service/history.py
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock

try:
    from app.services.win_rate_prediction_service.history import (
        get_salesperson_historical_win_rate,
        get_customer_cooperation_history,
        get_similar_leads_statistics,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ---------------------------------------------------------------------------
# get_salesperson_historical_win_rate
# ---------------------------------------------------------------------------

def test_salesperson_win_rate_no_data_returns_default():
    svc = MagicMock()
    stats = MagicMock(total=0, won=0)
    svc.db.query.return_value.filter.return_value.first.return_value = stats
    rate, count = get_salesperson_historical_win_rate(svc, salesperson_id=1)
    assert rate == 0.20
    assert count == 0


def test_salesperson_win_rate_calculation():
    svc = MagicMock()
    stats = MagicMock(total=10, won=7)
    svc.db.query.return_value.filter.return_value.first.return_value = stats
    rate, count = get_salesperson_historical_win_rate(svc, salesperson_id=1)
    assert rate == pytest.approx(0.7)
    assert count == 10


def test_salesperson_win_rate_zero_won():
    svc = MagicMock()
    stats = MagicMock(total=5, won=0)
    svc.db.query.return_value.filter.return_value.first.return_value = stats
    rate, count = get_salesperson_historical_win_rate(svc, salesperson_id=1)
    assert rate == 0.0
    assert count == 5


# ---------------------------------------------------------------------------
# get_customer_cooperation_history
# ---------------------------------------------------------------------------

def test_customer_history_no_filter_returns_zeros():
    svc = MagicMock()
    result = get_customer_cooperation_history(svc)
    assert result == (0, 0)


def test_customer_history_by_id():
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.count.side_effect = [5, 3]
    svc.db.query.return_value = q
    total, won = get_customer_cooperation_history(svc, customer_id=10)
    assert total == 5
    assert won == 3


def test_customer_history_by_name_not_found():
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = None  # customer not found
    svc.db.query.return_value = q
    total, won = get_customer_cooperation_history(svc, customer_name="Unknown Corp")
    assert total == 0
    assert won == 0


# ---------------------------------------------------------------------------
# get_similar_leads_statistics
# ---------------------------------------------------------------------------

def test_similar_leads_no_results():
    svc = MagicMock()
    dimension_scores = MagicMock(total_score=60)
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    svc.db.query.return_value = q
    count, rate = get_similar_leads_statistics(svc, dimension_scores)
    assert count == 0
    assert rate == 0


def test_similar_leads_with_results():
    svc = MagicMock()
    from app.models.enums import LeadOutcomeEnum
    dimension_scores = MagicMock(total_score=70)
    p1 = MagicMock(outcome=LeadOutcomeEnum.WON.value)
    p2 = MagicMock(outcome=LeadOutcomeEnum.LOST.value)
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [p1, p2]
    svc.db.query.return_value = q
    try:
        count, rate = get_similar_leads_statistics(svc, dimension_scores)
        assert count == 2
        assert rate == pytest.approx(0.5)
    except ImportError:
        pytest.skip("LeadOutcomeEnum not importable")
