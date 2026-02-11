# -*- coding: utf-8 -*-
"""Tests for resource_allocation_service/worker.py"""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestCheckWorkerAvailability:

    @patch("app.services.resource_allocation_service.worker.calculate_workdays", return_value=5)
    @patch("app.services.resource_allocation_service.worker.calculate_overlap_days", return_value=2)
    def test_worker_not_found(self, mock_overlap, mock_wd):
        from app.services.resource_allocation_service.worker import check_worker_availability
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        ok, reason, hours = check_worker_availability(db, 1, date(2024, 1, 1), date(2024, 1, 5))
        assert ok is False
        assert "不存在" in reason

    @patch("app.services.resource_allocation_service.worker.calculate_workdays", return_value=5)
    @patch("app.services.resource_allocation_service.worker.calculate_overlap_days", return_value=0)
    def test_worker_inactive(self, mock_overlap, mock_wd):
        from app.services.resource_allocation_service.worker import check_worker_availability
        db = MagicMock()
        worker = MagicMock()
        worker.is_active = False
        worker.status = "INACTIVE"
        db.query.return_value.filter.return_value.first.return_value = worker
        ok, reason, hours = check_worker_availability(db, 1, date(2024, 1, 1), date(2024, 1, 5))
        assert ok is False

    @patch("app.services.resource_allocation_service.worker.calculate_workdays", return_value=5)
    @patch("app.services.resource_allocation_service.worker.calculate_overlap_days", return_value=0)
    def test_worker_available(self, mock_overlap, mock_wd):
        from app.services.resource_allocation_service.worker import check_worker_availability
        db = MagicMock()
        worker = MagicMock()
        worker.is_active = True
        worker.status = "ACTIVE"
        db.query.return_value.filter.return_value.first.return_value = worker
        # No work orders, no allocations, no tasks
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value = MagicMock(__iter__=lambda s: iter([]))

        ok, reason, hours = check_worker_availability(db, 1, date(2024, 1, 1), date(2024, 1, 5))
        assert ok is True
        assert hours == 40.0  # 5 days * 8h


class TestFindAvailableWorkers:

    @patch("app.services.resource_allocation_service.worker.check_worker_availability")
    def test_find_no_workers(self, mock_check):
        from app.services.resource_allocation_service.worker import find_available_workers
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = find_available_workers(db, start_date=date(2024, 1, 1), end_date=date(2024, 1, 5))
        assert result == []

    @patch("app.services.resource_allocation_service.worker.check_worker_availability")
    def test_find_available_workers_happy(self, mock_check):
        from app.services.resource_allocation_service.worker import find_available_workers
        db = MagicMock()
        worker = MagicMock()
        worker.id = 1
        worker.worker_no = "W001"
        worker.worker_name = "张三"
        worker.workshop_id = 1
        worker.position = "技工"
        worker.skill_level = "高级"
        db.query.return_value.filter.return_value.all.return_value = [worker]
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [worker]
        mock_check.return_value = (True, None, 40.0)

        result = find_available_workers(db, start_date=date(2024, 1, 1), end_date=date(2024, 1, 5))
        assert len(result) == 1
        assert result[0]["worker_id"] == 1


class TestCheckWorkerSkill:

    def test_no_skills(self):
        from app.services.resource_allocation_service.worker import check_worker_skill
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        ok, matched = check_worker_skill(db, 1, "焊接")
        assert ok is False
        assert matched == []

    def test_skill_match(self):
        from app.services.resource_allocation_service.worker import check_worker_skill
        db = MagicMock()
        ws = MagicMock()
        proc = MagicMock()
        proc.process_code = "WELD01"
        proc.process_name = "焊接"
        proc.process_type = "加工"
        ws.process = proc
        db.query.return_value.join.return_value.filter.return_value.all.return_value = [ws]

        ok, matched = check_worker_skill(db, 1, "焊接")
        assert ok is True
        assert len(matched) == 1
