# -*- coding: utf-8 -*-
"""ai_prompt单元测试"""
import pytest
from unittest.mock import Mock
from app.services.work_log_ai.ai_prompt import AIPromptMixin

class TestAIPromptMixinInit:
    def test_init(self):
        service = AIPromptMixin(Mock())
        assert service is not None
