# -*- coding: utf-8 -*-
"""confidence_scorer单元测试"""
import pytest
from unittest.mock import Mock
from app.services.sales.cost.confidence_scorer import ConfidenceScorer

class TestConfidenceScorerInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ConfidenceScorer(mock_db)
        assert hasattr(service, 'db')
