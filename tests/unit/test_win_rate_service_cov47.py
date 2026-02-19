# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - win_rate_prediction_service/service.py
"""
import pytest

pytest.importorskip("app.services.win_rate_prediction_service.service")

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.win_rate_prediction_service.service import WinRatePredictionService


def run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def make_svc():
    db = MagicMock()
    # db.execute should be awaitable (returns a MagicMock synchronously when awaited)
    async def fake_execute(*args, **kwargs):
        return MagicMock()
    db.execute = fake_execute

    with patch("app.services.win_rate_prediction_service.service.AIWinRatePredictionService"):
        svc = WinRatePredictionService(db)
    return svc, db


def _set_execute_result(db, scalar_value):
    """Helper: make db.execute() return a result where scalar_one_or_none() = scalar_value"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = scalar_value

    async def fake_execute(*args, **kwargs):
        return result

    db.execute = fake_execute


def _set_execute_scalars(db, items):
    """Helper: make db.execute() return a result where scalars().all() = items"""
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = items
    result.scalars.return_value = scalars

    async def fake_execute(*args, **kwargs):
        return result

    db.execute = fake_execute


# ---------- get_influencing_factors ----------

def test_get_influencing_factors_no_prediction():
    svc, db = make_svc()
    _set_execute_result(db, None)
    factors = run(svc.get_influencing_factors(ticket_id=1))
    assert factors == []


def test_get_influencing_factors_sorted():
    svc, db = make_svc()
    prediction = MagicMock()
    prediction.influencing_factors = [
        {"factor": "A", "score": 3},
        {"factor": "B", "score": 9},
        {"factor": "C", "score": 7},
    ]
    _set_execute_result(db, prediction)
    factors = run(svc.get_influencing_factors(ticket_id=1))
    assert factors[0]["score"] == 9  # 最高分在前
    assert len(factors) <= 5


# ---------- get_competitor_analysis ----------

def test_get_competitor_analysis_no_prediction():
    svc, db = make_svc()
    _set_execute_result(db, None)
    result = run(svc.get_competitor_analysis(ticket_id=99))
    assert result is None


def test_get_competitor_analysis_returns_data():
    svc, db = make_svc()
    prediction = MagicMock()
    prediction.competitor_analysis = {"competitors": ["A", "B"]}
    _set_execute_result(db, prediction)
    result = run(svc.get_competitor_analysis(ticket_id=1))
    assert "competitors" in result


# ---------- get_improvement_suggestions ----------

def test_get_improvement_suggestions_none():
    svc, db = make_svc()
    _set_execute_result(db, None)
    result = run(svc.get_improvement_suggestions(ticket_id=5))
    assert result is None


# ---------- update_actual_result ----------

def test_update_actual_result_not_found():
    from app.models.sales.presale_ai_win_rate import WinRateResultEnum
    svc, db = make_svc()
    _set_execute_result(db, None)
    with pytest.raises(Exception):
        run(svc.update_actual_result(1, WinRateResultEnum.WON, updated_by=1))


# ---------- _get_historical_data ----------

def test_get_historical_data_empty():
    svc, db = make_svc()
    _set_execute_scalars(db, [])
    result = run(svc._get_historical_data({}))
    assert result == []


def test_get_historical_data_formats_correctly():
    svc, db = make_svc()
    h = MagicMock()
    h.presale_ticket_id = 10
    h.predicted_win_rate = Decimal("75")
    h.actual_result = MagicMock()
    h.actual_result.value = "won"
    h.features = {"key": "val"}
    _set_execute_scalars(db, [h])
    result = run(svc._get_historical_data({}))
    assert len(result) == 1
    assert result[0]["ticket_id"] == 10
    assert result[0]["result"] == "won"
