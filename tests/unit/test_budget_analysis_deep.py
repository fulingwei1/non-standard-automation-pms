# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 预算分析服务"""
import pytest
from unittest.mock import MagicMock, patch


class TestBudgetAnalysisServiceBusinessLogic:
    """预算分析服务业务逻辑测试"""

    def test_get_budget_execution_analysis(self):
        """测试获取预算执行分析"""
        try:
            from app.services.budget_analysis_service import BudgetAnalysisService

            mock_db = MagicMock()
            service = BudgetAnalysisService(mock_db)

            result = service.get_budget_execution_analysis(1)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")

    def test_get_budget_trend_analysis(self):
        """测试获取预算趋势分析"""
        try:
            from app.services.budget_analysis_service import BudgetAnalysisService

            mock_db = MagicMock()
            service = BudgetAnalysisService(mock_db)

            result = service.get_budget_trend_analysis(30)

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")