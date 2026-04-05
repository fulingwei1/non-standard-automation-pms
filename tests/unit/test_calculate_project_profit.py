# -*- coding: utf-8 -*-
"""
测试 calculate_project_profit 函数

测试场景：
1. 正常情况：有收入有成本
2. 边界条件 1：零成本（100% 毛利）
3. 边界条件 2：负利润（成本>收入）
"""

import pytest
from decimal import Decimal

from app.utils.numerical_utils import calculate_project_profit


class TestCalculateProjectProfit:
    """测试项目利润计算"""

    def test_normal_profit(self):
        """正常情况：有收入有成本，利润为正"""
        result = calculate_project_profit(revenue=100000, cost=70000)
        
        assert result["revenue"] == Decimal("100000.00")
        assert result["cost"] == Decimal("70000.00")
        assert result["profit"] == Decimal("30000.00")
        assert result["margin_rate"] == Decimal("0.300000")  # 30% 毛利率

    def test_zero_cost_100_percent_margin(self):
        """边界条件 1：零成本（100% 毛利）"""
        result = calculate_project_profit(revenue=50000, cost=0)
        
        assert result["revenue"] == Decimal("50000.00")
        assert result["cost"] == Decimal("0.00")
        assert result["profit"] == Decimal("50000.00")
        assert result["margin_rate"] == Decimal("1.000000")  # 100% 毛利率

    def test_negative_profit(self):
        """边界条件 2：负利润（成本>收入）"""
        result = calculate_project_profit(revenue=80000, cost=100000)
        
        assert result["revenue"] == Decimal("80000.00")
        assert result["cost"] == Decimal("100000.00")
        assert result["profit"] == Decimal("-20000.00")
        assert result["margin_rate"] == Decimal("-0.250000")  # -25% 毛利率

    def test_zero_revenue_zero_cost(self):
        """收入和成本都为0"""
        result = calculate_project_profit(revenue=0, cost=0)
        
        assert result["revenue"] == Decimal("0.00")
        assert result["cost"] == Decimal("0.00")
        assert result["profit"] == Decimal("0.00")
        assert result["margin_rate"] == Decimal("0.000000")

    def test_with_decimal_inputs(self):
        """Decimal 类型输入"""
        result = calculate_project_profit(
            revenue=Decimal("12345.67"),
            cost=Decimal("8000.50"),
        )
        
        assert result["revenue"] == Decimal("12345.67")
        assert result["cost"] == Decimal("8000.50")
        assert result["profit"] == Decimal("4345.17")