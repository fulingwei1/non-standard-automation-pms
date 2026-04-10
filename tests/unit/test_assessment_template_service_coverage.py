# -*- coding: utf-8 -*-
"""assessment_template_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.assessment_template_service import AssessmentTemplateService

class TestAssessmentTemplateServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = AssessmentTemplateService(mock_db)
        assert hasattr(service, 'db')
