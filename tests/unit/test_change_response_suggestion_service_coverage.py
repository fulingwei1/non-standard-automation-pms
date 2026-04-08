# -*- coding: utf-8 -*-
"""change_response_suggestion_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.change_response_suggestion_service import ChangeResponseSuggestionService

class TestChangeResponseSuggestionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ChangeResponseSuggestionService(mock_db)
        assert hasattr(service, 'db')
