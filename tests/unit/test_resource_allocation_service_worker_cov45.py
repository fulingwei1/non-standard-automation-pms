# -*- coding: utf-8 -*-
"""
第四十五批覆盖：resource_allocation_service/worker.py
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.resource_allocation_service.worker")

from app.services.resource_allocation_service.worker import (
    check_worker_availability,
    find_available_workers,
    check_worker_skill,
)


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_worker(worker_id=1, is_active=True, status="ACTIVE"):
    w = MagicMock()
    w.id = worker_id
    w.is_active = is_active
    w.status = status
    w.worker_no = f"W-{worker_id}"
    w.worker_name = f"Worker {worker_id}"
    w.workshop_id = 10
    w.position = "操作员"
    w.skill_level = "中级"
    return w


class TestCheckWorkerAvailability:
    def test_worker_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        ok, reason, hours = check_worker_availability(mock_db, 999, date(2024, 1, 1), date(2024, 1, 7))
        assert ok is False
        assert "不存在" in reason
        assert hours == 0.0

    def test_worker_inactive(self, mock_db):
        worker = _make_worker(is_active=False)
        mock_db.query.return_value.filter.return_value.first.return_value = worker
        ok, reason, hours = check_worker_availability(mock_db, 1, date(2024, 1, 1), date(2024, 1, 7))
        assert ok is False
        assert hours == 0.0

    @patch("app.services.resource_allocation_service.worker.calculate_workdays", return_value=5)
    @patch("app.services.resource_allocation_service.worker.calculate_overlap_days", return_value=0)
    def test_worker_fully_available(self, mock_overlap, mock_workdays, mock_db):
        worker = _make_worker()
        # first call: get worker
        mock_db.query.return_value.filter.return_value.first.return_value = worker
        # subsequent calls: no conflicting orders/allocations/tasks
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        ok, reason, hours = check_worker_availability(
            mock_db, 1, date(2024, 1, 1), date(2024, 1, 7), required_hours=8.0
        )
        # With 5 workdays and no allocations, available=40h, required=40h -> ok
        assert ok is True
        assert reason is None

    def test_worker_bad_status(self, mock_db):
        worker = _make_worker(status="RESIGNED")
        mock_db.query.return_value.filter.return_value.first.return_value = worker
        ok, reason, hours = check_worker_availability(mock_db, 1, date(2024, 1, 1), date(2024, 1, 7))
        assert ok is False


class TestFindAvailableWorkers:
    @patch("app.services.resource_allocation_service.worker.check_worker_availability")
    def test_returns_available_workers(self, mock_check, mock_db):
        worker = _make_worker(1)
        mock_db.query.return_value.filter.return_value.all.return_value = [worker]
        mock_check.return_value = (True, None, 40.0)

        result = find_available_workers(
            mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        assert len(result) == 1
        assert result[0]["worker_id"] == 1
        assert result[0]["available_hours"] == 40.0

    @patch("app.services.resource_allocation_service.worker.check_worker_availability")
    def test_filters_unavailable_workers(self, mock_check, mock_db):
        worker = _make_worker(1)
        mock_db.query.return_value.filter.return_value.all.return_value = [worker]
        mock_check.return_value = (False, "工时不足", 0.0)

        result = find_available_workers(
            mock_db,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
        )
        assert result == []

    @patch("app.services.resource_allocation_service.worker.check_worker_availability")
    def test_uses_default_dates_when_none(self, mock_check, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = find_available_workers(mock_db)
        assert result == []


class TestCheckWorkerSkill:
    def test_no_skills_returns_false(self, mock_db):
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        ok, matched = check_worker_skill(mock_db, 1, "焊接")
        assert ok is False
        assert matched == []
