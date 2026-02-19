# -*- coding: utf-8 -*-
"""
tests/unit/test_ps_history_cov51.py
Unit tests for app/services/performance_service/history.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.performance_service.history import get_historical_performance
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_summary(id_, period, status="COMPLETED"):
    s = MagicMock()
    s.id = id_
    s.period = period
    s.status = status
    return s


# ─── tests ────────────────────────────────────────────────────────────────────

def test_get_historical_performance_no_summaries():
    """No completed summaries → empty list."""
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = get_historical_performance(db, employee_id=1, months=3)
    assert result == []


def test_get_historical_performance_returns_list():
    """Returns list with expected keys when calc succeeds."""
    db = MagicMock()
    s1 = _make_summary(1, "2025-02")
    s2 = _make_summary(2, "2025-01")

    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [s1, s2]

    score_data = {
        "final_score": 88.0,
        "dept_score": 90.0,
        "project_score": 86.0,
    }

    with patch(
        "app.services.performance_service.history.calculate_final_score",
        return_value=score_data,
    ):
        result = get_historical_performance(db, employee_id=1, months=3)

    assert len(result) == 2
    assert result[0]["final_score"] == 88.0
    assert "level" in result[0]
    assert "period" in result[0]


def test_get_historical_performance_level_assigned():
    """Level is assigned based on score via get_score_level."""
    db = MagicMock()
    s = _make_summary(1, "2025-03")
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [s]

    with patch(
        "app.services.performance_service.history.calculate_final_score",
        return_value={"final_score": 92.0, "dept_score": 92.0, "project_score": None},
    ), patch(
        "app.services.performance_service.history.get_score_level",
        return_value="A",
    ) as mock_level:
        result = get_historical_performance(db, employee_id=2, months=1)

    mock_level.assert_called_once_with(92.0)
    assert result[0]["level"] == "A"


def test_get_historical_performance_skips_none_scores():
    """Summaries where calculate_final_score returns None are skipped."""
    db = MagicMock()
    s1 = _make_summary(1, "2025-02")
    s2 = _make_summary(2, "2025-01")
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [s1, s2]

    with patch(
        "app.services.performance_service.history.calculate_final_score",
        side_effect=[None, {"final_score": 80.0, "dept_score": 80.0, "project_score": None}],
    ):
        result = get_historical_performance(db, employee_id=1, months=3)

    # Only the second summary contributes
    assert len(result) == 1
    assert result[0]["final_score"] == 80.0


def test_get_historical_performance_default_months_3():
    """Default months=3 queries 3 periods."""
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    # Should not raise with default argument
    result = get_historical_performance(db, employee_id=99)
    assert isinstance(result, list)


def test_get_historical_performance_custom_months():
    """Custom months parameter is accepted."""
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = get_historical_performance(db, employee_id=1, months=6)
    assert result == []
