# -*- coding: utf-8 -*-
"""
资源计划服务 N2 深度覆盖测试
覆盖: get_project_resource_plans, create_resource_plan, assign_employee (冲突/强制),
      release_employee, check_assignment_conflict, detect_employee_conflicts,
      detect_project_conflicts, ResourcePlanningService 全部方法
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.resource_plan_service import ResourcePlanService, ResourcePlanningService


# ======================= get_project_resource_plans =======================

class TestGetProjectResourcePlans:
    def test_returns_all_plans_without_stage_filter(self):
        db = MagicMock()
        plans = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = plans
        result = ResourcePlanService.get_project_resource_plans(db, project_id=1)
        assert result == plans

    def test_returns_filtered_by_stage_code(self):
        db = MagicMock()
        plans = [MagicMock()]
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.all.return_value = plans
        db.query.return_value = q
        result = ResourcePlanService.get_project_resource_plans(db, project_id=1, stage_code="DESIGN")
        assert result == plans


# ======================= create_resource_plan =======================

class TestCreateResourcePlan:
    @patch("app.services.resource_plan_service.save_obj")
    def test_creates_plan(self, mock_save):
        db = MagicMock()
        plan_in = MagicMock()
        plan_in.model_dump.return_value = {
            "stage_code": "DESIGN",
            "role_code": "PM",
            "headcount": 1,
            "planned_start": date(2026, 1, 1),
            "planned_end": date(2026, 3, 31),
            "allocation_pct": Decimal("100"),
            "assignment_status": "PENDING",
        }
        result = ResourcePlanService.create_resource_plan(db, project_id=1, plan_in=plan_in)
        mock_save.assert_called_once()
        assert result.project_id == 1


# ======================= assign_employee =======================

class TestAssignEmployee:
    def test_raises_when_plan_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="资源计划不存在"):
            ResourcePlanService.assign_employee(db, plan_id=99, employee_id=1)

    def test_assigns_when_no_conflict(self):
        db = MagicMock()
        plan = MagicMock()
        plan.project_id = 1
        plan.planned_start = date(2026, 1, 1)
        plan.planned_end = date(2026, 3, 31)
        plan.allocation_pct = Decimal("50")
        db.query.return_value.filter.return_value.first.return_value = plan

        with patch.object(ResourcePlanService, "check_assignment_conflict", return_value=None):
            result_plan, conflict = ResourcePlanService.assign_employee(db, plan_id=1, employee_id=5)

        assert result_plan.assigned_employee_id == 5
        assert result_plan.assignment_status == "ASSIGNED"
        assert conflict is None

    def test_conflict_without_force_marks_conflict(self):
        db = MagicMock()
        plan = MagicMock()
        plan.project_id = 1
        plan.planned_start = date(2026, 1, 1)
        plan.planned_end = date(2026, 3, 31)
        plan.allocation_pct = Decimal("80")
        db.query.return_value.filter.return_value.first.return_value = plan

        mock_conflict = MagicMock()
        with patch.object(ResourcePlanService, "check_assignment_conflict", return_value=mock_conflict):
            result_plan, conflict = ResourcePlanService.assign_employee(
                db, plan_id=1, employee_id=5, force=False
            )

        assert result_plan.assignment_status == "CONFLICT"
        assert conflict is mock_conflict

    def test_force_assigns_despite_conflict(self):
        db = MagicMock()
        plan = MagicMock()
        plan.project_id = 1
        plan.planned_start = date(2026, 1, 1)
        plan.planned_end = date(2026, 3, 31)
        plan.allocation_pct = Decimal("80")
        db.query.return_value.filter.return_value.first.return_value = plan

        mock_conflict = MagicMock()
        with patch.object(ResourcePlanService, "check_assignment_conflict", return_value=mock_conflict):
            result_plan, conflict = ResourcePlanService.assign_employee(
                db, plan_id=1, employee_id=5, force=True
            )

        assert result_plan.assignment_status == "ASSIGNED"
        assert conflict is None


# ======================= release_employee =======================

class TestReleaseEmployee:
    def test_raises_when_plan_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="资源计划不存在"):
            ResourcePlanService.release_employee(db, plan_id=99)

    def test_releases_assignment(self):
        db = MagicMock()
        plan = MagicMock()
        plan.assigned_employee_id = 5
        plan.assignment_status = "ASSIGNED"
        db.query.return_value.filter.return_value.first.return_value = plan

        result = ResourcePlanService.release_employee(db, plan_id=1)
        assert plan.assigned_employee_id is None
        assert plan.assignment_status == "RELEASED"
        db.commit.assert_called_once()


# ======================= check_assignment_conflict =======================

class TestCheckAssignmentConflict:
    def test_no_conflict_when_no_dates(self):
        db = MagicMock()
        result = ResourcePlanService.check_assignment_conflict(
            db, employee_id=1, project_id=1,
            start_date=None, end_date=None,
            allocation_pct=Decimal("50")
        )
        assert result is None

    def test_no_conflict_when_no_existing_assignments(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = ResourcePlanService.check_assignment_conflict(
            db, employee_id=1, project_id=1,
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31),
            allocation_pct=Decimal("50")
        )
        assert result is None

    def test_conflict_detected_when_over_100pct(self):
        db = MagicMock()
        existing = MagicMock()
        existing.project_id = 2  # different project
        existing.planned_start = date(2026, 1, 15)
        existing.planned_end = date(2026, 2, 28)
        existing.allocation_pct = Decimal("70")
        existing.stage_code = "DESIGN"
        db.query.return_value.filter.return_value.all.return_value = [existing]

        # Employee lookup
        employee = MagicMock()
        employee.id = 1
        employee.username = "Alice"
        project = MagicMock()
        project.id = 2
        project.project_name = "Project B"

        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.all.return_value = [existing]
            elif call_count[0] == 2:
                q.filter.return_value.first.return_value = employee
            else:
                q.filter.return_value.first.return_value = project
            return q
        db.query.side_effect = query_side

        result = ResourcePlanService.check_assignment_conflict(
            db, employee_id=1, project_id=1,
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31),
            allocation_pct=Decimal("60")  # 60 + 70 = 130 > 100
        )
        assert result is not None
        assert result.total_allocation == Decimal("130")

    def test_no_conflict_when_overlap_under_100pct(self):
        db = MagicMock()
        existing = MagicMock()
        existing.project_id = 2
        existing.planned_start = date(2026, 1, 15)
        existing.planned_end = date(2026, 2, 28)
        existing.allocation_pct = Decimal("30")
        existing.stage_code = "DESIGN"
        db.query.return_value.filter.return_value.all.return_value = [existing]

        result = ResourcePlanService.check_assignment_conflict(
            db, employee_id=1, project_id=1,
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31),
            allocation_pct=Decimal("40")  # 40 + 30 = 70 <= 100
        )
        assert result is None


# ======================= detect_employee_conflicts =======================

class TestDetectEmployeeConflicts:
    def test_no_assignments_returns_empty(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = ResourcePlanService.detect_employee_conflicts(db, employee_id=1)
        assert result == []

    def test_single_assignment_no_conflict(self):
        db = MagicMock()
        a1 = MagicMock()
        a1.planned_start = date(2026, 1, 1)
        a1.planned_end = date(2026, 3, 31)
        a1.allocation_pct = Decimal("50")
        db.query.return_value.filter.return_value.all.return_value = [a1]
        result = ResourcePlanService.detect_employee_conflicts(db, employee_id=1)
        assert result == []

    def test_two_overlapping_assignments_over_100_gives_conflict(self):
        db = MagicMock()
        a1 = MagicMock()
        a1.planned_start = date(2026, 1, 1)
        a1.planned_end = date(2026, 3, 31)
        a1.allocation_pct = Decimal("70")
        a1.project_id = 1
        a1.stage_code = "DESIGN"

        a2 = MagicMock()
        a2.planned_start = date(2026, 2, 1)
        a2.planned_end = date(2026, 4, 30)
        a2.allocation_pct = Decimal("60")
        a2.project_id = 2
        a2.stage_code = "BUILD"

        employee = MagicMock()
        employee.id = 1
        employee.username = "Bob"

        project1 = MagicMock()
        project1.id = 1
        project1.project_name = "Project A"

        project2 = MagicMock()
        project2.id = 2
        project2.project_name = "Project B"

        call_count = [0]
        def q_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.all.return_value = [a1, a2]
            elif call_count[0] == 2:
                q.filter.return_value.first.return_value = employee
            elif call_count[0] == 3:
                q.filter.return_value.first.return_value = project1
            else:
                q.filter.return_value.first.return_value = project2
            return q
        db.query.side_effect = q_side

        result = ResourcePlanService.detect_employee_conflicts(db, employee_id=1)
        assert len(result) >= 1
        assert result[0].severity in ("LOW", "MEDIUM", "HIGH")


# ======================= detect_project_conflicts =======================

class TestDetectProjectConflicts:
    def test_no_plans_returns_empty(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = ResourcePlanService.detect_project_conflicts(db, project_id=1)
        assert result == []

    def test_with_no_employee_conflicts(self):
        db = MagicMock()
        plan = MagicMock()
        plan.assigned_employee_id = 5
        db.query.return_value.filter.return_value.all.return_value = [plan]

        with patch.object(ResourcePlanService, "detect_employee_conflicts", return_value=[]):
            result = ResourcePlanService.detect_project_conflicts(db, project_id=1)
        assert result == []


# ======================= ResourcePlanningService =======================

class TestResourcePlanningService:
    def setup_method(self):
        self.db = MagicMock()
        self.service = ResourcePlanningService(self.db)

    def test_analyze_user_workload_user_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.analyze_user_workload(user_id=999)
        assert "error" in result
        assert result["error"] == "用户不存在"

    def test_analyze_user_workload_with_tasks_and_timesheets(self):
        user = MagicMock()
        user.id = 1
        user.real_name = "Alice"
        user.username = "alice"

        task1 = MagicMock()
        task1.project_id = 10
        task1.estimated_hours = Decimal("40")
        task1.plan_start_date = date.today()
        task1.plan_end_date = date.today() + timedelta(days=5)

        ts1 = MagicMock()
        ts1.hours = Decimal("8")
        ts1.work_date = date.today()

        project = MagicMock()
        project.project_code = "P001"
        project.project_name = "Test Project"

        call_count = [0]
        def q_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:  # User
                q.filter.return_value.first.return_value = user
            elif call_count[0] == 2:  # Tasks
                q.filter.return_value.all.return_value = [task1]
            elif call_count[0] == 3:  # Timesheets
                q.filter.return_value.all.return_value = [ts1]
            else:  # Project
                q.filter.return_value.first.return_value = project
            return q
        self.db.query.side_effect = q_side

        result = self.service.analyze_user_workload(user_id=1)
        assert result["user_id"] == 1
        assert result["assigned_hours"] == 40.0
        assert result["recorded_hours"] == 8.0
        assert "load_rate" in result

    def test_analyze_user_workload_overloaded(self):
        """负载率超过110%时标记为过载"""
        user = MagicMock()
        user.id = 1
        user.real_name = "Bob"
        user.username = "bob"

        # Short 2-day period → standard_hours = 2*8 = 16
        # assigned_hours = 200 → load_rate >> 110%
        task = MagicMock()
        task.project_id = 1
        task.estimated_hours = Decimal("200")
        task.plan_start_date = date.today()
        task.plan_end_date = date.today() + timedelta(days=1)

        project = MagicMock()
        project.project_code = "P001"
        project.project_name = "Heavy Project"

        call_count = [0]
        def q_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = user
            elif call_count[0] == 2:
                q.filter.return_value.all.return_value = [task]
            elif call_count[0] == 3:
                q.filter.return_value.all.return_value = []
            else:
                q.filter.return_value.first.return_value = project
            return q
        self.db.query.side_effect = q_side

        result = self.service.analyze_user_workload(
            user_id=1,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1)
        )
        assert result["is_overloaded"] is True

    def test_predict_project_resource_needs_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.predict_project_resource_needs(project_id=999)
        assert "error" in result

    def test_predict_project_resource_needs_with_tasks(self):
        project = MagicMock()
        project.project_code = "P001"
        project.project_name = "My Project"

        user = MagicMock()
        user.id = 5
        user.real_name = "Charlie"
        user.username = "charlie"

        task = MagicMock()
        task.assignee_id = 5
        task.estimated_hours = Decimal("20")
        task.id = 1
        task.task_name = "Design Task"
        task.plan_start_date = date.today()
        task.plan_end_date = date.today() + timedelta(days=5)

        call_count = [0]
        def q_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = project
            elif call_count[0] == 2:
                q.filter.return_value.all.return_value = [task]
            else:
                q.filter.return_value.first.return_value = user
            return q
        self.db.query.side_effect = q_side

        result = self.service.predict_project_resource_needs(project_id=1)
        assert result["total_hours"] == 20.0
        assert result["total_personnel"] == 1

    def test_get_department_workload_stats_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.service.get_department_workload_stats(department_id=999)
        assert "error" in result

    def test_get_department_workload_stats_no_users(self):
        dept = MagicMock()
        dept.name = "Engineering"

        call_count = [0]
        def q_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = dept
            else:
                q.filter.return_value.all.return_value = []
            return q
        self.db.query.side_effect = q_side

        result = self.service.get_department_workload_stats(department_id=1)
        assert result["total_users"] == 0
        assert result["total_hours"] == 0


# ======================= _calculate_work_days =======================

class TestCalculateWorkDays:
    def setup_method(self):
        self.service = ResourcePlanningService(MagicMock())

    def test_full_work_week_5_days(self):
        # Monday to Friday
        monday = date(2026, 2, 16)
        friday = date(2026, 2, 20)
        result = self.service._calculate_work_days(monday, friday)
        assert result == 5

    def test_includes_only_weekdays(self):
        # Full week Mon-Sun should give 5 work days
        monday = date(2026, 2, 16)
        sunday = date(2026, 2, 22)
        result = self.service._calculate_work_days(monday, sunday)
        assert result == 5

    def test_single_weekday(self):
        wednesday = date(2026, 2, 18)
        result = self.service._calculate_work_days(wednesday, wednesday)
        assert result == 1

    def test_single_weekend_day(self):
        saturday = date(2026, 2, 21)
        result = self.service._calculate_work_days(saturday, saturday)
        assert result == 0

    def test_two_weeks_gives_10_work_days(self):
        start = date(2026, 2, 16)  # Monday
        end = date(2026, 2, 27)    # Friday 2 weeks later
        result = self.service._calculate_work_days(start, end)
        assert result == 10

    def test_same_day_start_end(self):
        monday = date(2026, 2, 16)
        result = self.service._calculate_work_days(monday, monday)
        assert result == 1
