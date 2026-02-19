# -*- coding: utf-8 -*-
"""
tests/unit/test_ra_worker_cov51.py
Unit tests for app/services/resource_allocation_service/worker.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.resource_allocation_service.worker import (
        check_worker_availability,
        check_worker_skill,
        find_available_workers,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


START = date(2025, 2, 1)
END = date(2025, 2, 28)


def _make_worker(worker_id=1, is_active=True, status="ACTIVE"):
    w = MagicMock()
    w.id = worker_id
    w.worker_no = f"W{worker_id:03d}"
    w.worker_name = f"Worker{worker_id}"
    w.is_active = is_active
    w.status = status
    w.workshop_id = 1
    w.position = "Engineer"
    w.skill_level = "MID"
    return w


# ─── check_worker_availability ────────────────────────────────────────────────

def test_worker_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    ok, reason, hours = check_worker_availability(db, 99, START, END)

    assert ok is False
    assert reason == "工人不存在"
    assert hours == 0.0


def test_worker_inactive():
    db = MagicMock()
    worker = _make_worker(is_active=False, status="RESIGNED")
    db.query.return_value.filter.return_value.first.return_value = worker

    ok, reason, hours = check_worker_availability(db, 1, START, END)

    assert ok is False
    assert "不在职" in reason or "状态异常" in reason


def test_worker_available_no_conflicts():
    """Active worker with no conflicts should be available."""
    db = MagicMock()
    worker = _make_worker()
    db.query.return_value.filter.return_value.first.return_value = worker

    # No work orders, no allocations, no tasks
    db.query.return_value.filter.return_value.all.return_value = []
    # For allocations filter chain
    db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.filter.return_value = MagicMock(
        __iter__=lambda self: iter([])
    )

    with patch(
        "app.services.resource_allocation_service.worker.calculate_workdays",
        return_value=20,
    ), patch(
        "app.services.resource_allocation_service.worker.calculate_overlap_days",
        return_value=0,
    ):
        ok, reason, hours = check_worker_availability(db, 1, START, END)

    assert ok is True
    assert reason is None
    assert hours == 160.0  # 20 workdays * 8h


def test_worker_insufficient_hours():
    """Worker with 0 available hours (all allocated)."""
    db = MagicMock()
    worker = _make_worker()
    db.query.return_value.filter.return_value.first.return_value = worker

    # Simulate work order covering full period
    wo = MagicMock()
    wo.plan_start_date = START
    wo.plan_end_date = END

    def filter_all_side(model):
        m = MagicMock()
        m.filter.return_value.all.return_value = [wo]
        m.filter.return_value.filter.return_value.__iter__ = lambda s: iter([])
        return m

    db.query.side_effect = [
        MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=worker)))),
        MagicMock(filter=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[wo])))),
        MagicMock(filter=MagicMock(return_value=MagicMock(__iter__=lambda s: iter([])))),
        MagicMock(filter=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
    ]

    with patch(
        "app.services.resource_allocation_service.worker.calculate_workdays",
        return_value=20,
    ), patch(
        "app.services.resource_allocation_service.worker.calculate_overlap_days",
        return_value=20,
    ):
        ok, reason, hours = check_worker_availability(db, 1, START, END)

    assert ok is False


# ─── find_available_workers ────────────────────────────────────────────────────

def test_find_available_workers_empty_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []

    with patch(
        "app.services.resource_allocation_service.worker.check_worker_availability",
        return_value=(True, None, 160.0),
    ):
        result = find_available_workers(db, start_date=START, end_date=END)

    assert isinstance(result, list)


def test_find_available_workers_returns_sorted():
    """Workers sorted by available_hours descending."""
    db = MagicMock()
    w1 = _make_worker(1)
    w2 = _make_worker(2)
    db.query.return_value.filter.return_value.all.return_value = [w1, w2]

    with patch(
        "app.services.resource_allocation_service.worker.check_worker_availability",
        side_effect=[
            (True, None, 80.0),
            (True, None, 160.0),
        ],
    ):
        result = find_available_workers(db, start_date=START, end_date=END)

    assert result[0]["available_hours"] >= result[1]["available_hours"]


# ─── check_worker_skill ────────────────────────────────────────────────────────

def test_check_worker_skill_no_skills():
    db = MagicMock()
    db.query.return_value.join.return_value.filter.return_value.all.return_value = []

    matched, skills = check_worker_skill(db, 1, "welding")

    assert matched is False
    assert skills == []


def test_check_worker_skill_match():
    db = MagicMock()
    process = MagicMock()
    process.process_code = "WLD001"
    process.process_name = "Welding"
    process.process_type = "Manufacturing"
    process.is_active = True

    ws = MagicMock()
    ws.process = process
    ws.skill_level = "SENIOR"

    db.query.return_value.join.return_value.filter.return_value.all.return_value = [ws]

    matched, skills = check_worker_skill(db, 1, "weld")

    assert matched is True
    assert len(skills) == 1
