# -*- coding: utf-8 -*-
"""
Timesheet分析服务测试
"""

from unittest.mock import MagicMock


class TestTimesheetAnalyticsService:
    """工时分析服务测试"""

    def test_init(self):
        """测试初始化"""
        from app.services.timesheet.timesheet_analytics_service import TimesheetAnalyticsService

        mock_db = MagicMock()
        service = TimesheetAnalyticsService(mock_db)

        assert service.db is mock_db

    def test_has_current_trend_api(self):
        """测试暴露当前趋势分析接口"""
        from app.services.timesheet.timesheet_analytics_service import TimesheetAnalyticsService

        service = TimesheetAnalyticsService(MagicMock())
        assert callable(service.analyze_trend)

    def test_has_current_workload_api(self):
        """测试暴露当前负荷分析接口"""
        from app.services.timesheet.timesheet_analytics_service import TimesheetAnalyticsService

        service = TimesheetAnalyticsService(MagicMock())
        assert callable(service.analyze_workload)

    def test_has_current_efficiency_api(self):
        """测试暴露当前效率分析接口"""
        from app.services.timesheet.timesheet_analytics_service import TimesheetAnalyticsService

        service = TimesheetAnalyticsService(MagicMock())
        assert callable(service.analyze_efficiency)

    def test_has_current_overtime_api(self):
        """测试暴露当前加班分析接口"""
        from app.services.timesheet.timesheet_analytics_service import TimesheetAnalyticsService

        service = TimesheetAnalyticsService(MagicMock())
        assert callable(service.analyze_overtime)

    def test_has_current_department_comparison_api(self):
        """测试暴露当前部门对比接口"""
        from app.services.timesheet.timesheet_analytics_service import TimesheetAnalyticsService

        service = TimesheetAnalyticsService(MagicMock())
        assert callable(service.analyze_department_comparison)

    def test_has_current_project_distribution_api(self):
        """测试暴露当前项目分布接口"""
        from app.services.timesheet.timesheet_analytics_service import TimesheetAnalyticsService

        service = TimesheetAnalyticsService(MagicMock())
        assert callable(service.analyze_project_distribution)
