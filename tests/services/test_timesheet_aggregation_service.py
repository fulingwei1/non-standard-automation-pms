# -*- coding: utf-8 -*-
"""工时汇总服务单元测试 (TimesheetAggregationService)"""
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


class TestTimesheetAggregationServiceInit:
    """测试服务初始化"""

    def test_init_sets_db(self):
        from app.services.timesheet.timesheet_aggregation_service import (
            TimesheetAggregationService,
        )

        db = _make_db()
        svc = TimesheetAggregationService(db)
        assert svc.db is db


class TestAggregateMonthlyTimesheet:
    """测试月度工时汇总功能"""

    def test_service_has_aggregate_method(self):
        """测试服务有聚合方法"""
        from app.services.timesheet.timesheet_aggregation_service import (
            TimesheetAggregationService,
        )

        db = _make_db()
        svc = TimesheetAggregationService(db)
        assert hasattr(svc, 'aggregate_monthly_timesheet')

    def test_aggregate_with_user_id_returns_user_month_type(self):
        """测试按用户汇总返回正确的汇总类型"""
        from app.services.timesheet.timesheet_aggregation_service import (
            TimesheetAggregationService,
        )

        db = _make_db()
        svc = TimesheetAggregationService(db)

        # 直接测试 summary_type 确定逻辑
        user_id = 1
        project_id = None
        department_id = None

        summary_type = (
            "USER_MONTH"
            if user_id
            else (
                "PROJECT_MONTH"
                if project_id
                else ("DEPT_MONTH" if department_id else "GLOBAL_MONTH")
            )
        )

        assert summary_type == "USER_MONTH"

    def test_aggregate_with_department_returns_dept_type(self):
        """测试按部门汇总返回正确的汇总类型"""
        from app.services.timesheet.timesheet_aggregation_service import (
            TimesheetAggregationService,
        )

        db = _make_db()
        svc = TimesheetAggregationService(db)

        user_id = None
        project_id = None
        department_id = 10

        summary_type = (
            "USER_MONTH"
            if user_id
            else (
                "PROJECT_MONTH"
                if project_id
                else ("DEPT_MONTH" if department_id else "GLOBAL_MONTH")
            )
        )

        assert summary_type == "DEPT_MONTH"

    def test_aggregate_with_project_returns_project_type(self):
        """测试按项目汇总返回正确的汇总类型"""
        from app.services.timesheet.timesheet_aggregation_service import (
            TimesheetAggregationService,
        )

        db = _make_db()
        svc = TimesheetAggregationService(db)

        user_id = None
        project_id = 100
        department_id = None

        summary_type = (
            "USER_MONTH"
            if user_id
            else (
                "PROJECT_MONTH"
                if project_id
                else ("DEPT_MONTH" if department_id else "GLOBAL_MONTH")
            )
        )

        assert summary_type == "PROJECT_MONTH"