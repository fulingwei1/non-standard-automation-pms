# -*- coding: utf-8 -*-
"""
Tests for project_dashboard_service service
Covers: app/services/project_dashboard_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 407 lines
Batch: P2 - 核心模块测试（项目管理）
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch

from app.models.project import Project, ProjectCost, ProjectMilestone, ProjectStatusLog
from app.models.progress import Task
from app.services.project_dashboard_service import (
    build_basic_info,
    calculate_progress_stats,
    calculate_cost_stats,
    calculate_task_stats,
    calculate_milestone_stats,
    calculate_risk_stats,
    calculate_issue_stats,
    calculate_resource_usage,
    get_recent_activities,
    calculate_key_metrics,
)


class TestBuildBasicInfo:
    """Test suite for build_basic_info function."""

    def test_build_basic_info_complete_project(self):
        """Test building basic info for a complete project."""
        project = Project(
        id=1,
        project_code="PJ250708001",
        project_name="测试项目",
        customer_name="测试客户",
        pm_name="张三",
        stage="S2",
        status="ST01",
        health="H1",
        progress_pct=50.5,
        planned_start_date=date(2025, 1, 1),
        planned_end_date=date(2025, 6, 30),
        actual_start_date=date(2025, 1, 5),
        actual_end_date=None,
        contract_amount=Decimal("100000.00"),
        budget_amount=Decimal("90000.00"),
        )

        result = build_basic_info(project)

        assert result["project_code"] == "PJ250708001"
        assert result["project_name"] == "测试项目"
        assert result["customer_name"] == "测试客户"
        assert result["pm_name"] == "张三"
        assert result["stage"] == "S2"
        assert result["status"] == "ST01"
        assert result["health"] == "H1"
        assert result["progress_pct"] == 50.5
        assert result["planned_start_date"] == "2025-01-01"
        assert result["planned_end_date"] == "2025-06-30"
        assert result["actual_start_date"] == "2025-01-05"
        assert result["actual_end_date"] is None
        assert result["contract_amount"] == 100000.0
        assert result["budget_amount"] == 90000.0

    def test_build_basic_info_with_null_values(self):
        """Test building basic info with null values."""
        project = Project(
        id=1,
        project_code="PJ250708001",
        project_name="测试项目",
        customer_name="测试客户",
        pm_name="张三",
        stage=None,
        status=None,
        health=None,
        progress_pct=None,
        planned_start_date=None,
        planned_end_date=None,
        actual_start_date=None,
        actual_end_date=None,
        contract_amount=None,
        budget_amount=None,
        )

        result = build_basic_info(project)

        assert result["stage"] == "S1"
        assert result["status"] == "ST01"
        assert result["health"] == "H1"
        assert result["progress_pct"] == 0.0
        assert result["planned_start_date"] is None
        assert result["planned_end_date"] is None
        assert result["actual_start_date"] is None
        assert result["actual_end_date"] is None
        assert result["contract_amount"] == 0.0
        assert result["budget_amount"] == 0.0


class TestCalculateProgressStats:
    """Test suite for calculate_progress_stats function."""

    def test_calculate_progress_stats_normal_case(self):
        """Test progress calculation for normal case."""
        project = Project(
        id=1,
        progress_pct=60.0,
        stage="S2",
        planned_start_date=date(2025, 1, 1),
        planned_end_date=date(2025, 6, 30),
        )
        today = date(2025, 3, 1)  # 60 days out of 180 = 33.33%

        result = calculate_progress_stats(project, today)

        assert result["actual_progress"] == 60.0
        assert result["plan_progress"] == pytest.approx(33.33, rel=0.01)
        assert result["progress_deviation"] == pytest.approx(26.67, rel=0.01)
        assert result["time_deviation_days"] == -121  # March 1 - June 30
        assert result["is_delayed"] is False

    def test_calculate_progress_stats_delayed(self):
        """Test progress calculation for delayed project."""
        project = Project(
        id=1,
        progress_pct=60.0,
        stage="S2",
        planned_end_date=date(2025, 1, 1),
        )
        today = date(2025, 2, 1)  # After planned end date

        result = calculate_progress_stats(project, today)

        assert result["time_deviation_days"] == 31  # Feb 1 - Jan 1
        assert result["is_delayed"] is True

    def test_calculate_progress_stats_completed_project(self):
        """Test that completed projects (S9) are not marked as delayed."""
        project = Project(
        id=1,
        progress_pct=100.0,
        stage="S9",
        planned_end_date=date(2025, 1, 1),
        )
        today = date(2025, 2, 1)

        result = calculate_progress_stats(project, today)

        assert result["time_deviation_days"] == 31
        assert result["is_delayed"] is False  # S9 projects are not delayed

    def test_calculate_progress_stats_no_dates(self):
        """Test progress calculation with no planned dates."""
        project = Project(
        id=1,
        progress_pct=50.0,
        planned_start_date=None,
        planned_end_date=None,
        )
        today = date(2025, 3, 1)

        result = calculate_progress_stats(project, today)

        assert result["actual_progress"] == 50.0
        assert result["plan_progress"] == 0
        assert result["progress_deviation"] == 50.0
        assert result["time_deviation_days"] == 0
        assert result["is_delayed"] is False

    def test_calculate_progress_stats_clamped(self):
        """Test that plan progress is clamped between 0 and 100."""
        # Test early start (before planned start)
        project = Project(
        id=1,
        progress_pct=0.0,
        planned_start_date=date(2025, 3, 1),
        planned_end_date=date(2025, 6, 30),
        )
        today = date(2025, 1, 1)

        result = calculate_progress_stats(project, today)

        assert result["plan_progress"] == 0

        # Test late completion (after planned end)
        project.progress_pct = 100.0
        today = date(2025, 8, 1)

        result = calculate_progress_stats(project, today)

        assert result["plan_progress"] == 100


class TestCalculateCostStats:
    """Test suite for calculate_cost_stats function."""

    def test_calculate_cost_stats_with_costs(self, db_session: Session):
        """Test cost calculation with project costs."""
        # Create project costs
        cost1 = ProjectCost(
        project_id=1,
        amount=Decimal("50000.00"),
        cost_type="DESIGN",
        cost_category="人工成本",
        )
        cost2 = ProjectCost(
        project_id=1,
        amount=Decimal("30000.00"),
        cost_type="MANUFACTURING",
        cost_category="材料成本",
        )
        db_session.add_all([cost1, cost2])
        db_session.commit()

        budget_amount = 90000.0

        result = calculate_cost_stats(db_session, 1, budget_amount)

        assert result["total_cost"] == 80000.0
        assert result["budget_amount"] == 90000.0
        assert result["cost_variance"] == 10000.0
        assert result["cost_variance_rate"] == pytest.approx(11.11, rel=0.01)
        assert result["is_over_budget"] is False
        assert result["cost_by_type"]["DESIGN"] == 50000.0
        assert result["cost_by_type"]["MANUFACTURING"] == 30000.0
        assert result["cost_by_category"]["人工成本"] == 50000.0
        assert result["cost_by_category"]["材料成本"] == 30000.0

    def test_calculate_cost_stats_over_budget(self, db_session: Session):
        """Test cost calculation when over budget."""
        cost = ProjectCost(
        project_id=1,
        amount=Decimal("100000.00"),
        cost_type="DESIGN",
        cost_category="人工成本",
        )
        db_session.add(cost)
        db_session.commit()

        budget_amount = 90000.0

        result = calculate_cost_stats(db_session, 1, budget_amount)

        assert result["total_cost"] == 100000.0
        assert result["cost_variance"] == -10000.0  # Negative = over budget
        assert result["cost_variance_rate"] == pytest.approx(-11.11, rel=0.01)
        assert result["is_over_budget"] is True

    def test_calculate_cost_stats_no_costs(self, db_session: Session):
        """Test cost calculation with no costs."""
        budget_amount = 90000.0

        result = calculate_cost_stats(db_session, 1, budget_amount)

        assert result["total_cost"] == 0.0
        assert result["budget_amount"] == 90000.0
        assert result["cost_variance"] == 90000.0
        assert result["cost_variance_rate"] == 100.0
        assert result["is_over_budget"] is False
        assert result["cost_by_type"] == {}
        assert result["cost_by_category"] == {}

    def test_calculate_cost_stats_zero_budget(self, db_session: Session):
        """Test cost calculation with zero budget."""
        cost = ProjectCost(
        project_id=1,
        amount=Decimal("50000.00"),
        cost_type="DESIGN",
        cost_category="人工成本",
        )
        db_session.add(cost)
        db_session.commit()

        budget_amount = 0.0

        result = calculate_cost_stats(db_session, 1, budget_amount)

        assert result["total_cost"] == 50000.0
        assert result["budget_amount"] == 0.0
        assert result["cost_variance"] == 0.0  # No variance when budget is 0
        assert result["cost_variance_rate"] == 0.0
        assert result["is_over_budget"] is False


class TestCalculateTaskStats:
    """Test suite for calculate_task_stats function."""

    def test_calculate_task_stats_with_tasks(self, db_session: Session):
        """Test task calculation with various task statuses."""
        # Create tasks
        tasks = [
        Task(project_id=1, status="COMPLETED", progress_pct=100.0),
        Task(project_id=1, status="COMPLETED", progress_pct=100.0),
        Task(project_id=1, status="IN_PROGRESS", progress_pct=50.0),
        Task(project_id=1, status="PENDING", progress_pct=0.0),
        Task(project_id=1, status="ACCEPTED", progress_pct=0.0),
        Task(project_id=1, status="BLOCKED", progress_pct=25.0),
        ]
        db_session.add_all(tasks)
        db_session.commit()

        result = calculate_task_stats(db_session, 1)

        assert result["total"] == 6
        assert result["completed"] == 2
        assert result["in_progress"] == 1
        assert result["pending"] == 2  # PENDING + ACCEPTED
        assert result["blocked"] == 1
        assert result["completion_rate"] == pytest.approx(33.33, rel=0.01)
        assert result["avg_progress"] == pytest.approx(45.83, rel=0.01)

    def test_calculate_task_stats_no_tasks(self, db_session: Session):
        """Test task calculation with no tasks."""
        result = calculate_task_stats(db_session, 1)

        assert result["total"] == 0
        assert result["completed"] == 0
        assert result["in_progress"] == 0
        assert result["pending"] == 0
        assert result["blocked"] == 0
        assert result["completion_rate"] == 0
        assert result["avg_progress"] == 0.0


class TestCalculateMilestoneStats:
    """Test suite for calculate_milestone_stats function."""

    def test_calculate_milestone_stats_with_milestones(self, db_session: Session):
        """Test milestone calculation with various milestones."""
        today = date(2025, 3, 1)

        # Create milestones
        milestones = [
        ProjectMilestone(
        project_id=1,
        status="COMPLETED",
        planned_date=date(2025, 1, 15),
        actual_date=date(2025, 1, 15),
        ),
        ProjectMilestone(
        project_id=1,
        status="COMPLETED",
        planned_date=date(2025, 2, 15),
        actual_date=date(2025, 2, 18),
        ),
        ProjectMilestone(
        project_id=1,
        status="PENDING",
        planned_date=date(2025, 3, 15),
        actual_date=None,
        ),
        ProjectMilestone(
        project_id=1,
        status="PENDING",
        planned_date=date(2025, 2, 1),  # Overdue
        actual_date=None,
        ),
        ProjectMilestone(
        project_id=1,
        status="PENDING",
        planned_date=date(2025, 4, 1),  # Upcoming
        actual_date=None,
        ),
        ]
        db_session.add_all(milestones)
        db_session.commit()

        result = calculate_milestone_stats(db_session, 1, today)

        assert result["total"] == 5
        assert result["completed"] == 2
        assert result["overdue"] == 1
        assert result["upcoming"] == 2
        assert result["completion_rate"] == pytest.approx(40.0, rel=0.01)

    def test_calculate_milestone_stats_no_milestones(self, db_session: Session):
        """Test milestone calculation with no milestones."""
        today = date(2025, 3, 1)

        result = calculate_milestone_stats(db_session, 1, today)

        assert result["total"] == 0
        assert result["completed"] == 0
        assert result["overdue"] == 0
        assert result["upcoming"] == 0
        assert result["completion_rate"] == 0


class TestCalculateRiskStats:
    """Test suite for calculate_risk_stats function."""

    def test_calculate_risk_stats_with_risks(self, db_session: Session):
        """Test risk calculation with project risks."""
        # Mock PmoProjectRisk model
        mock_risk = MagicMock()
        mock_risk.project_id = 1
        mock_risk.risk_level = "HIGH"
        mock_risk.status = "OPEN"

        with patch(
            "app.services.project_dashboard_service.PmoProjectRisk", new=MagicMock
        ):
            mock_query = MagicMock()
            mock_query.filter.return_value.all.return_value = [
                MagicMock(risk_level="HIGH", status="OPEN"),
                MagicMock(risk_level="HIGH", status="CLOSED"),
                MagicMock(risk_level="CRITICAL", status="OPEN"),
                MagicMock(risk_level="MEDIUM", status="OPEN"),
            ]
            db_session.query.return_value = mock_query

            result = calculate_risk_stats(db_session, 1)

            assert result["total"] == 4
            assert result["open"] == 3
            assert result["high"] == 1
            assert result["critical"] == 1

    def test_calculate_risk_stats_model_not_exists(self, db_session: Session):
        """Test risk calculation when PmoProjectRisk model doesn't exist."""
        with patch(
            "app.services.project_dashboard_service.PmoProjectRisk",
            side_effect=ImportError,
        ):
            result = calculate_risk_stats(db_session, 1)

        assert result is None


