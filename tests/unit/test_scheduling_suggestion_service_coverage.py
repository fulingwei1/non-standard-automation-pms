# -*- coding: utf-8 -*-
"""scheduling_suggestion_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.scheduling_suggestion_service import SchedulingSuggestionService

class TestSchedulingSuggestionServiceInit:
    def test_init(self):
        service = SchedulingSuggestionService(Mock())
        assert service is not None
