# -*- coding: utf-8 -*-
"""quality_analysis单元测试"""
from app.services.procurement_analysis.quality_analysis import QualityAnalyzer


class TestQualityAnalyzerInit:
    def test_init_with_db(self):
        assert callable(QualityAnalyzer.get_quality_rate_data)
