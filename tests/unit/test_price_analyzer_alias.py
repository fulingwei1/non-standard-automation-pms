# -*- coding: utf-8 -*-
"""价格分析器别名单元测试"""
import pytest
from app.services.procurement_analysis.price_analyzer import PriceAnalyzer


class TestPriceAnalyzerAlias:
    def test_import(self):
        assert PriceAnalyzer is not None
