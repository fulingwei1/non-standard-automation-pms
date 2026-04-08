# -*- coding: utf-8 -*-
"""ai_assessment_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.ai_assessment_service import AIAssessmentService

class TestAIAssessmentServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AIAssessmentService(mock_db)
        assert hasattr(service, 'db')
