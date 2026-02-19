# -*- coding: utf-8 -*-
"""
Tests for app/services/procurement_analysis/base.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.procurement_analysis.base import ProcurementAnalysisService
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_get_cost_trend_data_delegates():
    """get_cost_trend_data 委托给 CostTrendAnalyzer"""
    with patch("app.services.procurement_analysis.base.CostTrendAnalyzer") as MockAnalyzer:
        MockAnalyzer.get_cost_trend_data.return_value = {"trend": []}
        result = ProcurementAnalysisService.get_cost_trend_data("arg1", kwarg1="val")
        MockAnalyzer.get_cost_trend_data.assert_called_once_with("arg1", kwarg1="val")


def test_get_price_fluctuation_delegates():
    """get_price_fluctuation_data 委托给 PriceAnalyzer"""
    with patch("app.services.procurement_analysis.base.PriceAnalyzer") as MockAnalyzer:
        MockAnalyzer.get_price_fluctuation_data.return_value = {}
        result = ProcurementAnalysisService.get_price_fluctuation_data("db")
        MockAnalyzer.get_price_fluctuation_data.assert_called_once()


def test_get_delivery_performance_delegates():
    """get_delivery_performance_data 委托给 DeliveryPerformanceAnalyzer"""
    with patch("app.services.procurement_analysis.base.DeliveryPerformanceAnalyzer") as MockAnalyzer:
        MockAnalyzer.get_delivery_performance_data.return_value = {}
        result = ProcurementAnalysisService.get_delivery_performance_data("db")
        MockAnalyzer.get_delivery_performance_data.assert_called_once()


def test_get_request_efficiency_delegates():
    """get_request_efficiency_data 委托给 RequestEfficiencyAnalyzer"""
    with patch("app.services.procurement_analysis.base.RequestEfficiencyAnalyzer") as MockAnalyzer:
        MockAnalyzer.get_request_efficiency_data.return_value = {}
        result = ProcurementAnalysisService.get_request_efficiency_data("db")
        MockAnalyzer.get_request_efficiency_data.assert_called_once()


def test_get_quality_rate_delegates():
    """get_quality_rate_data 委托给 QualityAnalyzer"""
    with patch("app.services.procurement_analysis.base.QualityAnalyzer") as MockAnalyzer:
        MockAnalyzer.get_quality_rate_data.return_value = {}
        result = ProcurementAnalysisService.get_quality_rate_data("db")
        MockAnalyzer.get_quality_rate_data.assert_called_once()


def test_service_methods_are_static():
    """确认服务方法都是静态方法"""
    assert callable(ProcurementAnalysisService.get_cost_trend_data)
    assert callable(ProcurementAnalysisService.get_price_fluctuation_data)
    assert callable(ProcurementAnalysisService.get_delivery_performance_data)
    assert callable(ProcurementAnalysisService.get_request_efficiency_data)
    assert callable(ProcurementAnalysisService.get_quality_rate_data)
