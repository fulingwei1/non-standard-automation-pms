# -*- coding: utf-8 -*-
"""ai_predictor单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_cost_prediction.ai_predictor import GLM5CostPredictor

class TestGLM5CostPredictorInit:
    def test_init(self):
        service = GLM5CostPredictor(Mock())
        assert service is not None
