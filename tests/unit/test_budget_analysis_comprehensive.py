# -*- coding: utf-8 -*-
"""BudgetAnalysisService 综合测试"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock

import pytest

from app.services.budget_analysis_service import BudgetAnalysisService


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_project(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.project_code = kwargs.get("project_code", "P001")
    p.project_name = kwargs.get("project_name", "测试项目")
    p.budget_amount = kwargs.get("budget_amount", Decimal("100000"))
    p.actual_cost = kwargs.get("actual_cost", None)
    return p


def _make_budget(**kwargs):
    b = MagicMock()
    b.total_amount = kwargs.get("total_amount", Decimal("100000"))
    b.version = kwargs.get("version", 1)
    b.budget_no = kwargs.get("budget_no", "B001")
    b.items = kwargs.get("items", [])
    return b


def _make_cost(**kwargs):
    c = MagicMock()
    c.amount = kwargs.get("amount", Decimal("10000"))
    c.cost_category = kwargs.get("cost_category", "硬件")
    c.cost_date = kwargs.get("cost_date", date(2024, 3, 15))
    return c


class TestGetBudgetExecutionAnalysis:
    def test_project_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            BudgetAnalysisService.get_budget_execution_analysis(mock_db, 999)

    def test_no_budget_no_costs(self, mock_db):
        project = _make_project(budget_amount=Decimal("100000"), actual_cost=None)
        mock_db.query.return_value.filter.return_value.first.return_value = project
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)
        assert result["project_id"] == 1
        assert result["budget_amount"] == 100000.0
        assert result["actual_cost"] == 0.0
        assert result["warning_status"] == "正常"

    def test_with_budget_and_costs(self, mock_db):
        project = _make_project()
        budget = _make_budget(total_amount=Decimal("100000"))
        costs = [_make_cost(amount=Decimal("30000")), _make_cost(amount=Decimal("20000"))]
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = budget
            elif model.__name__ == "ProjectCost":
                q.filter.return_value.all.return_value = costs
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)
        assert result["actual_cost"] == 50000.0
        assert result["execution_rate"] == 50.0
        assert result["warning_status"] == "正常"

    def test_over_budget(self, mock_db):
        project = _make_project(actual_cost=Decimal("110000"))
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == "ProjectCost":
                q.filter.return_value.all.return_value = []
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)
        assert result["warning_status"] == "超支"
        assert result["execution_rate"] > 100

    def test_warning_90pct(self, mock_db):
        project = _make_project(actual_cost=Decimal("95000"))
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == "ProjectCost":
                q.filter.return_value.all.return_value = []
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)
        assert result["warning_status"] == "警告"

    def test_notice_80pct(self, mock_db):
        project = _make_project(actual_cost=Decimal("85000"))
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == "ProjectCost":
                q.filter.return_value.all.return_value = []
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)
        assert result["warning_status"] == "注意"

    def test_with_category_comparison(self, mock_db):
        project = _make_project()
        budget_item = MagicMock()
        budget_item.cost_category = "硬件"
        budget_item.budget_amount = 50000
        budget = _make_budget(items=[budget_item])
        cost = _make_cost(amount=Decimal("30000"), cost_category="硬件")
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = budget
            elif model.__name__ == "ProjectCost":
                q.filter.return_value.all.return_value = [cost]
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)
        assert len(result["category_comparison"]) >= 1

    def test_zero_budget(self, mock_db):
        project = _make_project(budget_amount=Decimal("0"), actual_cost=None)
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == "ProjectCost":
                q.filter.return_value.all.return_value = []
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_execution_analysis(mock_db, 1)
        assert result["execution_rate"] == 0


class TestGetBudgetTrendAnalysis:
    def test_project_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            BudgetAnalysisService.get_budget_trend_analysis(mock_db, 999)

    def test_no_costs(self, mock_db):
        project = _make_project()
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == "ProjectCost":
                q.filter.return_value.order_by.return_value.all.return_value = []
                q.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
                q.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, 1)
        assert result["project_id"] == 1
        assert result["monthly_trend"] == []

    def test_with_costs(self, mock_db):
        project = _make_project()
        budget = _make_budget()
        cost1 = _make_cost(amount=Decimal("10000"), cost_date=date(2024, 1, 15))
        cost2 = _make_cost(amount=Decimal("20000"), cost_date=date(2024, 2, 15))
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = budget
            elif model.__name__ == "ProjectCost":
                q.filter.return_value.order_by.return_value.all.return_value = [cost1, cost2]
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_trend_analysis(mock_db, 1)
        assert len(result["monthly_trend"]) == 2
        assert result["monthly_trend"][0]["month"] == "2024-01"
        assert result["total_actual_cost"] == 30000.0

    def test_with_date_filters(self, mock_db):
        project = _make_project()
        
        def query_side_effect(model):
            q = MagicMock()
            if model.__name__ == "Project":
                q.filter.return_value.first.return_value = project
            elif model.__name__ == "ProjectBudget":
                q.filter.return_value.order_by.return_value.first.return_value = None
            elif model.__name__ == "ProjectCost":
                inner_q = MagicMock()
                inner_q.filter.return_value = inner_q
                inner_q.order_by.return_value.all.return_value = []
                q.filter.return_value = inner_q
            return q
        
        mock_db.query.side_effect = query_side_effect
        result = BudgetAnalysisService.get_budget_trend_analysis(
            mock_db, 1, start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
        )
        assert isinstance(result, dict)
