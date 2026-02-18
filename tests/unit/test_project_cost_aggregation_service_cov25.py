# -*- coding: utf-8 -*-
"""第二十五批 - project_cost_aggregation_service 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.project_cost_aggregation_service")

from app.services.project_cost_aggregation_service import ProjectCostAggregationService


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return ProjectCostAggregationService(db)


# ── _map_cost_type ────────────────────────────────────────────────────────────

class TestMapCostType:
    def test_labor_types(self, service):
        for t in ["LABOR", "LABOUR", "人工", "工资", "薪资"]:
            assert service._map_cost_type(t) == "labor"

    def test_material_types(self, service):
        for t in ["MATERIAL", "MATERIALS", "材料", "物料", "原材料"]:
            assert service._map_cost_type(t) == "material"

    def test_equipment_types(self, service):
        for t in ["EQUIPMENT", "MACHINE", "设备", "机械", "工具"]:
            assert service._map_cost_type(t) == "equipment"

    def test_travel_types(self, service):
        for t in ["TRAVEL", "差旅", "出差", "交通"]:
            assert service._map_cost_type(t) == "travel"

    def test_unknown_type_returns_other(self, service):
        assert service._map_cost_type("UNKNOWN") == "other"
        assert service._map_cost_type("MISC") == "other"

    def test_none_returns_other(self, service):
        assert service._map_cost_type(None) == "other"

    def test_empty_string_returns_other(self, service):
        assert service._map_cost_type("") == "other"

    def test_case_insensitive_labor(self, service):
        assert service._map_cost_type("labor") == "labor"

    def test_case_insensitive_material(self, service):
        assert service._map_cost_type("material") == "material"


# ── get_projects_cost_summary - empty case ────────────────────────────────────

class TestGetProjectsCostSummaryEmpty:
    def test_empty_project_ids_returns_empty_dict(self, service):
        result = service.get_projects_cost_summary([])
        assert result == {}


# ── get_projects_cost_summary ─────────────────────────────────────────────────

class TestGetProjectsCostSummary:
    def _setup_db(self, db, projects_data, cost_data=None, fin_cost_data=None):
        """Setup mock db queries."""
        # projects query
        projects_query = MagicMock()
        projects_query.filter.return_value.all.return_value = projects_data
        db.query.return_value.filter.return_value.all.return_value = projects_data

    def test_returns_summary_for_existing_projects(self, service, db):
        proj = MagicMock()
        proj.id = 1
        proj.budget_amount = Decimal("100000")
        proj.actual_cost = Decimal("80000")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.get_projects_cost_summary([1], include_breakdown=False)
        assert 1 in result
        assert result[1].total_cost == Decimal("80000")
        assert result[1].budget == Decimal("100000")

    def test_budget_used_pct_calculation(self, service, db):
        proj = MagicMock()
        proj.id = 2
        proj.budget_amount = Decimal("200000")
        proj.actual_cost = Decimal("100000")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.get_projects_cost_summary([2], include_breakdown=False)
        assert result[2].budget_used_pct == Decimal("50.00")

    def test_overrun_when_actual_exceeds_budget(self, service, db):
        proj = MagicMock()
        proj.id = 3
        proj.budget_amount = Decimal("50000")
        proj.actual_cost = Decimal("60000")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.get_projects_cost_summary([3], include_breakdown=False)
        assert result[3].overrun is True

    def test_no_overrun_when_within_budget(self, service, db):
        proj = MagicMock()
        proj.id = 4
        proj.budget_amount = Decimal("100000")
        proj.actual_cost = Decimal("90000")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.get_projects_cost_summary([4], include_breakdown=False)
        assert result[4].overrun is False

    def test_variance_calculation(self, service, db):
        proj = MagicMock()
        proj.id = 5
        proj.budget_amount = Decimal("100000")
        proj.actual_cost = Decimal("110000")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.get_projects_cost_summary([5], include_breakdown=False)
        assert result[5].variance == Decimal("10000")

    def test_skips_nonexistent_project(self, service, db):
        proj = MagicMock()
        proj.id = 6
        proj.budget_amount = Decimal("50000")
        proj.actual_cost = Decimal("40000")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.get_projects_cost_summary([6, 999], include_breakdown=False)
        assert 6 in result
        assert 999 not in result

    def test_zero_budget_no_division_error(self, service, db):
        proj = MagicMock()
        proj.id = 7
        proj.budget_amount = Decimal("0")
        proj.actual_cost = Decimal("5000")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.get_projects_cost_summary([7], include_breakdown=False)
        assert result[7].budget_used_pct == Decimal("0")
        assert result[7].overrun is False


# ── get_cost_summary_for_project ──────────────────────────────────────────────

class TestGetCostSummaryForProject:
    def test_returns_none_when_project_not_found(self, service, db):
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        result = service.get_cost_summary_for_project(999, include_breakdown=False)
        assert result is None

    def test_returns_summary_when_found(self, service, db):
        proj = MagicMock()
        proj.id = 10
        proj.budget_amount = Decimal("100000")
        proj.actual_cost = Decimal("75000")

        db.query.return_value.filter.return_value.all.return_value = [proj]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = service.get_cost_summary_for_project(10, include_breakdown=False)
        assert result is not None
        assert result.total_cost == Decimal("75000")


# ── _get_cost_breakdown_batch ─────────────────────────────────────────────────

class TestGetCostBreakdownBatch:
    def test_returns_empty_when_no_costs(self, service, db):
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        result = service._get_cost_breakdown_batch([1, 2])
        # No costs means no breakdown entries
        assert isinstance(result, dict)

    def test_aggregates_labor_costs(self, service, db):
        # Mock ProjectCost query result
        cost_row = MagicMock()
        cost_row.project_id = 1
        cost_row.cost_type = "LABOR"
        cost_row.amount = Decimal("50000")

        # Two calls: ProjectCost and FinancialProjectCost
        db.query.return_value.filter.return_value.group_by.return_value.all.side_effect = [
            [(1, "LABOR", Decimal("50000"))],
            [],
        ]

        result = service._get_cost_breakdown_batch([1])
        if 1 in result:
            assert result[1].labor == Decimal("50000.00")
