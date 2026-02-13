# -*- coding: utf-8 -*-
"""交付分析器别名单元测试"""
import pytest
from app.services.procurement_analysis.delivery_analyzer import DeliveryPerformanceAnalyzer


class TestDeliveryAnalyzerAlias:
    def test_import(self):
        assert DeliveryPerformanceAnalyzer is not None
