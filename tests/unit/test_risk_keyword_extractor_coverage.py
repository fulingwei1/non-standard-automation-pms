# -*- coding: utf-8 -*-
"""risk_keyword_extractor单元测试"""
import pytest
from unittest.mock import Mock
from app.services.quality_risk_ai.risk_keyword_extractor import RiskKeywordExtractor

class TestRiskKeywordExtractorInit:
    def test_init(self):
        service = RiskKeywordExtractor(Mock())
        assert service is not None
