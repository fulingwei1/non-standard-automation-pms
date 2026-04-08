# -*- coding: utf-8 -*-
"""presale_ai_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.presale.presale_ai_service import PresaleAIService

class TestPresaleAIServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PresaleAIService(mock_db)
        assert hasattr(service, 'db')
