# -*- coding: utf-8 -*-
"""第二十九批 - user_workload_service.py 单元测试（用户负荷统计服务）"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.user_workload_service")

from app.services.user_workload_service import (
    calculate_workdays,
    get_user_tasks,
    get_user_allocations,
    calculate_task_hours,
    calculate_total_assigned_hours,
    calculate_total_actual_hours,
    build_project_workload,
    build_task_list,
    build_daily_load,
)


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_task(
    task_id=1,
    project_id=10,
    owner_id=1,
    task_name="测试任务",
    plan_start=None,
    plan_end=None,
    status="IN_PROGRESS",
    estimated_hours=None,
    progress_percent=0,
):
    plan_start = plan_start or date(2025, 1, 1)
    plan_end = plan_end or date(2025, 1, 5)
    t = MagicMock()
    t.id = task_id
    t.project_id = project_id
    t.owner_id = owner_id
    t.task_name = task_name
    t.plan_start = plan_start
    t.plan_end = plan_end
    t.status = status
    t.estimated_hours = estimated_hours
    t.progress_percent = progress_percent
    proj = MagicMock()
    proj.id = project_id
    proj.project_code = f"PROJ-{project_id:03d}"
    proj.project_name = f"项目{project_id}"
    t.project = proj
    return t


def _make_allocation(
    alloc_id=1,
    resource_id=1,
    planned_hours=40.0,
    actual_hours=32.0,
    start_date=None,
    end_date=None,
    status="ACTIVE",
):
    a = MagicMock()
    a.id = alloc_id
    a.resource_id = resource_id
    a.planned_hours = planned_hours
    a.actual_hours = actual_hours
    a.start_date = start_date or date(2025, 1, 1)
    a.end_date = end_date or date(2025, 1, 31)
    a.status = status
    return a


# ─── 测试：calculate_workdays ─────────────────────────────────────────────────

class TestCalculateWorkdays:
    """测试工作日计算"""

    def test_single_weekday(self):
        # 2025-01-06 是周一
        assert calculate_workdays(date(2025, 1, 6), date(2025, 1, 6)) == 1

    def test_one_full_week(self):
        # 2025-01-06 (Mon) to 2025-01-12 (Sun) = 5 weekdays + 2 weekend
        result = calculate_workdays(date(2025, 1, 6), date(2025, 1, 12))
        assert result == 5

    def test_two_full_weeks(self):
        result = calculate_workdays(date(2025, 1, 6), date(2025, 1, 19))
        assert result == 10

    def test_same_start_end(self):
        d = date(2025, 3, 15)
        result = calculate_workdays(d, d)
        assert result == 1


# ─── 测试：calculate_task_hours ───────────────────────────────────────────────

class TestCalculateTaskHours:
    """测试任务工时计算"""

    def test_single_day_task(self):
        task = _make_task(
            plan_start=date(2025, 1, 1),
            plan_end=date(2025, 1, 1),
        )
        assert calculate_task_hours(task) == 8.0

    def test_multi_day_task(self):
        task = _make_task(
            plan_start=date(2025, 1, 1),
            plan_end=date(2025, 1, 5),
        )
        # 5 days * 8 hours = 40
        assert calculate_task_hours(task) == 40.0

    def test_returns_zero_when_no_dates(self):
        task = MagicMock()
        task.plan_start = None
        task.plan_end = None
        assert calculate_task_hours(task) == 0.0


# ─── 测试：calculate_total_assigned_hours ────────────────────────────────────

class TestCalculateTotalAssignedHours:
    """测试总分配工时计算"""

    def test_sum_from_tasks_and_allocations(self):
        task1 = _make_task(plan_start=date(2025, 1, 1), plan_end=date(2025, 1, 5))   # 40h
        task2 = _make_task(plan_start=date(2025, 1, 6), plan_end=date(2025, 1, 6))   # 8h
        alloc = _make_allocation(planned_hours=20.0)
        result = calculate_total_assigned_hours([task1, task2], [alloc])
        assert result == 68.0  # 40 + 8 + 20

    def test_ignores_allocations_without_planned_hours(self):
        task = _make_task(plan_start=date(2025, 1, 1), plan_end=date(2025, 1, 1))
        alloc = _make_allocation(planned_hours=None)
        result = calculate_total_assigned_hours([task], [alloc])
        assert result == 8.0  # only from task

    def test_empty_inputs(self):
        assert calculate_total_assigned_hours([], []) == 0.0


# ─── 测试：calculate_total_actual_hours ──────────────────────────────────────

class TestCalculateTotalActualHours:
    """测试总实际工时计算"""

    def test_sums_actual_hours(self):
        alloc1 = _make_allocation(actual_hours=8.0)
        alloc2 = _make_allocation(actual_hours=16.0)
        result = calculate_total_actual_hours([alloc1, alloc2])
        assert result == 24.0

    def test_ignores_none_actual_hours(self):
        alloc1 = _make_allocation(actual_hours=None)
        alloc2 = _make_allocation(actual_hours=5.0)
        result = calculate_total_actual_hours([alloc1, alloc2])
        assert result == 5.0

    def test_empty_list(self):
        assert calculate_total_actual_hours([]) == 0.0


# ─── 测试：build_project_workload ────────────────────────────────────────────

class TestBuildProjectWorkload:
    """测试项目负荷构建"""

    def test_groups_tasks_by_project(self):
        task1 = _make_task(task_id=1, project_id=10, plan_start=date(2025,1,1), plan_end=date(2025,1,5))
        task2 = _make_task(task_id=2, project_id=10, plan_start=date(2025,1,6), plan_end=date(2025,1,6))
        task3 = _make_task(task_id=3, project_id=20, plan_start=date(2025,1,1), plan_end=date(2025,1,1))
        result = build_project_workload([task1, task2, task3])
        assert len(result) == 2

    def test_skips_tasks_without_project_id(self):
        task = MagicMock()
        task.project_id = None
        result = build_project_workload([task])
        assert result == []

    def test_returns_empty_for_no_tasks(self):
        assert build_project_workload([]) == []


# ─── 测试：build_daily_load ──────────────────────────────────────────────────

class TestBuildDailyLoad:
    """测试每日负荷构建"""

    def test_generates_one_entry_per_day(self):
        start = date(2025, 1, 1)
        end = date(2025, 1, 3)
        result = build_daily_load([], start, end)
        assert len(result) == 3

    def test_distributes_estimated_hours(self):
        start = date(2025, 1, 1)
        end = date(2025, 1, 5)
        task = _make_task(
            plan_start=start,
            plan_end=end,
            estimated_hours=50.0,
        )
        result = build_daily_load([task], start, end)
        # 50h / 5 days = 10h per day
        assert abs(result[0].assigned - 10.0) < 0.1

    def test_uses_8h_per_day_when_no_estimated_hours(self):
        d = date(2025, 1, 1)
        task = _make_task(plan_start=d, plan_end=d, estimated_hours=None)
        result = build_daily_load([task], d, d)
        assert result[0].assigned == 8.0
