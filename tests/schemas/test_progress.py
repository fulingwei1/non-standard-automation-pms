# -*- coding: utf-8 -*-
"""Tests for app/schemas/progress.py"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from pydantic import ValidationError

from app.schemas.progress import (
    WbsTemplateCreate,
    WbsTemplateUpdate,
    WbsTemplateResponse,
    WbsTemplateTaskCreate,
    WbsTemplateTaskUpdate,
    TaskCreate,
    TaskUpdate,
    TaskProgressUpdate,
    TaskResponse,
    InitWbsRequest,
    ProgressReportCreate,
    ProgressReportUpdate,
    ProgressSummaryResponse,
    GanttTaskItem,
    GanttDataResponse,
    TaskDependencyCreate,
    TaskAssigneeUpdate,
    BatchTaskProgressUpdate,
    BatchTaskAssigneeUpdate,
    BaselineCreate,
    DelayReasonItem,
    DelayReasonsResponse,
    ProgressBoardColumn,
)


class TestWbsTemplateCreate:
    def test_valid(self):
        w = WbsTemplateCreate(template_code="WBS001", template_name="标准模板")
        assert w.version_no == "V1"
        assert w.is_active is True

    def test_missing(self):
        with pytest.raises(ValidationError):
            WbsTemplateCreate()

    def test_long_code(self):
        with pytest.raises(ValidationError):
            WbsTemplateCreate(template_code="x" * 21, template_name="T")


class TestWbsTemplateTaskCreate:
    def test_valid(self):
        t = WbsTemplateTaskCreate(task_name="机械设计")
        assert t.weight == Decimal("1.00")
        assert t.stage is None

    def test_with_stage(self):
        t = WbsTemplateTaskCreate(task_name="T", stage="S3", plan_days=10)
        assert t.plan_days == 10

    def test_missing(self):
        with pytest.raises(ValidationError):
            WbsTemplateTaskCreate()


class TestTaskCreate:
    def test_valid(self):
        t = TaskCreate(task_name="电气设计")
        assert t.weight == Decimal("1.00")
        assert t.machine_id is None

    def test_with_dates(self):
        t = TaskCreate(
            task_name="T",
            plan_start=date(2024, 1, 1),
            plan_end=date(2024, 3, 1),
            owner_id=1,
        )
        assert t.owner_id == 1

    def test_missing(self):
        with pytest.raises(ValidationError):
            TaskCreate()


class TestTaskUpdate:
    def test_all_none(self):
        t = TaskUpdate()
        assert t.task_name is None

    def test_progress_bounds(self):
        t = TaskUpdate(progress_percent=0)
        assert t.progress_percent == 0
        t = TaskUpdate(progress_percent=100)
        assert t.progress_percent == 100

    def test_progress_too_high(self):
        with pytest.raises(ValidationError):
            TaskUpdate(progress_percent=101)

    def test_progress_negative(self):
        with pytest.raises(ValidationError):
            TaskUpdate(progress_percent=-1)


class TestTaskProgressUpdate:
    def test_valid(self):
        t = TaskProgressUpdate(progress_percent=50)
        assert t.update_note is None

    def test_bounds(self):
        TaskProgressUpdate(progress_percent=0)
        TaskProgressUpdate(progress_percent=100)

    def test_out_of_bounds(self):
        with pytest.raises(ValidationError):
            TaskProgressUpdate(progress_percent=101)
        with pytest.raises(ValidationError):
            TaskProgressUpdate(progress_percent=-1)

    def test_missing(self):
        with pytest.raises(ValidationError):
            TaskProgressUpdate()


class TestInitWbsRequest:
    def test_valid(self):
        r = InitWbsRequest(template_id=1)
        assert r.assign_owners is False
        assert r.start_date is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            InitWbsRequest()


class TestProgressReportCreate:
    def test_valid(self):
        r = ProgressReportCreate(
            report_type="daily", report_date=date(2024, 6, 1),
            content="今日完成机械设计评审",
        )
        assert r.issues is None

    def test_missing(self):
        with pytest.raises(ValidationError):
            ProgressReportCreate()


class TestProgressSummaryResponse:
    def test_valid(self):
        s = ProgressSummaryResponse(
            project_id=1, project_name="P1",
            overall_progress=50.0,
            task_count=20, completed_count=10,
            in_progress_count=8, blocked_count=2,
            overdue_count=1,
        )
        assert s.stage_progress == {}

    def test_missing(self):
        with pytest.raises(ValidationError):
            ProgressSummaryResponse()


class TestGanttTaskItem:
    def test_valid(self):
        g = GanttTaskItem(
            id=1, name="任务1",
            start=date(2024, 1, 1), end=date(2024, 2, 1),
            progress=50, status="IN_PROGRESS",
        )
        assert g.dependencies == []

    def test_missing(self):
        with pytest.raises(ValidationError):
            GanttTaskItem()


class TestTaskDependencyCreate:
    def test_valid(self):
        d = TaskDependencyCreate(depends_on_task_id=1)
        assert d.dependency_type == "FS"
        assert d.lag_days == 0

    def test_custom_type(self):
        d = TaskDependencyCreate(depends_on_task_id=1, dependency_type="SS", lag_days=2)
        assert d.dependency_type == "SS"


class TestBatchTaskProgressUpdate:
    def test_valid(self):
        b = BatchTaskProgressUpdate(task_ids=[1, 2, 3], progress_percent=80)
        assert b.update_note is None

    def test_out_of_range(self):
        with pytest.raises(ValidationError):
            BatchTaskProgressUpdate(task_ids=[1], progress_percent=101)

    def test_missing(self):
        with pytest.raises(ValidationError):
            BatchTaskProgressUpdate()


class TestBaselineCreate:
    def test_defaults(self):
        b = BaselineCreate()
        assert b.baseline_no is None
        assert b.description is None

    def test_with_data(self):
        b = BaselineCreate(baseline_no="BL1", description="Initial baseline")
        assert b.baseline_no == "BL1"


class TestDelayReasonItem:
    def test_valid(self):
        d = DelayReasonItem(reason="供应商延期", count=5, percentage=25.0)
        assert d.count == 5
