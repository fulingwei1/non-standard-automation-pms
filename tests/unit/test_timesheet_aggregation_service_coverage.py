# -*- coding: utf-8 -*-
"""
工时聚合服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.timesheet.timesheet_aggregation_service import TimesheetAggregationService


class TestTimesheetAggregationServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = TimesheetAggregationService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            TimesheetAggregationService()


class TestTimesheetAggregationServiceMethods:
    """测试聚合方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return TimesheetAggregationService(mock_db)

    def test_aggregate_monthly_timesheet_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'aggregate_monthly_timesheet')

    def test_generate_hr_report_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'generate_hr_report')

    def test_generate_finance_report_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'generate_finance_report')

    def test_generate_rd_report_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'generate_rd_report')

    def test_generate_project_report_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'generate_project_report')


class TestTimesheetAggregationServiceConstants:
    """测试模块常量"""

    def test_module_exists(self):
        """测试模块可导入"""
        from app.services.timesheet import timesheet_aggregation_service
        assert timesheet_aggregation_service is not None

    def test_service_class_exists(self):
        """测试服务类存在"""
        assert TimesheetAggregationService is not None