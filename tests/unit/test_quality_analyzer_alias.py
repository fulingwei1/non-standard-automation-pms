# -*- coding: utf-8 -*-
"""质量分析器别名单元测试"""
import pytest
from app.services.procurement_analysis.quality_analyzer import QualityAnalyzer


class TestQualityAnalyzerAlias:
    def test_import(self):
        assert QualityAnalyzer is not None
