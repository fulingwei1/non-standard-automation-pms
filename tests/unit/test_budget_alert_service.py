# -*- coding: utf-8 -*-
"""
预算预警服务测试（最小版）
"""

import pytest
from unittest.mock import MagicMock


class TestBudgetAlertService:
    """预算预警服务测试"""

    def test_service_creation(self):
        """测试服务创建"""
        from app.services.budget_alert_service import BudgetAlertService
        
        mock_db = MagicMock()
        service = BudgetAlertService(mock_db)
        
        assert service is not None
        assert service.db == mock_db


class TestCostBreakdown:
    """测试成本分解"""

    def test_cost_breakdown_creation(self):
        """测试成本分解创建"""
        from app.services.budget_alert_service import CostBreakdown
        from decimal import Decimal
        
        breakdown = CostBreakdown(
            actual_cost=Decimal("50000"),
            committed_cost=Decimal("10000"),
            forecast_remaining=Decimal("30000"),
            total_forecast=Decimal("90000"),
        )
        
        assert breakdown.actual_cost == Decimal("50000")
        assert breakdown.committed_cost == Decimal("10000")


class TestExecutionRates:
    """测试执行率"""

    def test_execution_rates_creation(self):
        """测试执行率创建"""
        from app.services.budget_alert_service import ExecutionRates
        
        rates = ExecutionRates(
            actual_rate=50.0,
            committed_rate=60.0,
            forecast_rate=80.0,
        )
        
        assert rates.actual_rate == 50.0
        assert rates.committed_rate == 60.0