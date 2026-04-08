# -*- coding: utf-8 -*-
"""budget_analysis_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.budget_analysis_service import BudgetAnalysisService

class TestBudgetAnalysisServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = BudgetAnalysisService(mock_db)
        assert hasattr(service, 'db')
