# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - production_schedule_service"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta

pytest.importorskip("app.services.production_schedule_service")

from app.services.production_schedule_service import ProductionScheduleService


def make_db():
    return MagicMock()


def make_work_order(**kw):
    wo = MagicMock()
    wo.id = kw.get("id", 1)
    wo.work_order_no = kw.get("work_order_no", "WO-001")
    wo.priority = kw.get("priority", "NORMAL")
    wo.plan_start_date = kw.get("plan_start_date", date(2024, 1, 1))
    wo.plan_end_date = kw.get("plan_end_date", date(2024, 12, 31))
    wo.standard_hours = kw.get("standard_hours", 8)
    wo.workstation_id = kw.get("workstation_id", None)
    wo.workshop_id = kw.get("workshop_id", 1)
    wo.process_id = kw.get("process_id", None)
    wo.status = kw.get("status", "PENDING")
    return wo


def make_schedule(**kw):
    s = MagicMock()
    s.work_order_id = kw.get("work_order_id", 1)
    s.equipment_id = kw.get("equipment_id", 1)
    s.worker_id = kw.get("worker_id", 1)
    s.scheduled_start_time = kw.get(
        "scheduled_start_time", datetime(2024, 1, 2, 8, 0)
    )
    s.scheduled_end_time = kw.get(
        "scheduled_end_time", datetime(2024, 1, 2, 16, 0)
    )
    s.duration_hours = kw.get("duration_hours", 8.0)
    s.priority_score = kw.get("priority_score", 20.0)
    return s


class TestPriorityScore:
    def test_urgent_priority(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        wo = make_work_order(priority="URGENT")
        score = svc._calculate_priority_score(wo)
        assert score == 5.0

    def test_high_priority(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        wo = make_work_order(priority="HIGH")
        score = svc._calculate_priority_score(wo)
        assert score == 3.0

    def test_unknown_priority_defaults(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        wo = make_work_order(priority="UNKNOWN")
        score = svc._calculate_priority_score(wo)
        assert score == 2.0


class TestPriorityWeight:
    def test_priority_weights(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        assert svc._get_priority_weight("URGENT") < svc._get_priority_weight("LOW")
        assert svc._get_priority_weight("HIGH") < svc._get_priority_weight("NORMAL")


class TestCalculateOverallMetrics:
    def test_empty_schedules(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        result = svc.calculate_overall_metrics([], [])
        assert result.completion_rate == 0
        assert result.equipment_utilization == 0

    def test_with_schedules(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        wo = make_work_order(plan_end_date=date(2024, 1, 31))
        schedule = make_schedule(
            work_order_id=1,
            scheduled_start_time=datetime(2024, 1, 2, 8, 0),
            scheduled_end_time=datetime(2024, 1, 2, 16, 0),
        )
        with patch.object(svc, "_detect_conflicts", return_value=[]):
            result = svc.calculate_overall_metrics([schedule], [wo])
        assert result.total_duration_hours >= 0


class TestCalculateScheduleScore:
    def test_score_within_plan(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        wo = make_work_order(plan_end_date=date(2024, 12, 31))
        schedule = make_schedule(
            work_order_id=1,
            scheduled_end_time=datetime(2024, 6, 1, 16, 0),
        )
        score = svc._calculate_schedule_score(schedule, [wo])
        assert score > 0

    def test_score_no_matching_order(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        schedule = make_schedule(work_order_id=999)
        score = svc._calculate_schedule_score(schedule, [])
        assert score == 0.0


class TestFetchWorkOrders:
    def test_fetch_work_orders(self):
        db = make_db()
        wo = make_work_order()
        db.query.return_value.filter.return_value.all.return_value = [wo]
        svc = ProductionScheduleService(db)
        result = svc._fetch_work_orders([1])
        assert len(result) == 1

    def test_fetch_empty_work_orders(self):
        db = make_db()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = ProductionScheduleService(db)
        result = svc._fetch_work_orders([999])
        assert result == []


class TestAdjustToWorkTime:
    def test_adjust_time_within_work_hours(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        request = MagicMock()
        request.start_date = datetime(2024, 1, 2, 10, 0)  # 10:00 - within work hours
        dt = datetime(2024, 1, 2, 10, 0)
        result = svc._adjust_to_work_time(dt, request)
        assert result is not None

    def test_adjust_time_after_work_hours(self):
        db = make_db()
        svc = ProductionScheduleService(db)
        request = MagicMock()
        request.start_date = datetime(2024, 1, 2, 8, 0)
        dt = datetime(2024, 1, 2, 20, 0)  # After work hours
        result = svc._adjust_to_work_time(dt, request)
        # Should move to next day 8:00
        assert result.hour == 8
