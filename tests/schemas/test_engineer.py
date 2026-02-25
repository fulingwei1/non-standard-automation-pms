# -*- coding: utf-8 -*-
"""Tests for app/schemas/engineer.py"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.engineer import (
    TaskStatsResponse,
    MyProjectResponse,
    MyProjectListResponse,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    ProgressUpdateRequest,
    ProgressUpdateResponse,
    TaskCompleteRequest,
    TaskCompleteResponse,
    DelayReportRequest,
    DelayReportResponse,
    TaskApprovalRequest,
    TaskRejectionRequest,
    TaskApprovalResponse,
    MemberProgressSummary,
    DepartmentProgressSummary,
    TaskListResponse,
)


class TestTaskStatsResponse:
    def test_defaults(self):
        t = TaskStatsResponse()
        assert t.total_tasks == 0
        assert t.overdue_tasks == 0

    def test_with_data(self):
        t = TaskStatsResponse(total_tasks=10, completed_tasks=5, overdue_tasks=2)
        assert t.completed_tasks == 5


class TestMyProjectResponse:
    def test_valid(self):
        p = MyProjectResponse(
            project_id=1, project_code="P001", project_name="项目A",
            stage="S3", status="IN_PROGRESS", health="GREEN",
            task_stats=TaskStatsResponse(),
        )
        assert p.progress_pct == 0
        assert p.my_allocation_pct == 100

    def test_missing(self):
        with pytest.raises(ValidationError):
            MyProjectResponse()


class TestTaskCreateRequest:
    def test_valid(self):
        t = TaskCreateRequest(project_id=1, title="设计任务")
        assert t.task_importance == "GENERAL"
        assert t.priority == "MEDIUM"
        assert t.tags == []

    def test_empty_title(self):
        with pytest.raises(ValidationError):
            TaskCreateRequest(project_id=1, title="")

    def test_long_title(self):
        with pytest.raises(ValidationError):
            TaskCreateRequest(project_id=1, title="x" * 201)

    def test_with_dates(self):
        t = TaskCreateRequest(
            project_id=1, title="任务",
            plan_start_date=date(2024, 1, 1),
            plan_end_date=date(2024, 3, 1),
            estimated_hours=Decimal("40"),
            priority="HIGH",
        )
        assert t.estimated_hours == Decimal("40")

    def test_missing_project(self):
        with pytest.raises(ValidationError):
            TaskCreateRequest(title="任务")


class TestTaskUpdateRequest:
    def test_all_none(self):
        t = TaskUpdateRequest()
        assert t.title is None

    def test_partial(self):
        t = TaskUpdateRequest(title="新标题", priority="URGENT")
        assert t.priority == "URGENT"


class TestTaskResponse:
    def test_valid(self):
        now = datetime.now()
        t = TaskResponse(
            id=1, task_code="T001", title="任务", task_type="DESIGN",
            assignee_id=1, status="IN_PROGRESS", priority="MEDIUM",
            created_at=now, updated_at=now,
        )
        assert t.progress == 0
        assert t.is_urgent is False
        assert t.approval_required is False

    def test_missing(self):
        with pytest.raises(ValidationError):
            TaskResponse()


class TestProgressUpdateRequest:
    def test_valid(self):
        p = ProgressUpdateRequest(progress=50)
        assert p.actual_hours is None

    def test_with_hours(self):
        p = ProgressUpdateRequest(progress=80, actual_hours=Decimal("16"))
        assert p.actual_hours == Decimal("16")

    def test_negative_hours(self):
        with pytest.raises(ValidationError):
            ProgressUpdateRequest(progress=50, actual_hours=Decimal("-1"))

    def test_missing_progress(self):
        with pytest.raises(ValidationError):
            ProgressUpdateRequest()


class TestTaskCompleteRequest:
    def test_valid(self):
        r = TaskCompleteRequest(completion_note="已完成")
        assert r.skip_proof_validation is False

    def test_empty_note(self):
        with pytest.raises(ValidationError):
            TaskCompleteRequest(completion_note="")

    def test_missing(self):
        with pytest.raises(ValidationError):
            TaskCompleteRequest()


class TestDelayReportRequest:
    def test_valid(self):
        r = DelayReportRequest(
            delay_reason="供应商交期延误导致物料不足",
            delay_responsibility="供应商",
            delay_impact_scope="PROJECT",
            schedule_impact_days=5,
            new_completion_date=date(2024, 7, 15),
        )
        assert r.cost_impact is None

    def test_short_reason(self):
        with pytest.raises(ValidationError):
            DelayReportRequest(
                delay_reason="短",
                delay_responsibility="A",
                delay_impact_scope="LOCAL",
                schedule_impact_days=1,
                new_completion_date=date(2024, 7, 15),
            )

    def test_zero_days(self):
        with pytest.raises(ValidationError):
            DelayReportRequest(
                delay_reason="原因原因原因原因原因",
                delay_responsibility="A",
                delay_impact_scope="LOCAL",
                schedule_impact_days=0,
                new_completion_date=date(2024, 7, 15),
            )

    def test_missing(self):
        with pytest.raises(ValidationError):
            DelayReportRequest()


class TestTaskRejectionRequest:
    def test_valid(self):
        r = TaskRejectionRequest(reason="任务描述不清楚需要补充")
        assert r.reason == "任务描述不清楚需要补充"

    def test_short_reason(self):
        with pytest.raises(ValidationError):
            TaskRejectionRequest(reason="短")

    def test_missing(self):
        with pytest.raises(ValidationError):
            TaskRejectionRequest()


class TestMemberProgressSummary:
    def test_valid(self):
        m = MemberProgressSummary(name="张三", total_tasks=10, completed_tasks=5)
        assert m.in_progress_tasks == 0
        assert m.progress_pct == 0


class TestTaskListResponse:
    def test_defaults(self):
        r = TaskListResponse(items=[], total=0)
        assert r.page == 1
        assert r.pages == 1
