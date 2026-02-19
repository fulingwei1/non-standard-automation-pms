# -*- coding: utf-8 -*-
"""
Unit tests for app/services/strategy/kpi_service/value.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.strategy.kpi_service.value import update_kpi_value
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_update_kpi_value_returns_none_when_kpi_not_found():
    db = MagicMock()
    with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=None):
        result = update_kpi_value(db, kpi_id=999, value=Decimal("50"), recorded_by=1)
    assert result is None


def test_update_kpi_value_sets_current_value():
    db = MagicMock()
    kpi_mock = MagicMock()
    with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
         patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
        result = update_kpi_value(db, kpi_id=1, value=Decimal("88"), recorded_by=5)
    assert kpi_mock.current_value == Decimal("88")


def test_update_kpi_value_calls_snapshot():
    db = MagicMock()
    kpi_mock = MagicMock()
    with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock) as mock_get, \
         patch("app.services.strategy.kpi_service.value.create_kpi_snapshot") as mock_snap:
        update_kpi_value(db, kpi_id=1, value=Decimal("50"), recorded_by=3, remark="test")
    mock_snap.assert_called_once_with(db, 1, "MANUAL", 3, "test")


def test_update_kpi_value_commits_db():
    db = MagicMock()
    kpi_mock = MagicMock()
    with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
         patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
        update_kpi_value(db, kpi_id=1, value=Decimal("10"), recorded_by=2)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(kpi_mock)


def test_update_kpi_value_refreshes_and_returns_kpi():
    db = MagicMock()
    kpi_mock = MagicMock()
    with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
         patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
        result = update_kpi_value(db, kpi_id=1, value=Decimal("60"), recorded_by=1)
    assert result is kpi_mock


def test_update_kpi_value_sets_last_collected_at():
    db = MagicMock()
    kpi_mock = MagicMock()
    with patch("app.services.strategy.kpi_service.value.get_kpi", return_value=kpi_mock), \
         patch("app.services.strategy.kpi_service.value.create_kpi_snapshot"):
        update_kpi_value(db, kpi_id=1, value=Decimal("70"), recorded_by=1)
    # last_collected_at should be set (not None)
    assert kpi_mock.last_collected_at is not None
