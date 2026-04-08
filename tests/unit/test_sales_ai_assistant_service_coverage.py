# -*- coding: utf-8 -*-
"""sales_ai_assistant_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales_ai_assistant_service import SalesAIAssistantService

class TestSalesAIAssistantServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SalesAIAssistantService(mock_db)
        assert hasattr(service, 'db')
