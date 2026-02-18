# -*- coding: utf-8 -*-
"""
第十四批：预算分析服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, call, patch

try:
    from app.services.budget_analysis_service import BudgetAnalysisService
    from app.models.project import Project, ProjectCost
    from app.models.budget import ProjectBudget
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def build_db(project=None, budget=None, costs=None):
    """构建能区分不同 model 查询的 mock db"""
    db = MagicMock()
    costs = costs or []

    def query_side_effect(model):
        q = MagicMock()
        if model is Project:
            q.filter.return_value.first.return_value = project
        elif model is ProjectBudget:
            q.filter.return_value.order_by.return_value.first.return_value = budget
        elif model is ProjectCost:
            q.filter.return_value.all.return_value = costs
        return q

    db.query.side_effect = query_side_effect
    return db


def make_project(**kwargs):
    p = MagicMock(spec=Project)
    p.id = 1
    p.budget_amount = kwargs.get("budget_amount", 100000)
    p.actual_cost = kwargs.get("actual_cost", None)
    return p


class TestBudgetAnalysisService:
    def test_project_not_found_raises(self):
        db = build_db(project=None)
        with pytest.raises(ValueError, match="项目不存在"):
            BudgetAnalysisService.get_budget_execution_analysis(db, 999)

    def test_no_budget_uses_project_budget_amount(self):
        project = make_project(budget_amount=100000, actual_cost=None)
        db = build_db(project=project, budget=None, costs=[])
        result = BudgetAnalysisService.get_budget_execution_analysis(db, 1)
        assert result["budget_amount"] == 100000.0
        assert result["actual_cost"] == 0.0
        assert result["execution_rate"] == 0.0

    def test_with_budget_record(self):
        project = make_project(budget_amount=100000, actual_cost=80000)
        budget = MagicMock()
        budget.total_amount = 120000
        budget.items = []
        db = build_db(project=project, budget=budget, costs=[])
        result = BudgetAnalysisService.get_budget_execution_analysis(db, 1)
        assert result["budget_amount"] == 120000.0
        assert result["actual_cost"] == 80000.0

    def test_variance_calculation_over_budget(self):
        project = make_project(budget_amount=100000, actual_cost=120000)
        db = build_db(project=project, budget=None, costs=[])
        result = BudgetAnalysisService.get_budget_execution_analysis(db, 1)
        assert result["variance"] == 20000.0
        assert result["variance_pct"] > 0

    def test_execution_rate_calculation(self):
        project = make_project(budget_amount=100000, actual_cost=50000)
        db = build_db(project=project, budget=None, costs=[])
        result = BudgetAnalysisService.get_budget_execution_analysis(db, 1)
        assert result["execution_rate"] == pytest.approx(50.0, abs=0.01)
        assert result["remaining_budget"] == pytest.approx(50000.0, abs=0.01)

    def test_with_cost_records(self):
        project = make_project(budget_amount=100000)
        project.actual_cost = None
        cost1 = MagicMock()
        cost1.amount = 30000
        cost1.cost_category = "人工"
        cost2 = MagicMock()
        cost2.amount = 20000
        cost2.cost_category = "材料"
        db = build_db(project=project, budget=None, costs=[cost1, cost2])
        result = BudgetAnalysisService.get_budget_execution_analysis(db, 1)
        assert result["actual_cost"] == 50000.0
