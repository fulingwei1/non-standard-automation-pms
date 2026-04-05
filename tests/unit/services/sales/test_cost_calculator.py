# -*- coding: utf-8 -*-
"""
成本计算器测试
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.sales.cost.cost_calculator import CostCalculator


class TestCostCalculator:
    """CostCalculator 测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def calculator(self, mock_db):
        """创建计算器实例"""
        return CostCalculator(mock_db)

    # ========== 硬件成本测试 ==========
    def test_calculate_hardware_cost_empty(self, calculator):
        """空硬件清单返回0"""
        assert calculator.calculate_hardware_cost(None) == Decimal("0")
        assert calculator.calculate_hardware_cost([]) == Decimal("0")

    def test_calculate_hardware_cost_single_item(self, calculator):
        """单个硬件项计算"""
        items = [{"unit_price": "1000", "quantity": "2"}]
        # 1000 * 2 * 1.15（加成）= 2300
        result = calculator.calculate_hardware_cost(items)
        assert result == Decimal("2300")

    def test_calculate_hardware_cost_multiple_items(self, calculator):
        """多个硬件项计算"""
        items = [
            {"unit_price": "1000", "quantity": "2"},
            {"unit_price": "500", "quantity": "5"},
        ]
        # (1000*2 + 500*5) * 1.15 = 4500 * 1.15 = 5175
        result = calculator.calculate_hardware_cost(items)
        assert result == Decimal("5175.00")

    def test_calculate_hardware_cost_missing_fields(self, calculator):
        """缺失字段使用默认值"""
        items = [{"unit_price": "1000"}]  # 缺少 quantity，默认为 1
        result = calculator.calculate_hardware_cost(items)
        assert result == Decimal("1150.00")

    # ========== 软件成本测试 ==========
    def test_calculate_software_cost_with_man_days(self, calculator):
        """指定人天计算"""
        # 10 人天 * 8 小时 * 800 元/小时 = 64000
        result = calculator.calculate_software_cost(None, 10)
        assert result == Decimal("64000")

    def test_calculate_software_cost_no_input(self, calculator):
        """无输入返回0"""
        result = calculator.calculate_software_cost(None, None)
        assert result == Decimal("0")

    def test_calculate_software_cost_short_requirements(self, calculator):
        """短需求描述估算5人天"""
        # 短描述 (<100字符) -> 5 人天 -> 5 * 8 * 800 = 32000
        result = calculator.calculate_software_cost("简单功能需求", None)
        assert result == Decimal("32000")

    def test_calculate_software_cost_medium_requirements(self, calculator):
        """中等需求描述估算15人天"""
        # 中等描述 (100-500字符) -> 15 人天 -> 15 * 8 * 800 = 96000
        requirements = "这是一个中等复杂度的需求描述，" * 10  # 约150字符
        result = calculator.calculate_software_cost(requirements, None)
        assert result == Decimal("96000")

    def test_calculate_software_cost_long_requirements(self, calculator):
        """长需求描述估算30人天"""
        # 长描述 (>500字符) -> 30 人天 -> 30 * 8 * 800 = 192000
        requirements = "这是一个非常复杂的需求描述，" * 50  # 约750字符
        result = calculator.calculate_software_cost(requirements, None)
        assert result == Decimal("192000")

    # ========== 安装成本测试 ==========
    def test_calculate_installation_cost_low_difficulty(self, calculator):
        """低难度安装"""
        hardware_cost = Decimal("10000")
        # 5000 * 1.0 + 10000 * 0.05 = 5500
        result = calculator.calculate_installation_cost("low", hardware_cost)
        assert result == Decimal("5500")

    def test_calculate_installation_cost_medium_difficulty(self, calculator):
        """中等难度安装"""
        hardware_cost = Decimal("10000")
        # 5000 * 1.5 + 10000 * 0.05 = 8000
        result = calculator.calculate_installation_cost("medium", hardware_cost)
        assert result == Decimal("8000")

    def test_calculate_installation_cost_high_difficulty(self, calculator):
        """高难度安装"""
        hardware_cost = Decimal("10000")
        # 5000 * 2.0 + 10000 * 0.05 = 10500
        result = calculator.calculate_installation_cost("high", hardware_cost)
        assert result == Decimal("10500")

    # ========== 服务成本测试 ==========
    def test_calculate_service_cost(self, calculator):
        """服务成本计算"""
        base_cost = Decimal("100000")
        # 100000 * 0.10 * 3 = 30000
        result = calculator.calculate_service_cost(base_cost, 3)
        assert result == Decimal("30000")

    def test_calculate_service_cost_one_year(self, calculator):
        """一年服务成本"""
        base_cost = Decimal("50000")
        # 50000 * 0.10 * 1 = 5000
        result = calculator.calculate_service_cost(base_cost, 1)
        assert result == Decimal("5000")

    # ========== 风险储备金测试 ==========
    def test_calculate_risk_reserve_low_complexity(self, calculator, mock_db):
        """低复杂度风险储备"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        base_cost = Decimal("100000")
        # 100000 * 0.08 * 0.5 = 4000
        result = calculator.calculate_risk_reserve("standard", "low", base_cost)
        assert result == Decimal("4000")

    def test_calculate_risk_reserve_high_complexity(self, calculator, mock_db):
        """高复杂度风险储备"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        base_cost = Decimal("100000")
        # 100000 * 0.08 * 1.5 = 12000
        result = calculator.calculate_risk_reserve("standard", "high", base_cost)
        assert result == Decimal("12000")

    def test_calculate_risk_reserve_medium_complexity(self, calculator, mock_db):
        """中等复杂度风险储备"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        base_cost = Decimal("100000")
        # 100000 * 0.08 = 8000
        result = calculator.calculate_risk_reserve("standard", "medium", base_cost)
        assert result == Decimal("8000")
