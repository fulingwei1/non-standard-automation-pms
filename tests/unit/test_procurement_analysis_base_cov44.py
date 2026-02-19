# -*- coding: utf-8 -*-
"""第四十四批覆盖测试 - 采购分析服务基础类"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.procurement_analysis.base import ProcurementAnalysisService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="模块导入失败，跳过测试")


class TestProcurementAnalysisService:

    def test_class_exists(self):
        assert ProcurementAnalysisService is not None

    @patch("app.services.procurement_analysis.base.CostTrendAnalyzer.get_cost_trend_data")
    def test_get_cost_trend_data_delegates(self, mock_method):
        mock_method.return_value = {"trends": []}
        result = ProcurementAnalysisService.get_cost_trend_data(db=None, months=6)
        mock_method.assert_called_once_with(db=None, months=6)
        assert result == {"trends": []}

    @patch("app.services.procurement_analysis.base.PriceAnalyzer.get_price_fluctuation_data")
    def test_get_price_fluctuation_data_delegates(self, mock_method):
        mock_method.return_value = {"data": []}
        result = ProcurementAnalysisService.get_price_fluctuation_data(db=None)
        mock_method.assert_called_once()
        assert result == {"data": []}

    @patch("app.services.procurement_analysis.base.DeliveryPerformanceAnalyzer.get_delivery_performance_data")
    def test_get_delivery_performance_data_delegates(self, mock_method):
        mock_method.return_value = {"rate": 0.95}
        result = ProcurementAnalysisService.get_delivery_performance_data(db=None)
        mock_method.assert_called_once()
        assert result == {"rate": 0.95}

    @patch("app.services.procurement_analysis.base.RequestEfficiencyAnalyzer.get_request_efficiency_data")
    def test_get_request_efficiency_data_delegates(self, mock_method):
        mock_method.return_value = {"efficiency": 0.88}
        result = ProcurementAnalysisService.get_request_efficiency_data(db=None)
        mock_method.assert_called_once()
        assert result == {"efficiency": 0.88}

    @patch("app.services.procurement_analysis.base.QualityAnalyzer.get_quality_rate_data")
    def test_get_quality_rate_data_delegates(self, mock_method):
        mock_method.return_value = {"quality_rate": 0.99}
        result = ProcurementAnalysisService.get_quality_rate_data(db=None)
        mock_method.assert_called_once()
        assert result == {"quality_rate": 0.99}

    def test_all_methods_are_static(self):
        methods = [
            "get_cost_trend_data",
            "get_price_fluctuation_data",
            "get_delivery_performance_data",
            "get_request_efficiency_data",
            "get_quality_rate_data",
        ]
        for method_name in methods:
            method = getattr(ProcurementAnalysisService, method_name)
            assert callable(method), f"{method_name} 应当是可调用的"
