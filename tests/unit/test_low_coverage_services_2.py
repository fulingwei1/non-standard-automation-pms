# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for low-coverage service modules.
Focus: Simple mock-based tests to achieve 60-70% coverage per service.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

# Import services under test
from app.services.project_evaluation_service import ProjectEvaluationService
from app.services.change_impact_analysis_service import (
    analyze_schedule_impact,
    analyze_cost_impact,
    analyze_resource_impact,
    analyze_related_project_impact,
    build_impact_analysis,
    calculate_change_statistics,
)
from app.services.data_scope_service import DataScopeService
from app.services.notification_service import (
    NotificationService,
    NotificationChannel,
    NotificationType,
)
from app.services.progress_aggregation_service import (
    aggregate_task_progress,
    _check_and_update_health,
    create_progress_log,
    get_project_progress_summary,
    ProgressAggregationService,
)
from app.services.progress_auto_service import ProgressAutoService
from app.services.project_statistics_service import (
    calculate_status_statistics,
    calculate_stage_statistics,
    calculate_health_statistics,
    calculate_pm_statistics,
    calculate_customer_statistics,
    calculate_monthly_statistics,
    build_project_statistics,
)
from app.services.project_import_service import (
    validate_excel_file,
    parse_excel_data,
    validate_project_columns,
    get_column_value,
    parse_project_row,
    find_or_create_customer,
    find_project_manager,
    parse_date_value,
    parse_decimal_value,
    import_projects_from_dataframe,
)
# from app.services.material_transfer_service import MaterialTransferService


# ============================================
# Test: ProjectEvaluationService
# ============================================


