# -*- coding: utf-8 -*-
"""template_recommendation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.template_recommendation_service import TemplateRecommendationService

class TestTemplateRecommendationServiceInit:
    def test_init(self):
        service = TemplateRecommendationService(Mock())
        assert service is not None
