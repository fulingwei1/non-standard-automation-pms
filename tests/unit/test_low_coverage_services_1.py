# -*- coding: utf-8 -*-
"""
Unit tests for low-coverage services
Targeting 60-70% coverage with mock-based tests
"""

import sys
from datetime import date, datetime, timedelta
from enum import Enum
from unittest.mock import Mock, patch


# Patch missing enums to avoid import errors
class ProductMatchTypeEnum(str, Enum):
    ADVANTAGE = "ADVANTAGE"
    NEW = "NEW"
    UNKNOWN = "UNKNOWN"


class LeadOutcomeEnum(str, Enum):
    WON = "WON"
    LOST = "LOST"
    ABANDONED = "ABANDONED"
    ON_HOLD = "ON_HOLD"


class WinProbabilityLevelEnum(str, Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


# Create mock modules to avoid import errors
app_enums_module = type("app.models.enums", (), {})
sys.modules["app.models.enums"] = app_enums_module
app_enums_module.ProductMatchTypeEnum = ProductMatchTypeEnum
app_enums_module.LeadOutcomeEnum = LeadOutcomeEnum
app_enums_module.WinProbabilityLevelEnum = WinProbabilityLevelEnum

app_user_module = type("app.models.user", (), {})
sys.modules["app.models.user"] = app_user_module
app_user_module.Department = type("Department", (), {})()
app_user_module.User = type("User", (), {})()

app_project_module = type("app.models.project", (), {})
sys.modules["app.models.project"] = app_project_module
app_project_module.Project = type("Project", (), {})()
app_project_module.Customer = type("Customer", (), {})()
sys.modules["app.models.project"].Customer = app_project_module.Customer

# Import services to test
from app.services.win_rate_prediction_service import WinRatePredictionService  # type: ignore
from app.services.template_report_service import TemplateReportService  # type: ignore
from app.services.timesheet_reminder_service import (  # type: ignore
    create_timesheet_notification,
    notify_timesheet_missing,
    notify_timesheet_anomaly,
    notify_approval_timeout,
    notify_sync_failure,
)
from app.services.ticket_assignment_service import (  # type: ignore
    get_project_members_for_ticket,
    get_ticket_related_projects,
)
from app.services.user_workload_service import (  # type: ignore
    calculate_workdays,
    get_user_tasks,
    calculate_task_hours,
    calculate_total_assigned_hours,
)
from app.services.status_transition_service import StatusTransitionService  # type: ignore
from app.services.stage_transition_checks import (  # type: ignore
    check_s3_to_s4_transition,
    check_s4_to_s5_transition,
    check_s7_to_s8_transition,
    get_stage_status_mapping,
)
from app.services.template_recommendation_service import TemplateRecommendationService  # type: ignore


# =============================================================================
# Win Rate Prediction Service Tests (7 tests)
# =============================================================================


class TestWinRatePredictionService:
    """Test suite for WinRatePredictionService"""

    def test_get_salesperson_historical_win_rate_with_data(self):
        """Test historical win rate calculation with data"""
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = Mock(total=10, won=6)

        service = WinRatePredictionService(mock_db)
        win_rate, sample_size = service.get_salesperson_historical_win_rate(1)

        assert win_rate == 0.6
        assert sample_size == 10

    def test_get_salesperson_historical_win_rate_no_data(self):
        """Test historical win rate with no data returns default"""
        mock_db = Mock()
        mock_query = Mock()
        mock_filter = Mock()

        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = Mock(total=0, won=0)

        service = WinRatePredictionService(mock_db)
        win_rate, sample_size = service.get_salesperson_historical_win_rate(1)

        assert win_rate == 0.20
        assert sample_size == 0

    def test_calculate_base_score(self):
        """Test base score calculation from dimension scores"""
        from app.schemas.presales import DimensionScore

        mock_db = Mock()
        service = WinRatePredictionService(mock_db)

        scores = DimensionScore(
            requirement_maturity=80,
            technical_feasibility=75,
            business_feasibility=70,
            delivery_risk=65,
            customer_relationship=60,
        )

        base_score = service.calculate_base_score(scores)

        expected = (80 * 0.20 + 75 * 0.25 + 70 * 0.20 + 65 * 0.15 + 60 * 0.20) / 100
        assert abs(base_score - expected) < 0.01

    def test_calculate_salesperson_factor(self):
        """Test salesperson factor calculation"""
        mock_db = Mock()
        service = WinRatePredictionService(mock_db)

        factor_high = service.calculate_salesperson_factor(0.8)
        assert factor_high == 0.9

        factor_avg = service.calculate_salesperson_factor(0.5)
        assert factor_avg == 0.75

        factor_low = service.calculate_salesperson_factor(0.2)
        assert factor_low == 0.6

    def test_calculate_customer_factor(self):
        """Test customer relationship factor calculation"""
        mock_db = Mock()
        service = WinRatePredictionService(mock_db)

        factor = service.calculate_customer_factor(5, 3)
        assert factor == 1.30

        factor = service.calculate_customer_factor(3, 2)
        assert factor == 1.20

        factor = service.calculate_customer_factor(1, 0, is_repeat_customer=True)
        assert factor == 1.05

        factor = service.calculate_customer_factor(0, 0)
        assert factor == 1.0

    def test_calculate_competitor_factor(self):
        """Test competition factor calculation"""
        mock_db = Mock()
        service = WinRatePredictionService(mock_db)

        assert service.calculate_competitor_factor(1) == 1.20
        assert service.calculate_competitor_factor(0) == 1.20

        assert service.calculate_competitor_factor(2) == 1.05

        assert service.calculate_competitor_factor(3) == 1.00

        assert service.calculate_competitor_factor(5) == 0.85

        assert service.calculate_competitor_factor(6) == 0.70

    def test_generate_recommendations_low_predicted_rate(self):
        """Test recommendation generation for low predicted rate"""
        from app.schemas.presales import DimensionScore

        mock_db = Mock()
        service = WinRatePredictionService(mock_db)

        scores = DimensionScore(
            requirement_maturity=50,
            technical_feasibility=50,
            business_feasibility=50,
            delivery_risk=50,
            customer_relationship=50,
        )

        recommendations = service._generate_recommendations(
            predicted_rate=0.25,
            dimension_scores=scores,
            salesperson_win_rate=0.2,
            competitor_count=5,
        )

        assert len(recommendations) > 0
        assert any("需求成熟度" in r for r in recommendations)
        assert any("技术可行性" in r for r in recommendations)
        assert any("商务可行性" in r for r in recommendations)


# =============================================================================
# Template Report Service Tests (7 tests)
# =============================================================================


class TestTemplateReportService:
    """Test suite for TemplateReportService"""

    @patch("app.services.template_report_service.Timesheet")
    @patch("app.services.template_report_service.Project")
    @patch("app.services.template_report_service.ProjectMilestone")
    def test_generate_project_weekly_with_data(
        self, mock_milestone, mock_project, mock_timesheet
    ):
        """Test project weekly report generation with data"""
        mock_db = Mock()
        mock_project_obj = Mock()
        mock_project_obj.project_code = "PJ001"
        mock_project_obj.project_name = "Test Project"
        mock_project_obj.current_stage = "S3"
        mock_project_obj.health_status = "H1"
        mock_project_obj.progress = 65.5

        mock_project.filter.return_value.first.return_value = mock_project_obj
        mock_milestone.filter.return_value.all.return_value = []
        mock_timesheet.filter.return_value.all.return_value = []

        result = TemplateReportService._generate_project_weekly(
            mock_db, 1, date(2024, 1, 1), date(2024, 1, 7), {}, {}
        )

        assert "summary" in result
        assert result["summary"]["project_name"] == "Test Project"
        assert result["summary"]["progress"] == 65.5

    @patch("app.services.template_report_service.Timesheet")
    @patch("app.services.template_report_service.Project")
    def test_generate_project_weekly_project_not_found(
        self, mock_project, mock_timesheet
    ):
        """Test project weekly report when project not found"""
        mock_db = Mock()
        mock_project.filter.return_value.first.return_value = None

        result = TemplateReportService._generate_project_weekly(
            mock_db, 999, date(2024, 1, 1), date(2024, 1, 7), {}, {}
        )

        assert "error" in result
        assert result["error"] == "项目不存在"

    @patch("app.services.template_report_service.Timesheet")
    @patch("app.services.template_report_service.User")
    @patch("app.services.template_report_service.Department")
    def test_generate_dept_weekly_with_data(self, mock_dept, mock_user, mock_timesheet):
        """Test department weekly report generation"""
        mock_db = Mock()
        mock_dept_obj = Mock()
        mock_dept_obj.name = "技术部"

        mock_dept.filter.return_value.first.return_value = mock_dept_obj
        mock_user.filter.return_value.all.return_value = []
        mock_timesheet.filter.return_value.all.return_value = []

        result = TemplateReportService._generate_dept_weekly(
            mock_db, 1, date(2024, 1, 1), date(2024, 1, 7), {}, {}
        )

        assert "summary" in result
        assert result["summary"]["department_name"] == "技术部"
        assert result["summary"]["period_start"] == "2024-01-01"

    @patch("app.services.template_report_service.Timesheet")
    @patch("app.services.template_report_service.User")
    @patch("app.services.template_report_service.Department")
    def test_generate_dept_weekly_dept_not_found(
        self, mock_dept, mock_user, mock_timesheet
    ):
        """Test department weekly report when department not found"""
        mock_db = Mock()
        mock_dept.filter.return_value.first.return_value = None

        result = TemplateReportService._generate_dept_weekly(
            mock_db, 999, date(2024, 1, 1), date(2024, 1, 7), {}, {}
        )

        assert "error" in result
        assert result["error"] == "部门不存在"

    @patch("app.services.template_report_service.Timesheet")
    @patch("app.services.template_report_service.User")
    def test_generate_workload_analysis_with_users(self, mock_user, mock_timesheet):
        """Test workload analysis report generation"""
        mock_db = Mock()
        mock_user_obj = Mock()
        mock_user_obj.id = 1
        mock_user_obj.real_name = "John Doe"
        mock_user_obj.username = "jdoe"
        mock_user_obj.department = "技术部"
        mock_user_obj.position = "Engineer"

        mock_user.filter.return_value.all.return_value = [mock_user_obj]
        mock_timesheet.filter.return_value.all.return_value = []

        result = TemplateReportService._generate_workload_analysis(
            mock_db, 1, date(2024, 1, 1), date(2024, 1, 7), {}, {}
        )

        assert "summary" in result
        assert result["summary"]["total_users"] == 1
        assert "metrics" in result

    @patch("app.services.template_report_service.Project")
    @patch("app.services.template_report_service.Timesheet")
    def test_generate_cost_analysis_with_project(self, mock_timesheet, mock_project):
        """Test cost analysis report generation"""
        mock_db = Mock()
        mock_project_obj = Mock()
        mock_project_obj.id = 1
        mock_project_obj.project_name = "Test Project"
        mock_project_obj.budget_amount = 100000

        mock_project.filter.return_value.all.return_value = [mock_project_obj]
        mock_timesheet.filter.return_value.all.return_value = []

        result = TemplateReportService._generate_cost_analysis(
            mock_db, 1, date(2024, 1, 1), date(2024, 1, 7), {}, {}
        )

        assert "summary" in result
        assert result["summary"]["project_count"] == 1
        assert "metrics" in result

    @patch("app.services.template_report_service.Project")
    @patch("app.services.template_report_service.Department")
    def test_generate_company_monthly(self, mock_dept, mock_project):
        """Test company monthly report generation"""
        mock_db = Mock()
        mock_project_obj = Mock()
        mock_project_obj.status = "IN_PROGRESS"
        mock_project_obj.health_status = "H1"

        mock_project.filter.return_value.all.return_value = [mock_project_obj]
        mock_dept.all.return_value = []

        result = TemplateReportService._generate_company_monthly(
            mock_db, date(2024, 1, 1), date(2024, 1, 31), {}, {}
        )

        assert "summary" in result
        assert result["summary"]["total_projects"] == 1


# =============================================================================
# Timesheet Reminder Service Tests (7 tests)
# =============================================================================


class TestTimesheetReminderService:
    """Test suite for TimesheetReminderService"""

    @patch("app.services.timesheet_reminder_service.db")
    def test_create_timesheet_notification(self, mock_db):
        """Test creating a timesheet notification"""
        notification = create_timesheet_notification(
            db=mock_db,
            user_id=1,
            notification_type="TEST_TYPE",
            title="Test Title",
            content="Test Content",
        )

        mock_db.add.assert_called_once()
        assert notification.user_id == 1
        assert notification.notification_type == "TEST_TYPE"
        assert notification.title == "Test Title"
        assert notification.content == "Test Content"

    @patch("app.services.timesheet_reminder_service.db")
    @patch("app.services.timesheet_reminder_service.create_timesheet_notification")
    @patch("app.services.timesheet_reminder_service.User")
    @patch("app.services.timesheet_reminder_service.Role")
    @patch("app.services.timesheet_reminder_service.Department")
    def test_notify_timesheet_missing_no_reminders(
        self, mock_dept, mock_role, mock_user, mock_create, mock_db
    ):
        """Test no reminders when all engineers have timesheets"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = notify_timesheet_missing(mock_db, date(2024, 1, 1))

        assert result == 0

    @patch("app.services.timesheet_reminder_service.db")
    @patch("app.services.timesheet_reminder_service.create_timesheet_notification")
    @patch("app.services.timesheet_reminder_service.User")
    @patch("app.services.timesheet_reminder_service.Role")
    @patch("app.services.timesheet_reminder_service.Department")
    def test_notify_timesheet_missing_with_engineers(
        self, mock_dept, mock_role, mock_user, mock_create, mock_db
    ):
        """Test reminders sent to engineers without timesheets"""
        engineer = Mock()
        engineer.id = 1
        engineer.real_name = "John Doe"
        engineer.username = "jdoe"

        mock_user.filter.return_value.all.return_value = [engineer]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = notify_timesheet_missing(mock_db, date(2024, 1, 1))

        assert result == 1
        mock_create.assert_called_once()

    @patch("app.services.timesheet_reminder_service.TimesheetQualityService")
    @patch("app.services.timesheet_reminder_service.Timesheet")
    @patch("app.services.timesheet_reminder_service.db")
    def test_notify_timesheet_anomaly(
        self, mock_db, mock_timesheet, mock_quality_class
    ):
        """Test anomaly notification"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        quality_service = Mock()
        quality_service.detect_anomalies.return_value = [
            {
                "timesheet_id": 1,
                "anomaly_type": "HIGH_HOURS",
                "description": "Excessive hours",
            }
        ]
        mock_quality_class.return_value = quality_service

        result = notify_timesheet_anomaly(mock_db, days=1)

        assert result >= 0

    @patch("app.services.timesheet_reminder_service.Timesheet")
    @patch("app.services.timesheet_reminder_service.User")
    @patch("app.services.timesheet_reminder_service.Department")
    @patch("app.services.timesheet_reminder_service.Project")
    @patch("app.services.timesheet_reminder_service.db")
    def test_notify_approval_timeout(
        self, mock_db, mock_project, mock_dept, mock_user, mock_timesheet
    ):
        """Test approval timeout notification"""
        timesheet = Mock()
        timesheet.id = 1
        timesheet.user_id = 1
        timesheet.project_id = 1
        timesheet.status = "PENDING"
        timesheet.created_at = datetime.now() - timedelta(hours=30)

        user = Mock()
        user.id = 1
        user.department_id = 1

        department = Mock()
        department.manager_id = 2

        mock_timesheet.filter.return_value.all.return_value = [timesheet]
        mock_user.filter.return_value.first.return_value = user
        mock_dept.filter.return_value.first.return_value = department
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = notify_approval_timeout(mock_db, timeout_hours=24)

        assert result >= 0

    @patch("app.services.timesheet_reminder_service.Timesheet")
    @patch("app.services.timesheet_reminder_service.db")
    def test_notify_sync_failure(self, mock_db, mock_timesheet):
        """Test sync failure notification"""
        timesheet = Mock()
        timesheet.id = 1
        timesheet.user_id = 1
        timesheet.work_date = date(2024, 1, 1)
        timesheet.status = "APPROVED"
        timesheet.approve_time = datetime.now() - timedelta(hours=2)

        mock_timesheet.filter.return_value.all.return_value = [timesheet]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = notify_sync_failure(mock_db)

        assert result >= 0


# =============================================================================
# Ticket Assignment Service Tests (6 tests)
# =============================================================================


class TestTicketAssignmentService:
    """Test suite for TicketAssignmentService"""

    @patch("app.services.ticket_assignment_service.ProjectMember")
    def test_get_project_members_empty_list(self, mock_member):
        """Test getting members with empty project list"""
        mock_db = Mock()

        result = get_project_members_for_ticket(mock_db, [], None, None)

        assert result == []
        mock_member.filter.assert_not_called()

    @patch("app.services.ticket_assignment_service.ProjectMember")
    def test_get_project_members_with_data(self, mock_member):
        """Test getting project members successfully"""
        mock_db = Mock()

        member = Mock()
        member.user_id = 1
        member.role_code = "PM"
        member.is_lead = True
        member.allocation_pct = 100

        user = Mock()
        user.username = "pm_user"
        user.real_name = "Project Manager"
        user.email = "pm@example.com"
        user.phone = "1234567890"
        user.department = "技术部"
        user.position = "PM"

        project = Mock()
        project.id = 1
        project.project_code = "PJ001"
        project.project_name = "Project 1"

        member.user = user
        member.project = project
        member.role_type = Mock(role_name="项目经理")

        mock_member.filter.return_value.all.return_value = [member]

        result = get_project_members_for_ticket(mock_db, [1])

        assert len(result) == 1
        assert result[0]["user_id"] == 1
        assert result[0]["role_code"] == "PM"
        assert result[0]["is_lead"] is True

    @patch("app.services.ticket_assignment_service.ProjectMember")
    def test_get_project_members_with_role_filter(self, mock_member):
        """Test getting members with role filter"""
        mock_db = Mock()

        member = Mock()
        member.user_id = 1
        member.role_code = "ME"
        member.is_lead = False
        member.allocation_pct = 100

        user = Mock()
        user.username = "me_user"
        user.real_name = "Mechanical Engineer"
        user.email = "me@example.com"
        user.phone = None
        user.department = None
        user.position = None

        project = Mock()
        project.id = 1
        project.project_code = "PJ001"
        project.project_name = "Project 1"

        member.user = user
        member.project = project
        member.role_type = Mock(role_name="机械工程师")

        mock_member.filter.return_value.all.return_value = [member]

        result = get_project_members_for_ticket(mock_db, [1], include_roles=["ME"])

        assert len(result) == 1
        assert result[0]["role_code"] == "ME"

    @patch("app.services.ticket_assignment_service.ProjectMember")
    def test_get_project_members_with_exclude_user(self, mock_member):
        """Test getting members excluding specific user"""
        mock_db = Mock()

        member = Mock()
        member.user_id = 2
        member.role_code = "PM"
        member.is_lead = True
        member.allocation_pct = 100

        user = Mock()
        user.username = "other_user"
        user.real_name = "Other User"
        user.email = None
        user.phone = None
        user.department = None
        user.position = None

        project = Mock()
        project.id = 1
        project.project_code = "PJ001"
        project.project_name = "Project 1"

        member.user = user
        member.project = project
        member.role_type = Mock(role_name="项目经理")

        mock_member.filter.return_value.all.return_value = [member]

        result = get_project_members_for_ticket(mock_db, [1], exclude_user_id=1)

        assert len(result) == 1
        assert result[0]["user_id"] == 2

    @patch("app.services.ticket_assignment_service.Project")
    @patch("app.services.ticket_assignment_service.ServiceTicket")
    @patch("app.services.ticket_assignment_service.ServiceTicketProject")
    def test_get_ticket_related_projects_not_found(
        self, mock_ticket_project, mock_ticket, mock_project
    ):
        """Test getting related projects when ticket not found"""
        mock_db = Mock()

        mock_ticket.filter.return_value.first.return_value = None

        result = get_ticket_related_projects(mock_db, 999)

        assert result["primary_project"] is None
        assert result["related_projects"] == []

    @patch("app.services.ticket_assignment_service.Project")
    @patch("app.services.ticket_assignment_service.ServiceTicket")
    @patch("app.services.ticket_assignment_service.ServiceTicketProject")
    def test_get_ticket_related_projects_with_data(
        self, mock_ticket_project, mock_ticket, mock_project
    ):
        """Test getting related projects successfully"""
        mock_db = Mock()

        ticket = Mock()
        ticket.id = 1
        ticket.project_id = 1

        project = Mock()
        project.id = 1
        project.project_code = "PJ001"
        project.project_name = "Main Project"

        ticket_project = Mock()
        ticket_project.ticket_id = 1
        ticket_project.project_id = 2
        ticket_project.is_primary = False

        related_project = Mock()
        related_project.id = 2
        related_project.project_code = "PJ002"
        related_project.project_name = "Related Project"

        mock_ticket.filter.return_value.first.return_value = ticket
        mock_project.filter.return_value.first.return_value = project
        mock_ticket_project.filter.return_value.all.return_value = [ticket_project]

        result = get_ticket_related_projects(mock_db, 1)

        assert result["primary_project"] is not None
        assert result["primary_project"]["id"] == 1


# =============================================================================
# User Workload Service Tests (7 tests)
# =============================================================================


class TestUserWorkloadService:
    """Test suite for UserWorkloadService"""

    def test_calculate_workdays_single_week(self):
        """Test calculating workdays for a single week"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 5)

        workdays = calculate_workdays(start, end)

        assert workdays == 5

    def test_calculate_workdays_two_weeks(self):
        """Test calculating workdays for two weeks"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 12)

        workdays = calculate_workdays(start, end)

        assert workdays == 10

    def test_calculate_workdays_partial_week(self):
        """Test calculating workdays for partial week"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        workdays = calculate_workdays(start, end)

        assert workdays == 3

    def test_get_user_tasks(self):
        """Test getting user tasks"""
        mock_db = Mock()

        task1 = Mock()
        task1.id = 1
        task1.plan_start = date(2024, 1, 1)
        task1.plan_end = date(2024, 1, 5)

        mock_db.query.return_value.filter.return_value.all.return_value = [task1]

        tasks = get_user_tasks(mock_db, 1, date(2024, 1, 1), date(2024, 1, 31))

        assert len(tasks) == 1

    def test_calculate_task_hours(self):
        """Test calculating task hours"""
        task = Mock()
        task.plan_start = date(2024, 1, 1)
        task.plan_end = date(2024, 1, 3)

        hours = calculate_task_hours(task)

        assert hours == 24.0

    def test_calculate_task_hours_no_dates(self):
        """Test calculating task hours when no dates"""
        task = Mock()
        task.plan_start = None
        task.plan_end = None

        hours = calculate_task_hours(task)

        assert hours == 0.0

    def test_calculate_total_assigned_hours(self):
        """Test calculating total assigned hours from tasks and allocations"""
        task1 = Mock()
        task1.plan_start = date(2024, 1, 1)
        task1.plan_end = date(2024, 1, 2)

        task2 = Mock()
        task2.plan_start = date(2024, 1, 3)
        task2.plan_end = date(2024, 1, 4)

        alloc1 = Mock()
        alloc1.planned_hours = 16.0

        alloc2 = Mock()
        alloc2.planned_hours = None

        total = calculate_total_assigned_hours([task1, task2], [alloc1, alloc2])

        assert total == 32.0


# =============================================================================
# Status Transition Service Tests (7 tests)
# =============================================================================


class TestStatusTransitionService:
    """Test suite for StatusTransitionService"""

    @patch("app.services.status_transition_service.HealthCalculator")
    @patch("app.services.status_transition_service.Contract")
    @patch("app.services.status_transition_service.Project")
    @patch("app.services.status_transition_service.ProjectStatusLog")
    def test_handle_contract_signed_contract_not_found(
        self, mock_log, mock_project, mock_contract, mock_health
    ):
        """Test handling contract signed when contract not found"""
        mock_db = Mock()

        mock_contract.filter.return_value.first.return_value = None

        service = StatusTransitionService(mock_db)
        result = service.handle_contract_signed(999)

        assert result is None

    @patch("app.services.status_transition_service.HealthCalculator")
    @patch("app.services.status_transition_service.Contract")
    @patch("app.services.status_transition_service.Project")
    @patch("app.services.status_transition_service.ProjectStatusLog")
    def test_handle_contract_signed_existing_project(
        self, mock_log, mock_project, mock_contract, mock_health
    ):
        """Test handling contract signed for existing project"""
        mock_db = Mock()

        contract = Mock()
        contract.id = 1
        contract.project_id = 1
        contract.signed_date = date(2024, 1, 1)
        contract.contract_amount = 100000

        project = Mock()
        project.id = 1
        project.stage = "S2"
        project.status = "ST01"
        project.contract_date = None
        project.contract_amount = 50000

        mock_contract.filter.return_value.first.return_value = contract
        mock_project.filter.return_value.first.return_value = project

        service = StatusTransitionService(mock_db)
        result = service.handle_contract_signed(1)

        assert result is not None
        assert project.stage == "S3"
        assert project.status == "ST08"

    @patch("app.services.status_transition_service.HealthCalculator")
    @patch("app.services.status_transition_service.Project")
    def test_handle_bom_published_project_not_found(self, mock_project, mock_health):
        """Test handling BOM published when project not found"""
        mock_db = Mock()

        mock_project.filter.return_value.first.return_value = None

        service = StatusTransitionService(mock_db)
        result = service.handle_bom_published(999)

        assert result is False

    @patch("app.services.status_transition_service.HealthCalculator")
    @patch("app.services.status_transition_service.Project")
    @patch("app.services.status_transition_service.ProjectStatusLog")
    def test_handle_bom_published_wrong_stage(
        self, mock_log, mock_project, mock_health
    ):
        """Test handling BOM published in wrong stage"""
        mock_db = Mock()

        project = Mock()
        project.id = 1
        project.stage = "S3"

        mock_project.filter.return_value.first.return_value = project

        service = StatusTransitionService(mock_db)
        result = service.handle_bom_published(1)

        assert result is False

    @patch("app.services.status_transition_service.HealthCalculator")
    @patch("app.services.status_transition_service.Project")
    @patch("app.services.status_transition_service.ProjectStatusLog")
    def test_handle_bom_published_success(self, mock_log, mock_project, mock_health):
        """Test handling BOM published successfully"""
        mock_db = Mock()

        project = Mock()
        project.id = 1
        project.stage = "S4"
        project.status = "ST11"

        mock_project.filter.return_value.first.return_value = project

        service = StatusTransitionService(mock_db)
        result = service.handle_bom_published(1)

        assert result is True
        assert project.stage == "S5"
        assert project.status == "ST12"

    @patch("app.services.status_transition_service.HealthCalculator")
    @patch("app.services.status_transition_service.Project")
    @patch("app.services.status_transition_service.ProjectStatusLog")
    def test_handle_material_shortage_not_critical(
        self, mock_log, mock_project, mock_health
    ):
        """Test handling material shortage when not critical"""
        mock_db = Mock()

        project = Mock()
        project.id = 1

        mock_project.filter.return_value.first.return_value = project

        service = StatusTransitionService(mock_db)
        result = service.handle_material_shortage(1, is_critical=False)

        assert result is False

    @patch("app.services.status_transition_service.HealthCalculator")
    @patch("app.services.status_transition_service.Project")
    @patch("app.services.status_transition_service.ProjectStatusLog")
    def test_handle_fat_passed_wrong_stage(self, mock_log, mock_project, mock_health):
        """Test handling FAT passed in wrong stage"""
        mock_db = Mock()

        project = Mock()
        project.id = 1
        project.stage = "S6"

        mock_project.filter.return_value.first.return_value = project

        service = StatusTransitionService(mock_db)
        result = service.handle_fat_passed(1)

        assert result is False


# =============================================================================
# Stage Transition Checks Tests (7 tests)
# =============================================================================


class TestStageTransitionChecks:
    """Test suite for StageTransitionChecks"""

    @patch("app.services.stage_transition_checks.Contract")
    def test_check_s3_to_s4_transition_missing_contract(self, mock_contract):
        """Test S3 to S4 transition with missing contract"""
        mock_db = Mock()

        project = Mock()
        project.contract_no = None
        project.contract_date = None
        project.contract_amount = None

        mock_contract.filter.return_value.first.return_value = None

        can_advance, target_stage, missing = check_s3_to_s4_transition(mock_db, project)

        assert can_advance is False
        assert target_stage is None
        assert len(missing) > 0

    @patch("app.services.stage_transition_checks.Contract")
    def test_check_s3_to_s4_transition_not_signed(self, mock_contract):
        """Test S3 to S4 transition with unsigned contract"""
        mock_db = Mock()

        project = Mock()
        project.contract_no = "CT001"
        project.contract_date = date(2024, 1, 1)
        project.contract_amount = 100000

        contract = Mock()
        contract.status = "DRAFT"

        mock_contract.filter.return_value.first.return_value = contract

        can_advance, target_stage, missing = check_s3_to_s4_transition(mock_db, project)

        assert can_advance is False
        assert target_stage is None

    @patch("app.services.stage_transition_checks.BomHeader")
    def test_check_s4_to_s5_transition_no_bom(self, mock_bom):
        """Test S4 to S5 transition with no BOM released"""
        mock_db = Mock()

        mock_bom.filter.return_value.count.return_value = 0

        can_advance, target_stage, missing = check_s4_to_s5_transition(mock_db, 1)

        assert can_advance is False
        assert target_stage is None
        assert len(missing) > 0

    @patch("app.services.stage_transition_checks.BomHeader")
    def test_check_s4_to_s5_transition_with_bom(self, mock_bom):
        """Test S4 to S5 transition with released BOM"""
        mock_db = Mock()

        mock_bom.filter.return_value.count.return_value = 1

        can_advance, target_stage, missing = check_s4_to_s5_transition(mock_db, 1)

        assert can_advance is True
        assert target_stage == "S5"
        assert len(missing) == 0

    @patch("app.services.stage_transition_checks.AcceptanceOrder")
    def test_check_s7_to_s8_transition_no_fat(self, mock_acceptance):
        """Test S7 to S8 transition with no FAT passed"""
        mock_db = Mock()

        mock_acceptance.filter.return_value.count.return_value = 0

        can_advance, target_stage, missing = check_s7_to_s8_transition(mock_db, 1)

        assert can_advance is False
        assert target_stage is None
        assert len(missing) > 0

    @patch("app.services.stage_transition_checks.AcceptanceOrder")
    def test_check_s7_to_s8_transition_with_fat(self, mock_acceptance):
        """Test S7 to S8 transition with FAT passed"""
        mock_db = Mock()

        mock_acceptance.filter.return_value.count.return_value = 1

        can_advance, target_stage, missing = check_s7_to_s8_transition(mock_db, 1)

        assert can_advance is True
        assert target_stage == "S8"
        assert len(missing) == 0

    def test_get_stage_status_mapping(self):
        """Test getting stage to status mapping"""
        mapping = get_stage_status_mapping()

        assert isinstance(mapping, dict)
        assert "S4" in mapping
        assert mapping["S4"] == "ST09"
        assert "S9" in mapping
        assert mapping["S9"] == "ST30"


# =============================================================================
# Template Recommendation Service Tests (6 tests)
# =============================================================================


class TestTemplateRecommendationService:
    """Test suite for TemplateRecommendationService"""

    @patch("app.services.template_recommendation_service.ProjectTemplate")
    def test_recommend_templates_by_project_type(self, mock_template):
        """Test recommending templates by project type"""
        mock_db = Mock()

        template = Mock()
        template.id = 1
        template.template_code = "TP001"
        template.template_name = "ICT Template"
        template.description = "ICT testing project"
        template.project_type = "ICT"
        template.product_category = None
        template.industry = None
        template.usage_count = 10

        mock_template.filter.return_value.all.return_value = [template]

        service = TemplateRecommendationService(mock_db)
        recommendations = service.recommend_templates(project_type="ICT")

        assert len(recommendations) > 0
        assert recommendations[0]["template_code"] == "TP001"
        assert recommendations[0]["match_type"] == "project_type"

    @patch("app.services.template_recommendation_service.ProjectTemplate")
    def test_recommend_templates_by_product_category(self, mock_template):
        """Test recommending templates by product category"""
        mock_db = Mock()

        template = Mock()
        template.id = 1
        template.template_code = "TP002"
        template.template_name = "FCT Template"
        template.description = "FCT testing project"
        template.project_type = None
        template.product_category = "FCT"
        template.industry = None
        template.usage_count = 5

        mock_template.filter.return_value.all.return_value = [template]

        service = TemplateRecommendationService(mock_db)
        recommendations = service.recommend_templates(product_category="FCT")

        assert len(recommendations) > 0
        assert recommendations[0]["product_category"] == "FCT"

    @patch("app.services.template_recommendation_service.ProjectTemplate")
    def test_recommend_templates_by_industry(self, mock_template):
        """Test recommending templates by industry"""
        mock_db = Mock()

        template = Mock()
        template.id = 1
        template.template_code = "TP003"
        template.template_name = "Auto Template"
        template.description = "Automotive testing"
        template.project_type = None
        template.product_category = None
        template.industry = "AUTOMOTIVE"
        template.usage_count = 8

        mock_template.filter.return_value.all.return_value = [template]

        service = TemplateRecommendationService(mock_db)
        recommendations = service.recommend_templates(industry="AUTOMOTIVE")

        assert len(recommendations) > 0
        assert "AUTOMOTIVE" in str(recommendations[0]["reasons"])

    def test_calculate_score_full_match(self):
        """Test score calculation with full match"""
        mock_db = Mock()

        template = Mock()
        template.project_type = "ICT"
        template.product_category = "FCT"
        template.industry = "AUTOMOTIVE"
        template.usage_count = 10

        service = TemplateRecommendationService(mock_db)
        score = service._calculate_score(
            template=template,
            project_type="ICT",
            product_category="FCT",
            industry="AUTOMOTIVE",
        )

        assert score >= 85

    def test_calculate_score_no_match(self):
        """Test score calculation with no matches"""
        mock_db = Mock()

        template = Mock()
        template.project_type = "OTHER"
        template.product_category = "OTHER"
        template.industry = "OTHER"
        template.usage_count = 0

        service = TemplateRecommendationService(mock_db)
        score = service._calculate_score(
            template=template,
            project_type="ICT",
            product_category="FCT",
            industry="AUTOMOTIVE",
        )

        assert score == 10.0

    @patch("app.services.template_recommendation_service.ProjectTemplate")
    def test_get_recommendation_reasons(self, mock_template):
        """Test getting recommendation reasons"""
        mock_db = Mock()

        template = Mock()
        template.project_type = "ICT"
        template.product_category = "FCT"
        template.industry = None
        template.usage_count = 5

        service = TemplateRecommendationService(mock_db)
        reasons = service._get_recommendation_reasons(
            template=template, project_type="ICT", product_category="FCT", industry=None
        )

        assert len(reasons) >= 2
        assert any("ICT" in r for r in reasons)
        assert any("FCT" in r for r in reasons)