class TestProjectEvaluationService:
    """Tests for ProjectEvaluationService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Service instance"""
        return ProjectEvaluationService(mock_db)

    def test_get_dimension_weights_default(self, service, mock_db):
        """Test get_dimension_weights returns default when no dimensions in DB"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        weights = service.get_dimension_weights()
        assert weights == service.DEFAULT_WEIGHTS

    def test_get_dimension_weights_from_db(self, service, mock_db):
        """Test get_dimension_weights loads from database"""
        mock_dim = MagicMock()
        mock_dim.dimension_type = "NOVELTY"
        mock_dim.default_weight = Decimal("100")
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_dim]
        weights = service.get_dimension_weights()
        assert "novelty" in weights

    def test_get_level_thresholds_default(self, service):
        """Test get_level_thresholds returns default thresholds"""
        thresholds = service.get_level_thresholds()
        assert thresholds is not None
        assert "S" in thresholds

    def test_calculate_total_score(self, service):
        """Test calculate_total_score with default weights"""
        result = service.calculate_total_score(
            Decimal("8"), Decimal("7"), Decimal("6"), Decimal("9"), Decimal("8")
        )
        assert isinstance(result, Decimal)
        assert result > 0

    def test_calculate_total_score_custom_weights(self, service):
        """Test calculate_total_score with custom weights"""
        custom_weights = {
            "novelty": Decimal("0.2"),
            "new_tech": Decimal("0.2"),
            "difficulty": Decimal("0.2"),
            "workload": Decimal("0.2"),
            "amount": Decimal("0.2"),
        }
        result = service.calculate_total_score(
            Decimal("5"),
            Decimal("5"),
            Decimal("5"),
            Decimal("5"),
            Decimal("5"),
            weights=custom_weights,
        )
        assert result == Decimal("5.0")

    def test_determine_evaluation_level_s(self, service):
        """Test determine_evaluation_level for S level"""
        level = service.determine_evaluation_level(Decimal("95"))
        assert level == "S"

    def test_determine_evaluation_level_d(self, service):
        """Test determine_evaluation_level for D level"""
        level = service.determine_evaluation_level(Decimal("50"))
        assert level == "D"

    def test_auto_calculate_novelty_score_no_similar(self, service, mock_db):
        """Test auto_calculate_novelty_score with no similar projects"""
        mock_project = MagicMock(
            id=1, project_type="TEST", product_category="A", industry="B"
        )
        mock_db.query.return_value.filter.return_value.all.return_value = []
        score = service.auto_calculate_novelty_score(mock_project)
        assert score == Decimal("2.0")

    def test_auto_calculate_amount_score_large(self, service):
        """Test auto_calculate_amount_score for large project"""
        mock_project = MagicMock(contract_amount=Decimal("6000000"))
        score = service.auto_calculate_amount_score(mock_project)
        assert score == Decimal("2.0")

    def test_auto_calculate_amount_score_small(self, service):
        """Test auto_calculate_amount_score for small project"""
        mock_project = MagicMock(contract_amount=Decimal("300000"))
        score = service.auto_calculate_amount_score(mock_project)
        assert score == Decimal("9.5")

    def test_auto_calculate_workload_score_not_implemented(self, service):
        """Test auto_calculate_workload_score returns None (not implemented)"""
        mock_project = MagicMock()
        score = service.auto_calculate_workload_score(mock_project)
        assert score is None

    def test_generate_evaluation_code(self, service):
        """Test generate_evaluation_code generates valid code"""
        code = service.generate_evaluation_code()
        assert code.startswith("PE")
        assert len(code) > 10

    def test_create_evaluation(self, service, mock_db):
        """Test create_evaluation creates valid evaluation"""
        evaluation = service.create_evaluation(
            project_id=1,
            novelty_score=Decimal("8"),
            new_tech_score=Decimal("7"),
            difficulty_score=Decimal("6"),
            workload_score=Decimal("7"),
            amount_score=Decimal("8"),
            evaluator_id=1,
            evaluator_name="Test User",
        )
        assert evaluation.project_id == 1
        assert evaluation.total_score > 0
        assert evaluation.status == "DRAFT"

    def test_get_latest_evaluation(self, service, mock_db):
        """Test get_latest_evaluation queries correctly"""

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = service.get_latest_evaluation(1)
        assert result is None

    def test_get_bonus_coefficient_no_evaluation(self, service, mock_db):
        """Test get_bonus_coefficient with no evaluation returns 1.0"""
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_project = MagicMock(id=1)
        coefficient = service.get_bonus_coefficient(mock_project)
        assert coefficient == Decimal("1.0")

    def test_get_bonus_coefficient_with_evaluation(self, service, mock_db):
        """Test get_bonus_coefficient with evaluation"""

        mock_eval = MagicMock(evaluation_level="S")
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_eval
        mock_project = MagicMock(id=1)
        coefficient = service.get_bonus_coefficient(mock_project)
        assert coefficient == Decimal("1.5")

    def test_get_difficulty_bonus_coefficient_no_eval(self, service, mock_db):
        """Test get_difficulty_bonus_coefficient with no evaluation"""
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_project = MagicMock(id=1)
        coefficient = service.get_difficulty_bonus_coefficient(mock_project)
        assert coefficient == Decimal("1.0")

    def test_get_difficulty_bonus_coefficient_high_difficulty(self, service, mock_db):
        """Test get_difficulty_bonus_coefficient for high difficulty"""

        mock_eval = MagicMock(difficulty_score=Decimal("2.5"))
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_eval
        mock_project = MagicMock(id=1)
        coefficient = service.get_difficulty_bonus_coefficient(mock_project)
        assert coefficient == Decimal("1.5")

    def test_get_new_tech_bonus_coefficient_no_new_tech(self, service, mock_db):
        """Test get_new_tech_bonus_coefficient with no new tech"""
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_project = MagicMock(id=1)
        coefficient = service.get_new_tech_bonus_coefficient(mock_project)
        assert coefficient == Decimal("1.0")


# ============================================
# Test: ChangeImpactAnalysisService
# ============================================


class TestChangeImpactAnalysisService:
    """Tests for change impact analysis functions"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def mock_change(self):
        """Mock change request"""
        mock = MagicMock()
        mock.change_no = "CR001"
        mock.change_type = "DESIGN"
        mock.change_level = "MAJOR"
        mock.title = "Test Change"
        mock.status = "APPROVED"
        mock.schedule_impact = "Delay by 5 days"
        mock.cost_impact = Decimal("10000")
        mock.resource_impact = "Need extra engineer"
        return mock

    @pytest.fixture
    def mock_project(self):
        """Mock project"""
        mock = MagicMock(id=1, budget_amount=Decimal("100000"))
        return mock

    def test_analyze_schedule_impact_no_impact(self, mock_change):
        """Test analyze_schedule_impact with no schedule impact"""
        mock_change.schedule_impact = None
        result = analyze_schedule_impact(MagicMock(), mock_change, 1)
        assert result is None

    def test_analyze_schedule_impact_with_impact(self, mock_db, mock_change):
        """Test analyze_schedule_impact returns impact info"""
        mock_task = MagicMock(
            id=1,
            task_name="Task 1",
            plan_start=datetime.now(),
            plan_end=datetime.now() + timedelta(days=1),
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]
        result = analyze_schedule_impact(mock_db, mock_change, 1)
        assert result is not None
        assert result["description"] == mock_change.schedule_impact
        assert len(result["affected_items"]) > 0

    def test_analyze_cost_impact_no_impact(self, mock_change):
        """Test analyze_cost_impact with no cost impact"""
        mock_change.cost_impact = None
        result = analyze_cost_impact(mock_change, MagicMock())
        assert result is None

    def test_analyze_cost_impact_high_severity(self, mock_change, mock_project):
        """Test analyze_cost_impact with high severity"""
        mock_project.budget_amount = Decimal("50000")
        result = analyze_cost_impact(mock_change, mock_project)
        assert result is not None
        assert result["severity"] == "HIGH"

    def test_analyze_cost_impact_medium_severity(self, mock_change, mock_project):
        """Test analyze_cost_impact with medium severity"""
        result = analyze_cost_impact(mock_change, mock_project)
        assert result is not None
        assert result["severity"] == "MEDIUM"

    def test_analyze_resource_impact_no_impact(self, mock_change):
        """Test analyze_resource_impact with no resource impact"""
        mock_change.resource_impact = None
        result = analyze_resource_impact(MagicMock(), mock_change, 1)
        assert result is None

    def test_analyze_resource_impact_with_impact(self, mock_db, mock_change):
        """Test analyze_resource_impact returns impact info"""
        mock_alloc = MagicMock(
            id=1,
            resource_name="Engineer 1",
            allocation_percent=100,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=30),
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_alloc]
        result = analyze_resource_impact(mock_db, mock_change, 1)
        assert result is not None
        assert len(result["affected_resources"]) > 0

    def test_analyze_related_project_impact_empty(self, mock_db, mock_change):
        """Test analyze_related_project_impact with no related projects"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = analyze_related_project_impact(mock_db, mock_change, 1)
        assert result["count"] == 0

    def test_build_impact_analysis(self, mock_db, mock_change, mock_project):
        """Test build_impact_analysis combines all impacts"""
        with (
            patch(
                "app.services.change_impact_analysis_service.analyze_schedule_impact"
            ) as mock_schedule,
            patch(
                "app.services.change_impact_analysis_service.analyze_cost_impact"
            ) as mock_cost,
            patch(
                "app.services.change_impact_analysis_service.analyze_resource_impact"
            ) as mock_resource,
            patch(
                "app.services.change_impact_analysis_service.analyze_related_project_impact"
            ) as mock_related,
        ):
            mock_schedule.return_value = None
            mock_cost.return_value = {"cost_impact": 10000}
            mock_resource.return_value = None
            mock_related.return_value = {"affected_projects": [], "count": 0}

            result = build_impact_analysis(mock_db, mock_change, mock_project, 1)
            assert result["change_id"] == mock_change.id
            assert "impacts" in result

    def test_calculate_change_statistics(self):
        """Test calculate_change_statistics"""
        mock_change1 = MagicMock(
            change_type="DESIGN",
            change_level="MAJOR",
            status="APPROVED",
            cost_impact=Decimal("10000"),
        )
        mock_change2 = MagicMock(
            change_type="SCOPE",
            change_level="MINOR",
            status="PENDING",
            cost_impact=Decimal("5000"),
        )
        mock_impact = {"impacts": {"related_projects": {"affected_projects": []}}}

        result = calculate_change_statistics(
            [mock_change1, mock_change2], [mock_impact]
        )
        assert result["total_changes"] == 2
        assert result["by_type"]["DESIGN"] == 1
        assert result["by_level"]["MAJOR"] == 1
        assert result["by_status"]["APPROVED"] == 1
        assert result["total_cost_impact"] == 15000


# ============================================
# Test: DataScopeService
# ============================================


class TestDataScopeService:
    """Tests for DataScopeService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def mock_user(self):
        """Mock user"""
        mock = MagicMock()
        mock.id = 1
        mock.is_superuser = False
        mock.department = "Engineering"
        return mock

    def test_get_user_data_scope_superuser(self, mock_user):
        """Test get_user_data_scope for superuser"""
        mock_user.is_superuser = True
        scope = DataScopeService.get_user_data_scope(MagicMock(), mock_user)
        assert scope == "ALL"

    def test_get_user_data_scope_no_roles(self, mock_user):
        """Test get_user_data_scope with no roles"""
        mock_user.roles = []
        scope = DataScopeService.get_user_data_scope(MagicMock(), mock_user)
        assert scope == "OWN"

    def test_get_user_data_scope_with_role(self, mock_user):
        """Test get_user_data_scope with role"""
        mock_role = MagicMock()
        mock_role.is_active = True
        mock_role.data_scope = "DEPT"
        mock_user_role = MagicMock()
        mock_user_role.role = mock_role
        mock_user.roles = [mock_user_role]
        scope = DataScopeService.get_user_data_scope(MagicMock(), mock_user)
        assert scope == "DEPT"

    def test_get_user_project_ids(self, mock_db):
        """Test get_user_project_ids"""
        mock_db.query.return_value.filter.return_value.all.return_value = [(1,), (2,)]
        project_ids = DataScopeService.get_user_project_ids(mock_db, 1)
        assert project_ids == {1, 2}

    def test_get_subordinate_ids(self, mock_db):
        """Test get_subordinate_ids"""
        mock_db.query.return_value.filter.return_value.all.return_value = [(2,), (3,)]
        subordinate_ids = DataScopeService.get_subordinate_ids(mock_db, 1)
        assert subordinate_ids == {2, 3}

    def test_filter_projects_by_scope_superuser(self, mock_user):
        """Test filter_projects_by_scope for superuser"""
        mock_user.is_superuser = True
        mock_query = MagicMock()
        result = DataScopeService.filter_projects_by_scope(
            MagicMock(), mock_query, mock_user
        )
        assert result == mock_query

    def test_filter_projects_by_scope_all(self, mock_db, mock_user):
        """Test filter_projects_by_scope for ALL scope"""
        with patch.object(DataScopeService, "get_user_data_scope", return_value="ALL"):
            mock_query = MagicMock()
            result = DataScopeService.filter_projects_by_scope(
                mock_db, mock_query, mock_user
            )
            assert result == mock_query

    def test_filter_projects_by_scope_own(self, mock_db, mock_user):
        """Test filter_projects_by_scope for OWN scope"""
        with patch.object(DataScopeService, "get_user_data_scope", return_value="OWN"):
            mock_query = MagicMock()
            result = DataScopeService.filter_projects_by_scope(
                mock_db, mock_query, mock_user
            )
            assert result is not None

    def test_filter_issues_by_scope_superuser(self, mock_user):
        """Test filter_issues_by_scope for superuser"""
        mock_user.is_superuser = True
        mock_query = MagicMock()
        result = DataScopeService.filter_issues_by_scope(
            MagicMock(), mock_query, mock_user
        )
        assert result == mock_query

    def test_filter_issues_by_scope_own(self, mock_db, mock_user):
        """Test filter_issues_by_scope for OWN scope"""
        with patch.object(DataScopeService, "get_user_data_scope", return_value="OWN"):
            mock_query = MagicMock()
            result = DataScopeService.filter_issues_by_scope(
                mock_db, mock_query, mock_user
            )
            assert result is not None

    def test_check_project_access_superuser(self, mock_user):
        """Test check_project_access for superuser"""
        mock_user.is_superuser = True
        result = DataScopeService.check_project_access(MagicMock(), mock_user, 1)
        assert result is True

    def test_check_project_access_no_project(self, mock_db, mock_user):
        """Test check_project_access when project doesn't exist"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with patch.object(DataScopeService, "get_user_data_scope", return_value="OWN"):
            result = DataScopeService.check_project_access(mock_db, mock_user, 1)
            assert result is False

    def test_check_customer_access_superuser(self, mock_user):
        """Test check_customer_access for superuser"""
        mock_user.is_superuser = True
        result = DataScopeService.check_customer_access(MagicMock(), mock_user, 1)
        assert result is True


# ============================================
# Test: NotificationService
# ============================================


class TestNotificationService:
    """Tests for NotificationService"""

    @pytest.fixture
    def service(self):
        """Service instance"""
        return NotificationService()

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()

    def test_get_enabled_channels(self, service):
        """Test _get_enabled_channels returns WEB channel"""
        channels = service._get_enabled_channels()
        assert NotificationChannel.WEB in channels

    def test_send_notification_web_only(self, service, mock_db):
        """Test send_notification with only WEB channel"""
        with patch.object(service, "_save_web_notification"):
            result = service.send_notification(
                mock_db,
                recipient_id=1,
                notification_type=NotificationType.TASK_ASSIGNED,
                title="Test",
                content="Test content",
                channels=[NotificationChannel.WEB],
            )
            assert result is True

    def test_send_task_assigned_notification(self, service, mock_db):
        """Test send_task_assigned_notification"""
        with patch.object(service, "send_notification"):
            service.send_task_assigned_notification(
                mock_db,
                assignee_id=1,
                task_name="Task 1",
                project_name="Project 1",
                task_id=1,
            )

    def test_send_task_completed_notification(self, service, mock_db):
        """Test send_task_completed_notification"""
        with patch.object(service, "send_notification"):
            service.send_task_completed_notification(
                mock_db, task_owner_id=1, task_name="Task 1", project_name="Project 1"
            )

    def test_send_deadline_reminder_urgent(self, service, mock_db):
        """Test send_deadline_reminder with urgent priority"""
        with patch.object(service, "send_notification"):
            service.send_deadline_reminder(
                mock_db,
                recipient_id=1,
                task_name="Task 1",
                due_date=datetime.now() + timedelta(days=1),
                days_remaining=1,
            )

    def test_send_deadline_reminder_high_priority(self, service, mock_db):
        """Test send_deadline_reminder with high priority"""
        with patch.object(service, "send_notification"):
            service.send_deadline_reminder(
                mock_db,
                recipient_id=1,
                task_name="Task 1",
                due_date=datetime.now() + timedelta(days=3),
                days_remaining=3,
            )


# ============================================
# Test: ProgressAggregationService
# ============================================


class TestProgressAggregationService:
    """Tests for progress aggregation functions"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def mock_task(self):
        """Mock task"""
        mock = MagicMock()
        mock.id = 1
        mock.project_id = 1
        mock.progress = 50
        mock.stage = None
        return mock

    def test_aggregate_task_progress_no_task(self, mock_db):
        """Test aggregate_task_progress when task doesn't exist"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = aggregate_task_progress(mock_db, 1)
        assert result["project_progress_updated"] is False

    def test_aggregate_task_progress_with_task(self, mock_db, mock_task):
        """Test aggregate_task_progress updates project progress"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        mock_db.query.return_value.filter.return_value.scalar.return_value = (
            2  # total tasks
        )

        with patch(
            "app.services.progress_aggregation_service._check_and_update_health"
        ):
            result = aggregate_task_progress(mock_db, 1)
            assert result["project_id"] == 1

    def test_check_and_update_health_no_project(self, mock_db):
        """Test _check_and_update_health when project doesn't exist"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        _check_and_update_health(mock_db, 1)
        # Should not raise error

    def test_get_project_progress_summary(self, mock_db):
        """Test get_project_progress_summary"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        result = get_project_progress_summary(mock_db, 1)
        assert result["project_id"] == 1
        assert result["total_tasks"] == 0

    def test_create_progress_log(self, mock_db):
        """Test create_progress_log"""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = create_progress_log(
            mock_db,
            task_id=1,
            progress=50,
            actual_hours=8,
            note="Test note",
            updater_id=1,
        )
        # Should not raise error

    def test_progress_aggregation_service_aggregate(self, mock_db):
        """Test ProgressAggregationService.aggregate_project_progress"""
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10

        result = ProgressAggregationService.aggregate_project_progress(1, mock_db)
        assert result["project_id"] == 1
        assert "total_tasks" in result
        assert "overall_progress" in result


