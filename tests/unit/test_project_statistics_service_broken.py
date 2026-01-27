# -*- coding: utf-8 -*-
"""
Tests for project_statistics_service service
Covers: app/services/project_statistics_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 225 lines
Batch: P2 - 核心模块测试（项目管理）
"""

import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.project_statistics_service import (
    calculate_status_statistics,
    calculate_stage_statistics,
    calculate_health_statistics,
    calculate_pm_statistics,
    calculate_customer_statistics,
    calculate_monthly_statistics,
    build_project_statistics,
)


class TestCalculateStatusStatistics:
    """Test suite for calculate_status_statistics function."""

    def test_calculate_status_statistics_with_various_statuses(
        self, db_session: Session
    ):
        """Test status calculation with various project statuses."""
        # Create projects with different statuses
        projects = [
        Project(project_code="PJ001", status="ST01", progress_pct=10),
        Project(project_code="PJ002", status="ST01", progress_pct=15),
        Project(project_code="PJ003", status="ST02", progress_pct=30),
        Project(project_code="PJ004", status="ST03", progress_pct=50),
        Project(project_code="PJ005", status="ST04", progress_pct=70),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_status_statistics(query)

        assert result["ST01"] == 2
        assert result["ST02"] == 1
        assert result["ST03"] == 1
        assert result["ST04"] == 1

    def test_calculate_status_statistics_empty_result(self, db_session: Session):
        """Test status calculation with no projects."""
        query = db_session.query(Project)
        result = calculate_status_statistics(query)

        assert result == {}

    def test_calculate_status_statistics_filters_null_status(self, db_session: Session):
        """Test that null statuses are filtered out."""
        projects = [
        Project(project_code="PJ001", status="ST01", progress_pct=10),
        Project(project_code="PJ002", status=None, progress_pct=0),
        Project(project_code="PJ003", status="ST02", progress_pct=20),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_status_statistics(query)

        # Only non-null statuses should be included
        assert "ST01" in result
        assert "ST02" in result
        assert None not in result


class TestCalculateStageStatistics:
    """Test suite for calculate_stage_statistics function."""

    def test_calculate_stage_statistics_with_various_stages(self, db_session: Session):
        """Test stage calculation with various project stages."""
        projects = [
        Project(project_code="PJ001", stage="S1", progress_pct=5),
        Project(project_code="PJ002", stage="S1", progress_pct=10),
        Project(project_code="PJ003", stage="S2", progress_pct=25),
        Project(project_code="PJ004", stage="S2", progress_pct=30),
        Project(project_code="PJ005", stage="S3", progress_pct=40),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_stage_statistics(query)

        assert result["S1"] == 2
        assert result["S2"] == 2
        assert result["S3"] == 1

    def test_calculate_stage_statistics_empty_result(self, db_session: Session):
        """Test stage calculation with no projects."""
        query = db_session.query(Project)
        result = calculate_stage_statistics(query)

        assert result == {}


class TestCalculateHealthStatistics:
    """Test suite for calculate_health_statistics function."""

    def test_calculate_health_statistics_with_various_health(self, db_session: Session):
        """Test health calculation with various health statuses."""
        projects = [
        Project(project_code="PJ001", health="H1", progress_pct=50),
        Project(project_code="PJ002", health="H1", progress_pct=60),
        Project(project_code="PJ003", health="H2", progress_pct=40),
        Project(project_code="PJ004", health="H3", progress_pct=20),
        Project(project_code="PJ005", health="H4", progress_pct=100),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_health_statistics(query)

        assert result["H1"] == 2
        assert result["H2"] == 1
        assert result["H3"] == 1
        assert result["H4"] == 1

    def test_calculate_health_statistics_empty_result(self, db_session: Session):
        """Test health calculation with no projects."""
        query = db_session.query(Project)
        result = calculate_health_statistics(query)

        assert result == {}


class TestCalculatePMStatistics:
    """Test suite for calculate_pm_statistics function."""

    def test_calculate_pm_statistics_with_assigned_pms(self, db_session: Session):
        """Test PM calculation with assigned project managers."""
        projects = [
        Project(project_code="PJ001", pm_id=1, pm_name="张三"),
        Project(project_code="PJ002", pm_id=1, pm_name="张三"),
        Project(project_code="PJ003", pm_id=2, pm_name="李四"),
        Project(project_code="PJ004", pm_id=3, pm_name="王五"),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_pm_statistics(query)

        assert len(result) == 3

        # Check that results are correct
        pm_stats = {r["pm_name"]: r["count"] for r in result}
        assert pm_stats["张三"] == 2
        assert pm_stats["李四"] == 1
        assert pm_stats["王五"] == 1

        # Check pm_id is included
        for r in result:
            assert "pm_id" in r
            assert "pm_name" in r
            assert "count" in r

    def test_calculate_pm_statistics_with_null_pm(self, db_session: Session):
        """Test that projects without PM are filtered out."""
        projects = [
        Project(project_code="PJ001", pm_id=1, pm_name="张三"),
        Project(project_code="PJ002", pm_id=None, pm_name=None),
        Project(project_code="PJ003", pm_id=2, pm_name="李四"),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_pm_statistics(query)

        # Should only include projects with assigned PM
        assert len(result) == 2
        pm_names = [r["pm_name"] for r in result]
        assert "张三" in pm_names
        assert "李四" in pm_names
        assert None not in pm_names

    def test_calculate_pm_statistics_empty_result(self, db_session: Session):
        """Test PM calculation with no assigned PMs."""
        projects = [
        Project(project_code="PJ001", pm_id=None, pm_name=None),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_pm_statistics(query)

        assert result == []


class TestCalculateCustomerStatistics:
    """Test suite for calculate_customer_statistics function."""

    def test_calculate_customer_statistics_with_customers(self, db_session: Session):
        """Test customer calculation with various customers."""
        projects = [
        Project(
        project_code="PJ001",
        customer_id=1,
        customer_name="客户A",
        contract_amount=50000.0,
        ),
        Project(
        project_code="PJ002",
        customer_id=1,
        customer_name="客户A",
        contract_amount=30000.0,
        ),
        Project(
        project_code="PJ003",
        customer_id=2,
        customer_name="客户B",
        contract_amount=60000.0,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_customer_statistics(query)

        assert len(result) == 2

        # Check customer A
        customer_a = next(r for r in result if r["customer_name"] == "客户A")
        assert customer_a["customer_id"] == 1
        assert customer_a["count"] == 2
        assert customer_a["total_amount"] == 80000.0

        # Check customer B
        customer_b = next(r for r in result if r["customer_name"] == "客户B")
        assert customer_b["customer_id"] == 2
        assert customer_b["count"] == 1
        assert customer_b["total_amount"] == 60000.0

    def test_calculate_customer_statistics_with_null_customer(
        self, db_session: Session
    ):
        """Test that projects without customer are filtered out."""
        projects = [
        Project(
        project_code="PJ001",
        customer_id=1,
        customer_name="客户A",
        contract_amount=50000.0,
        ),
        Project(
        project_code="PJ002",
        customer_id=None,
        customer_name=None,
        contract_amount=0.0,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_customer_statistics(query)

        # Should only include projects with assigned customer
        assert len(result) == 1
        assert result[0]["customer_name"] == "客户A"

    def test_calculate_customer_statistics_null_name(self, db_session: Session):
        """Test that null customer names default to '未知客户'."""
        projects = [
        Project(
        project_code="PJ001",
        customer_id=1,
        customer_name=None,
        contract_amount=50000.0,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = calculate_customer_statistics(query)

        assert result[0]["customer_name"] == "未知客户"


class TestCalculateMonthlyStatistics:
    """Test suite for calculate_monthly_statistics function."""

    def test_calculate_monthly_statistics_with_date_range(self, db_session: Session):
        """Test monthly calculation with specific date range."""
        # Create projects in different months
        projects = [
        Project(
        project_code="PJ001",
        created_at=datetime(2025, 1, 15),
        contract_amount=50000.0,
        ),
        Project(
        project_code="PJ002",
        created_at=datetime(2025, 1, 20),
        contract_amount=30000.0,
        ),
        Project(
        project_code="PJ003",
        created_at=datetime(2025, 2, 10),
        contract_amount=60000.0,
        ),
        Project(
        project_code="PJ004",
        created_at=datetime(2025, 3, 5),
        contract_amount=40000.0,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        start_date = date(2025, 1, 1)
        end_date = date(2025, 3, 31)

        query = db_session.query(Project)
        result = calculate_monthly_statistics(query, start_date, end_date)

        assert len(result) == 3

        # Check January
        jan = next(r for r in result if r["month"] == 1)
        assert jan["year"] == 2025
        assert jan["month_label"] == "2025-01"
        assert jan["count"] == 2
        assert jan["total_amount"] == 80000.0

        # Check February
        feb = next(r for r in result if r["month"] == 2)
        assert feb["year"] == 2025
        assert feb["month_label"] == "2025-02"
        assert feb["count"] == 1
        assert feb["total_amount"] == 60000.0

        # Check March
        mar = next(r for r in result if r["month"] == 3)
        assert mar["year"] == 2025
        assert mar["month_label"] == "2025-03"
        assert mar["count"] == 1
        assert mar["total_amount"] == 40000.0

    def test_calculate_monthly_statistics_empty_result(self, db_session: Session):
        """Test monthly calculation with no projects in date range."""
        projects = [
        Project(
        project_code="PJ001",
        created_at=datetime(2024, 1, 1),
        contract_amount=50000.0,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        start_date = date(2025, 1, 1)
        end_date = date(2025, 3, 31)

        query = db_session.query(Project)
        result = calculate_monthly_statistics(query, start_date, end_date)

        assert result == []

    def test_calculate_monthly_statistics_order(self, db_session: Session):
        """Test that monthly statistics are ordered by year and month."""
        projects = [
        Project(
        project_code="PJ001",
        created_at=datetime(2025, 3, 1),
        contract_amount=10000.0,
        ),
        Project(
        project_code="PJ002",
        created_at=datetime(2025, 1, 1),
        contract_amount=10000.0,
        ),
        Project(
        project_code="PJ003",
        created_at=datetime(2025, 2, 1),
        contract_amount=10000.0,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        start_date = date(2025, 1, 1)
        end_date = date(2025, 3, 31)

        query = db_session.query(Project)
        result = calculate_monthly_statistics(query, start_date, end_date)

        # Check order
        assert result[0]["month"] == 1
        assert result[1]["month"] == 2
        assert result[2]["month"] == 3


class TestBuildProjectStatistics:
    """Test suite for build_project_statistics function."""

    def test_build_project_statistics_basic(self, db_session: Session):
        """Test building basic project statistics."""
        projects = [
        Project(
        project_code="PJ001",
        project_name="项目A",
        status="ST01",
        stage="S1",
        health="H1",
        progress_pct=20,
        pm_id=1,
        pm_name="张三",
        ),
        Project(
        project_code="PJ002",
        project_name="项目B",
        status="ST02",
        stage="S2",
        health="H2",
        progress_pct=40,
        pm_id=2,
        pm_name="李四",
        ),
        Project(
        project_code="PJ003",
        project_name="项目C",
        status="ST01",
        stage="S1",
        health="H1",
        progress_pct=30,
        pm_id=1,
        pm_name="张三",
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = build_project_statistics(
        db=db_session,
        query=query,
        group_by=None,
        start_date=None,
        end_date=None,
        )

        # Check basic stats
        assert result["total"] == 3
        assert result["average_progress"] == pytest.approx(30.0, rel=0.01)

        # Check grouped stats
        assert result["by_status"]["ST01"] == 2
        assert result["by_status"]["ST02"] == 1
        assert result["by_stage"]["S1"] == 2
        assert result["by_stage"]["S2"] == 1
        assert result["by_health"]["H1"] == 2
        assert result["by_health"]["H2"] == 1

        # Check PM stats
        assert len(result["by_pm"]) == 2
        pm_stats = {r["pm_name"]: r["count"] for r in result["by_pm"]}
        assert pm_stats["张三"] == 2
        assert pm_stats["李四"] == 1

    def test_build_project_statistics_group_by_customer(self, db_session: Session):
        """Test building statistics grouped by customer."""
        projects = [
        Project(
        project_code="PJ001",
        project_name="客户项目A",
        customer_id=1,
        customer_name="客户A",
        contract_amount=50000.0,
        progress_pct=30,
        ),
        Project(
        project_code="PJ002",
        project_name="客户项目B",
        customer_id=1,
        customer_name="客户A",
        contract_amount=30000.0,
        progress_pct=40,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = build_project_statistics(
        db=db_session,
        query=query,
        group_by="customer",
        start_date=None,
        end_date=None,
        )

        # Should include customer statistics
        assert "by_customer" in result
        assert len(result["by_customer"]) == 1
        assert result["by_customer"][0]["customer_name"] == "客户A"
        assert result["by_customer"][0]["total_amount"] == 80000.0

    def test_build_project_statistics_group_by_month(self, db_session: Session):
        """Test building statistics grouped by month."""
        today = date(2025, 3, 1)
        projects = [
        Project(
        project_code="PJ001",
        created_at=datetime(2025, 2, 15),
        contract_amount=50000.0,
        progress_pct=30,
        ),
        Project(
        project_code="PJ002",
        created_at=datetime(2025, 3, 1),
        contract_amount=30000.0,
        progress_pct=40,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = build_project_statistics(
        db=db_session,
        query=query,
        group_by="month",
        start_date=None,
        end_date=None,
        )

        # Should include monthly statistics
        assert "by_month" in result
        assert len(result["by_month"]) == 2

        # Should default to last 12 months when no date range provided
        assert result["by_month"][0]["month_label"] == "2025-02"
        assert result["by_month"][1]["month_label"] == "2025-03"

    def test_build_project_statistics_group_by_month_with_custom_dates(
        self, db_session: Session
    ):
        """Test building monthly statistics with custom date range."""
        projects = [
        Project(
        project_code="PJ001",
        created_at=datetime(2025, 1, 15),
        contract_amount=50000.0,
        progress_pct=30,
        ),
        Project(
        project_code="PJ002",
        created_at=datetime(2025, 2, 1),
        contract_amount=30000.0,
        progress_pct=40,
        ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        query = db_session.query(Project)
        result = build_project_statistics(
        db=db_session,
        query=query,
        group_by="month",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 31),
        )

        # Should only include projects in January
        assert "by_month" in result
        assert len(result["by_month"]) == 1
        assert result["by_month"][0]["month_label"] == "2025-01"
        assert result["by_month"][0]["count"] == 1
