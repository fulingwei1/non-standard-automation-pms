# -*- coding: utf-8 -*-
"""效率分析器别名单元测试"""
import pytest
from app.services.procurement_analysis.efficiency_analyzer import RequestEfficiencyAnalyzer


class TestEfficiencyAnalyzerAlias:
    def test_import(self):
        assert RequestEfficiencyAnalyzer is not None
