# -*- coding: utf-8 -*-
"""issue_statistics_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.issue_statistics_service import IssueStatistics

class TestIssueStatisticsInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = IssueStatistics(mock_db)
        assert hasattr(service, 'db')
