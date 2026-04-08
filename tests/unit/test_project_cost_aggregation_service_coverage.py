# -*- coding: utf-8 -*-
"""project_cost_aggregation_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.project_cost_aggregation_service import ProjectCostAggregationService

class TestProjectCostAggregationServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ProjectCostAggregationService(mock_db)
        assert hasattr(service, 'db')
