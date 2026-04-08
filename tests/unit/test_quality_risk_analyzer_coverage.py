# -*- coding: utf-8 -*-
"""quality_risk_analyzer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.quality_risk_ai.quality_risk_analyzer import QualityRiskAnalyzer

class TestQualityRiskAnalyzerInit:
    def test_init(self):
        service = QualityRiskAnalyzer(Mock())
        assert service is not None
