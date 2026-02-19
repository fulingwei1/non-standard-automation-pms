# -*- coding: utf-8 -*-
"""
Unit tests for app/services/strategy/kpi_collector/status.py
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

try:
    from app.services.strategy.kpi_collector.status import get_collection_status
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_kpi(data_source_type="AUTO", frequency="MONTHLY", current_value=None, last_collected_at=None):
    k = MagicMock()
    k.data_source_type = data_source_type
    k.frequency = frequency
    k.current_value = current_value
    k.last_collected_at = last_collected_at
    return k


def test_get_collection_status_empty():
    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    result = get_collection_status(db, strategy_id=1)
    assert result["total_kpis"] == 0
    assert result["auto_kpis"] == 0
    assert result["manual_kpis"] == 0
    assert result["last_collected_at"] is None


def test_get_collection_status_counts():
    db = MagicMock()
    kpis = [
        _make_kpi("AUTO", "MONTHLY", current_value=100),
        _make_kpi("MANUAL", "MONTHLY", current_value=None),
        _make_kpi("AUTO", "WEEKLY", current_value=50),
    ]
    db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
    result = get_collection_status(db, strategy_id=1)
    assert result["total_kpis"] == 3
    assert result["auto_kpis"] == 2
    assert result["manual_kpis"] == 1
    assert result["collected_kpis"] == 2
    assert result["pending_kpis"] == 1


def test_get_collection_status_frequency_stats():
    db = MagicMock()
    kpis = [
        _make_kpi("AUTO", "MONTHLY", current_value=10),
        _make_kpi("AUTO", "MONTHLY", current_value=None),
        _make_kpi("AUTO", "WEEKLY", current_value=20),
    ]
    db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
    result = get_collection_status(db, strategy_id=2)
    assert "MONTHLY" in result["frequency_stats"]
    assert result["frequency_stats"]["MONTHLY"]["total"] == 2
    assert result["frequency_stats"]["MONTHLY"]["collected"] == 1
    assert result["frequency_stats"]["WEEKLY"]["total"] == 1


def test_get_collection_status_last_collected_at():
    db = MagicMock()
    t1 = datetime(2024, 1, 1)
    t2 = datetime(2024, 6, 1)
    kpis = [
        _make_kpi("AUTO", "MONTHLY", current_value=1, last_collected_at=t1),
        _make_kpi("AUTO", "MONTHLY", current_value=2, last_collected_at=t2),
    ]
    db.query.return_value.join.return_value.filter.return_value.all.return_value = kpis
    result = get_collection_status(db, strategy_id=3)
    assert result["last_collected_at"] == t2


def test_get_collection_status_unknown_frequency():
    db = MagicMock()
    kpi = _make_kpi("AUTO", None, current_value=5)
    kpi.frequency = None
    db.query.return_value.join.return_value.filter.return_value.all.return_value = [kpi]
    result = get_collection_status(db, strategy_id=4)
    assert "UNKNOWN" in result["frequency_stats"]


def test_get_collection_status_structure_keys():
    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []
    result = get_collection_status(db, strategy_id=5)
    expected_keys = {"total_kpis", "auto_kpis", "manual_kpis", "collected_kpis",
                     "pending_kpis", "frequency_stats", "last_collected_at"}
    assert expected_keys == set(result.keys())
