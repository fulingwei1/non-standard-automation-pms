# -*- coding: utf-8 -*-
"""performance_feedback_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.performance_feedback_service import PerformanceFeedbackService

class TestPerformanceFeedbackServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PerformanceFeedbackService(mock_db)
        assert hasattr(service, 'db')