class TestCalculateIssueStats:
    """Test suite for calculate_issue_stats function."""

    def test_calculate_issue_stats_with_issues(self, db_session: Session):
        """Test issue calculation with project issues."""
        # Mock Issue model
        with patch("app.services.project_dashboard_service.Issue", new=MagicMock):
            mock_query = MagicMock()
            mock_query.filter.return_value.all.return_value = [
            MagicMock(status="OPEN", is_blocking=False),
            MagicMock(status="OPEN", is_blocking=False),
            MagicMock(status="PROCESSING", is_blocking=False),
            MagicMock(status="CLOSED", is_blocking=True),
            MagicMock(status="OPEN", is_blocking=True),
            ]
            db_session.query.return_value = mock_query

            result = calculate_issue_stats(db_session, 1)

            assert result["total"] == 5
            assert result["open"] == 2
            assert result["processing"] == 1
            assert result["blocking"] == 2

    def test_calculate_issue_stats_model_not_exists(self, db_session: Session):
        """Test issue calculation when Issue model doesn't exist."""
        with patch(
            "app.services.project_dashboard_service.Issue", side_effect=ImportError
        ):
            result = calculate_issue_stats(db_session, 1)

            assert result is None


class TestCalculateResourceUsage:
    """Test suite for calculate_resource_usage function."""

    def test_calculate_resource_usage_with_allocations(self, db_session: Session):
        """Test resource usage calculation with allocations."""
        # Mock PmoResourceAllocation model
        with patch(
            "app.services.project_dashboard_service.PmoResourceAllocation",
            new=MagicMock,
        ):
            mock_query = MagicMock()
            mock_allocations = [
                MagicMock(department_name="研发部", role="设计工程师"),
                MagicMock(department_name="研发部", role="设计工程师"),
                MagicMock(department_name="制造部", role="装配技师"),
                MagicMock(department_name=None, role=None),
                MagicMock(role="测试工程师"),
            ]
        mock_query.filter.return_value.all.return_value = mock_allocations
        db_session.query.return_value = mock_query

        result = calculate_resource_usage(db_session, 1)

        assert result["total_allocations"] == 5
        assert result["by_department"]["研发部"] == 2
        assert result["by_department"]["制造部"] == 1
        assert result["by_department"]["未分配"] == 2
        assert result["by_role"]["设计工程师"] == 2
        assert result["by_role"]["装配技师"] == 1
        assert result["by_role"]["测试工程师"] == 1
        assert result["by_role"]["未分配"] == 1

    def test_calculate_resource_usage_no_allocations(self, db_session: Session):
        """Test resource usage calculation with no allocations."""
        with patch(
            "app.services.project_dashboard_service.PmoResourceAllocation",
            new=MagicMock,
        ):
            mock_query = MagicMock()
            mock_query.filter.return_value.all.return_value = []
            db_session.query.return_value = mock_query

            result = calculate_resource_usage(db_session, 1)

            assert result is None

    def test_calculate_resource_usage_model_not_exists(self, db_session: Session):
        """Test resource usage when PmoResourceAllocation model doesn't exist."""
        with patch(
            "app.services.project_dashboard_service.PmoResourceAllocation",
            side_effect=ImportError,
        ):
            result = calculate_resource_usage(db_session, 1)

            assert result is None


