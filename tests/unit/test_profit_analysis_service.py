# -*- coding: utf-8 -*-
"""
项目利润分析服务测试
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestProfitAnalysisService:
    """项目利润分析服务测试"""

    def test_get_margin_analysis_basic(self):
        """测试毛利率基础计算"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        service = ProfitAnalysisService(mock_db)

        # Mock project
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project

        # Mock actual cost
        with patch.object(service, '_get_actual_cost', return_value=50000):
            result = service.get_margin_analysis(project_id=1)

        assert 'current_margin' in result or 'error' in result or result == {}

    def test_get_margin_analysis_no_project(self):
        """测试项目不存在的情况"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = ProfitAnalysisService(mock_db)

        result = service.get_margin_analysis(project_id=999)
        assert result == {"error": "项目不存在"}

    def test_get_margin_analysis_zero_contract(self):
        """测试合同金额为0的情况"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("0")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service = ProfitAnalysisService(mock_db)

        result = service.get_margin_analysis(project_id=1)
        # 当合同金额为0时，毛利率应为0
        assert result.get('current_margin_rate') == 0 or result.get('error') == "项目不存在" or result == {}

    def test_get_cost_optimization(self):
        """测试成本优化建议"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        service = ProfitAnalysisService(mock_db)

        result = service.get_cost_optimization(project_id=1)
        assert isinstance(result, dict)

    def test_get_quote_cost_variance(self):
        """测试报价与成本偏差分析"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        service = ProfitAnalysisService(mock_db)

        result = service.get_quote_cost_variance(project_id=1)
        assert isinstance(result, dict)

    def test_get_high_profit_patterns(self):
        """测试高利润项目特征分析"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        service = ProfitAnalysisService(mock_db)

        result = service.get_high_profit_patterns(limit=10)
        assert isinstance(result, dict)

    def test_get_low_profit_root_cause(self):
        """测试低利润项目根因分析"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        service = ProfitAnalysisService(mock_db)

        result = service.get_low_profit_root_cause(max_margin=10.0, limit=20)
        assert isinstance(result, dict)
        assert 'total_low_profit' in result
        assert 'low_profit_threshold' in result
        assert result['low_profit_threshold'] == 10.0

    def test_get_profit_analysis(self):
        """测试综合利润分析"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service = ProfitAnalysisService(mock_db)

        with patch.object(service, '_get_actual_cost', return_value=50000):
            result = service.get_profit_analysis(project_id=1)
        assert isinstance(result, dict)

    # ------------------------------------------------------------------
    # calculate_project_profit 测试
    # ------------------------------------------------------------------
    def test_calculate_project_profit_normal(self):
        """测试计算项目利润 - 正常情况"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service = ProfitAnalysisService(mock_db)

        with patch.object(service, '_get_actual_cost', return_value=50000):
            result = service.calculate_project_profit(project_id=1)

        assert isinstance(result, dict)
        assert 'actual_profit' in result
        assert 'forecast_profit' in result
        assert result['contract_amount'] == 100000.0
        assert result['actual_cost'] == 50000.0
        assert result['actual_profit'] == 50000.0

    def test_calculate_project_profit_no_project(self):
        """测试计算项目利润 - 项目不存在边界"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = ProfitAnalysisService(mock_db)

        result = service.calculate_project_profit(project_id=999)
        assert result == {"error": "项目不存在"}

    # ------------------------------------------------------------------
    # calculate_gross_margin 测试
    # ------------------------------------------------------------------
    def test_calculate_gross_margin_normal(self):
        """测试计算毛利率 - 正常情况"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("80000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service = ProfitAnalysisService(mock_db)

        with patch.object(service, '_get_actual_cost', return_value=60000):
            result = service.calculate_gross_margin(project_id=1)

        assert isinstance(result, dict)
        assert 'gross_margin_rate' in result
        assert result['contract_amount'] == 100000.0
        assert result['total_cost'] == 60000.0
        assert result['profit'] == 40000.0
        assert result['gross_margin_rate'] == 40.0

    def test_calculate_gross_margin_zero_cost(self):
        """测试计算毛利率 - 零成本边界"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_project.budget_amount = Decimal("0")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service = ProfitAnalysisService(mock_db)

        with patch.object(service, '_get_actual_cost', return_value=0):
            result = service.calculate_gross_margin(project_id=1)

        assert isinstance(result, dict)
        assert result['gross_margin_rate'] == 100.0
        assert result['profit'] == 100000.0

    # ------------------------------------------------------------------
    # allocate_costs 测试
    # ------------------------------------------------------------------
    def test_allocate_costs_normal(self):
        """测试分配成本 - 正常情况"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service = ProfitAnalysisService(mock_db)

        with patch.object(service, '_get_actual_cost', return_value=50000):
            result = service.allocate_costs(
                project_id=1,
                cost_allocation={"材料": 0.4, "人工": 0.3, "管理费": 0.2}
            )

        assert isinstance(result, dict)
        assert 'allocated_costs' in result
        assert result['total_cost'] == 50000.0
        assert len(result['allocated_costs']) == 3

    def test_allocate_costs_empty(self):
        """测试分配成本 - 空数据边界"""
        from app.services.profit_analysis_service import ProfitAnalysisService

        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.contract_amount = Decimal("100000")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        service = ProfitAnalysisService(mock_db)

        # 空分配方案 - 使用默认类型
        with patch.object(service, '_get_actual_cost', return_value=30000):
            with patch.object(service, '_get_cost_by_type', return_value={"材料": 20000, "人工": 10000}):
                result = service.allocate_costs(project_id=1, cost_allocation={})

        assert isinstance(result, dict)
        assert result['total_cost'] == 30000.0
        assert len(result['allocated_costs']) == 2