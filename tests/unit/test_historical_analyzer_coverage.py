# -*- coding: utf-8 -*-
"""historical_analyzer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.cost.historical_analyzer import HistoricalAnalyzer

class TestHistoricalAnalyzerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = HistoricalAnalyzer(mock_db)
        assert hasattr(service, 'db')