class TestGetRecentActivities:
    """Test suite for get_recent_activities function."""

    def test_get_recent_activities(self, db_session: Session):
        """Test getting recent activities."""
        # Create status logs
        status_logs = [
        ProjectStatusLog(
        project_id=1,
        old_status="S1",
        new_status="S2",
        changed_at=datetime(2025, 3, 1, 10, 0),
        change_reason="需求确认完成",
        ),
        ProjectStatusLog(
        project_id=1,
        old_status="S2",
        new_status="S3",
        changed_at=datetime(2025, 2, 15, 14, 0),
        change_reason="设计方案完成",
        ),
        ]

        # Create milestones
        milestones = [
        ProjectMilestone(
        project_id=1,
        milestone_name="需求冻结",
        status="COMPLETED",
        actual_date=datetime(2025, 3, 5, 9, 0),
        ),
        ProjectMilestone(
        project_id=1,
        milestone_name="设计评审",
        status="COMPLETED",
        actual_date=datetime(2025, 2, 20, 16, 0),
        ),
        ]

        db_session.add_all(status_logs + milestones)
        db_session.commit()

        result = get_recent_activities(db_session, 1)

        # Should return up to 10 activities, sorted by time
        assert len(result) == 4

        # Check types
        types = [a["type"] for a in result]
        assert "STATUS_CHANGE" in types
        assert "MILESTONE" in types

        # Check that activities are sorted by time (descending)
        times = [a.get("time") for a in result]
        assert times == sorted(times, reverse=True)

    def test_get_recent_activities_limit(self, db_session: Session):
        """Test that get_recent_activities limits to 10 results."""
        # Create more than 10 status logs
        logs = []
        for i in range(15):
            logs.append(
            ProjectStatusLog(
            project_id=1,
            old_status=f"S{i}",
            new_status=f"S{i + 1}",
            changed_at=datetime(2025, 3, 1, i, 0),
            change_reason=f"变更{i}",
            )
            )
            db_session.add_all(logs)
            db_session.commit()

            result = get_recent_activities(db_session, 1)

            # Should limit to 10
            assert len(result) == 10