# ============================================
# Test: ProgressAutoService
# ============================================


class TestProgressAutoService:
    """Tests for ProgressAutoService"""

    @pytest.fixture
    def service(self, mock_db):
        """Service instance"""
        return ProgressAutoService(mock_db)

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def mock_forecast_item(self):
        """Mock forecast item"""
        from app.schemas.progress import TaskForecastItem

        return TaskForecastItem(
            task_id=1,
            task_name="Task 1",
            progress_percent=50,
            predicted_finish_date=date.today() + timedelta(days=5),
            critical=True,
            status="Delayed",
            delay_days=5,
        )

    def test_apply_forecast_to_tasks_no_forecast(self, service, mock_db):
        """Test apply_forecast_to_tasks with no forecast items"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = service.apply_forecast_to_tasks(1, [])
        assert result["total"] == 0

    def test_apply_forecast_to_tasks_with_forecast(
        self, service, mock_db, mock_forecast_item
    ):
        """Test apply_forecast_to_tasks blocks delayed tasks"""
        mock_task = MagicMock(
            id=1, task_name="Task 1", status="IN_PROGRESS", progress_percent=30
        )
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        result = service.apply_forecast_to_tasks(
            1, [mock_forecast_item], auto_block=True, delay_threshold=3
        )
        assert result["total"] == 1
        assert result["blocked"] == 1

    def test_auto_fix_dependency_issues_no_issues(self, service):
        """Test auto_fix_dependency_issues with no issues"""
        result = service.auto_fix_dependency_issues(1, [])
        assert result["total_issues"] == 0

    def test_auto_fix_dependency_issues_with_cycle(self, service):
        """Test auto_fix_dependency_issues skips cycle issues"""
        mock_issue = MagicMock(issue_type="CYCLE", detail="Cycle detected")
        result = service.auto_fix_dependency_issues(1, [mock_issue])
        assert result["cycles_skipped"] == 1

    def test_run_auto_processing_no_project(self, service, mock_db):
        """Test run_auto_processing when project doesn't exist"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = service.run_auto_processing(1)
        assert result["success"] is False
        assert "error" in result

    def test_run_auto_processing_no_tasks(self, service, mock_db):
        """Test run_auto_processing when project has no tasks"""
        mock_project = MagicMock(id=1)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = service.run_auto_processing(1)
        assert result["success"] is False


