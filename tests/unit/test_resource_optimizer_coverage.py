# -*- coding: utf-8 -*-
"""resource_optimizer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_planning.resource_optimizer import AIResourceOptimizer

class TestAIResourceOptimizerInit:
    def test_init(self):
        service = AIResourceOptimizer(Mock())
        assert service is not None
