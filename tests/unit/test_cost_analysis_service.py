# -*- coding: utf-8 -*-
"""Tests for cost_analysis_service.py"""
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date

from app.services.cost_analysis_service import CostAnalysisService


class TestPredictProjectCost:
    def setup_method(self):
        self.db = MagicMock()
        self.service = CostAnalysisService(self.db)

    def test_project_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.predict_project_cost(1)
        assert result == {'error': '项目不存在'}

    @patch("app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate", return_value=100)
    def test_basic_prediction(self, mock_rate):
        project = MagicMock(id=1, project_code="P001", project_name="测试",
                            budget_amount=100000, actual_cost=30000)
        self.db.query.return_value.filter.return_value.first.return_value = project

        ts = MagicMock(user_id=1, hours=10, work_date=date(2025, 1, 1))
        self.db.query.return_value.filter.return_value.all.return_value = [ts]

        task = MagicMock(estimated_hours=20)
        # Second .all() call for tasks
        self.db.query.return_value.filter.return_value.all.side_effect = [[ts], [task]]

        result = self.service.predict_project_cost(1)
        assert 'predicted_total_cost' in result
        assert result['project_id'] == 1


class TestCheckCostOverrunAlerts:
    def setup_method(self):
        self.db = MagicMock()
        self.service = CostAnalysisService(self.db)

    def test_no_budget(self):
        project = MagicMock(budget_amount=0, is_active=True)
        self.db.query.return_value.filter.return_value.all.return_value = [project]
        result = self.service.check_cost_overrun_alerts()
        assert result == []

    @patch.object(CostAnalysisService, 'predict_project_cost', return_value={'predicted_total_cost': 120000})
    def test_critical_alert(self, mock_predict):
        project = MagicMock(id=1, project_code="P001", project_name="测试",
                            budget_amount=100000, actual_cost=110000, is_active=True)
        self.db.query.return_value.filter.return_value.all.return_value = [project]
        result = self.service.check_cost_overrun_alerts()
        assert len(result) == 1
        assert result[0]['alert_level'] == 'CRITICAL'


class TestCompareProjectCosts:
    def setup_method(self):
        self.db = MagicMock()
        self.service = CostAnalysisService(self.db)

    def test_no_projects(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.service.compare_project_costs([1, 2])
        assert result == {'error': '项目不存在'}

    @patch("app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate", return_value=100)
    def test_basic_comparison(self, mock_rate):
        p1 = MagicMock(id=1, project_code="P001", project_name="A", budget_amount=100000, actual_cost=50000)
        self.db.query.return_value.filter.return_value.all.side_effect = [
            [p1],  # projects
            [MagicMock(user_id=1, hours=10, work_date=date(2025, 1, 1))],  # timesheets for p1
        ]
        result = self.service.compare_project_costs([1])
        assert 'projects' in result
