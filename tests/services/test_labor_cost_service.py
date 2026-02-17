# -*- coding: utf-8 -*-
"""工时成本服务单元测试 (LaborCostService)"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


def _make_db():
    return MagicMock()


def _make_project(**kw):
    p = MagicMock()
    defaults = dict(
        id=1,
        project_name="比亚迪ADAS ICT测试系统",
        project_code="BYD-2024-001",
        salesperson_id=10,
        source_lead_id=None,
        opportunity_id=None,
        outcome="LOST",
        loss_reason="价格偏高",
        created_at=date(2024, 1, 1),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


class TestLaborCostServiceInit:
    def test_init_sets_db(self):
        from app.services.labor_cost_service import LaborCostService
        db = _make_db()
        svc = LaborCostService(db)
        assert svc.db is db

    def test_default_hourly_rate_exists(self):
        from app.services.labor_cost_service import LaborCostService
        assert LaborCostService.DEFAULT_HOURLY_RATE == Decimal("100")


class TestCalculateProjectLaborCost:
    def test_project_not_found_returns_failure(self):
        from app.services.labor_cost_service import LaborCostService
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = LaborCostService.calculate_project_labor_cost(db, project_id=999)
        assert result["success"] is False
        assert "项目不存在" in result["message"]

    def test_no_approved_timesheets_returns_success_zero_cost(self):
        from app.services.labor_cost_service import LaborCostService
        db = _make_db()
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project

        with patch('app.services.labor_cost_service.LaborCostService.calculate_project_labor_cost') as mock_calc:
            # Directly test the logic by patching inner utils
            pass

        # Test through the actual function with mocked utils
        with patch('app.services.labor_cost.utils.query_approved_timesheets', return_value=[]) as mock_query, \
             patch('app.services.labor_cost.utils.group_timesheets_by_user', return_value={}) as mock_group, \
             patch('app.services.labor_cost.utils.delete_existing_costs') as mock_delete, \
             patch('app.services.labor_cost.utils.process_user_costs', return_value=([], Decimal("0"))) as mock_process:
            result = LaborCostService.calculate_project_labor_cost(db, project_id=1)
            # 无工时记录时应返回 cost_count=0
            assert result["success"] is True
            assert result["cost_count"] == 0

    def test_with_timesheets_returns_cost_result(self):
        from app.services.labor_cost_service import LaborCostService
        db = _make_db()
        project = _make_project()
        db.query.return_value.filter.return_value.first.return_value = project

        mock_timesheet = MagicMock()
        mock_timesheet.user_id = 1
        mock_timesheet.hours = Decimal("8")
        mock_timesheet.work_date = date(2024, 1, 15)

        with patch('app.services.labor_cost.utils.query_approved_timesheets', return_value=[mock_timesheet]), \
             patch('app.services.labor_cost.utils.group_timesheets_by_user', return_value={
                 1: {"total_hours": Decimal("8"), "timesheets": [mock_timesheet]}
             }), \
             patch('app.services.labor_cost.utils.delete_existing_costs'), \
             patch('app.services.labor_cost.utils.process_user_costs', return_value=(
                 [MagicMock()], Decimal("800")
             )):
            result = LaborCostService.calculate_project_labor_cost(db, project_id=1)
            assert result["success"] is True
            assert result["cost_count"] == 1
            assert result["total_cost"] == 800.0


class TestCalculateAllProjectsLaborCost:
    def test_no_timesheets_returns_empty_results(self):
        from app.services.labor_cost_service import LaborCostService
        db = _make_db()
        # query returns empty list of project ids
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = LaborCostService.calculate_all_projects_labor_cost(db)
        assert result["success"] is True
        assert result["total_projects"] == 0
        assert result["success_count"] == 0


class TestCalculateMonthlyLaborCost:
    def test_delegates_to_all_projects(self):
        from app.services.labor_cost_service import LaborCostService
        db = _make_db()
        with patch.object(LaborCostService, 'calculate_all_projects_labor_cost') as mock_all:
            mock_all.return_value = {"success": True, "total_projects": 0}
            result = LaborCostService.calculate_monthly_labor_cost(db, year=2024, month=1)
            mock_all.assert_called_once()
            assert result["success"] is True


class TestLaborCostExpenseServiceIdentifyLostProjects:
    def test_identify_lost_projects_no_outcome_filter(self):
        from app.services.labor_cost_service import LaborCostExpenseService
        db = _make_db()
        project = _make_project(id=1, outcome="LOST")
        db.query.return_value.filter.return_value.all.return_value = [project]

        svc = LaborCostExpenseService(db)
        svc._has_detailed_design = MagicMock(return_value=False)
        svc._get_project_hours = MagicMock(return_value=40.0)
        svc._calculate_project_cost = MagicMock(return_value=Decimal("4000"))

        result = svc.identify_lost_projects()
        assert len(result) == 1
        assert result[0]["project_id"] == 1
        assert result[0]["total_hours"] == 40.0

    def test_identify_lost_projects_empty(self):
        from app.services.labor_cost_service import LaborCostExpenseService
        db = _make_db()
        db.query.return_value.filter.return_value.all.return_value = []

        svc = LaborCostExpenseService(db)
        result = svc.identify_lost_projects()
        assert result == []
