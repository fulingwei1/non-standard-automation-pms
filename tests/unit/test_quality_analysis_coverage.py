# -*- coding: utf-8 -*-
"""quality_analysis单元测试"""
import pytest
from unittest.mock import Mock
from services/procurement_analysis/quality_analysis import QualityAnalyzer

class TestQualityAnalyzerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = QualityAnalyzer(mock_db)
        assert hasattr(service, 'db')
