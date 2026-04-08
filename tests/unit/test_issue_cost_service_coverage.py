# -*- coding: utf-8 -*-
"""issue_cost_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.issue_cost_service import IssueCostService

class TestIssueCostServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = IssueCostService(mock_db)
        assert hasattr(service, 'db')
