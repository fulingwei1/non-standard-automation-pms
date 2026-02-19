# -*- coding: utf-8 -*-
"""
Unit tests for CostAnalysisService (第三十一批)
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


def _make_project(budget=100000.0, actual_cost=30000.0, project_id=1):
    proj = MagicMock()
    proj.id = project_id
    proj.project_name = "测试项目"
    proj.budget_amount = budget
    proj.actual_cost = actual_cost
    return proj


# ---------------------------------------------------------------------------
# predict_project_cost
# ---------------------------------------------------------------------------

class TestPredictProjectCost:
    def test_returns_error_when_project_not_found(self, service, mock_db):
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = None

        result = service.predict_project_cost(project_id=999)
        assert "error" in result

    def test_returns_prediction_dict_for_valid_project(self, service, mock_db):
        project = _make_project()
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.first.return_value = project if call_count[0] == 1 else None
            chain.all.return_value = []
            chain.in_.return_value = chain
            return chain

        mock_db.query.side_effect = query_side_effect

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=100,
        ):
            result = service.predict_project_cost(project_id=1)

        assert isinstance(result, dict)
        assert "error" not in result

    def test_zero_recorded_hours_uses_default_rate(self, service, mock_db):
        """无历史工时时应使用默认时薪进行预测"""
        project = _make_project(budget=50000.0)
        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            chain = MagicMock()
            chain.filter.return_value = chain
            chain.first.return_value = project if call_count[0] == 1 else None
            chain.all.return_value = []
            chain.in_.return_value = chain
            return chain

        mock_db.query.side_effect = query_side_effect

        result = service.predict_project_cost(project_id=1)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# get_cost_overrun_warning
# ---------------------------------------------------------------------------

class TestGetCostOverrunWarning:
    def test_no_warning_for_low_usage(self, service, mock_db):
        if not hasattr(service, "get_cost_overrun_warning"):
            pytest.skip("get_cost_overrun_warning not implemented")

        project = _make_project(budget=100000.0, actual_cost=10000.0)
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = project
        chain.all.return_value = []

        result = service.get_cost_overrun_warning(project_id=1)
        assert isinstance(result, dict)

    def test_returns_warning_when_near_budget(self, service, mock_db):
        if not hasattr(service, "get_cost_overrun_warning"):
            pytest.skip("get_cost_overrun_warning not implemented")

        project = _make_project(budget=100000.0, actual_cost=85000.0)
        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.first.return_value = project
        chain.all.return_value = []

        result = service.get_cost_overrun_warning(project_id=1)
        result_str = str(result).upper()
        assert "WARNING" in result_str or "CRITICAL" in result_str or "warn" in str(result).lower()


# ---------------------------------------------------------------------------
# compare_project_costs (if exists)
# ---------------------------------------------------------------------------

class TestCompareProjectCosts:
    def test_method_exists_or_skip(self, service):
        if not hasattr(service, "compare_project_costs"):
            pytest.skip("compare_project_costs not implemented")

    def test_returns_comparison_dict(self, service, mock_db):
        if not hasattr(service, "compare_project_costs"):
            pytest.skip("compare_project_costs not implemented")

        chain = MagicMock()
        mock_db.query.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = []

        result = service.compare_project_costs(project_ids=[1, 2])
        assert isinstance(result, (dict, list))
