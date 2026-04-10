# -*- coding: utf-8 -*-
"""report_generator单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_review_ai.report_generator import ProjectReviewReportGenerator

class TestProjectReviewReportGeneratorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectReviewReportGenerator(mock_db)
        assert hasattr(service, 'db')
