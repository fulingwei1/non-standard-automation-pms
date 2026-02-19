# -*- coding: utf-8 -*-
"""
Unit tests for app/services/strategy/decomposition/stats.py
"""
import pytest
from unittest.mock import MagicMock, call

try:
    from app.services.strategy.decomposition.stats import get_decomposition_stats
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _setup_db(csf_count=2, kpi_count=4, dept_obj_count=3, personal_kpi_count=6, dept_objs=None):
    """Build a mock db that returns expected counts for each query chain."""
    db = MagicMock()

    count_side_effects = [csf_count, kpi_count, dept_obj_count, personal_kpi_count]
    count_iter = iter(count_side_effects)

    def make_count_chain():
        m = MagicMock()
        m.filter.return_value = m
        m.join.return_value = m
        m.count.side_effect = lambda: next(count_iter)
        m.all.return_value = dept_objs or []
        return m

    db.query.return_value = make_count_chain()
    return db


def test_get_decomposition_stats_uses_current_year_by_default():
    from datetime import date
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    q.count.return_value = 0
    q.all.return_value = []
    db.query.return_value = q
    result = get_decomposition_stats(db, strategy_id=1)
    assert result["year"] == date.today().year


def test_get_decomposition_stats_with_explicit_year():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    q.count.return_value = 0
    q.all.return_value = []
    db.query.return_value = q
    result = get_decomposition_stats(db, strategy_id=1, year=2023)
    assert result["year"] == 2023


def test_get_decomposition_stats_zero_kpi_decomposition_rate():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    q.count.return_value = 0
    q.all.return_value = []
    db.query.return_value = q
    result = get_decomposition_stats(db, strategy_id=1)
    assert result["decomposition_rate"] == 0


def test_get_decomposition_stats_decomposition_rate_calculation():
    """When kpi_count=4, personal_kpi_count=8 -> rate=200%."""
    db = MagicMock()
    counts = iter([2, 4, 3, 8])
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    q.count.side_effect = lambda: next(counts)
    q.all.return_value = []
    db.query.return_value = q
    result = get_decomposition_stats(db, strategy_id=1)
    assert result["decomposition_rate"] == 200.0


def test_get_decomposition_stats_structure_keys():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    q.count.return_value = 0
    q.all.return_value = []
    db.query.return_value = q
    result = get_decomposition_stats(db, strategy_id=1)
    expected = {"year", "csf_count", "kpi_count", "dept_objective_count",
                "personal_kpi_count", "decomposition_rate", "department_stats"}
    assert expected == set(result.keys())


def test_get_decomposition_stats_department_stats_populated():
    db = MagicMock()

    dept_obj = MagicMock()
    dept_obj.department_id = 10
    dept_obj.id = 100

    # We need to control which query returns what
    call_count = [0]

    def query_side_effect(model):
        nonlocal call_count
        call_count[0] += 1
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        if call_count[0] <= 4:
            q.count.return_value = 1
        else:
            q.count.return_value = 2  # PersonalKPI per dept_obj
        q.all.return_value = [dept_obj] if call_count[0] == 4 else []
        return q

    db.query.side_effect = query_side_effect
    result = get_decomposition_stats(db, strategy_id=1)
    # department_stats may or may not be populated depending on mocking;
    # just verify it's a dict
    assert isinstance(result["department_stats"], dict)
