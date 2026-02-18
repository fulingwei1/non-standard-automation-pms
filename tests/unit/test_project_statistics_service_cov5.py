# -*- coding: utf-8 -*-
"""第五批：project_statistics_service.py 单元测试"""
import pytest
from unittest.mock import MagicMock

try:
    from app.services.project_statistics_service import (
        calculate_status_statistics,
        calculate_stage_statistics,
        calculate_health_statistics,
        calculate_pm_statistics,
        calculate_customer_statistics,
    )
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="project_statistics_service not importable")


def make_project(**kwargs):
    p = MagicMock()
    p.status = kwargs.get("status", None)
    p.stage = kwargs.get("stage", None)
    p.health = kwargs.get("health", None)
    p.pm_id = kwargs.get("pm_id", None)
    p.pm_name = kwargs.get("pm_name", None)
    p.customer_id = kwargs.get("customer_id", None)
    p.customer_name = kwargs.get("customer_name", None)
    p.contract_amount = kwargs.get("contract_amount", 0)
    return p


def make_query(projects):
    q = MagicMock()
    q.all.return_value = projects
    return q


class TestCalculateStatusStatistics:
    def test_basic_counts(self):
        q = make_query([make_project(status="ACTIVE"), make_project(status="ACTIVE"), make_project(status="CLOSED")])
        result = calculate_status_statistics(q)
        assert result["ACTIVE"] == 2
        assert result["CLOSED"] == 1

    def test_none_status_ignored(self):
        q = make_query([make_project(status=None), make_project(status="ACTIVE")])
        result = calculate_status_statistics(q)
        assert "ACTIVE" in result
        assert None not in result

    def test_empty(self):
        q = make_query([])
        result = calculate_status_statistics(q)
        assert result == {}


class TestCalculateStageStatistics:
    def test_basic_counts(self):
        q = make_query([make_project(stage="DESIGN"), make_project(stage="DESIGN"), make_project(stage="PRODUCTION")])
        result = calculate_stage_statistics(q)
        assert result["DESIGN"] == 2
        assert result["PRODUCTION"] == 1


class TestCalculateHealthStatistics:
    def test_basic_counts(self):
        q = make_query([make_project(health="GREEN"), make_project(health="RED")])
        result = calculate_health_statistics(q)
        assert result["GREEN"] == 1
        assert result["RED"] == 1


class TestCalculatePmStatistics:
    def test_single_pm(self):
        q = make_query([
            make_project(pm_id=1, pm_name="Alice"),
            make_project(pm_id=1, pm_name="Alice"),
            make_project(pm_id=2, pm_name="Bob"),
        ])
        result = calculate_pm_statistics(q)
        counts = {r["pm_id"]: r["count"] for r in result}
        assert counts[1] == 2
        assert counts[2] == 1

    def test_none_pm_ignored(self):
        q = make_query([make_project(pm_id=None)])
        result = calculate_pm_statistics(q)
        assert result == []


class TestCalculateCustomerStatistics:
    def test_accumulate_amount(self):
        q = make_query([
            make_project(customer_id=10, customer_name="CustA", contract_amount=100),
            make_project(customer_id=10, customer_name="CustA", contract_amount=200),
        ])
        result = calculate_customer_statistics(q)
        assert len(result) == 1
        assert result[0]["total_amount"] == 300.0

    def test_multiple_customers(self):
        q = make_query([
            make_project(customer_id=1, customer_name="A", contract_amount=50),
            make_project(customer_id=2, customer_name="B", contract_amount=80),
        ])
        result = calculate_customer_statistics(q)
        assert len(result) == 2
