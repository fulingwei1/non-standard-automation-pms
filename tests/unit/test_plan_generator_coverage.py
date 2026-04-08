# -*- coding: utf-8 -*-
"""plan_generator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_planning.plan_generator import AIProjectPlanGenerator

class TestAIProjectPlanGeneratorInit:
    def test_init(self):
        service = AIProjectPlanGenerator(Mock())
        assert service is not None
