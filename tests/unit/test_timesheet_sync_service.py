# -*- coding: utf-8 -*-
"""工时数据同步服务测试"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.timesheet_sync_service import TimesheetSyncService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return TimesheetSyncService(db)


class TestSyncToFinance:
    def test_timesheet_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_to_finance(timesheet_id=999)
        assert result['success'] is False
        assert '不存在' in result['message']

    def test_timesheet_not_approved(self, service, db):
        ts = MagicMock(status='DRAFT')
        db.query.return_value.filter.return_value.first.return_value = ts
        result = service.sync_to_finance(timesheet_id=1)
        assert result['success'] is False
        assert '已审批' in result['message']

    def test_timesheet_no_project(self, service, db):
        ts = MagicMock(status='APPROVED', project_id=None)
        db.query.return_value.filter.return_value.first.return_value = ts
        result = service.sync_to_finance(timesheet_id=1)
        assert result['success'] is False

    def test_incomplete_params(self, service):
        result = service.sync_to_finance()
        assert result['success'] is False
        assert '参数不完整' in result['message']


class TestSyncToRd:
    def test_timesheet_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_to_rd(timesheet_id=999)
        assert result['success'] is False

    def test_no_rd_project(self, service, db):
        ts = MagicMock(status='APPROVED', rd_project_id=None)
        db.query.return_value.filter.return_value.first.return_value = ts
        result = service.sync_to_rd(timesheet_id=1)
        assert result['success'] is False

    def test_incomplete_params(self, service):
        result = service.sync_to_rd()
        assert result['success'] is False


class TestSyncToProject:
    def test_timesheet_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_to_project(timesheet_id=999)
        assert result['success'] is False

    def test_not_approved(self, service, db):
        ts = MagicMock(status='DRAFT')
        db.query.return_value.filter.return_value.first.return_value = ts
        result = service.sync_to_project(timesheet_id=1)
        assert result['success'] is False

    def test_incomplete_params(self, service):
        result = service.sync_to_project()
        assert result['success'] is False


class TestSyncToHr:
    @patch('app.services.timesheet_sync_service.OvertimeCalculationService')
    def test_sync_hr(self, mock_ot, service, db):
        mock_instance = MagicMock()
        mock_ot.return_value = mock_instance
        mock_instance.get_overtime_statistics.return_value = {'total': 10}
        result = service.sync_to_hr(2026, 1)
        assert result['success'] is True


class TestSyncAllOnApproval:
    def test_not_found(self, service, db):
        db.query.return_value.filter.return_value.first.return_value = None
        result = service.sync_all_on_approval(999)
        assert result['success'] is False

    def test_with_project_and_rd(self, service, db):
        ts = MagicMock(id=1, project_id=1, rd_project_id=2, status='APPROVED')
        db.query.return_value.filter.return_value.first.return_value = ts
        with patch.object(service, 'sync_to_finance', return_value={'success': True}), \
             patch.object(service, 'sync_to_project', return_value={'success': True}), \
             patch.object(service, 'sync_to_rd', return_value={'success': True}):
            result = service.sync_all_on_approval(1)
            assert result['success'] is True
