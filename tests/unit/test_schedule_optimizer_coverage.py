# -*- coding: utf-8 -*-
"""schedule_optimizer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

class TestAIScheduleOptimizerInit:
    def test_init(self):
        service = AIScheduleOptimizer(Mock())
        assert service is not None
