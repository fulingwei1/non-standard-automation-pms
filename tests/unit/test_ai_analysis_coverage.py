# -*- coding: utf-8 -*-
"""ai_analysis单元测试"""
import pytest
from unittest.mock import Mock
from app.services.work_log_ai.ai_analysis import AIAnalysisMixin

class TestAIAnalysisMixinInit:
    def test_init(self):
        service = AIAnalysisMixin(Mock())
        assert service is not None
