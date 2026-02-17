# -*- coding: utf-8 -*-
"""
N1组深度覆盖: LaborCostService / LaborCostCalculationService / LaborCostExpenseService
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.labor_cost_service import (
    LaborCostService,
    LaborCostCalculationService,
    LaborCostExpenseService,
)


# ============================================================
# Helper builders
# ============================================================

def _make_project(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.project_code = kwargs.get("project_code", "PRJ001")
    p.project_name = kwargs.get("project_name", "测试项目")
    p.outcome = kwargs.get("outcome", "LOST")
    p.loss_reason = kwargs.get("loss_reason", "价格")
    p.salesperson_id = kwargs.get("salesperson_id", 10)
    p.source_lead_id = kwargs.get("source_lead_id", None)
    p.opportunity_id = kwargs.get("opportunity_id", None)
    p.stage = kwargs.get("stage", "S1")
    p.created_at = kwargs.get("created_at", MagicMock())
    p.updated_at = kwargs.get("updated_at", MagicMock())
    p.updated_at.date.return_value = date(2025, 1, 15)
    return p


def _make_user(**kwargs):
    u = MagicMock()
    u.id = kwargs.get("id", 1)
    u.real_name = kwargs.get("real_name", "张三")
    u.username = kwargs.get("username", "zhangsan")
    u.department = kwargs.get("department", "工程部")
    return u


def _make_timesheet(**kwargs):
    ts = MagicMock()
    ts.id = kwargs.get("id", 1)
    ts.user_id = kwargs.get("user_id", 1)
    ts.project_id = kwargs.get("project_id", 1)
    ts.hours = kwargs.get("hours", 8)
    ts.work_date = kwargs.get("work_date", date(2025, 1, 10))
    ts.status = kwargs.get("status", "APPROVED")
    ts.department_id = kwargs.get("department_id", None)
    ts.department_name = kwargs.get("department_name", "工程部")
    return ts


# ============================================================
# 1. LaborCostService.calculate_all_projects_labor_cost
# ============================================================

class TestCalculateAllProjectsLaborCost:
    def test_no_projects_returns_success(self):
        """没有项目时返回空结果"""
        db = MagicMock()
        # 模拟 query Timesheet.project_id distinct
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = LaborCostService.calculate_all_projects_labor_cost(db)
        assert result["success"] is True
        assert result["total_projects"] == 0
        assert result["success_count"] == 0

    def test_with_project_ids_filter(self):
        """传入 project_ids 时只处理指定项目"""
        db = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = LaborCostService.calculate_all_projects_labor_cost(
            db, project_ids=[1, 2, 3]
        )
        assert result["total_projects"] == 0

    def test_error_counted_as_fail(self):
        """某项目计算失败时 fail_count 增加"""
        db = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [(1,)]

        with patch.object(
            LaborCostService,
            "calculate_project_labor_cost",
            side_effect=Exception("DB错误")
        ):
            result = LaborCostService.calculate_all_projects_labor_cost(db)

        assert result["fail_count"] == 1
        assert result["success_count"] == 0


# ============================================================
# 2. LaborCostService.calculate_monthly_labor_cost
# ============================================================

class TestCalculateMonthlyLaborCost:
    def test_monthly_delegates_to_all_projects(self):
        """月度计算实际调用 calculate_all_projects_labor_cost"""
        db = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        result = LaborCostService.calculate_monthly_labor_cost(db, year=2025, month=1)
        assert result["success"] is True


# ============================================================
# 3. LaborCostCalculationService.calculate_monthly_costs
# ============================================================

class TestLaborCostCalculationService:
    def _make_service(self):
        db = MagicMock()
        svc = LaborCostCalculationService(db)
        return svc, db

    def test_no_projects_returns_zero(self):
        """没有工时记录的项目时返回0"""
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        result = svc.calculate_monthly_costs(2025, 1)
        assert result["projects_processed"] == 0
        assert result["total_cost"] == 0.0

    def test_skips_none_project_id(self):
        """project_id 为 None 时跳过"""
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [(None,)]

        result = svc.calculate_monthly_costs(2025, 1)
        assert result["projects_processed"] == 0


# ============================================================
# 4. LaborCostExpenseService - identify_lost_projects
# ============================================================

class TestIdentifyLostProjects:
    def _make_svc(self, projects):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = projects
        db.query.return_value.filter.return_value.scalar.return_value = 0

        with patch("app.services.labor_cost_service.HourlyRateService"):
            svc = LaborCostExpenseService(db)
        # 覆盖内部方法
        svc._has_detailed_design = MagicMock(return_value=False)
        svc._get_project_hours = MagicMock(return_value=0.0)
        svc._calculate_project_cost = MagicMock(return_value=Decimal("0"))
        return svc, db

    def test_returns_list_of_dicts(self):
        p = _make_project()
        svc, db = self._make_svc([p])
        result = svc.identify_lost_projects()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["project_id"] == p.id

    def test_include_abandoned_true(self):
        """include_abandoned=True 时包含 ABANDONED 项目"""
        p = _make_project(outcome="ABANDONED")
        svc, db = self._make_svc([p])
        result = svc.identify_lost_projects(include_abandoned=True)
        assert len(result) == 1

    def test_include_abandoned_false(self):
        """include_abandoned=False 时通过查询条件排除"""
        with patch("app.services.labor_cost_service.HourlyRateService"):
            db = MagicMock()
            db.query.return_value.filter.return_value.all.return_value = []
            svc = LaborCostExpenseService(db)
            svc._has_detailed_design = MagicMock(return_value=False)
            svc._get_project_hours = MagicMock(return_value=0.0)
            svc._calculate_project_cost = MagicMock(return_value=Decimal("0"))

            result = svc.identify_lost_projects(include_abandoned=False)
            assert result == []


# ============================================================
# 5. LaborCostExpenseService - _has_detailed_design
# ============================================================

class TestHasDetailedDesign:
    def _make_svc(self):
        db = MagicMock()
        with patch("app.services.labor_cost_service.HourlyRateService"):
            svc = LaborCostExpenseService(db)
        svc._get_project_hours = MagicMock(return_value=0.0)
        return svc, db

    def test_stage_s4_is_detailed(self):
        """S4 及以后阶段认为已进入详细设计"""
        svc, db = self._make_svc()
        p = _make_project(stage="S4")
        result = svc._has_detailed_design(p)
        assert result is True

    def test_stage_s2_not_detailed(self):
        """S2 阶段未进入详细设计"""
        svc, db = self._make_svc()
        p = _make_project(stage="S2")
        svc._get_project_hours = MagicMock(return_value=0.0)
        result = svc._has_detailed_design(p)
        assert result is False

    def test_high_hours_triggers_detailed(self):
        """工时 > 80 时认为已进入详细设计"""
        svc, db = self._make_svc()
        p = _make_project(stage="S1")
        svc._get_project_hours = MagicMock(return_value=100.0)
        result = svc._has_detailed_design(p)
        assert result is True

    def test_invalid_stage_falls_back_to_hours(self):
        """无效阶段时回退到工时判断"""
        svc, db = self._make_svc()
        p = _make_project(stage="INVALID")
        svc._get_project_hours = MagicMock(return_value=50.0)
        result = svc._has_detailed_design(p)
        assert result is False

    def test_no_stage_falls_back_to_hours(self):
        """没有阶段字段时回退到工时判断"""
        svc, db = self._make_svc()
        p = _make_project()
        p.stage = None
        svc._get_project_hours = MagicMock(return_value=0.0)
        result = svc._has_detailed_design(p)
        assert result is False


# ============================================================
# 6. LaborCostExpenseService - _get_project_hours
# ============================================================

class TestGetProjectHours:
    def test_returns_float(self):
        with patch("app.services.labor_cost_service.HourlyRateService"):
            db = MagicMock()
            db.query.return_value.filter.return_value.scalar.return_value = 40
            svc = LaborCostExpenseService(db)
        result = svc._get_project_hours(1)
        assert result == 40.0

    def test_none_returns_zero(self):
        with patch("app.services.labor_cost_service.HourlyRateService"):
            db = MagicMock()
            db.query.return_value.filter.return_value.scalar.return_value = None
            svc = LaborCostExpenseService(db)
        result = svc._get_project_hours(1)
        assert result == 0.0


# ============================================================
# 7. LaborCostExpenseService - _get_user_name
# ============================================================

class TestGetUserName:
    def _make_svc(self):
        db = MagicMock()
        with patch("app.services.labor_cost_service.HourlyRateService"):
            svc = LaborCostExpenseService(db)
        return svc, db

    def test_returns_real_name(self):
        svc, db = self._make_svc()
        user = _make_user(real_name="李四")
        db.query.return_value.filter.return_value.first.return_value = user
        assert svc._get_user_name(1) == "李四"

    def test_returns_username_when_no_real_name(self):
        svc, db = self._make_svc()
        user = _make_user(real_name=None, username="lisi")
        db.query.return_value.filter.return_value.first.return_value = user
        assert svc._get_user_name(1) == "lisi"

    def test_none_user_id_returns_none(self):
        svc, db = self._make_svc()
        assert svc._get_user_name(None) is None

    def test_user_not_found_returns_none(self):
        svc, db = self._make_svc()
        db.query.return_value.filter.return_value.first.return_value = None
        assert svc._get_user_name(999) is None


# ============================================================
# 8. LaborCostExpenseService - get_expense_statistics (group_by分支)
# ============================================================

class TestGetExpenseStatistics:
    def _make_svc_with_expenses(self, expenses):
        db = MagicMock()
        with patch("app.services.labor_cost_service.HourlyRateService"):
            svc = LaborCostExpenseService(db)
        # Mock get_lost_project_expenses
        svc.get_lost_project_expenses = MagicMock(return_value={
            "expenses": expenses,
            "total_amount": sum(e["amount"] for e in expenses),
            "total_hours": sum(e["labor_hours"] for e in expenses),
            "total_expenses": len(expenses),
        })
        return svc, db

    def test_statistics_by_person(self):
        expenses = [
            {
                "project_id": 1,
                "project_code": "P001",
                "project_name": "proj",
                "expense_category": "LOST_BID",
                "amount": 1000.0,
                "labor_hours": 10.0,
                "expense_date": date(2025, 1, 1),
                "salesperson_id": 1,
                "salesperson_name": "张三",
                "loss_reason": "价格"
            }
        ]
        svc, db = self._make_svc_with_expenses(expenses)
        user = _make_user(id=1, real_name="张三")
        db.query.return_value.filter.return_value.first.return_value = user

        result = svc.get_expense_statistics(group_by="person")
        assert result["group_by"] == "person"
        assert "statistics" in result
        assert "summary" in result

    def test_statistics_by_time(self):
        expenses = [
            {
                "project_id": 1,
                "project_code": "P001",
                "project_name": "proj",
                "expense_category": "LOST_BID",
                "amount": 500.0,
                "labor_hours": 5.0,
                "expense_date": date(2025, 1, 1),
                "salesperson_id": 1,
                "salesperson_name": "张三",
                "loss_reason": "价格"
            }
        ]
        svc, db = self._make_svc_with_expenses(expenses)
        result = svc.get_expense_statistics(group_by="time")
        assert result["group_by"] == "time"
        assert len(result["statistics"]) == 1
        assert result["statistics"][0]["month"] == "2025-01"

    def test_statistics_by_department(self):
        expenses = [
            {
                "project_id": 1,
                "project_code": "P001",
                "project_name": "proj",
                "expense_category": "LOST_BID",
                "amount": 800.0,
                "labor_hours": 8.0,
                "expense_date": date(2025, 1, 1),
                "salesperson_id": 1,
                "salesperson_name": "张三",
                "loss_reason": "价格"
            }
        ]
        svc, db = self._make_svc_with_expenses(expenses)
        ts = _make_timesheet(department_id=100, department_name="工程部")
        db.query.return_value.filter.return_value.all.return_value = [ts]
        db.query.return_value.filter.return_value.first.return_value = None  # no dept record

        result = svc.get_expense_statistics(group_by="department")
        assert result["group_by"] == "department"


# ============================================================
# 9. LaborCostExpenseService.get_lost_project_expenses - filters
# ============================================================

class TestGetLostProjectExpenses:
    def _make_svc(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        with patch("app.services.labor_cost_service.HourlyRateService"):
            svc = LaborCostExpenseService(db)
        svc._get_project_hours = MagicMock(return_value=0.0)
        svc._calculate_project_cost = MagicMock(return_value=Decimal("0"))
        svc._get_user_name = MagicMock(return_value="张三")
        return svc, db

    def test_empty_returns_zero(self):
        svc, db = self._make_svc()
        result = svc.get_lost_project_expenses()
        assert result["total_expenses"] == 0
        assert result["total_amount"] == 0

    def test_with_salesperson_filter(self):
        svc, db = self._make_svc()
        result = svc.get_lost_project_expenses(salesperson_id=5)
        assert result["total_expenses"] == 0
