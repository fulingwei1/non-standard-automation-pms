# -*- coding: utf-8 -*-
"""
calculate_gross_margin() 方法测试

测试用例：
1. 正常情况：标准毛利率计算
2. 边界条件 1：零成本（100% 毛利）
3. 边界条件 2：负毛利（成本>收入）
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestCalculateGrossMargin:
    """calculate_gross_margin 方法测试"""

    def test_calculate_gross_margin_normal(self):
        """测试正常情况：标准毛利率计算"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        service = ProfitAnalysisService(mock_db)

        # Mock project: 合同金额 100000, 实际成本 60000
        # 毛利 = 100000 - 60000 = 40000
        # 毛利率 = 40000 / 100000 * 100% = 40%
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=60000):
            result = service.calculate_gross_margin(project_id=1, use_forecast=False)

        assert "error" not in result
        assert result["project_id"] == 1
        assert result["contract_amount"] == 100000.0
        assert result["total_cost"] == 60000.0
        assert result["profit"] == 40000.0
        assert result["gross_margin_rate"] == 40.0

    def test_calculate_gross_margin_zero_cost(self):
        """测试边界条件 1：零成本（100% 毛利）"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        service = ProfitAnalysisService(mock_db)

        # Mock project: 合同金额 100000, 实际成本 0
        # 毛利 = 100000 - 0 = 100000
        # 毛利率 = 100000 / 100000 * 100% = 100%
        mock_project = MagicMock()
        mock_project.id = 2
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=0):
            result = service.calculate_gross_margin(project_id=2, use_forecast=False)

        assert "error" not in result
        assert result["project_id"] == 2
        assert result["contract_amount"] == 100000.0
        assert result["total_cost"] == 0.0
        assert result["profit"] == 100000.0
        assert result["gross_margin_rate"] == 100.0

    def test_calculate_gross_margin_negative_margin(self):
        """测试边界条件 2：负毛利（成本 > 收入）"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        service = ProfitAnalysisService(mock_db)

        # Mock project: 合同金额 100000, 实际成本 120000
        # 毛利 = 100000 - 120000 = -20000
        # 毛利率 = -20000 / 100000 * 100% = -20%
        mock_project = MagicMock()
        mock_project.id = 3
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        with patch.object(service, '_get_actual_cost', return_value=120000):
            result = service.calculate_gross_margin(project_id=3, use_forecast=False)

        assert "error" not in result
        assert result["project_id"] == 3
        assert result["contract_amount"] == 100000.0
        assert result["total_cost"] == 120000.0
        assert result["profit"] == -20000.0
        assert result["gross_margin_rate"] == -20.0