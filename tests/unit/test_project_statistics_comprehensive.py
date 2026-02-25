# -*- coding: utf-8 -*-
"""project_statistics_service 综合测试"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.project_statistics_service import (
    calculate_status_statistics,
    calculate_stage_statistics,
    calculate_health_statistics,
    calculate_pm_statistics,
    calculate_customer_statistics,
    calculate_monthly_statistics,
    build_project_statistics,
    ProjectStatisticsServiceBase,
    CostStatisticsService,
    TimesheetStatisticsService,
    WorkLogStatisticsService,
)


def _make_project(**kwargs):
    p = MagicMock()
    p.status = kwargs.get("status")
    p.stage = kwargs.get("stage")
    p.health = kwargs.get("health")
    p.pm_id = kwargs.get("pm_id")
    p.pm_name = kwargs.get("pm_name")
    p.customer_id = kwargs.get("customer_id")
    p.customer_name = kwargs.get("customer_name")
    p.contract_amount = kwargs.get("contract_amount")
    p.progress_pct = kwargs.get("progress_pct", 50)
    p.created_at = kwargs.get("created_at")
    return p


class TestCalculateStatusStatistics:
    def test_empty(self):
        q = MagicMock()
        q.all.return_value = []
        assert calculate_status_statistics(q) == {}

    def test_single_status(self):
        q = MagicMock()
        q.all.return_value = [_make_project(status="进行中")]
        result = calculate_status_statistics(q)
        assert result["进行中"] == 1

    def test_multiple_statuses(self):
        q = MagicMock()
        q.all.return_value = [
            _make_project(status="进行中"),
            _make_project(status="进行中"),
            _make_project(status="已完成"),
        ]
        result = calculate_status_statistics(q)
        assert result["进行中"] == 2
        assert result["已完成"] == 1

    def test_none_status_ignored(self):
        q = MagicMock()
        q.all.return_value = [_make_project(status=None)]
        assert calculate_status_statistics(q) == {}


class TestCalculateStageStatistics:
    def test_empty(self):
        q = MagicMock()
        q.all.return_value = []
        assert calculate_stage_statistics(q) == {}

    def test_multiple_stages(self):
        q = MagicMock()
        q.all.return_value = [
            _make_project(stage="设计"),
            _make_project(stage="设计"),
            _make_project(stage="生产"),
        ]
        result = calculate_stage_statistics(q)
        assert result["设计"] == 2
        assert result["生产"] == 1

    def test_none_stage_ignored(self):
        q = MagicMock()
        q.all.return_value = [_make_project(stage=None)]
        assert calculate_stage_statistics(q) == {}


class TestCalculateHealthStatistics:
    def test_empty(self):
        q = MagicMock()
        q.all.return_value = []
        assert calculate_health_statistics(q) == {}

    def test_multiple(self):
        q = MagicMock()
        q.all.return_value = [
            _make_project(health="正常"),
            _make_project(health="预警"),
            _make_project(health="正常"),
        ]
        result = calculate_health_statistics(q)
        assert result["正常"] == 2
        assert result["预警"] == 1

    def test_none_ignored(self):
        q = MagicMock()
        q.all.return_value = [_make_project(health=None)]
        assert calculate_health_statistics(q) == {}


class TestCalculatePmStatistics:
    def test_empty(self):
        q = MagicMock()
        q.all.return_value = []
        assert calculate_pm_statistics(q) == []

    def test_single_pm(self):
        q = MagicMock()
        q.all.return_value = [
            _make_project(pm_id=1, pm_name="张三"),
            _make_project(pm_id=1, pm_name="张三"),
        ]
        result = calculate_pm_statistics(q)
        assert len(result) == 1
        assert result[0]["pm_name"] == "张三"
        assert result[0]["count"] == 2

    def test_no_pm_id(self):
        q = MagicMock()
        q.all.return_value = [_make_project(pm_id=None)]
        assert calculate_pm_statistics(q) == []

    def test_no_pm_name_defaults(self):
        q = MagicMock()
        q.all.return_value = [_make_project(pm_id=1, pm_name=None)]
        result = calculate_pm_statistics(q)
        assert result[0]["pm_name"] == "未知"


class TestCalculateCustomerStatistics:
    def test_empty(self):
        q = MagicMock()
        q.all.return_value = []
        assert calculate_customer_statistics(q) == []

    def test_with_customer(self):
        q = MagicMock()
        q.all.return_value = [
            _make_project(customer_id=1, customer_name="客户A", contract_amount=100000),
            _make_project(customer_id=1, customer_name="客户A", contract_amount=200000),
        ]
        result = calculate_customer_statistics(q)
        assert len(result) == 1
        assert result[0]["count"] == 2
        assert result[0]["total_amount"] == 300000.0

    def test_no_customer(self):
        q = MagicMock()
        q.all.return_value = [_make_project(customer_id=None, customer_name=None, contract_amount=None)]
        result = calculate_customer_statistics(q)
        assert len(result) == 1
        assert result[0]["customer_name"] == "未知客户"


class TestCalculateMonthlyStatistics:
    def test_empty(self):
        q = MagicMock()
        q.all.return_value = []
        q.filter.return_value = q
        assert calculate_monthly_statistics(q) == []

    def test_with_data(self):
        q = MagicMock()
        p1 = _make_project(contract_amount=100000, created_at=datetime(2024, 1, 15))
        p2 = _make_project(contract_amount=200000, created_at=datetime(2024, 1, 20))
        p3 = _make_project(contract_amount=150000, created_at=datetime(2024, 2, 10))
        q.all.return_value = [p1, p2, p3]
        q.filter.return_value = q
        result = calculate_monthly_statistics(q)
        assert len(result) == 2
        assert result[0]["month_label"] == "2024-01"
        assert result[0]["count"] == 2

    def test_no_created_at_ignored(self):
        q = MagicMock()
        q.all.return_value = [_make_project(created_at=None)]
        q.filter.return_value = q
        result = calculate_monthly_statistics(q)
        assert result == []

    def test_with_date_filters(self):
        q = MagicMock()
        q.all.return_value = []
        q.filter.return_value = q
        result = calculate_monthly_statistics(q, start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
        assert result == []


class TestBuildProjectStatistics:
    def test_empty(self):
        q = MagicMock()
        q.all.return_value = []
        result = build_project_statistics(None, q)
        assert result["total"] == 0
        assert result["average_progress"] == 0

    def test_with_projects(self):
        q = MagicMock()
        projects = [
            _make_project(progress_pct=60, status="进行中", stage="设计", health="正常", pm_id=1, pm_name="PM1"),
            _make_project(progress_pct=80, status="进行中", stage="生产", health="正常", pm_id=2, pm_name="PM2"),
        ]
        q.all.return_value = projects
        result = build_project_statistics(None, q)
        assert result["total"] == 2
        assert result["average_progress"] == 70

    def test_group_by_customer(self):
        q = MagicMock()
        q.all.return_value = [_make_project(progress_pct=50, customer_id=1, customer_name="C1", contract_amount=100)]
        result = build_project_statistics(None, q, group_by="customer")
        assert "by_customer" in result

    def test_group_by_month(self):
        q = MagicMock()
        q.all.return_value = []
        q.filter.return_value = q
        result = build_project_statistics(None, q, group_by="month")
        assert "by_month" in result


class TestCostStatisticsService:
    def test_get_model(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        model = svc.get_model()
        assert model is not None

    def test_get_project_id_field(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        assert svc.get_project_id_field() == "project_id"

    def test_get_summary(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        project = MagicMock()
        project.project_name = "测试项目"
        project.budget_amount = Decimal("100000")
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value.with_entities.return_value.scalar.return_value = Decimal("50000")
        
        result = svc.get_summary(1)
        assert result["project_id"] == 1
        assert result["total_cost"] == 50000.0

    def test_get_project_not_found(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            svc.get_project(999)


class TestTimesheetStatisticsService:
    def test_get_model(self):
        db = MagicMock()
        svc = TimesheetStatisticsService(db)
        model = svc.get_model()
        assert model is not None

    def test_get_project_id_field(self):
        db = MagicMock()
        svc = TimesheetStatisticsService(db)
        assert svc.get_project_id_field() == "project_id"


class TestWorkLogStatisticsService:
    def test_get_model(self):
        db = MagicMock()
        svc = WorkLogStatisticsService(db)
        model = svc.get_model()
        assert model is not None

    def test_get_project_id_field(self):
        db = MagicMock()
        svc = WorkLogStatisticsService(db)
        assert svc.get_project_id_field() == "id"


class TestProjectStatisticsServiceBase:
    def test_apply_date_filter_no_dates(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        result = svc.apply_date_filter(q)
        # No filter applied
        assert result == q

    def test_apply_date_filter_with_dates(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        q.filter.return_value = q
        result = svc.apply_date_filter(q, start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
        assert result is not None

    def test_calculate_total(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = Decimal("12345")
        result = svc.calculate_total(q, "amount")
        assert result == 12345.0

    def test_calculate_total_none(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = None
        result = svc.calculate_total(q, "amount")
        assert result == 0.0

    def test_calculate_avg(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = Decimal("500")
        result = svc.calculate_avg(q, "amount")
        assert result == 500.0

    def test_calculate_avg_none(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = None
        result = svc.calculate_avg(q, "amount")
        assert result == 0.0

    def test_count_distinct(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = 5
        result = svc.count_distinct(q, "project_id")
        assert result == 5

    def test_count_distinct_none(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = None
        result = svc.count_distinct(q, "project_id")
        assert result == 0

    def test_calculate_total_no_field(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        result = svc.calculate_total(q, "nonexistent_field_xyz")
        assert result == 0.0

    def test_calculate_avg_no_field(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        result = svc.calculate_avg(q, "nonexistent_field_xyz")
        assert result == 0.0

    def test_count_distinct_no_field(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        result = svc.count_distinct(q, "nonexistent_field_xyz")
        assert result == 0

    def test_group_by_field_no_field(self):
        db = MagicMock()
        svc = CostStatisticsService(db)
        q = MagicMock()
        result = svc.group_by_field(q, "nonexistent_field_xyz")
        assert result == {}
