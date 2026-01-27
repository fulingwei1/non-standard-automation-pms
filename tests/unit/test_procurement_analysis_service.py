# -*- coding: utf-8 -*-
"""
采购分析服务单元测试

测试覆盖:
- CostTrendAnalyzer: 成本趋势分析
- PriceAnalyzer: 价格分析
- DeliveryPerformanceAnalyzer: 交付绩效分析
- RequestEfficiencyAnalyzer: 请求效率分析
- QualityAnalyzer: 质量分析
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestPriceAnalyzer:
    """测试价格分析器"""

    def test_import_analyzer(self):
        """测试导入分析器"""
        from app.services.procurement_analysis.price_analyzer import PriceAnalyzer
        assert PriceAnalyzer is not None

    def test_get_price_fluctuation_data_empty(self, db_session):
        """测试获取价格波动数据 - 空数据"""
        from app.services.procurement_analysis.price_analyzer import PriceAnalyzer

        analyzer = PriceAnalyzer(db_session)
        result = analyzer.get_price_fluctuation_data(
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )

        assert isinstance(result, (list, dict))

    def test_get_price_fluctuation_data_with_material(self, db_session):
        """测试获取价格波动数据 - 指定物料"""
        from app.services.procurement_analysis.price_analyzer import PriceAnalyzer

        analyzer = PriceAnalyzer(db_session)
        result = analyzer.get_price_fluctuation_data(
            material_id=1,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )

        assert isinstance(result, (list, dict))

    def test_get_price_fluctuation_data_with_supplier(self, db_session):
        """测试获取价格波动数据 - 指定供应商"""
        from app.services.procurement_analysis.price_analyzer import PriceAnalyzer

        analyzer = PriceAnalyzer(db_session)
        result = analyzer.get_price_fluctuation_data(
            supplier_id=1,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )

        assert isinstance(result, (list, dict))


class TestCostTrendAnalyzer:
    """测试成本趋势分析器"""

    def test_import_analyzer(self):
        """测试导入分析器"""
        from app.services.procurement_analysis.cost_trend_analyzer import CostTrendAnalyzer
        assert CostTrendAnalyzer is not None


class TestDeliveryPerformanceAnalyzer:
    """测试交付绩效分析器"""

    def test_import_analyzer(self):
        """测试导入分析器"""
        from app.services.procurement_analysis.delivery_analyzer import DeliveryPerformanceAnalyzer
        assert DeliveryPerformanceAnalyzer is not None


class TestRequestEfficiencyAnalyzer:
    """测试请求效率分析器"""

    def test_import_analyzer(self):
        """测试导入分析器"""
        from app.services.procurement_analysis.efficiency_analyzer import RequestEfficiencyAnalyzer
        assert RequestEfficiencyAnalyzer is not None


class TestQualityAnalyzer:
    """测试质量分析器"""

    def test_import_analyzer(self):
        """测试导入分析器"""
        from app.services.procurement_analysis.quality_analyzer import QualityAnalyzer
        assert QualityAnalyzer is not None


class TestProcurementAnalysisModule:
    """测试采购分析模块"""

    def test_import_all_analyzers(self):
        """测试导入所有分析器"""
        from app.services.procurement_analysis import (
            CostTrendAnalyzer,
            PriceAnalyzer,
            DeliveryPerformanceAnalyzer,
            RequestEfficiencyAnalyzer,
            QualityAnalyzer,
        )

        assert CostTrendAnalyzer is not None
        assert PriceAnalyzer is not None
        assert DeliveryPerformanceAnalyzer is not None
        assert RequestEfficiencyAnalyzer is not None
        assert QualityAnalyzer is not None
