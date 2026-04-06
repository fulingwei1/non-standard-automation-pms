# -*- coding: utf-8 -*-
"""
物料采购优化服务测试
目标覆盖率: 60%+
测试用例数: 6个
"""
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.services.material_procurement_optimization_service import (
    MaterialProcurementOptimizationService,
)


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return Mock()


@pytest.fixture
def procurement_service(mock_db):
    """创建物料采购优化服务实例"""
    return MaterialProcurementOptimizationService(mock_db)


class TestMaterialProcurementOptimization:
    """物料采购优化服务测试类"""

    def test_service_initialization(self, mock_db):
        """测试服务初始化"""
        service = MaterialProcurementOptimizationService(mock_db)
        assert service is not None

    def test_d_helper_method(self, procurement_service):
        """测试_d辅助方法"""
        result = procurement_service._d("100")
        assert result == Decimal("100")

    def test_d_helper_default(self, procurement_service):
        """测试_d辅助方法-默认值"""
        result = procurement_service._d(None, "0")
        assert result == Decimal("0")

    def test_round_money(self, procurement_service):
        """测试金额舍入"""
        value = Decimal("123.456")
        result = procurement_service._round_money(value)
        assert isinstance(result, Decimal)

    def test_safe_str_normal(self, procurement_service):
        """测试安全字符串转换-正常"""
        result = procurement_service._safe_str("  test  ")
        assert result == "test"

    def test_safe_str_none(self, procurement_service):
        """测试安全字符串转换-None"""
        result = procurement_service._safe_str(None)
        assert result == ""

    def test_round_up_to_moq_basic(self, procurement_service):
        """测试按MOQ向上取整"""
        qty = Decimal("15")
        moq = Decimal("10")

        result = procurement_service._round_up_to_moq(qty, moq)
        assert result == Decimal("20")

    def test_round_up_to_moq_below_moq(self, procurement_service):
        """测试按MOQ向上取整-低于MOQ"""
        qty = Decimal("5")
        moq = Decimal("10")

        result = procurement_service._round_up_to_moq(qty, moq)
        assert result == Decimal("10")