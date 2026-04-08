# -*- coding: utf-8 -*-
"""ai_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_service import AIService

class TestAIServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AIService(mock_db)
        assert hasattr(service, 'db')
