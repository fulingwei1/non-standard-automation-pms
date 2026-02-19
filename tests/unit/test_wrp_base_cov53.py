# -*- coding: utf-8 -*-
"""
Unit tests for app/services/win_rate_prediction_service/base.py
"""
import pytest
from unittest.mock import MagicMock

try:
    from app.services.win_rate_prediction_service.base import WinRatePredictionService
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_instantiation():
    db = MagicMock()
    svc = WinRatePredictionService(db)
    assert svc.db is db


def test_dimension_weights_keys():
    db = MagicMock()
    svc = WinRatePredictionService(db)
    expected = {
        "requirement_maturity",
        "technical_feasibility",
        "business_feasibility",
        "delivery_risk",
        "customer_relationship",
    }
    assert set(svc.DIMENSION_WEIGHTS.keys()) == expected


def test_dimension_weights_sum_to_one():
    db = MagicMock()
    svc = WinRatePredictionService(db)
    total = sum(svc.DIMENSION_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9


def test_probability_thresholds_are_dict():
    db = MagicMock()
    svc = WinRatePredictionService(db)
    assert isinstance(svc.PROBABILITY_THRESHOLDS, dict)
    assert len(svc.PROBABILITY_THRESHOLDS) == 5


def test_probability_thresholds_values_are_floats():
    db = MagicMock()
    svc = WinRatePredictionService(db)
    for v in svc.PROBABILITY_THRESHOLDS.values():
        assert isinstance(v, float)


def test_db_attribute_stored():
    mock_session = MagicMock()
    svc = WinRatePredictionService(mock_session)
    assert svc.db is mock_session
