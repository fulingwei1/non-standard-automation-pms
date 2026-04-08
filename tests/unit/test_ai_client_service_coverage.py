# -*- coding: utf-8 -*-
"""ai_client_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_client_service import AIClientService

class TestAIClientServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AIClientService(mock_db)
        assert hasattr(service, 'db')
