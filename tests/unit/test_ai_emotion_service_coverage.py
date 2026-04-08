# -*- coding: utf-8 -*-
"""ai_emotion_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_emotion_service import AIEmotionService

class TestAIEmotionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AIEmotionService(mock_db)
        assert hasattr(service, 'db')
