# -*- coding: utf-8 -*-
"""technical_assessment_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.technical_assessment_service import TechnicalAssessmentService

class TestTechnicalAssessmentServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = TechnicalAssessmentService(mock_db)
        assert hasattr(service, 'db')
