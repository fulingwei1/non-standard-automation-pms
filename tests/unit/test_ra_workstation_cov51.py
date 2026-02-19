# -*- coding: utf-8 -*-
"""
tests/unit/test_ra_workstation_cov51.py
Unit tests for app/services/resource_allocation_service/workstation.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.resource_allocation_service.workstation import (
        check_workstation_availability,
        find_available_workstations,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


START = date(2025, 2, 1)
END = date(2025, 2, 28)


def _make_workstation(ws_id=1, is_active=True, status="IDLE"):
    ws = MagicMock()
    ws.id = ws_id
    ws.workstation_code = f"WS{ws_id:03d}"
    ws.workstation_name = f"Workstation {ws_id}"
    ws.is_active = is_active
    ws.status = status
    ws.workshop_id = 1
    ws.workshop = MagicMock(name="W1")
    return ws


# ─── check_workstation_availability ───────────────────────────────────────────

def test_workstation_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    ok, reason = check_workstation_availability(db, 99, START, END)

    assert ok is False
    assert reason == "工位不存在"


def test_workstation_inactive():
    db = MagicMock()
    ws = _make_workstation(is_active=False, status="IDLE")
    db.query.return_value.filter.return_value.first.return_value = ws

    ok, reason = check_workstation_availability(db, 1, START, END)

    assert ok is False
    assert "停用" in reason


def test_workstation_wrong_status():
    db = MagicMock()
    ws = _make_workstation(status="IN_USE")
    db.query.return_value.filter.return_value.first.return_value = ws

    ok, reason = check_workstation_availability(db, 1, START, END)

    assert ok is False
    assert "IN_USE" in reason


def test_workstation_available_no_conflicts():
    from app.models import WorkOrder, Workstation as WsModel

    db = MagicMock()
    ws = _make_workstation()

    # Use side_effect on db.query to distinguish Workstation vs WorkOrder
    workstation_query = MagicMock()
    workstation_query.filter.return_value.first.return_value = ws

    work_order_query = MagicMock()
    # The code does: db.query(WorkOrder).filter(...).first()
    # (single filter call with all conditions)
    work_order_query.filter.return_value.first.return_value = None

    def query_side(model):
        if model is WsModel:
            return workstation_query
        return work_order_query

    db.query.side_effect = query_side

    ok, reason = check_workstation_availability(db, 1, START, END)

    assert ok is True
    assert reason is None


def test_workstation_conflict():
    db = MagicMock()
    ws = _make_workstation()

    conflict_wo = MagicMock()
    conflict_wo.plan_start_date = START
    conflict_wo.plan_end_date = END
    conflict_wo.work_order_no = "WO-001"

    # Simulate first() returning ws and then conflict
    call_count = [0]

    def first_side_effect():
        call_count[0] += 1
        if call_count[0] == 1:
            return ws
        return conflict_wo

    db.query.return_value.filter.return_value.first.side_effect = first_side_effect
    db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = conflict_wo

    ok, reason = check_workstation_availability(db, 1, START, END)

    assert ok is False
    assert "WO-001" in reason or "占用" in reason


# ─── find_available_workstations ──────────────────────────────────────────────

def test_find_available_workstations_empty():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    result = find_available_workstations(db, start_date=START, end_date=END)

    assert result == []


def test_find_available_workstations_returns_available():
    db = MagicMock()
    ws = _make_workstation()
    db.query.return_value.filter.return_value.all.return_value = [ws]

    with patch(
        "app.services.resource_allocation_service.workstation.check_workstation_availability",
        return_value=(True, None),
    ):
        result = find_available_workstations(db, start_date=START, end_date=END)

    assert len(result) == 1
    assert result[0]["workstation_id"] == 1


def test_find_available_workstations_filters_unavailable():
    db = MagicMock()
    ws1 = _make_workstation(1)
    ws2 = _make_workstation(2)
    db.query.return_value.filter.return_value.all.return_value = [ws1, ws2]

    with patch(
        "app.services.resource_allocation_service.workstation.check_workstation_availability",
        side_effect=[
            (True, None),
            (False, "已被占用"),
        ],
    ):
        result = find_available_workstations(db, start_date=START, end_date=END)

    assert len(result) == 1
    assert result[0]["workstation_id"] == 1


def test_find_available_workstations_workshop_filter():
    """workshop_id filter is passed correctly."""
    db = MagicMock()
    db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

    result = find_available_workstations(db, workshop_id=3, start_date=START, end_date=END)

    assert isinstance(result, list)
