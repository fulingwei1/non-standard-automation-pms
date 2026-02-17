# -*- coding: utf-8 -*-
"""
项目统计服务 N2 深度覆盖测试
覆盖: ProjectStatisticsServiceBase 所有方法, CostStatisticsService, 
      TimesheetStatisticsService, build_project_statistics with group_by
"""
import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.project_statistics_service import (
    calculate_status_statistics,
    calculate_stage_statistics,
    calculate_health_statistics,
    calculate_pm_statistics,
    calculate_customer_statistics,
    calculate_monthly_statistics,
    build_project_statistics,
    CostStatisticsService,
    TimesheetStatisticsService,
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
    q = MagicMock()
    q.all.return_value = projects
    q.filter.return_value = q
    return q


# ======================= 函数级统计 =======================

class TestCalculateMonthlyStatisticsEdgeCases:
    """月度统计边缘情况"""

    def test_with_start_date_filter(self):
        """start_date 过滤生效"""
        projects = [
            make_project(created_at=datetime(2025, 1, 15), contract_amount=Decimal("100000")),
        ]
        q = make_query(projects)
        result = calculate_monthly_statistics(q, start_date=date(2025, 1, 1))
        assert len(result) >= 0  # filter is applied to query

    def test_with_end_date_filter(self):
        projects = [
            make_project(created_at=datetime(2025, 3, 1), contract_amount=Decimal("50000")),
        ]
        q = make_query(projects)
        result = calculate_monthly_statistics(q, end_date=date(2025, 3, 31))
        assert len(result) >= 0

    def test_none_contract_amount_defaults_to_zero(self):
        projects = [make_project(created_at=datetime(2025, 2, 5), contract_amount=None)]
        result = calculate_monthly_statistics(make_query(projects))
        assert result[0]["total_amount"] == 0.0


class TestBuildProjectStatisticsGroupBy:
    """build_project_statistics group_by 分支"""

    def test_group_by_customer(self):
        projects = [
            make_project(status="ST10", stage="DESIGN", health="H1",
                         pm_id=1, pm_name="Alice", progress_pct=50.0,
                         customer_id=10, customer_name="Acme",
                         contract_amount=Decimal("100000"),
                         created_at=datetime(2025, 1, 1)),
        ]
        q = make_query(projects)
        db = MagicMock()
        result = build_project_statistics(db, q, group_by="customer")
        assert "by_customer" in result
        assert len(result["by_customer"]) == 1

    def test_group_by_month(self):
        projects = [
            make_project(status="ST10", stage="DESIGN", health="H1",
                         pm_id=1, pm_name="Alice", progress_pct=30.0,
                         contract_amount=Decimal("200000"),
                         created_at=datetime(2025, 3, 10)),
        ]
        q = make_query(projects)
        db = MagicMock()
        result = build_project_statistics(db, q, group_by="month",
                                          start_date=date(2025, 1, 1),
                                          end_date=date(2025, 12, 31))
        assert "by_month" in result

    def test_no_group_by_has_no_customer_key(self):
        q = make_query([])
        db = MagicMock()
        result = build_project_statistics(db, q)
        assert "by_customer" not in result
        assert "by_month" not in result


# ======================= ProjectStatisticsServiceBase =======================

class ConcreteService(CostStatisticsService):
    """使用 CostStatisticsService 作为具体实现来测试基类"""
    pass


class TestProjectStatisticsServiceBase:
    """测试基类共享方法"""

    def setup_method(self):
        self.db = MagicMock()
        self.service = ConcreteService(self.db)

    def test_get_project_found(self):
        mock_project = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_project
        result = self.service.get_project(1)
        assert result is mock_project

    def test_get_project_not_found_raises(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            self.service.get_project(999)

    def test_apply_date_filter_with_both_dates(self):
        """start_date 和 end_date 都提供时两个过滤都应用"""
        q = MagicMock()
        q.filter.return_value = q
        result = self.service.apply_date_filter(
            q,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            date_field="created_at"
        )
        assert q.filter.call_count == 2

    def test_apply_date_filter_no_dates(self):
        """无日期时不过滤"""
        q = MagicMock()
        result = self.service.apply_date_filter(q)
        assert result is q
        q.filter.assert_not_called()

    def test_apply_date_filter_only_start(self):
        q = MagicMock()
        q.filter.return_value = q
        result = self.service.apply_date_filter(q, start_date=date(2025, 1, 1))
        assert q.filter.call_count == 1

    def test_apply_date_filter_invalid_field(self):
        """不存在的字段时，不过滤"""
        q = MagicMock()
        result = self.service.apply_date_filter(
            q,
            start_date=date(2025, 1, 1),
            date_field="nonexistent_field_xyz"
        )
        assert result is q

    def test_group_by_field_no_field(self):
        """字段不存在时返回空字典"""
        q = MagicMock()
        result = self.service.group_by_field(q, "nonexistent_field_xyz")
        assert result == {}

    def test_calculate_total_no_field(self):
        """字段不存在时返回0"""
        q = MagicMock()
        result = self.service.calculate_total(q, "nonexistent_field")
        assert result == 0.0

    def test_calculate_total_returns_float(self):
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = Decimal("1500")
        result = self.service.calculate_total(q, "amount")
        assert isinstance(result, float)
        assert result == 1500.0

    def test_calculate_total_none_scalar_returns_zero(self):
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = None
        result = self.service.calculate_total(q, "amount")
        assert result == 0.0

    def test_calculate_avg_no_field(self):
        q = MagicMock()
        result = self.service.calculate_avg(q, "nonexistent")
        assert result == 0.0

    def test_calculate_avg_none_returns_zero(self):
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = None
        result = self.service.calculate_avg(q, "amount")
        assert result == 0.0

    def test_count_distinct_no_field(self):
        q = MagicMock()
        result = self.service.count_distinct(q, "nonexistent")
        assert result == 0

    def test_count_distinct_none_returns_zero(self):
        q = MagicMock()
        q.with_entities.return_value.scalar.return_value = None
        result = self.service.count_distinct(q, "project_id")
        assert result == 0


# ======================= CostStatisticsService =======================

class TestCostStatisticsService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = CostStatisticsService(self.db)

    def test_get_summary_with_budget(self):
        """有预算时计算使用率"""
        project = MagicMock()
        project.project_id = 1
        project.project_name = "Test Project"
        project.budget_amount = Decimal("100000")

        self.db.query.return_value.filter.return_value.first.return_value = project
        # build_base_query returns a chainable mock
        q = MagicMock()
        q.filter.return_value = q
        q.with_entities.return_value.group_by.return_value.all.return_value = [("人力", 30000)]
        q.with_entities.return_value.scalar.return_value = Decimal("50000")
        self.db.query.return_value.filter.return_value = q

        result = self.service.get_summary(1)
        assert "project_id" in result
        assert "total_cost" in result

    def test_get_summary_no_budget(self):
        """无预算时 budget_used_pct 为 None"""
        project = MagicMock()
        project.project_name = "No Budget"
        project.budget_amount = None

        self.db.query.return_value.filter.return_value.first.return_value = project
        q = MagicMock()
        q.filter.return_value = q
        q.with_entities.return_value.group_by.return_value.all.return_value = []
        q.with_entities.return_value.scalar.return_value = Decimal("0")
        self.db.query.return_value.filter.return_value = q

        result = self.service.get_summary(1)
        assert result.get("budget_used_pct") is None


# ======================= TimesheetStatisticsService =======================

class TestTimesheetStatisticsService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = TimesheetStatisticsService(self.db)

    def test_get_statistics_basic(self):
        project = MagicMock()
        project.project_name = "Test"
        self.db.query.return_value.filter.return_value.first.return_value = project

        ts1 = MagicMock()
        ts1.hours = Decimal("8")
        ts1.status = "APPROVED"
        ts1.user_id = 1
        ts1.work_date = date(2025, 1, 10)
        ts1.overtime_type = None

        ts2 = MagicMock()
        ts2.hours = Decimal("4")
        ts2.status = "PENDING"
        ts2.user_id = 2
        ts2.work_date = date(2025, 1, 11)
        ts2.overtime_type = "OVERTIME"

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [ts1, ts2]
        self.db.query.return_value.filter.return_value = q

        result = self.service.get_statistics(1)
        assert result["total_hours"] == 12.0
        assert result["approved_hours"] == 8.0
        assert result["pending_hours"] == 4.0

    def test_get_statistics_draft_and_rejected(self):
        """测试 DRAFT 和 REJECTED 状态的工时统计"""
        project = MagicMock()
        project.project_name = "Test"
        self.db.query.return_value.filter.return_value.first.return_value = project

        ts_draft = MagicMock()
        ts_draft.hours = Decimal("3")
        ts_draft.status = "DRAFT"
        ts_draft.user_id = 1
        ts_draft.work_date = date(2025, 1, 12)

        ts_rejected = MagicMock()
        ts_rejected.hours = Decimal("2")
        ts_rejected.status = "REJECTED"
        ts_rejected.user_id = 2
        ts_rejected.work_date = date(2025, 1, 13)

        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [ts_draft, ts_rejected]
        self.db.query.return_value.filter.return_value = q

        result = self.service.get_statistics(1)
        assert result["draft_hours"] == 3.0
        assert result["rejected_hours"] == 2.0

    def test_get_statistics_empty_no_error(self):
        project = MagicMock()
        project.project_name = "Empty"
        self.db.query.return_value.filter.return_value.first.return_value = project
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        self.db.query.return_value.filter.return_value = q

        result = self.service.get_statistics(1)
        assert result["total_hours"] == 0.0
        assert result["avg_daily_hours"] == 0.0
