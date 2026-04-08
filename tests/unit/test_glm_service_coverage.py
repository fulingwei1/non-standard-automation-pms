# -*- coding: utf-8 -*-
"""glm_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_planning.glm_service import GLMService

class TestGLMServiceInit:
    def test_init(self):
        service = GLMService(Mock())
        assert service is not None
