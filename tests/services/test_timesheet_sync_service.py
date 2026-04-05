# -*- coding: utf-8 -*-
"""工时同步服务单元测试 (TimesheetSyncService)"""
import os
import sys

# Setup environment BEFORE importing app
from unittest.mock import MagicMock
redis_mock = MagicMock()
sys.modules['redis'] = redis_mock
sys.modules['redis.exceptions'] = MagicMock()

os.environ['SQLITE_DB_PATH'] = ':memory:'
os.environ['REDIS_URL'] = ''
os.environ['DEBUG'] = 'true'
os.environ['ENABLE_SCHEDULER'] = 'false'
os.environ['RATE_LIMIT_ENABLED'] = 'false'


def _make_db():
    return MagicMock()


def _make_timesheet(**kw):
    t = MagicMock()
    defaults = dict(
        id=1,
        user_id=1,
        project_id=1,
        hours=8.0,
        status="APPROVED",
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


class TestTimesheetSyncServiceInit:
    """测试服务初始化"""

    def test_init_sets_db(self):
        from app.services.timesheet.timesheet_sync_service import (
            TimesheetSyncService,
        )

        db = _make_db()
        svc = TimesheetSyncService(db)
        assert svc.db is db


class TestSyncToFinance:
    """测试同步到财务系统"""

    def test_sync_single_timesheet_not_found(self):
        """测试同步不存在的工时记录"""
        from app.services.timesheet.timesheet_sync_service import (
            TimesheetSyncService,
        )

        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        db.query.return_value = mock_query

        svc = TimesheetSyncService(db)
        result = svc.sync_to_finance(timesheet_id=999)

        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_sync_single_timesheet_not_approved(self):
        """测试同步未审批的工时记录"""
        from app.services.timesheet.timesheet_sync_service import (
            TimesheetSyncService,
        )

        db = MagicMock()
        mock_ts = _make_timesheet(status="PENDING")
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_ts
        db.query.return_value = mock_query

        svc = TimesheetSyncService(db)
        result = svc.sync_to_finance(timesheet_id=1)

        assert result["success"] is False
        assert "审批" in result["message"]

    def test_sync_single_timesheet_no_project(self):
        """测试同步未关联项目的工时记录"""
        from app.services.timesheet.timesheet_sync_service import (
            TimesheetSyncService,
        )

        db = MagicMock()
        mock_ts = _make_timesheet(status="APPROVED", project_id=None)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_ts
        db.query.return_value = mock_query

        svc = TimesheetSyncService(db)
        result = svc.sync_to_finance(timesheet_id=1)

        assert result["success"] is False
        assert "关联项目" in result["message"]

    def test_sync_single_approved_timesheet(self):
        """测试同步已审批且有关联项目的工时记录"""
        from app.services.timesheet.timesheet_sync_service import (
            TimesheetSyncService,
        )

        db = MagicMock()
        mock_ts = _make_timesheet(
            id=1, status="APPROVED", project_id=100, hours=8.0
        )
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_ts
        db.query.return_value = mock_query

        svc = TimesheetSyncService(db)
        svc._create_financial_cost_from_timesheet = MagicMock(
            return_value={"success": True, "created": True}
        )
        result = svc.sync_to_finance(timesheet_id=1)

        assert result["success"] is True


class TestSyncServiceMethods:
    """测试同步服务其他方法"""

    def test_service_has_sync_to_rd_method(self):
        """测试服务有同步到研发系统的方法"""
        from app.services.timesheet.timesheet_sync_service import (
            TimesheetSyncService,
        )

        db = _make_db()
        svc = TimesheetSyncService(db)
        assert hasattr(svc, 'sync_to_rd')

    def test_service_has_sync_to_finance_method(self):
        """测试服务有同步到财务系统的方法"""
        from app.services.timesheet.timesheet_sync_service import (
            TimesheetSyncService,
        )

        db = _make_db()
        svc = TimesheetSyncService(db)
        assert hasattr(svc, 'sync_to_finance')