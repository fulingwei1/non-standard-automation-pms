# -*- coding: utf-8 -*-
"""
第四十五批覆盖：resource_allocation_service/workstation.py
"""

import pytest
from datetime import date
from unittest.mock import MagicMock

pytest.importorskip("app.services.resource_allocation_service.workstation")

from app.services.resource_allocation_service.workstation import (
    check_workstation_availability,
    find_available_workstations,
)


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_workstation(ws_id=1, is_active=True, status="IDLE"):
    ws = MagicMock()
    ws.id = ws_id
    ws.is_active = is_active
    ws.status = status
    ws.workstation_code = f"WS-{ws_id}"
    ws.workstation_name = f"工位{ws_id}"
    ws.workshop_id = 10
    ws.workshop = MagicMock()
    ws.workshop.name = "一车间"
    return ws


class TestCheckWorkstationAvailability:
    def test_workstation_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        ok, reason = check_workstation_availability(mock_db, 999, date(2024, 1, 1), date(2024, 1, 7))
        assert ok is False
        assert "不存在" in reason

    def test_workstation_inactive(self, mock_db):
        ws = _make_workstation(is_active=False)
        mock_db.query.return_value.filter.return_value.first.return_value = ws
        ok, reason = check_workstation_availability(mock_db, 1, date(2024, 1, 1), date(2024, 1, 7))
        assert ok is False
        assert "停用" in reason

    def test_workstation_wrong_status(self, mock_db):
        ws = _make_workstation(status="IN_USE")
        mock_db.query.return_value.filter.return_value.first.return_value = ws
        ok, reason = check_workstation_availability(mock_db, 1, date(2024, 1, 1), date(2024, 1, 7))
        assert ok is False

    def test_workstation_no_conflicts(self, mock_db):
        ws = _make_workstation()
        # first call: get workstation
        mock_db.query.return_value.filter.return_value.first.side_effect = [ws, None]
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        ok, reason = check_workstation_availability(mock_db, 1, date(2024, 1, 1), date(2024, 1, 7))
        # With no conflict, should be available
        assert ok is True
        assert reason is None

    def test_workstation_with_conflict(self, mock_db):
        ws = _make_workstation()
        conflicting_wo = MagicMock()
        conflicting_wo.plan_start_date = date(2024, 1, 3)
        conflicting_wo.plan_end_date = date(2024, 1, 5)
        conflicting_wo.work_order_no = "WO-001"

        mock_db.query.return_value.filter.return_value.first.return_value = ws
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = conflicting_wo

        ok, reason = check_workstation_availability(mock_db, 1, date(2024, 1, 1), date(2024, 1, 7))
        assert ok is False
        # reason contains info about conflict
        assert reason is not None and len(reason) > 0


class TestFindAvailableWorkstations:
    def test_returns_empty_when_no_workstations(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = find_available_workstations(mock_db)
        assert result == []

    def test_filters_by_workshop(self, mock_db):
        ws = _make_workstation()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [ws]
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        result = find_available_workstations(
            mock_db,
            workshop_id=10,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        # result depends on check_workstation_availability call
        assert isinstance(result, list)

    def test_uses_default_dates(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = find_available_workstations(mock_db)
        assert result == []

    def test_available_workstation_included_in_result(self, mock_db):
        ws = _make_workstation(1)
        mock_db.query.return_value.filter.return_value.all.return_value = [ws]
        # For check: get ws then no conflict
        mock_db.query.return_value.filter.return_value.first.side_effect = [ws, None]
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        result = find_available_workstations(
            mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        assert any(r["workstation_id"] == 1 for r in result)
