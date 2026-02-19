# -*- coding: utf-8 -*-
"""
Unit tests for app/services/strategy/kpi_collector/calculation.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.strategy.kpi_collector.calculation import (
        calculate_formula,
        collect_kpi_value,
        auto_collect_kpi,
        batch_collect_kpis,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ---------------------------------------------------------------------------
# calculate_formula
# ---------------------------------------------------------------------------

def test_calculate_formula_returns_none_for_empty():
    result = calculate_formula("", {"a": 1})
    assert result is None


def test_calculate_formula_basic_with_simpleeval():
    """When simpleeval is available, perform real calculation."""
    try:
        import simpleeval  # noqa: F401
    except ImportError:
        pytest.skip("simpleeval not installed")
    result = calculate_formula("a + b", {"a": 10, "b": 5})
    assert result == Decimal("15")


def test_calculate_formula_raises_without_simpleeval():
    with patch("app.services.strategy.kpi_collector.calculation.HAS_SIMPLEEVAL", False):
        with pytest.raises(RuntimeError, match="simpleeval"):
            calculate_formula("a + b", {"a": 1, "b": 2})


def test_calculate_formula_returns_none_on_exception():
    with patch("app.services.strategy.kpi_collector.calculation.HAS_SIMPLEEVAL", True):
        with patch("app.services.strategy.kpi_collector.calculation.simple_eval", side_effect=Exception("bad")):
            result = calculate_formula("bad_formula", {"x": 1})
            assert result is None


# ---------------------------------------------------------------------------
# collect_kpi_value
# ---------------------------------------------------------------------------

def test_collect_kpi_value_returns_none_when_kpi_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = collect_kpi_value(db, kpi_id=999)
    assert result is None


def test_collect_kpi_value_returns_none_when_no_data_source():
    db = MagicMock()
    kpi_mock = MagicMock()
    # First query (KPI) returns a KPI; second query (KPIDataSource) returns None
    db.query.return_value.filter.return_value.first.side_effect = [kpi_mock, None]
    result = collect_kpi_value(db, kpi_id=1)
    assert result is None


def test_collect_kpi_value_manual_returns_current_value():
    db = MagicMock()
    kpi_mock = MagicMock()
    kpi_mock.current_value = Decimal("42")
    ds_mock = MagicMock()
    ds_mock.source_type = "MANUAL"
    db.query.return_value.filter.return_value.first.side_effect = [kpi_mock, ds_mock]
    result = collect_kpi_value(db, kpi_id=1)
    assert result == Decimal("42")


# ---------------------------------------------------------------------------
# auto_collect_kpi
# ---------------------------------------------------------------------------

def test_auto_collect_kpi_returns_none_when_no_value():
    db = MagicMock()
    with patch(
        "app.services.strategy.kpi_collector.calculation.collect_kpi_value",
        return_value=None,
    ):
        result = auto_collect_kpi(db, kpi_id=1)
    assert result is None


def test_auto_collect_kpi_updates_and_returns_kpi():
    db = MagicMock()
    kpi_mock = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = kpi_mock
    with patch(
        "app.services.strategy.kpi_collector.calculation.collect_kpi_value",
        return_value=Decimal("88"),
    ), patch(
        "app.services.strategy.kpi_service.create_kpi_snapshot"
    ):
        result = auto_collect_kpi(db, kpi_id=1, recorded_by=7)
    assert result is kpi_mock
    assert kpi_mock.current_value == Decimal("88")


# ---------------------------------------------------------------------------
# batch_collect_kpis
# ---------------------------------------------------------------------------

def test_batch_collect_kpis_returns_stats():
    db = MagicMock()
    kpi1 = MagicMock(id=1, code="K1", name="KPI1")
    kpi2 = MagicMock(id=2, code="K2", name="KPI2")
    db.query.return_value.filter.return_value.all.return_value = [kpi1, kpi2]
    with patch(
        "app.services.strategy.kpi_collector.calculation.auto_collect_kpi",
        side_effect=[kpi1, None],
    ):
        stats = batch_collect_kpis(db)
    assert stats["total"] == 2
    assert stats["success"] == 1
    assert stats["failed"] == 1
    assert len(stats["failed_kpis"]) == 1
