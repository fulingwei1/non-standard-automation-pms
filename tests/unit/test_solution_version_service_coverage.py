# -*- coding: utf-8 -*-
"""solution_version_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.solution_version_service import SolutionVersionService

class TestSolutionVersionServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = SolutionVersionService(mock_db)
        assert hasattr(service, 'db')
