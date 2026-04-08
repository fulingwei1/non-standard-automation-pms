# -*- coding: utf-8 -*-
"""cost_prediction_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.cost.cost_prediction_service import GLM5CostPredictor

class TestGLM5CostPredictorInit:
    def test_init(self):
        service = GLM5CostPredictor(Mock())
        assert service is not None
