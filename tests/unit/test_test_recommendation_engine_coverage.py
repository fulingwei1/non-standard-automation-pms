# -*- coding: utf-8 -*-
"""test_recommendation_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.quality_risk_ai.test_recommendation_engine import TestRecommendationEngine

class TestTestRecommendationEngineInit:
    def test_init(self):
        service = TestRecommendationEngine(Mock())
        assert service is not None
