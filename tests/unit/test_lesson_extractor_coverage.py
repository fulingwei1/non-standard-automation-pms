# -*- coding: utf-8 -*-
"""lesson_extractor单元测试"""
import pytest
from unittest.mock import Mock
from services/project_review_ai/lesson_extractor import ProjectLessonExtractor

class TestProjectLessonExtractorInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectLessonExtractor(mock_db)
        assert hasattr(service, 'db')
