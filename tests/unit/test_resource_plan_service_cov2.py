# -*- coding: utf-8 -*-
"""
resource_plan_service.py 单元测试（第二批）
"""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


# ─── 1. calculate_fill_rate ──────────────────────────────────────────────────
def test_fill_rate_empty():
    from app.services.resource_plan_service import ResourcePlanService
    assert ResourcePlanService.calculate_fill_rate([]) == 100.0


def test_fill_rate_all_assigned():
    from app.services.resource_plan_service import ResourcePlanService

    r1 = MagicMock()
    r1.headcount = 2
    r1.assignment_status = "ASSIGNED"

    r2 = MagicMock()
    r2.headcount = 1
    r2.assignment_status = "ASSIGNED"

    assert ResourcePlanService.calculate_fill_rate([r1, r2]) == 100.0


def test_fill_rate_partial():
    from app.services.resource_plan_service import ResourcePlanService

    r1 = MagicMock()
    r1.headcount = 4
    r1.assignment_status = "ASSIGNED"

    r2 = MagicMock()
    r2.headcount = 6
    r2.assignment_status = "PENDING"

    # 4/10 * 100 = 40%
    assert ResourcePlanService.calculate_fill_rate([r1, r2]) == 40.0


def test_fill_rate_zero_headcount():
    from app.services.resource_plan_service import ResourcePlanService

    r = MagicMock()
    r.headcount = 0
    r.assignment_status = "ASSIGNED"

    assert ResourcePlanService.calculate_fill_rate([r]) == 100.0


# ─── 2. calculate_date_overlap ───────────────────────────────────────────────
def test_date_overlap_exists():
    from app.services.resource_plan_service import ResourcePlanService

    overlap = ResourcePlanService.calculate_date_overlap(
        date(2024, 1, 1), date(2024, 1, 31),
        date(2024, 1, 15), date(2024, 2, 15)
    )
    assert overlap == (date(2024, 1, 15), date(2024, 1, 31))


def test_date_overlap_no_overlap():
    from app.services.resource_plan_service import ResourcePlanService

    overlap = ResourcePlanService.calculate_date_overlap(
        date(2024, 1, 1), date(2024, 1, 31),
        date(2024, 2, 1), date(2024, 2, 28)
    )
    assert overlap is None


def test_date_overlap_missing_dates():
    from app.services.resource_plan_service import ResourcePlanService

    overlap = ResourcePlanService.calculate_date_overlap(None, date(2024, 1, 31), date(2024, 1, 1), None)
    assert overlap is None


def test_date_overlap_adjacent():
    from app.services.resource_plan_service import ResourcePlanService

    # 紧邻（同一天结束/开始）
    overlap = ResourcePlanService.calculate_date_overlap(
        date(2024, 1, 1), date(2024, 1, 15),
        date(2024, 1, 15), date(2024, 1, 31)
    )
    assert overlap == (date(2024, 1, 15), date(2024, 1, 15))


# ─── 3. calculate_conflict_severity ─────────────────────────────────────────
def test_conflict_severity_high():
    from app.services.resource_plan_service import ResourcePlanService
    assert ResourcePlanService.calculate_conflict_severity(Decimal("150")) == "HIGH"


def test_conflict_severity_medium():
    from app.services.resource_plan_service import ResourcePlanService
    assert ResourcePlanService.calculate_conflict_severity(Decimal("125")) == "MEDIUM"


def test_conflict_severity_low():
    from app.services.resource_plan_service import ResourcePlanService
    assert ResourcePlanService.calculate_conflict_severity(Decimal("110")) == "LOW"


# ─── 4. release_employee ─────────────────────────────────────────────────────
def test_release_employee_not_found():
    from app.services.resource_plan_service import ResourcePlanService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="资源计划不存在"):
        ResourcePlanService.release_employee(mock_db, 999)


def test_release_employee_success():
    from app.services.resource_plan_service import ResourcePlanService

    mock_plan = MagicMock()
    mock_plan.assigned_employee_id = 1
    mock_plan.assignment_status = "ASSIGNED"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_plan

    result = ResourcePlanService.release_employee(mock_db, 1)
    assert mock_plan.assigned_employee_id is None
    assert mock_plan.assignment_status == "RELEASED"
    mock_db.commit.assert_called_once()


# ─── 5. ResourcePlanningService._calculate_work_days ────────────────────────
def test_calculate_work_days():
    from app.services.resource_plan_service import ResourcePlanningService

    mock_db = MagicMock()
    svc = ResourcePlanningService(mock_db)

    # 2024-01-08 (Mon) to 2024-01-12 (Fri) = 5 work days
    work_days = svc._calculate_work_days(date(2024, 1, 8), date(2024, 1, 12))
    assert work_days == 5


def test_calculate_work_days_includes_weekend():
    from app.services.resource_plan_service import ResourcePlanningService

    mock_db = MagicMock()
    svc = ResourcePlanningService(mock_db)

    # Mon ~ Sun (7 days), 5 work days
    work_days = svc._calculate_work_days(date(2024, 1, 8), date(2024, 1, 14))
    assert work_days == 5


def test_calculate_work_days_single_day():
    from app.services.resource_plan_service import ResourcePlanningService

    mock_db = MagicMock()
    svc = ResourcePlanningService(mock_db)

    # 2024-01-08 Monday
    work_days = svc._calculate_work_days(date(2024, 1, 8), date(2024, 1, 8))
    assert work_days == 1
