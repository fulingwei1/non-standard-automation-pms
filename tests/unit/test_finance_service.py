# -*- coding: utf-8 -*-
"""Tests for project/finance_service.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestProjectFinanceService:
    @patch('app.services.project.finance_service.DataScopeService')
    def test_no_accessible_projects(self, mock_scope):
        from app.services.project.finance_service import ProjectFinanceService
        db = MagicMock()
        mock_scope.filter_projects_by_scope.return_value.all.return_value = []
        svc = ProjectFinanceService(db)
        user = MagicMock()
        result = svc.get_cost_summary(user)
        assert result['projects'] == 0
        assert result['total_cost'] == 0.0

    @patch('app.services.project.finance_service.DataScopeService')
    def test_with_projects(self, mock_scope):
        from app.services.project.finance_service import ProjectFinanceService
        db = MagicMock()
        mock_scope.filter_projects_by_scope.return_value.all.return_value = [(1,), (2,)]
        # Mock cost query
        cost_query = db.query.return_value.filter.return_value
        cost_query.with_entities.return_value.scalar.return_value = 5000
        cost_query.with_entities.return_value.group_by.return_value.all.return_value = [('MATERIAL', 3000), ('LABOR', 2000)]
        cost_query.with_entities.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [(1, 3000)]
        # Mock project query
        project = MagicMock(id=1, project_code='P001', project_name='Test', budget_amount=10000)
        db.query.return_value.filter.return_value.all.return_value = [project]
        svc = ProjectFinanceService(db)
        user = MagicMock()
        result = svc.get_cost_summary(user)
        assert result['projects'] == 2
