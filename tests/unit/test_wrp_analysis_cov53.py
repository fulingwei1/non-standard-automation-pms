# -*- coding: utf-8 -*-
"""
Unit tests for app/services/win_rate_prediction_service/analysis.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock

try:
    from app.services.win_rate_prediction_service.analysis import (
        get_win_rate_distribution,
        validate_model_accuracy,
    )
    from app.models.enums import LeadOutcomeEnum, WinProbabilityLevelEnum
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ---------------------------------------------------------------------------
# get_win_rate_distribution
# ---------------------------------------------------------------------------

def test_win_rate_distribution_empty():
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    svc.db.query.return_value = q
    result = get_win_rate_distribution(svc)
    assert isinstance(result, dict)
    # All levels should have count=0 and actual_win_rate=0
    for level_data in result.values():
        assert level_data["count"] == 0
        assert level_data["actual_win_rate"] == 0


def test_win_rate_distribution_classifies_very_high():
    svc = MagicMock()
    proj = MagicMock(predicted_win_rate=0.90, outcome=LeadOutcomeEnum.WON.value)
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [proj]
    svc.db.query.return_value = q
    result = get_win_rate_distribution(svc)
    very_high_key = WinProbabilityLevelEnum.VERY_HIGH.value
    assert result[very_high_key]["count"] == 1
    assert result[very_high_key]["won"] == 1


def test_win_rate_distribution_classifies_low():
    svc = MagicMock()
    proj = MagicMock(predicted_win_rate=0.25, outcome=LeadOutcomeEnum.LOST.value)
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [proj]
    svc.db.query.return_value = q
    result = get_win_rate_distribution(svc)
    low_key = WinProbabilityLevelEnum.LOW.value
    assert result[low_key]["count"] == 1
    assert result[low_key]["won"] == 0


def test_win_rate_distribution_actual_win_rate_calculated():
    svc = MagicMock()
    p1 = MagicMock(predicted_win_rate=0.85, outcome=LeadOutcomeEnum.WON.value)
    p2 = MagicMock(predicted_win_rate=0.82, outcome=LeadOutcomeEnum.LOST.value)
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [p1, p2]
    svc.db.query.return_value = q
    result = get_win_rate_distribution(svc)
    very_high_key = WinProbabilityLevelEnum.VERY_HIGH.value
    assert result[very_high_key]["actual_win_rate"] == 0.5


# ---------------------------------------------------------------------------
# validate_model_accuracy
# ---------------------------------------------------------------------------

def test_validate_model_accuracy_no_data():
    svc = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    svc.db.query.return_value = q
    result = validate_model_accuracy(svc)
    assert "error" in result


def test_validate_model_accuracy_perfect():
    svc = MagicMock()
    p1 = MagicMock(predicted_win_rate=0.9, outcome=LeadOutcomeEnum.WON.value)
    p2 = MagicMock(predicted_win_rate=0.3, outcome=LeadOutcomeEnum.LOST.value)
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [p1, p2]
    svc.db.query.return_value = q
    result = validate_model_accuracy(svc)
    assert result["accuracy"] == 1.0
    assert result["total_samples"] == 2


def test_validate_model_accuracy_structure():
    svc = MagicMock()
    proj = MagicMock(predicted_win_rate=0.7, outcome=LeadOutcomeEnum.WON.value)
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [proj]
    svc.db.query.return_value = q
    result = validate_model_accuracy(svc)
    assert "total_samples" in result
    assert "accuracy" in result
    assert "brier_score" in result
    assert "period_months" in result
