# -*- coding: utf-8 -*-
"""project_statistics_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_statistics_service import ProjectStatistics

class TestProjectStatisticsInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectStatistics(mock_db)
        assert hasattr(service, 'db')
