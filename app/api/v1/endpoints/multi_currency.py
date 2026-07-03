# -*- coding: utf-8 -*-
"""Multi-currency compatibility endpoints for the finance UI."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api import deps

router = APIRouter()


DEFAULT_RATES: dict[str, float] = {
    "CNY": 1.0,
    "USD": 7.24,
    "EUR": 7.85,
    "JPY": 0.046,
    "GBP": 9.22,
    "KRW": 0.0052,
    "TWD": 0.224,
}

DEFAULT_CHANGES: dict[str, float] = {
    "CNY": 0.0,
    "USD": 0.18,
    "EUR": -0.12,
    "JPY": 0.05,
    "GBP": 0.21,
    "KRW": -0.04,
    "TWD": 0.03,
}


def _number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return float(value)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else default


def _rate_row(currency: str, rate: float) -> dict[str, Any]:
    change = DEFAULT_CHANGES.get(currency, 0.0)
    return {
        "currency": currency,
        "rate": round(rate, 6),
        "change": change,
        "change_24h": change,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }


@router.get("/rates")
def get_rates(current_user=Depends(deps.get_current_user)):
    return [_rate_row(currency, rate) for currency, rate in DEFAULT_RATES.items()]


@router.post("/rates")
def update_rate(payload: dict[str, Any], current_user=Depends(deps.get_current_user)):
    currency = str(payload.get("currency") or "").upper()
    if currency not in DEFAULT_RATES:
        raise HTTPException(status_code=400, detail="不支持的币种")
    rate = _number(payload.get("rate"))
    if rate <= 0:
        raise HTTPException(status_code=400, detail="汇率必须大于0")
    DEFAULT_RATES[currency] = rate
    return _rate_row(currency, rate)


@router.get("/convert")
def convert_currency(
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    amount: float = Query(...),
    current_user=Depends(deps.get_current_user),
):
    source = from_currency.upper()
    target = to_currency.upper()
    if source not in DEFAULT_RATES or target not in DEFAULT_RATES:
        raise HTTPException(status_code=400, detail="不支持的币种")
    source_to_cny = DEFAULT_RATES[source]
    target_to_cny = DEFAULT_RATES[target]
    converted_amount = _number(amount) * source_to_cny / target_to_cny
    return {
        "from_currency": source,
        "to_currency": target,
        "amount": round(_number(amount), 2),
        "converted_amount": round(converted_amount, 2),
        "rate": round(source_to_cny / target_to_cny, 6),
    }


@router.get("/history")
def get_history(
    currency: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(deps.get_current_user),
):
    currencies = [currency.upper()] if currency else list(DEFAULT_RATES)
    rows: list[dict[str, Any]] = []
    now = datetime.now()
    for idx in range(limit):
        target_currency = currencies[idx % len(currencies)]
        if target_currency not in DEFAULT_RATES:
            continue
        recorded_at = now - timedelta(days=idx)
        rate = DEFAULT_RATES[target_currency] * (1 + DEFAULT_CHANGES.get(target_currency, 0) / 100)
        rows.append(
            {
                "currency": target_currency,
                "rate": round(rate, 6),
                "note": "演示汇率记录",
                "recorded_at": recorded_at.isoformat(timespec="seconds"),
                "updated_at": recorded_at.isoformat(timespec="seconds"),
            }
        )
    return rows


@router.get("/project-summary/{project_id}")
def get_project_currency_summary(
    project_id: int,
    current_user=Depends(deps.get_current_user),
):
    return {
        "project_id": project_id,
        "currency": "CNY",
        "original_amount": 0,
        "amount_cny": 0,
        "rate_to_cny": 1,
        "fx_gain_loss": 0,
    }
