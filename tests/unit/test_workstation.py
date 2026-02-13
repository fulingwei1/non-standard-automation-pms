# -*- coding: utf-8 -*-
"""Tests for resource_allocation_service/workstation.py"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date


class TestCheckWorkstationAvailability:
    def test_not_found(self):
        from app.services.resource_allocation_service.workstation import check_workstation_availability
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        ok, reason = check_workstation_availability(db, 1, date(2025, 1, 1), date(2025, 1, 7))
        assert ok is False
        assert '不存在' in reason

    def test_inactive(self):
        from app.services.resource_allocation_service.workstation import check_workstation_availability
        db = MagicMock()
        ws = MagicMock(is_active=False)
        db.query.return_value.filter.return_value.first.return_value = ws
        ok, reason = check_workstation_availability(db, 1, date(2025, 1, 1), date(2025, 1, 7))
        assert ok is False
        assert '停用' in reason

    def test_wrong_status(self):
        from app.services.resource_allocation_service.workstation import check_workstation_availability
        db = MagicMock()
        ws = MagicMock(is_active=True, status='IN_USE')
        db.query.return_value.filter.return_value.first.return_value = ws
        ok, reason = check_workstation_availability(db, 1, date(2025, 1, 1), date(2025, 1, 7))
        assert ok is False

    def test_available(self):
        from app.services.resource_allocation_service.workstation import check_workstation_availability
        db = MagicMock()
        ws = MagicMock(is_active=True, status='IDLE')
        db.query.return_value.filter.return_value.first.side_effect = [ws, None]
        # No conflicting orders
        db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        ok, reason = check_workstation_availability(db, 1, date(2025, 1, 1), date(2025, 1, 7))
        assert ok is True


class TestFindAvailableWorkstations:
    def test_empty(self):
        from app.services.resource_allocation_service.workstation import find_available_workstations
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = find_available_workstations(db)
        assert result == []
