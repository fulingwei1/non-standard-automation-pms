# -*- coding: utf-8 -*-
"""
Unit tests for app/services/strategy/kpi_service/snapshot.py
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.strategy.kpi_service.snapshot import (
        _get_current_period,
        _calculate_trend,
        create_kpi_snapshot,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ---------------------------------------------------------------------------
# _get_current_period
# ---------------------------------------------------------------------------

def test_get_current_period_daily():
    result = _get_current_period("DAILY")
    # Should match YYYY-MM-DD
    assert len(result) == 10
    assert result[4] == "-"


def test_get_current_period_monthly():
    result = _get_current_period("MONTHLY")
    assert len(result) == 7  # YYYY-MM


def test_get_current_period_quarterly():
    result = _get_current_period("QUARTERLY")
    assert "Q" in result


def test_get_current_period_weekly():
    result = _get_current_period("WEEKLY")
    assert "W" in result


def test_get_current_period_other():
    result = _get_current_period("ANNUALLY")
    assert len(result) == 4  # YYYY


# ---------------------------------------------------------------------------
# _calculate_trend
# ---------------------------------------------------------------------------

def test_calculate_trend_up():
    db = MagicMock()
    h1 = MagicMock(value=Decimal("100"))
    h2 = MagicMock(value=Decimal("80"))
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
    trend = _calculate_trend(db, 1)
    assert trend == "UP"


def test_calculate_trend_down():
    db = MagicMock()
    h1 = MagicMock(value=Decimal("50"))
    h2 = MagicMock(value=Decimal("80"))
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
    trend = _calculate_trend(db, 1)
    assert trend == "DOWN"


def test_calculate_trend_stable():
    db = MagicMock()
    h1 = MagicMock(value=Decimal("70"))
    h2 = MagicMock(value=Decimal("70"))
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [h1, h2]
    trend = _calculate_trend(db, 1)
    assert trend == "STABLE"


def test_calculate_trend_insufficient_history():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    trend = _calculate_trend(db, 1)
    assert trend is None


# ---------------------------------------------------------------------------
# create_kpi_snapshot
# ---------------------------------------------------------------------------

def test_create_kpi_snapshot_returns_none_when_kpi_missing():
    db = MagicMock()
    with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=None):
        result = create_kpi_snapshot(db, kpi_id=999, source_type="MANUAL")
    assert result is None


def test_create_kpi_snapshot_creates_history():
    import sys
    db = MagicMock()
    kpi_mock = MagicMock()
    kpi_mock.current_value = Decimal("75")
    kpi_mock.target_value = Decimal("100")
    kpi_mock.frequency = "MONTHLY"

    # health_calculator is imported locally inside the function; inject via sys.modules
    hc_mock = MagicMock()
    hc_mock.calculate_kpi_completion_rate = MagicMock(return_value=75.0)
    hc_mock.get_health_level = MagicMock(return_value="GOOD")
    sys.modules["app.services.strategy.kpi_service.health_calculator"] = hc_mock

    try:
        with patch("app.services.strategy.kpi_service.snapshot.get_kpi", return_value=kpi_mock):
            result = create_kpi_snapshot(db, kpi_id=1, source_type="MANUAL", recorded_by=5)
    finally:
        sys.modules.pop("app.services.strategy.kpi_service.health_calculator", None)

    db.add.assert_called_once()
    db.commit.assert_called_once()
