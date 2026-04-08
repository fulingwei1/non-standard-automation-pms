# -*- coding: utf-8 -*-
"""
物料采购优化服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List

from app.services.material_procurement_optimization_service import MaterialProcurementOptimizationService


class TestMaterialProcurementOptimizationServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = MaterialProcurementOptimizationService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            MaterialProcurementOptimizationService()


class TestMaterialProcurementOptimizationServiceMethods:
    """测试优化方法"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return MaterialProcurementOptimizationService(mock_db)

    def test_calculate_shortage_waste_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'calculate_shortage_waste')

    def test_get_safety_stock_alerts_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_safety_stock_alerts')

    def test_check_duplicate_purchase_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'check_duplicate_purchase')

    def test_get_slow_moving_analysis_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_slow_moving_analysis')


class TestMaterialProcurementOptimizationServiceConstants:
    """测试模块常量"""

    def test_module_exists(self):
        """测试模块可导入"""
        from app.services import material_procurement_optimization_service
        assert material_procurement_optimization_service is not None

    def test_service_class_exists(self):
        """测试服务类存在"""
        assert MaterialProcurementOptimizationService is not None