# -*- coding: utf-8 -*-
"""
第十四批：预算执行检查服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services import budget_execution_check_service as becs
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_project(**kwargs):
    proj = MagicMock()
    proj.id = kwargs.get("id", 1)
    proj.project_code = "P-001"
    proj.project_name = "测试项目"
    proj.budget_amount = kwargs.get("budget_amount", 100000)
    proj.actual_cost = kwargs.get("actual_cost", None)
    return proj


class TestBudgetExecutionCheckService:
    def test_get_project_budget_from_budget_table(self):
        db = make_db()
        budget = MagicMock()
        budget.total_amount = 200000
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = budget
        project = make_project(budget_amount=100000)
        result = becs.get_project_budget(db, 1, project)
        assert result == 200000.0

    def test_get_project_budget_fallback_to_project(self):
        db = make_db()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        project = make_project(budget_amount=150000)
        result = becs.get_project_budget(db, 1, project)
        assert result == 150000.0

    def test_get_actual_cost_from_project(self):
        db = make_db()
        project = make_project(actual_cost=80000)
        result = becs.get_actual_cost(db, 1, project)
        assert result == 80000.0

    def test_get_actual_cost_from_costs(self):
        db = make_db()
        project = make_project(actual_cost=None)
        project.actual_cost = None
        cost1 = MagicMock()
        cost1.amount = 30000
        cost2 = MagicMock()
        cost2.amount = 20000
        db.query.return_value.filter.return_value.all.return_value = [cost1, cost2]
        result = becs.get_actual_cost(db, 1, project)
        assert result == 50000.0

    def test_determine_alert_level_urgent(self):
        level, title, content = becs.determine_alert_level(
            execution_rate=130.0,
            overrun_ratio=30.0,
            project_name="大项目",
            project_code="P-001",
            budget_amount=100000,
            actual_cost=130000
        )
        assert level is not None
        assert "超支" in (title or "")

    def test_determine_alert_level_warning(self):
        level, title, content = becs.determine_alert_level(
            execution_rate=107.0,
            overrun_ratio=7.0,
            project_name="测试项目",
            project_code="P-002",
            budget_amount=100000,
            actual_cost=107000
        )
        assert level is not None

    def test_get_or_create_alert_rule_existing(self):
        db = make_db()
        existing_rule = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing_rule
        rule = becs.get_or_create_alert_rule(db)
        assert rule is existing_rule
        db.add.assert_not_called()

    def test_get_or_create_alert_rule_creates_new(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        rule = becs.get_or_create_alert_rule(db)
        db.add.assert_called_once()
        db.flush.assert_called_once()
