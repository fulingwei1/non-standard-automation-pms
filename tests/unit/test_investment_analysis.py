# -*- coding: utf-8 -*-
"""资源投入分析模块单元测试"""
import pytest
from unittest.mock import MagicMock
from decimal import Decimal
from app.services.resource_waste_analysis.investment import InvestmentAnalysisMixin


class TestInvestmentAnalysisMixin:
    def setup_method(self):
        self.mixin = InvestmentAnalysisMixin()
        self.mixin.db = MagicMock()
        self.mixin.hourly_rate = Decimal("200")

    def test_get_lead_resource_investment_empty(self):
        self.mixin.db.query.return_value.filter.return_value.all.return_value = []
        result = self.mixin.get_lead_resource_investment(1)
        assert result['total_hours'] == 0.0
        assert result['engineer_count'] == 0

    def test_get_lead_resource_investment_with_logs(self):
        log1 = MagicMock()
        log1.work_hours = 8.0
        log1.employee_id = 1
        log1.work_date = MagicMock()
        log1.work_date.strftime.return_value = "2024-01"
        log1.work_type = "design"

        log2 = MagicMock()
        log2.work_hours = 4.0
        log2.employee_id = 2
        log2.work_date = MagicMock()
        log2.work_date.strftime.return_value = "2024-01"
        log2.work_type = "testing"

        self.mixin.db.query.return_value.filter.return_value.all.return_value = [log1, log2]
        # For user queries
        user_mock = MagicMock()
        user_mock.name = "张三"
        self.mixin.db.query.return_value.filter.return_value.first.return_value = user_mock

        result = self.mixin.get_lead_resource_investment(1)
        assert result['total_hours'] == 12.0
        assert result['engineer_count'] == 2
