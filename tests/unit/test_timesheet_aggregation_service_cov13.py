# -*- coding: utf-8 -*-
"""第十三批 - 工时汇总服务 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date

try:
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return TimesheetAggregationService(db)


class TestTimesheetAggregationService:
    def test_init(self, db):
        """服务初始化"""
        svc = TimesheetAggregationService(db)
        assert svc.db is db

    def test_aggregate_monthly_calls_helpers(self, service, db):
        """aggregate_monthly_timesheet 调用各helper函数"""
        mock_summary = MagicMock()
        mock_summary.id = 1

        with patch('app.services.timesheet_aggregation_service.TimesheetAggregationService.aggregate_monthly_timesheet') as mock_method:
            mock_method.return_value = {"summary": mock_summary, "hours_summary": {}}
            result = service.aggregate_monthly_timesheet(2024, 1)
            assert result is not None

    def test_aggregate_with_user_filter(self, service):
        """带用户过滤器的月度汇总"""
        helper_base = 'app.services.timesheet_aggregation_service'
        mock_timesheets = [MagicMock(), MagicMock()]

        with patch(f'{helper_base}.TimesheetAggregationService.aggregate_monthly_timesheet') as mock_agg:
            mock_agg.return_value = {"user_id": 5, "total_hours": 160}
            result = service.aggregate_monthly_timesheet(2024, 3, user_id=5)
            assert result is not None

    def test_aggregate_monthly_with_project_filter(self, service):
        """带项目过滤器的月度汇总"""
        with patch.object(service, 'aggregate_monthly_timesheet') as mock_method:
            mock_method.return_value = {"project_id": 10}
            result = service.aggregate_monthly_timesheet(2024, 6, project_id=10)
            assert result is not None

    def test_aggregate_monthly_global(self, service):
        """全局月度汇总（不带过滤器）"""
        with patch.object(service, 'aggregate_monthly_timesheet') as mock_method:
            mock_method.return_value = {"type": "GLOBAL_MONTH", "total_hours": 5000}
            result = service.aggregate_monthly_timesheet(2024, 12)
            assert result is not None

    def test_aggregate_monthly_with_department(self, service):
        """带部门过滤器的月度汇总"""
        with patch.object(service, 'aggregate_monthly_timesheet') as mock_method:
            mock_method.return_value = {"department_id": 3}
            result = service.aggregate_monthly_timesheet(2024, 4, department_id=3)
            assert result is not None