# ============================================
# Test: ProjectStatisticsService
# ============================================


class TestProjectStatisticsService:
    """Tests for project statistics functions"""

    @pytest.fixture
    def mock_query(self):
        """Mock query object"""
        return MagicMock()

    def test_calculate_status_statistics(self, mock_query):
        """Test calculate_status_statistics"""
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = [
            ("ACTIVE", 5),
            ("INACTIVE", 2),
        ]
        result = calculate_status_statistics(mock_query)
        assert result["ACTIVE"] == 5
        assert result["INACTIVE"] == 2

    def test_calculate_stage_statistics(self, mock_query):
        """Test calculate_stage_statistics"""
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = [
            ("S1", 3),
            ("S2", 2),
        ]
        result = calculate_stage_statistics(mock_query)
        assert result["S1"] == 3
        assert result["S2"] == 2

    def test_calculate_health_statistics(self, mock_query):
        """Test calculate_health_statistics"""
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = [
            ("H1", 8),
            ("H2", 1),
        ]
        result = calculate_health_statistics(mock_query)
        assert result["H1"] == 8
        assert result["H2"] == 1

    def test_calculate_pm_statistics(self, mock_query):
        """Test calculate_pm_statistics"""
        mock_query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = [
            (1, "PM A", 3),
            (2, "PM B", 2),
        ]
        result = calculate_pm_statistics(mock_query)
        assert len(result) == 2
        assert result[0]["pm_id"] == 1

    def test_calculate_customer_statistics(self, mock_query):
        """Test calculate_customer_statistics"""
        mock_query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = [
            (1, "Customer A", 2, Decimal("100000")),
            (2, "Customer B", 1, Decimal("50000")),
        ]
        result = calculate_customer_statistics(mock_query)
        assert len(result) == 2
        assert result[0]["customer_id"] == 1
        assert result[0]["total_amount"] == 100000.0

    def test_calculate_monthly_statistics(self, mock_query):
        """Test calculate_monthly_statistics"""
        mock_query.filter.return_value.with_entities.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            (2024, 1, 5, Decimal("250000")),
            (2024, 2, 3, Decimal("150000")),
        ]
        result = calculate_monthly_statistics(
            mock_query, date(2024, 1, 1), date(2024, 2, 29)
        )
        assert len(result) == 2
        assert result[0]["year"] == 2024
        assert result[0]["month"] == 1

    def test_build_project_statistics(self, mock_query):
        """Test build_project_statistics"""
        mock_query.count.return_value = 10
        mock_query.with_entities.return_value.scalar.return_value = 75.5

        with (
            patch(
                "app.services.project_statistics_service.calculate_status_statistics",
                return_value={},
            ),
            patch(
                "app.services.project_statistics_service.calculate_stage_statistics",
                return_value={},
            ),
            patch(
                "app.services.project_statistics_service.calculate_health_statistics",
                return_value={},
            ),
            patch(
                "app.services.project_statistics_service.calculate_pm_statistics",
                return_value=[],
            ),
        ):
            result = build_project_statistics(MagicMock(), mock_query, None, None, None)
            assert result["total"] == 10
            assert result["average_progress"] == 75.5


