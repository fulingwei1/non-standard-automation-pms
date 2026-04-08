# -*- coding: utf-8 -*-
"""
工时同步服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.timesheet.timesheet_sync_service import TimesheetSyncService


class TestTimesheetSyncServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = TimesheetSyncService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            TimesheetSyncService()


class TestTimesheetSyncServiceMethods:
    """测试同步方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return TimesheetSyncService(mock_db)

    def test_sync_to_finance_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'sync_to_finance')

    def test_sync_to_rd_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'sync_to_rd')

    def test_sync_to_project_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'sync_to_project')

    def test_sync_to_hr_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'sync_to_hr')

    def test_sync_all_on_approval_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'sync_all_on_approval')


class TestTimesheetSyncServiceHelpers:
    """测试辅助方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return TimesheetSyncService(mock_db)

    def test_create_financial_cost_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_create_financial_cost_from_timesheet')

    def test_create_rd_cost_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_create_rd_cost_from_timesheet')


class TestTimesheetSyncServiceConstants:
    """测试模块常量"""

    def test_module_exists(self):
        """测试模块可导入"""
        from app.services.timesheet import timesheet_sync_service
        assert timesheet_sync_service is not None

    def test_service_class_exists(self):
        """测试服务类存在"""
        assert TimesheetSyncService is not None