# -*- coding: utf-8 -*-
"""
Unit tests for CostAnalysisService (第三十批)
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services.cost_analysis_service import CostAnalysisService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return CostAnalysisService(db=mock_db)


# ---------------------------------------------------------------------------
# predict_project_cost
# ---------------------------------------------------------------------------

class TestPredictProjectCost:
    def test_returns_error_when_project_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.predict_project_cost(project_id=999)
        assert "error" in result

    def test_returns_cost_prediction_with_no_timesheets(self, service, mock_db):
        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "测试项目"
        project.budget_amount = 100000
        project.actual_cost = 10000

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            inner = MagicMock()
            if call_count[0] == 1:
                # Project query
                inner.filter.return_value.first.return_value = project
            elif call_count[0] == 2:
                # Timesheet query
                inner.filter.return_value.filter.return_value.all.return_value = []
            else:
                # Task query
                inner.filter.return_value.filter.return_value.all.return_value = []
            return inner

        mock_db.query.side_effect = query_side_effect

        result = service.predict_project_cost(project_id=1)
        assert result["project_id"] == 1
        assert result["budget"] == 100000
        assert "predicted_total_cost" in result

    def test_is_over_budget_flag(self, service, mock_db):
        project = MagicMock()
        project.id = 2
        project.project_code = "P002"
        project.project_name = "超支项目"
        project.budget_amount = 5000
        project.actual_cost = 8000  # Over budget

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            inner = MagicMock()
            if call_count[0] == 1:
                inner.filter.return_value.first.return_value = project
            else:
                inner.filter.return_value.filter.return_value.all.return_value = []
            return inner

        mock_db.query.side_effect = query_side_effect

        result = service.predict_project_cost(project_id=2)
        assert result["is_over_budget"] is True


# ---------------------------------------------------------------------------
# check_cost_overrun_alerts
# ---------------------------------------------------------------------------

class TestCheckCostOverrunAlerts:
    def test_returns_empty_when_no_projects(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        result = service.check_cost_overrun_alerts()
        assert result == []

    def test_skips_project_without_budget(self, service, mock_db):
        project = MagicMock()
        project.budget_amount = 0
        project.actual_cost = 500

        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [project]

        result = service.check_cost_overrun_alerts()
        assert result == []

    def test_generates_warning_alert(self, service, mock_db):
        project = MagicMock()
        project.id = 3
        project.project_code = "P003"
        project.project_name = "预警项目"
        project.budget_amount = 10000
        project.actual_cost = 8500  # 85% - warning threshold

        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [project]

        with patch.object(service, "predict_project_cost") as mock_predict:
            mock_predict.return_value = {"predicted_total_cost": 9000}
            result = service.check_cost_overrun_alerts()

        assert len(result) == 1
        assert result[0]["alert_level"] == "WARNING"

    def test_generates_critical_alert(self, service, mock_db):
        project = MagicMock()
        project.id = 4
        project.project_code = "P004"
        project.project_name = "严重超支项目"
        project.budget_amount = 10000
        project.actual_cost = 12000  # 120% - critical threshold

        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [project]

        with patch.object(service, "predict_project_cost") as mock_predict:
            mock_predict.return_value = {"predicted_total_cost": 14000}
            result = service.check_cost_overrun_alerts()

        assert len(result) == 1
        assert result[0]["alert_level"] == "CRITICAL"

    def test_skips_projects_below_threshold(self, service, mock_db):
        project = MagicMock()
        project.budget_amount = 10000
        project.actual_cost = 5000  # only 50%

        mock_query = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [project]

        result = service.check_cost_overrun_alerts()
        assert result == []


# ---------------------------------------------------------------------------
# compare_project_costs
# ---------------------------------------------------------------------------

class TestCompareProjectCosts:
    def test_returns_error_when_no_projects_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.compare_project_costs([999, 1000])
        assert "error" in result

    def test_returns_comparison_data(self, service, mock_db):
        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "项目1"
        project.budget_amount = 10000
        project.actual_cost = 6000
        project.start_date = None
        project.end_date = None

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            inner = MagicMock()
            if call_count[0] == 1:
                # Projects query
                inner.filter.return_value.all.return_value = [project]
            else:
                # Timesheet query
                inner.filter.return_value.filter.return_value.all.return_value = []
            return inner

        mock_db.query.side_effect = query_side_effect

        result = service.compare_project_costs([1])
        assert "error" not in result
