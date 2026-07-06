# -*- coding: utf-8 -*-
"""Shared labor-cost helpers for timesheet-backed cost calculations."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable, Optional

from sqlalchemy.orm import Session

from app.services.hourly_rate_service import HourlyRateService


@dataclass(frozen=True)
class TimesheetLaborCostSummary:
    total_hours: Decimal
    total_cost: Decimal

    @property
    def weighted_hourly_rate(self) -> Decimal:
        if self.total_hours == 0:
            return Decimal("0")
        return (self.total_cost / self.total_hours).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


def calculate_timesheet_labor_cost(db: Session, timesheets: Iterable[Any]) -> Decimal:
    """Calculate labor cost from timesheets using configured user hourly rates."""
    return calculate_timesheet_labor_summary(db, timesheets).total_cost


def calculate_timesheet_labor_summary(
    db: Session, timesheets: Iterable[Any]
) -> TimesheetLaborCostSummary:
    """Calculate labor hours and cost from timesheets using configured hourly rates."""
    total_hours = Decimal("0")
    total_cost = Decimal("0")
    for timesheet in timesheets:
        hours = Decimal(str(getattr(timesheet, "hours", 0) or 0))
        if hours == 0:
            continue

        total_hours += hours
        user_id = getattr(timesheet, "user_id", None)
        work_date = _get_work_date(timesheet)
        hourly_rate = _get_hourly_rate(db, user_id, work_date)
        total_cost += hours * hourly_rate

    return TimesheetLaborCostSummary(total_hours=total_hours, total_cost=total_cost)


def _get_work_date(timesheet: Any) -> Optional[date]:
    work_date = getattr(timesheet, "work_date", None)
    return work_date if isinstance(work_date, date) else None


def _get_hourly_rate(db: Session, user_id: Any, work_date: Optional[date]) -> Decimal:
    if isinstance(user_id, int):
        return HourlyRateService.get_user_hourly_rate(db, user_id, work_date)
    return HourlyRateService.DEFAULT_HOURLY_RATE
