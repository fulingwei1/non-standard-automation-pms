# -*- coding: utf-8 -*-
"""
labor_cost_service.py 单元测试（第二批）
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


# ─── 1. LaborCostService.calculate_project_labor_cost - 项目不存在 ───────────
def test_calculate_project_labor_cost_project_not_found():
    from app.services.labor_cost_service import LaborCostService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = LaborCostService.calculate_project_labor_cost(mock_db, 999)
    assert result["success"] is False
    assert "项目不存在" in result["message"]


def test_calculate_project_labor_cost_no_timesheets():
    from app.services.labor_cost_service import LaborCostService

    mock_db = MagicMock()
    mock_project = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project

    with patch("app.services.labor_cost.utils.query_approved_timesheets", return_value=[]) as mock_q:
        # The function imports from labor_cost.utils inside, patch the utils module
        import app.services.labor_cost.utils as utils_mod
        original = utils_mod.query_approved_timesheets
        utils_mod.query_approved_timesheets = lambda *a, **kw: []
        try:
            result = LaborCostService.calculate_project_labor_cost(mock_db, 1)
        finally:
            utils_mod.query_approved_timesheets = original

    assert result["success"] is True
    assert result["cost_count"] == 0


def test_calculate_project_labor_cost_with_timesheets():
    from app.services.labor_cost_service import LaborCostService
    import app.services.labor_cost.utils as utils_mod

    mock_db = MagicMock()
    mock_project = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_project

    fake_timesheets = [MagicMock()]
    fake_user_costs = {1: {"total_hours": Decimal("10"), "user_id": 1}}
    fake_costs = [MagicMock()]
    fake_total_cost = Decimal("1000")

    orig_q = utils_mod.query_approved_timesheets
    orig_g = utils_mod.group_timesheets_by_user
    orig_p = utils_mod.process_user_costs
    utils_mod.query_approved_timesheets = lambda *a, **kw: fake_timesheets
    utils_mod.group_timesheets_by_user = lambda *a, **kw: fake_user_costs
    utils_mod.process_user_costs = lambda *a, **kw: (fake_costs, fake_total_cost)
    try:
        result = LaborCostService.calculate_project_labor_cost(mock_db, 1)
    finally:
        utils_mod.query_approved_timesheets = orig_q
        utils_mod.group_timesheets_by_user = orig_g
        utils_mod.process_user_costs = orig_p

    assert result["success"] is True
    assert result["cost_count"] == 1
    assert result["total_cost"] == 1000.0


# ─── 2. LaborCostService.calculate_all_projects_labor_cost ──────────────────
def test_calculate_all_projects_no_projects():
    from app.services.labor_cost_service import LaborCostService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

    result = LaborCostService.calculate_all_projects_labor_cost(mock_db)
    assert result["success"] is True
    assert result["total_projects"] == 0


def test_calculate_all_projects_with_filter():
    from app.services.labor_cost_service import LaborCostService

    mock_db = MagicMock()
    # Return two project IDs
    mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [(1,), (2,)]

    with patch.object(LaborCostService, "calculate_project_labor_cost",
                      return_value={"success": True, "message": "ok", "cost_count": 1}):
        result = LaborCostService.calculate_all_projects_labor_cost(mock_db)

    assert result["total_projects"] == 2
    assert result["success_count"] == 2


# ─── 3. LaborCostCalculationService.calculate_monthly_costs ─────────────────
def test_calculate_monthly_costs_basic():
    from app.services.labor_cost_service import LaborCostCalculationService

    mock_db = MagicMock()
    # No projects with timesheets in that month
    mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

    with patch("app.services.labor_cost_service.get_month_range_by_ym",
               return_value=(date(2024, 1, 1), date(2024, 1, 31))):
        svc = LaborCostCalculationService(mock_db)
        result = svc.calculate_monthly_costs(2024, 1)

    assert result["year"] == 2024
    assert result["month"] == 1
    assert result["projects_processed"] == 0


# ─── 4. LaborCostExpenseService.identify_lost_projects ──────────────────────
def _make_expense_service(mock_db):
    """辅助函数：创建 LaborCostExpenseService，绕过 HourlyRateService 导入"""
    from app.services.labor_cost_service import LaborCostExpenseService
    with patch("app.services.hourly_rate_service.HourlyRateService", MagicMock()):
        svc = LaborCostExpenseService.__new__(LaborCostExpenseService)
        svc.db = mock_db
        svc.hourly_rate_service = MagicMock()
        return svc


def test_identify_lost_projects_empty():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []
    svc = _make_expense_service(mock_db)
    result = svc.identify_lost_projects()
    assert result == []


# ─── 5. LaborCostExpenseService._has_detailed_design ────────────────────────
def test_has_detailed_design_by_stage():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.scalar.return_value = 10.0
    svc = _make_expense_service(mock_db)

    project = MagicMock()
    project.stage = "S4"
    project.id = 1
    assert svc._has_detailed_design(project) is True


def test_has_detailed_design_by_hours():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.scalar.return_value = 90.0
    svc = _make_expense_service(mock_db)

    project = MagicMock()
    project.stage = None
    project.id = 1
    assert svc._has_detailed_design(project) is True


def test_has_detailed_design_false():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.scalar.return_value = 20.0
    svc = _make_expense_service(mock_db)

    project = MagicMock()
    project.stage = "S1"
    project.id = 1
    assert svc._has_detailed_design(project) is False


# ─── 6. LaborCostExpenseService._get_project_hours ───────────────────────────
def test_get_project_hours():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.scalar.return_value = 42.5
    svc = _make_expense_service(mock_db)
    result = svc._get_project_hours(1)
    assert result == 42.5


def test_get_project_hours_none():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.scalar.return_value = None
    svc = _make_expense_service(mock_db)
    result = svc._get_project_hours(1)
    assert result == 0.0
