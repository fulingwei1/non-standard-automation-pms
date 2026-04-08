# -*- coding: utf-8 -*-
"""wbs_decomposer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_planning.wbs_decomposer import AIWbsDecomposer

class TestAIWbsDecomposerInit:
    def test_init(self):
        service = AIWbsDecomposer(Mock())
        assert service is not None
