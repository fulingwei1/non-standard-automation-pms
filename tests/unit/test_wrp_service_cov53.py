# -*- coding: utf-8 -*-
"""
Unit tests for app/services/win_rate_prediction_service/service.py
(async service using AsyncSession)
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from app.services.win_rate_prediction_service.service import WinRatePredictionService
    from app.models.sales.presale_ai_win_rate import WinRateResultEnum
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service():
    """Build a WinRatePredictionService with a mocked async db."""
    db = AsyncMock()
    with patch(
        "app.services.win_rate_prediction_service.service.AIWinRatePredictionService"
    ) as MockAI:
        MockAI.return_value = MagicMock()
        svc = WinRatePredictionService(db)
    return svc, db


def _sync_result(value):
    """Return a MagicMock whose scalar_one_or_none() returns value synchronously."""
    r = MagicMock()
    r.scalar_one_or_none.return_value = value
    return r


def _sync_scalars_result(values):
    """Return a MagicMock whose scalars().all() returns values synchronously."""
    r = MagicMock()
    r.scalars.return_value.all.return_value = values
    return r


# ---------------------------------------------------------------------------
# get_prediction
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_prediction_found():
    svc, db = _make_service()
    mock_pred = MagicMock()
    db.execute.return_value = _sync_result(mock_pred)
    result = await svc.get_prediction(prediction_id=1)
    assert result is mock_pred


@pytest.mark.asyncio
async def test_get_prediction_not_found():
    svc, db = _make_service()
    db.execute.return_value = _sync_result(None)
    result = await svc.get_prediction(prediction_id=999)
    assert result is None


# ---------------------------------------------------------------------------
# get_predictions_by_ticket
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_predictions_by_ticket_returns_list():
    svc, db = _make_service()
    preds = [MagicMock(), MagicMock()]
    db.execute.return_value = _sync_scalars_result(preds)
    result = await svc.get_predictions_by_ticket(presale_ticket_id=10)
    assert result == preds


# ---------------------------------------------------------------------------
# get_influencing_factors
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_influencing_factors_no_prediction():
    svc, db = _make_service()
    db.execute.return_value = _sync_result(None)
    result = await svc.get_influencing_factors(ticket_id=1)
    assert result == []


@pytest.mark.asyncio
async def test_get_influencing_factors_sorted_top5():
    svc, db = _make_service()
    pred = MagicMock()
    pred.influencing_factors = [
        {"name": "f1", "score": 10},
        {"name": "f2", "score": 90},
        {"name": "f3", "score": 50},
        {"name": "f4", "score": 30},
        {"name": "f5", "score": 70},
        {"name": "f6", "score": 20},
    ]
    db.execute.return_value = _sync_result(pred)
    result = await svc.get_influencing_factors(ticket_id=1)
    assert len(result) == 5
    assert result[0]["score"] == 90  # highest first


# ---------------------------------------------------------------------------
# get_competitor_analysis / get_improvement_suggestions
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_competitor_analysis_none():
    svc, db = _make_service()
    db.execute.return_value = _sync_result(None)
    result = await svc.get_competitor_analysis(ticket_id=1)
    assert result is None


@pytest.mark.asyncio
async def test_get_improvement_suggestions_returns_data():
    svc, db = _make_service()
    pred = MagicMock()
    pred.improvement_suggestions = {"tip": "improve pricing"}
    db.execute.return_value = _sync_result(pred)
    result = await svc.get_improvement_suggestions(ticket_id=1)
    assert result == {"tip": "improve pricing"}


# ---------------------------------------------------------------------------
# get_model_accuracy
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_model_accuracy_structure():
    svc, db = _make_service()

    stats_row = MagicMock(total=10, correct=8)
    avg_error_r = MagicMock()
    avg_error_r.scalar.return_value = 12.5
    by_result_r = MagicMock()
    by_result_r.__iter__ = MagicMock(return_value=iter([]))

    call_count = [0]

    def execute_side_effect(stmt):
        call_count[0] += 1
        if call_count[0] == 1:
            r = MagicMock()
            r.one.return_value = stats_row
            return r
        elif call_count[0] == 2:
            return avg_error_r
        else:
            return by_result_r

    db.execute = AsyncMock(side_effect=execute_side_effect)

    result = await svc.get_model_accuracy()
    assert "overall_accuracy" in result
    assert "total_predictions" in result
    assert result["total_predictions"] == 10