class TestCalculateKeyMetrics:
    """Test suite for calculate_key_metrics function."""

    def test_calculate_key_metrics_healthy_project(self):
        """Test key metrics calculation for healthy project."""
        project = Project(
        id=1,
        health="H1",
        progress_pct=75.0,
        )

        result = calculate_key_metrics(
        project=project,
        progress_deviation=5.0,
        cost_variance_rate=-2.0,
        task_completed=8,
        task_total=10,
        )

        assert result["health_score"] == 100.0
        assert result["progress_score"] == 75.0
        assert result["schedule_score"] == 95.0
        assert result["cost_score"] == 96.0
        assert result["quality_score"] == 80.0
        # Overall = 100*0.3 + 75*0.25 + 95*0.2 + 96*0.15 + 80*0.1
        assert result["overall_score"] == pytest.approx(91.9, rel=0.01)

    def test_calculate_key_metrics_at_risk_project(self):
        """Test key metrics calculation for at-risk project."""
        project = Project(
        id=1,
        health="H2",
        progress_pct=50.0,
        )

        result = calculate_key_metrics(
        project=project,
        progress_deviation=-15.0,
        cost_variance_rate=15.0,
        task_completed=3,
        task_total=10,
        )

        assert result["health_score"] == 75.0
        assert result["progress_score"] == 50.0
        # Deviation > 20, so penalty applies: 100 - abs(-15) * 2 = 70
        assert result["schedule_score"] == 70.0
        # Variance > 10, so penalty applies: 100 - abs(15) * 2 = 70
        assert result["cost_score"] == 70.0
        assert result["quality_score"] == 30.0

    def test_calculate_key_metrics_critical_project(self):
        """Test key metrics calculation for critical project."""
        project = Project(
        id=1,
        health="H3",
        progress_pct=25.0,
        )

        result = calculate_key_metrics(
        project=project,
        progress_deviation=-30.0,
        cost_variance_rate=25.0,
        task_completed=1,
        task_total=10,
        )

        assert result["health_score"] == 50.0
        assert result["progress_score"] == 25.0
        assert result["schedule_score"] == 40.0
        assert result["cost_score"] == 50.0
        assert result["quality_score"] == 10.0

    def test_calculate_key_metrics_completed_project(self):
        """Test key metrics calculation for completed project."""
        project = Project(
        id=1,
        health="H4",
        progress_pct=100.0,
        )

        result = calculate_key_metrics(
        project=project,
        progress_deviation=0.0,
        cost_variance_rate=5.0,
        task_completed=10,
        task_total=10,
        )

        assert result["health_score"] == 25.0
        assert result["progress_score"] == 100.0
        assert result["schedule_score"] == 100.0
        assert result["cost_score"] == 90.0
        assert result["quality_score"] == 100.0

    def test_calculate_key_metrics_no_tasks(self):
        """Test key metrics calculation with no tasks."""
        project = Project(
        id=1,
        health="H1",
        progress_pct=50.0,
        )

        result = calculate_key_metrics(
        project=project,
        progress_deviation=0.0,
        cost_variance_rate=0.0,
        task_completed=0,
        task_total=0,
        )

        # When no tasks, quality_score defaults to 100
        assert result["quality_score"] == 100.0
