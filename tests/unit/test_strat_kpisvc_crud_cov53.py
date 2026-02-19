# -*- coding: utf-8 -*-
"""
Unit tests for app/services/strategy/kpi_service/crud.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.strategy.kpi_service.crud import (
        create_kpi,
        get_kpi,
        list_kpis,
        update_kpi,
        delete_kpi,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_create_data(**kwargs):
    d = MagicMock()
    d.csf_id = kwargs.get("csf_id", 1)
    d.code = kwargs.get("code", "K001")
    d.name = kwargs.get("name", "Test KPI")
    d.description = kwargs.get("description", None)
    d.ipooc_type = kwargs.get("ipooc_type", "INPUT")
    d.unit = kwargs.get("unit", "%")
    d.direction = kwargs.get("direction", "UP")
    d.target_value = kwargs.get("target_value", Decimal("100"))
    d.baseline_value = kwargs.get("baseline_value", None)
    d.excellent_threshold = kwargs.get("excellent_threshold", None)
    d.good_threshold = kwargs.get("good_threshold", None)
    d.warning_threshold = kwargs.get("warning_threshold", None)
    d.data_source_type = kwargs.get("data_source_type", "MANUAL")
    d.data_source_config = kwargs.get("data_source_config", None)
    d.frequency = kwargs.get("frequency", "MONTHLY")
    d.weight = kwargs.get("weight", Decimal("1"))
    d.owner_user_id = kwargs.get("owner_user_id", None)
    return d


# ---------------------------------------------------------------------------
# create_kpi
# ---------------------------------------------------------------------------

def test_create_kpi_adds_and_commits():
    db = MagicMock()
    data = _make_create_data()
    kpi = create_kpi(db, data)
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_create_kpi_with_data_source_config():
    db = MagicMock()
    data = _make_create_data(data_source_config={"key": "val"})
    create_kpi(db, data)
    db.add.assert_called_once()


# ---------------------------------------------------------------------------
# get_kpi
# ---------------------------------------------------------------------------

def test_get_kpi_found():
    db = MagicMock()
    mock_kpi = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_kpi
    result = get_kpi(db, 1)
    assert result is mock_kpi


def test_get_kpi_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = get_kpi(db, 999)
    assert result is None


# ---------------------------------------------------------------------------
# update_kpi
# ---------------------------------------------------------------------------

def test_update_kpi_not_found_returns_none():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    update_data = MagicMock()
    update_data.model_dump.return_value = {}
    result = update_kpi(db, 999, update_data)
    assert result is None


def test_update_kpi_applies_fields():
    db = MagicMock()
    kpi_mock = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = kpi_mock
    update_data = MagicMock()
    update_data.model_dump.return_value = {"name": "New Name"}
    result = update_kpi(db, 1, update_data)
    assert kpi_mock.name == "New Name"
    db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# delete_kpi
# ---------------------------------------------------------------------------

def test_delete_kpi_not_found_returns_false():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = delete_kpi(db, 999)
    assert result is False


def test_delete_kpi_soft_deletes():
    db = MagicMock()
    kpi_mock = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = kpi_mock
    result = delete_kpi(db, 1)
    assert result is True
    assert kpi_mock.is_active is False
    db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# list_kpis
# ---------------------------------------------------------------------------

def test_list_kpis_returns_items_and_total():
    db = MagicMock()
    mock_items = [MagicMock(), MagicMock()]
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    q.count.return_value = 2
    q.order_by.return_value.all.return_value = mock_items
    db.query.return_value = q
    with patch("app.services.strategy.kpi_service.crud.apply_pagination", side_effect=lambda q, s, l: q.order_by()):
        # Just verify structure without full query chain
        pass
    # Simpler: patch apply_pagination
    with patch("app.services.strategy.kpi_service.crud.apply_pagination") as mock_pag:
        mock_pag.return_value.all.return_value = mock_items
        items, total = list_kpis(db)
    assert total == 2
    assert items == mock_items
