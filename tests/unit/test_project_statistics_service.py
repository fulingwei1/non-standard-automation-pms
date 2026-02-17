# -*- coding: utf-8 -*-
"""
项目统计服务单元测试
覆盖纯函数统计方法（不依赖真实DB）
"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

from app.services.project_statistics_service import (
    calculate_status_statistics,
    calculate_stage_statistics,
    calculate_health_statistics,
    calculate_pm_statistics,
    calculate_customer_statistics,
    calculate_monthly_statistics,
    build_project_statistics,
)


def make_project(status=None, stage=None, health=None, pm_id=None, pm_name=None,
                 customer_id=None, customer_name=None, contract_amount=None,
                 created_at=None, progress_pct=None):
    p = MagicMock()
    p.status = status
    p.stage = stage
    p.health = health
    p.pm_id = pm_id
    p.pm_name = pm_name
    p.customer_id = customer_id
    p.customer_name = customer_name
    p.contract_amount = contract_amount
    p.created_at = created_at
    p.progress_pct = progress_pct
    return p


def make_query(projects):
    """返回一个 .all() 会给出 projects 的 mock 查询对象"""
    q = MagicMock()
    q.all.return_value = projects
    q.filter.return_value = q
    return q


class TestCalculateStatusStatistics:
    def test_counts_by_status(self):
        projects = [
            make_project(status="ST10"),
            make_project(status="ST10"),
            make_project(status="ST20"),
        ]
        result = calculate_status_statistics(make_query(projects))
        assert result["ST10"] == 2
        assert result["ST20"] == 1

    def test_ignores_none_status(self):
        projects = [make_project(status=None), make_project(status="ST10")]
        result = calculate_status_statistics(make_query(projects))
        assert None not in result
        assert result.get("ST10") == 1

    def test_empty_returns_empty_dict(self):
        result = calculate_status_statistics(make_query([]))
        assert result == {}


class TestCalculateStageStatistics:
    def test_counts_by_stage(self):
        projects = [
            make_project(stage="DESIGN"),
            make_project(stage="DESIGN"),
            make_project(stage="ASSEMBLY"),
        ]
        result = calculate_stage_statistics(make_query(projects))
        assert result["DESIGN"] == 2
        assert result["ASSEMBLY"] == 1

    def test_ignores_none_stage(self):
        projects = [make_project(stage=None)]
        result = calculate_stage_statistics(make_query(projects))
        assert result == {}


class TestCalculateHealthStatistics:
    def test_counts_by_health(self):
        projects = [
            make_project(health="H1"),
            make_project(health="H2"),
            make_project(health="H1"),
        ]
        result = calculate_health_statistics(make_query(projects))
        assert result["H1"] == 2
        assert result["H2"] == 1


class TestCalculatePmStatistics:
    def test_aggregates_by_pm_id(self):
        projects = [
            make_project(pm_id=1, pm_name="Alice"),
            make_project(pm_id=1, pm_name="Alice"),
            make_project(pm_id=2, pm_name="Bob"),
        ]
        result = calculate_pm_statistics(make_query(projects))
        counts = {r["pm_id"]: r["count"] for r in result}
        assert counts[1] == 2
        assert counts[2] == 1

    def test_ignores_none_pm_id(self):
        projects = [make_project(pm_id=None)]
        result = calculate_pm_statistics(make_query(projects))
        assert result == []


class TestCalculateCustomerStatistics:
    def test_sums_contract_amount(self):
        projects = [
            make_project(customer_id=10, customer_name="Acme", contract_amount=Decimal("500000")),
            make_project(customer_id=10, customer_name="Acme", contract_amount=Decimal("300000")),
        ]
        result = calculate_customer_statistics(make_query(projects))
        assert len(result) == 1
        assert result[0]["total_amount"] == pytest.approx(800000.0)
        assert result[0]["count"] == 2

    def test_none_customer_id_groups_as_zero(self):
        projects = [make_project(customer_id=None, customer_name=None, contract_amount=Decimal("0"))]
        result = calculate_customer_statistics(make_query(projects))
        assert result[0]["customer_id"] == 0


class TestCalculateMonthlyStatistics:
    def test_groups_by_year_month(self):
        projects = [
            make_project(created_at=datetime(2025, 1, 15), contract_amount=Decimal("100000")),
            make_project(created_at=datetime(2025, 1, 20), contract_amount=Decimal("200000")),
            make_project(created_at=datetime(2025, 2, 5), contract_amount=Decimal("150000")),
        ]
        result = calculate_monthly_statistics(make_query(projects))
        assert len(result) == 2
        assert result[0]["month_label"] == "2025-01"
        assert result[0]["count"] == 2
        assert result[1]["month_label"] == "2025-02"

    def test_sorted_chronologically(self):
        projects = [
            make_project(created_at=datetime(2025, 3, 1), contract_amount=Decimal("0")),
            make_project(created_at=datetime(2025, 1, 1), contract_amount=Decimal("0")),
        ]
        result = calculate_monthly_statistics(make_query(projects))
        assert result[0]["month"] == 1
        assert result[1]["month"] == 3

    def test_ignores_none_created_at(self):
        projects = [make_project(created_at=None)]
        result = calculate_monthly_statistics(make_query(projects))
        assert result == []


class TestBuildProjectStatistics:
    def test_total_and_average_progress(self):
        projects = [
            make_project(status="ST10", stage="DESIGN", health="H1",
                         pm_id=1, pm_name="Alice", progress_pct=60.0,
                         created_at=datetime(2025, 1, 1), contract_amount=Decimal("0")),
            make_project(status="ST10", stage="DESIGN", health="H1",
                         pm_id=1, pm_name="Alice", progress_pct=40.0,
                         created_at=datetime(2025, 1, 1), contract_amount=Decimal("0")),
        ]
        q = make_query(projects)
        db = MagicMock()
        result = build_project_statistics(db, q)
        assert result["total"] == 2
        assert result["average_progress"] == pytest.approx(50.0)

    def test_empty_projects_returns_zero_total(self):
        q = make_query([])
        db = MagicMock()
        result = build_project_statistics(db, q)
        assert result["total"] == 0
        assert result["average_progress"] == 0
