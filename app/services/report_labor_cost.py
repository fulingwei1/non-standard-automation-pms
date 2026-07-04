# -*- coding: utf-8 -*-
"""Shared labor-cost helpers for report generation."""

from datetime import date
from decimal import Decimal
from typing import Any, Iterable, Optional

from sqlalchemy.orm import Session

from app.services.hourly_rate_service import HourlyRateService


def calculate_timesheet_labor_cost(db: Session, timesheets: Iterable[Any]) -> Decimal:
    """Calculate labor cost from timesheets using configured user hourly rates."""
    total_cost = Decimal("0")
    for timesheet in timesheets:
        hours = Decimal(str(getattr(timesheet, "hours", 0) or 0))
        if hours == 0:
            continue

        user_id = getattr(timesheet, "user_id", None)
        work_date = _get_work_date(timesheet)
        hourly_rate = _get_hourly_rate(db, user_id, work_date)
        total_cost += hours * hourly_rate

    return total_cost


def _get_work_date(timesheet: Any) -> Optional[date]:
    work_date = getattr(timesheet, "work_date", None)
    return work_date if isinstance(work_date, date) else None


def _get_hourly_rate(db: Session, user_id: Any, work_date: Optional[date]) -> Decimal:
    if isinstance(user_id, int):
        return HourlyRateService.get_user_hourly_rate(db, user_id, work_date)
    return HourlyRateService.DEFAULT_HOURLY_RATE
