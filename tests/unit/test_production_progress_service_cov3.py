# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - production_progress_service"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
from decimal import Decimal

pytest.importorskip("app.services.production_progress_service")

from app.services.production_progress_service import ProductionProgressService


def make_db():
    return MagicMock()


def make_work_order(**kw):
    wo = MagicMock()
    wo.id = kw.get("id", 1)
    wo.work_order_no = kw.get("work_order_no", "WO-001")
    wo.plan_start_date = kw.get("plan_start_date", date(2024, 1, 1))
    wo.plan_end_date = kw.get("plan_end_date", date(2024, 12, 31))
    wo.status = kw.get("status", "IN_PROGRESS")
    wo.workstation_id = kw.get("workstation_id", 1)
    wo.project_id = kw.get("project_id", 1)
    return wo


class TestCalculateProgressDeviation:
    def test_work_order_not_found_returns_zeros(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ProductionProgressService(db)
        plan, deviation, is_delayed = svc.calculate_progress_deviation(999, 50)
        assert plan == 0
        assert deviation == 0
        assert is_delayed is False

    def test_actual_ahead_of_plan(self):
        db = make_db()
        wo = make_work_order(
            plan_start_date=date(2024, 1, 1),
            plan_end_date=date(2024, 12, 31),
        )
        db.query.return_value.filter.return_value.first.return_value = wo
        svc = ProductionProgressService(db)
        # Midyear actual vs 50% plan: on track
        plan, deviation, is_delayed = svc.calculate_progress_deviation(
            1, 70, actual_date=date(2024, 7, 1)
        )
        assert deviation > 0  # ahead
        assert is_delayed is False

    def test_actual_behind_plan(self):
        db = make_db()
        wo = make_work_order(
            plan_start_date=date(2024, 1, 1),
            plan_end_date=date(2024, 12, 31),
        )
        db.query.return_value.filter.return_value.first.return_value = wo
        svc = ProductionProgressService(db)
        plan, deviation, is_delayed = svc.calculate_progress_deviation(
            1, 10, actual_date=date(2024, 7, 1)
        )
        assert is_delayed is True

    def test_before_plan_start(self):
        db = make_db()
        wo = make_work_order(
            plan_start_date=date(2025, 1, 1),
            plan_end_date=date(2025, 12, 31),
        )
        db.query.return_value.filter.return_value.first.return_value = wo
        svc = ProductionProgressService(db)
        plan, _, _ = svc.calculate_progress_deviation(1, 0, actual_date=date(2024, 6, 1))
        assert plan == 0


class TestCalculatePlannedProgress:
    def test_no_dates_returns_zero(self):
        db = make_db()
        svc = ProductionProgressService(db)
        wo = MagicMock()
        wo.plan_start_date = None
        wo.plan_end_date = None
        result = svc._calculate_planned_progress(wo, date.today())
        assert result == 0

    def test_after_end_returns_100(self):
        db = make_db()
        svc = ProductionProgressService(db)
        wo = make_work_order(
            plan_start_date=date(2023, 1, 1),
            plan_end_date=date(2023, 12, 31),
        )
        result = svc._calculate_planned_progress(wo, date(2024, 1, 1))
        assert result == 100


class TestCalculateDeviationPercentage:
    def test_zero_plan_returns_zero(self):
        db = make_db()
        svc = ProductionProgressService(db)
        result = svc.calculate_deviation_percentage(10, 0)
        assert result == Decimal("0")

    def test_normal_calculation(self):
        db = make_db()
        svc = ProductionProgressService(db)
        result = svc.calculate_deviation_percentage(20, 100)
        assert result == Decimal("20")


class TestIdentifyBottlenecks:
    def test_no_bottlenecks(self):
        db = make_db()
        mock_q = MagicMock()
        mock_q.join.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q
        svc = ProductionProgressService(db)
        result = svc.identify_bottlenecks()
        assert result == []


class TestGetAlerts:
    def test_get_alerts_returns_list(self):
        db = make_db()
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q
        svc = ProductionProgressService(db)
        result = svc.get_alerts(work_order_id=1)
        assert isinstance(result, list)


class TestDismissAlert:
    def test_dismiss_alert_not_found(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ProductionProgressService(db)
        result = svc.dismiss_alert(999, 1)
        assert result is False

    def test_dismiss_alert_success(self):
        db = make_db()
        alert = MagicMock()
        alert.status = "ACTIVE"
        db.query.return_value.filter.return_value.first.return_value = alert
        svc = ProductionProgressService(db)
        result = svc.dismiss_alert(1, 1, note="Resolved")
        assert result is True
