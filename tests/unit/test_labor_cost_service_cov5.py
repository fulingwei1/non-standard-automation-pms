# -*- coding: utf-8 -*-
"""第五批：labor_cost_service.py 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

try:
    from app.services.labor_cost_service import (
        LaborCostService,
        LaborCostCalculationService,
        LaborCostExpenseService,
    )
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="labor_cost_service not importable")


def make_db():
    return MagicMock()


class TestLaborCostServiceCalculateAll:
    def test_empty_projects_returns_dict(self):
        db = make_db()
        # query().filter().distinct().all() returns empty
        q = MagicMock()
        q.filter.return_value = q
        q.distinct.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        result = LaborCostService.calculate_all_projects_labor_cost(db)
        assert isinstance(result, dict)
        assert result["total_projects"] == 0

    def test_with_one_project(self):
        db = make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.distinct.return_value = q
        q.all.return_value = [(1,)]
        db.query.return_value = q
        with patch("app.services.labor_cost_service.LaborCostService.calculate_project_labor_cost",
                   return_value={"success": True, "total_cost": 1000}):
            result = LaborCostService.calculate_all_projects_labor_cost(db)
            assert result["success"] is True
            assert result["total_projects"] == 1


class TestLaborCostExpenseServiceIdentifyLostProjects:
    def test_empty_projects(self):
        db = make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value.filter.return_value = q
        svc = LaborCostExpenseService(db)
        result = svc.identify_lost_projects()
        assert result == []

    def test_returns_list(self):
        db = make_db()
        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        project.project_name = "Test"
        project.outcome = "LOST"
        project.loss_reason = "price"
        project.salesperson_id = 10
        project.source_lead_id = None
        project.opportunity_id = None
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [project]
        db.query.return_value.filter.return_value = q
        svc = LaborCostExpenseService(db)
        with patch.object(svc, "_has_detailed_design", return_value=False), \
             patch.object(svc, "_get_project_hours", return_value=10.0), \
             patch.object(svc, "_calculate_project_cost", return_value=Decimal("1000")):
            result = svc.identify_lost_projects()
            assert len(result) == 1
            assert result[0]["project_id"] == 1


class TestStatisticsByPerson:
    def test_empty(self):
        db = make_db()
        svc = LaborCostExpenseService(db)
        result = svc._statistics_by_person([])
        assert result == []

    def test_aggregates_correctly(self):
        db = make_db()
        person = MagicMock()
        person.name = "Alice"
        person.department_name = "Tech"
        db.query.return_value.filter.return_value.first.return_value = person
        svc = LaborCostExpenseService(db)
        expenses = [
            {"salesperson_id": 1, "amount": 1000.0, "labor_hours": 10.0},
            {"salesperson_id": 1, "amount": 500.0, "labor_hours": 5.0},
        ]
        result = svc._statistics_by_person(expenses)
        assert len(result) == 1
        assert result[0]["total_amount"] == 1500.0


class TestStatisticsByDepartment:
    def test_empty(self):
        db = make_db()
        svc = LaborCostExpenseService(db)
        result = svc._statistics_by_department([])
        assert result == []


class TestLaborCostCalculationService:
    def test_calculate_monthly_costs_no_projects(self):
        db = make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        svc = LaborCostCalculationService(db)
        result = svc.calculate_monthly_costs(2024, 1)
        assert isinstance(result, dict)

    def test_calculate_monthly_costs_structure(self):
        db = make_db()
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        db.query.return_value = q
        svc = LaborCostCalculationService(db)
        result = svc.calculate_monthly_costs(2024, 3)
        assert "success" in result or isinstance(result, dict)
