# -*- coding: utf-8 -*-
"""request_efficiency单元测试"""
import pytest
from unittest.mock import Mock
from services/procurement_analysis/request_efficiency import RequestEfficiencyAnalyzer

class TestRequestEfficiencyAnalyzerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = RequestEfficiencyAnalyzer(mock_db)
        assert hasattr(service, 'db')
