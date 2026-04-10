# -*- coding: utf-8 -*-
"""comparison_analyzer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_review_ai.comparison_analyzer import ProjectComparisonAnalyzer

class TestProjectComparisonAnalyzerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectComparisonAnalyzer(mock_db)
        assert hasattr(service, 'db')
