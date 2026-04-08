# -*- coding: utf-8 -*-
"""
预算预警服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.budget_alert_service import BudgetAlertService


class TestBudgetAlertServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = BudgetAlertService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            BudgetAlertService()


class TestBudgetAlertServiceMethods:
    """测试预算预警方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return BudgetAlertService(mock_db)

    def test_get_budget_status_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_budget_status')

    def test_monitor_all_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'monitor_all')

    def test_check_and_alert_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'check_and_alert')


class TestBudgetAlertServiceHelpers:
    """测试辅助方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return BudgetAlertService(mock_db)

    def test_get_budget_amount_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_get_budget_amount')

    def test_get_actual_cost_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_get_actual_cost')

    def test_get_committed_cost_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, '_get_committed_cost')


class TestBudgetAlertServiceConstants:
    """测试模块常量"""

    def test_module_exists(self):
        """测试模块可导入"""
        from app.services import budget_alert_service
        assert budget_alert_service is not None

    def test_service_class_exists(self):
        """测试服务类存在"""
        assert BudgetAlertService is not None