# ============================================
# Test: ProjectImportService
# ============================================


class TestProjectImportService:
    """Tests for project import functions"""

    def test_validate_excel_file_valid(self):
        """Test validate_excel_file with valid file"""
        from fastapi import HTTPException

        try:
            validate_excel_file("test.xlsx")
        except HTTPException:
            pytest.fail("Should not raise for valid file")

    def test_validate_excel_file_invalid(self):
        """Test validate_excel_file with invalid file"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_excel_file("test.pdf")
        assert "只支持Excel文件" in str(exc_info.value.detail)

    def test_parse_excel_data_valid(self):
        """Test parse_excel_data with valid Excel"""
        data = b"test data"
        with patch("pandas.read_excel") as mock_read_excel:
            mock_read_excel.return_value = pd.DataFrame(
                {"col1": [1, 2], "col2": ["a", "b"]}
            )
            result = parse_excel_data(data)
            assert len(result) > 0

    def test_validate_project_columns_valid(self):
        """Test validate_project_columns with valid columns"""
        df = pd.DataFrame({"项目编码*": ["P001"], "项目名称*": ["Project 1"]})
        from fastapi import HTTPException

        try:
            validate_project_columns(df)
        except HTTPException:
            pytest.fail("Should not raise for valid columns")

    def test_validate_project_columns_missing(self):
        """Test validate_project_columns with missing columns"""
        df = pd.DataFrame({"col1": [1], "col2": [2]})
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_project_columns(df)
        assert "缺少必需的列" in str(exc_info.value.detail)

    def test_get_column_value_with_star(self):
        """Test get_column_value with starred column"""
        row = pd.Series({"项目编码*": "P001", "项目名称*": "Project 1"})
        result = get_column_value(row, "项目编码*")
        assert result == "P001"

    def test_get_column_value_without_star(self):
        """Test get_column_value without starred column"""
        row = pd.Series({"项目编码": "P001", "项目名称": "Project 1"})
        result = get_column_value(row, "项目编码*")
        assert result == "P001"

    def test_parse_project_row_valid(self):
        """Test parse_project_row with valid data"""
        row = pd.Series({"项目编码*": "P001", "项目名称*": "Project 1"})
        code, name, errors = parse_project_row(row, 0)
        assert code == "P001"
        assert name == "Project 1"
        assert len(errors) == 0

    def test_parse_project_row_invalid(self):
        """Test parse_project_row with invalid data"""
        row = pd.Series({"项目编码*": None, "项目名称*": None})
        code, name, errors = parse_project_row(row, 0)
        assert code is None
        assert name is None
        assert len(errors) > 0

    def test_parse_date_value_valid(self):
        """Test parse_date_value with valid date"""
        result = parse_date_value("2024-01-01")
        assert isinstance(result, date)

    def test_parse_date_value_invalid(self):
        """Test parse_date_value with invalid date"""
        result = parse_date_value("invalid")
        assert result is None

    def test_parse_decimal_value_valid(self):
        """Test parse_decimal_value with valid decimal"""
        result = parse_decimal_value("12345.67")
        assert isinstance(result, Decimal)
        assert result == Decimal("12345.67")

    def test_parse_decimal_value_invalid(self):
        """Test parse_decimal_value with invalid decimal"""
        result = parse_decimal_value("invalid")
        assert result is None

    def test_find_project_manager_exists(self):
        """Test find_project_manager when manager exists"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        result = find_project_manager(mock_db, "PM Name")
        assert result == mock_user

    def test_find_project_manager_not_exists(self):
        """Test find_project_manager when manager doesn't exist"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = find_project_manager(mock_db, "PM Name")
        assert result is None

    def test_find_or_create_customer_exists(self):
        """Test find_or_create_customer when customer exists"""
        mock_db = MagicMock()
        mock_customer = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_customer
        )
        result = find_or_create_customer(mock_db, "Customer Name")
        assert result == mock_customer

    def test_import_projects_from_dataframe_success(self):
        """Test import_projects_from_dataframe with valid data"""
        mock_db = MagicMock()
        df = pd.DataFrame(
            {"项目编码*": ["P001", "P002"], "项目名称*": ["Project 1", "Project 2"]}
        )
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with patch("app.services.project_import_service.init_project_stages"):
            imported, updated, failed = import_projects_from_dataframe(
                mock_db, df, False
            )
        assert imported == 2
        assert updated == 0
        assert len(failed) == 0
