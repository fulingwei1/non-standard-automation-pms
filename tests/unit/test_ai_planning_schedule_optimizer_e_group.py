# -*- coding: utf-8 -*-
"""
E组 - AI进度排期优化器 单元测试
覆盖: app/services/ai_planning/schedule_optimizer.py
"""
import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest


# ─── fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def optimizer(db_session):
    from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer
    return AIScheduleOptimizer(db=db_session)


def _make_task(task_id, wbs_code, duration_days=5, dependencies=None,
               wbs_level=1, parent_wbs_id=None, risk_level="LOW"):
    task = MagicMock()
    task.id = task_id
    task.task_name = f"Task {task_id}"
    task.wbs_code = wbs_code
    task.wbs_level = wbs_level
    task.estimated_duration_days = duration_days
    task.parent_wbs_id = parent_wbs_id
    task.dependencies = json.dumps(dependencies) if dependencies else None
    task.risk_level = risk_level
    task.is_active = True
    return task


# ─── _get_predecessors ───────────────────────────────────────────────────────

class TestGetPredecessors:

    def test_no_dependencies_returns_empty(self, optimizer):
        task = _make_task(1, "1.0")
        task.dependencies = None
        result = optimizer._get_predecessors(task, {})
        assert result == []

    def test_valid_dependencies(self, optimizer):
        task_a = _make_task(1, "1.1")
        task_b = _make_task(2, "1.2", dependencies=[{"task_id": 1}])
        task_dict = {1: task_a, 2: task_b}
        result = optimizer._get_predecessors(task_b, task_dict)
        assert len(result) == 1
        assert result[0].id == 1

    def test_missing_predecessor_id_skipped(self, optimizer):
        task = _make_task(2, "1.2", dependencies=[{"task_id": 99}])
        result = optimizer._get_predecessors(task, {})
        assert result == []

    def test_invalid_json_dependencies_returns_empty(self, optimizer):
        task = _make_task(1, "1.1")
        task.dependencies = "invalid json {{"
        result = optimizer._get_predecessors(task, {})
        assert result == []


# ─── _get_successors ────────────────────────────────────────────────────────

class TestGetSuccessors:

    def test_no_successors(self, optimizer):
        task_a = _make_task(1, "1.1")
        task_b = _make_task(2, "1.2")  # no deps on task_a
        task_dict = {1: task_a, 2: task_b}
        result = optimizer._get_successors(task_a, task_dict)
        assert result == []

    def test_one_successor(self, optimizer):
        task_a = _make_task(1, "1.1")
        task_b = _make_task(2, "1.2", dependencies=[{"task_id": 1}])
        task_dict = {1: task_a, 2: task_b}
        result = optimizer._get_successors(task_a, task_dict)
        assert len(result) == 1
        assert result[0].id == 2

    def test_multiple_successors(self, optimizer):
        task_a = _make_task(1, "1.1")
        task_b = _make_task(2, "1.2", dependencies=[{"task_id": 1}])
        task_c = _make_task(3, "1.3", dependencies=[{"task_id": 1}])
        task_dict = {1: task_a, 2: task_b, 3: task_c}
        result = optimizer._get_successors(task_a, task_dict)
        assert len(result) == 2


# ─── _calculate_cpm ─────────────────────────────────────────────────────────

class TestCalculateCPM:

    def test_single_task(self, optimizer):
        task = _make_task(1, "1.0", duration_days=10)
        result = optimizer._calculate_cpm([task], date(2025, 1, 1))
        assert result["total_duration"] == 10
        assert result["es"][1] == 0
        assert result["ef"][1] == 10

    def test_sequential_tasks(self, optimizer):
        """A -> B -> C (linear chain)"""
        task_a = _make_task(1, "1.1", duration_days=5)
        task_b = _make_task(2, "1.2", duration_days=3, dependencies=[{"task_id": 1}])
        task_c = _make_task(3, "1.3", duration_days=2, dependencies=[{"task_id": 2}])
        tasks = [task_a, task_b, task_c]

        result = optimizer._calculate_cpm(tasks, date(2025, 1, 1))
        assert result["total_duration"] == 10  # 5+3+2
        assert result["ef"][3] == 10

    def test_parallel_tasks(self, optimizer):
        """A and B run in parallel, both depend on nothing"""
        task_a = _make_task(1, "1.1", duration_days=5)
        task_b = _make_task(2, "1.2", duration_days=8)
        result = optimizer._calculate_cpm([task_a, task_b], date(2025, 1, 1))
        assert result["total_duration"] == 8  # max(5, 8)

    def test_empty_task_list(self, optimizer):
        result = optimizer._calculate_cpm([], date(2025, 1, 1))
        assert result["total_duration"] == 0

    def test_slack_zero_on_critical_path(self, optimizer):
        task = _make_task(1, "1.0", duration_days=7)
        result = optimizer._calculate_cpm([task], date(2025, 1, 1))
        assert result["slack"][1] == 0


# ─── _generate_gantt_data ────────────────────────────────────────────────────

class TestGenerateGanttData:

    def test_gantt_has_correct_structure(self, optimizer):
        task = _make_task(1, "1.1", duration_days=5)
        cpm_result = {"es": {1: 0}, "ef": {1: 5}, "slack": {1: 0}}
        start = date(2025, 1, 1)
        result = optimizer._generate_gantt_data([task], cpm_result, start)
        assert len(result) == 1
        item = result[0]
        assert item["task_id"] == 1
        assert item["start_date"] == "2025-01-01"
        assert item["end_date"] == "2025-01-06"
        assert item["is_critical"] is True

    def test_non_critical_task(self, optimizer):
        task = _make_task(1, "1.1", duration_days=3)
        cpm_result = {"es": {1: 2}, "ef": {1: 5}, "slack": {1: 2}}  # slack=2
        start = date(2025, 1, 1)
        result = optimizer._generate_gantt_data([task], cpm_result, start)
        assert result[0]["is_critical"] is False

    def test_multiple_tasks_in_gantt(self, optimizer):
        tasks = [_make_task(i, f"1.{i}", duration_days=i) for i in range(1, 4)]
        cpm_result = {
            "es": {1: 0, 2: 1, 3: 2},
            "ef": {1: 1, 2: 3, 3: 5},
            "slack": {1: 0, 2: 0, 3: 0}
        }
        result = optimizer._generate_gantt_data(tasks, cpm_result, date(2025, 1, 1))
        assert len(result) == 3


# ─── _identify_critical_path ─────────────────────────────────────────────────

class TestIdentifyCriticalPath:

    def test_all_tasks_critical(self, optimizer):
        tasks = [_make_task(i, f"1.{i}") for i in range(1, 4)]
        cpm_result = {"slack": {1: 0, 2: 0, 3: 0}}
        result = optimizer._identify_critical_path(tasks, cpm_result)
        assert len(result) == 3

    def test_some_non_critical(self, optimizer):
        tasks = [_make_task(i, f"1.{i}") for i in range(1, 4)]
        cpm_result = {"slack": {1: 0, 2: 5, 3: 0}}
        result = optimizer._identify_critical_path(tasks, cpm_result)
        ids = [t["task_id"] for t in result]
        assert 2 not in ids

    def test_empty_returns_empty(self, optimizer):
        result = optimizer._identify_critical_path([], {"slack": {}})
        assert result == []


# ─── _analyze_resource_load ──────────────────────────────────────────────────

class TestAnalyzeResourceLoad:

    def test_no_allocations_returns_empty(self, optimizer, db_session):
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        result = optimizer._analyze_resource_load(1, {})
        assert result == {}

    def test_one_allocation(self, optimizer, db_session):
        alloc = MagicMock()
        alloc.user_id = 1
        alloc.allocated_hours = 80
        alloc.wbs_suggestion_id = 10
        alloc.overall_match_score = 85
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = [alloc]
        result = optimizer._analyze_resource_load(1, {})
        assert 1 in result
        assert result[1]["total_hours"] == 80

    def test_same_user_multiple_allocations(self, optimizer, db_session):
        alloc1 = MagicMock()
        alloc1.user_id = 1
        alloc1.allocated_hours = 40
        alloc1.wbs_suggestion_id = 10
        alloc1.overall_match_score = 80

        alloc2 = MagicMock()
        alloc2.user_id = 1
        alloc2.allocated_hours = 60
        alloc2.wbs_suggestion_id = 11
        alloc2.overall_match_score = 75

        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = [alloc1, alloc2]
        result = optimizer._analyze_resource_load(1, {})
        assert result[1]["total_hours"] == 100
        assert result[1]["task_count"] == 2


# ─── _detect_conflicts ──────────────────────────────────────────────────────

class TestDetectConflicts:

    def test_overloaded_user_detected(self, optimizer):
        tasks = [_make_task(i, f"1.{i}") for i in range(1, 3)]
        cpm_result = {"slack": {1: 0, 2: 0}}
        resource_load = {
            1: {"total_hours": 600, "task_count": 5, "tasks": []}  # > 160*3=480
        }
        conflicts = optimizer._detect_conflicts(tasks, cpm_result, resource_load)
        types = [c["type"] for c in conflicts]
        assert "RESOURCE_OVERLOAD" in types

    def test_too_many_critical_tasks(self, optimizer):
        tasks = [_make_task(i, f"1.{i}") for i in range(1, 11)]
        cpm_result = {"slack": {i: 0 for i in range(1, 11)}}  # all critical
        resource_load = {}
        conflicts = optimizer._detect_conflicts(tasks, cpm_result, resource_load)
        types = [c["type"] for c in conflicts]
        assert "TOO_MANY_CRITICAL_TASKS" in types

    def test_long_task_flagged(self, optimizer):
        task = _make_task(1, "1.1", duration_days=90)
        cpm_result = {"slack": {1: 0}}
        conflicts = optimizer._detect_conflicts([task], cpm_result, {})
        types = [c["type"] for c in conflicts]
        assert "TASK_TOO_LONG" in types

    def test_normal_scenario_no_conflicts(self, optimizer):
        tasks = [_make_task(i, f"1.{i}", duration_days=5) for i in range(1, 3)]
        cpm_result = {"slack": {1: 0, 2: 5}}
        resource_load = {1: {"total_hours": 80, "task_count": 1, "tasks": []}}
        conflicts = optimizer._detect_conflicts(tasks, cpm_result, resource_load)
        # No overload (80 < 480), no too-many-critical, no long tasks
        assert all(c["type"] != "RESOURCE_OVERLOAD" for c in conflicts)


# ─── _generate_recommendations ──────────────────────────────────────────────

class TestGenerateRecommendations:

    def test_critical_path_recommendation(self, optimizer):
        critical_path = [{"task_id": 1, "task_name": "T1"}]
        result = optimizer._generate_recommendations([], critical_path, [], {})
        cats = [r["category"] for r in result]
        assert "CRITICAL_PATH" in cats

    def test_unbalanced_resource_recommendation(self, optimizer):
        resource_load = {
            1: {"total_hours": 400, "task_count": 3, "tasks": []},
            2: {"total_hours": 20, "task_count": 1, "tasks": []},  # avg=210, max=400 > 420
        }
        result = optimizer._generate_recommendations([], [], [], resource_load)
        cats = [r["category"] for r in result]
        assert "RESOURCE_BALANCE" in cats

    def test_high_risk_task_recommendation(self, optimizer):
        tasks = [_make_task(1, "1.1", risk_level="HIGH")]
        result = optimizer._generate_recommendations(tasks, [], [], {})
        cats = [r["category"] for r in result]
        assert "RISK_MANAGEMENT" in cats

    def test_empty_inputs_no_crash(self, optimizer):
        result = optimizer._generate_recommendations([], [], [], {})
        assert isinstance(result, list)


# ─── _calculate_resource_utilization ────────────────────────────────────────

class TestCalculateResourceUtilization:

    def test_empty_load_returns_zero(self, optimizer):
        result = optimizer._calculate_resource_utilization({})
        assert result == 0.0

    def test_full_utilization(self, optimizer):
        # 1 person, 160*3=480 standard hours, total=480 => 100%
        resource_load = {1: {"total_hours": 480, "task_count": 5, "tasks": []}}
        result = optimizer._calculate_resource_utilization(resource_load)
        assert result == pytest.approx(100.0)

    def test_half_utilization(self, optimizer):
        resource_load = {1: {"total_hours": 240, "task_count": 3, "tasks": []}}
        result = optimizer._calculate_resource_utilization(resource_load)
        assert result == pytest.approx(50.0)

    def test_capped_at_100(self, optimizer):
        resource_load = {1: {"total_hours": 10000, "task_count": 10, "tasks": []}}
        result = optimizer._calculate_resource_utilization(resource_load)
        assert result == 100.0


# ─── optimize_schedule (integration mock) ───────────────────────────────────

class TestOptimizeSchedule:

    def test_project_not_found_returns_empty(self, optimizer, db_session):
        db_session.query.return_value.get.return_value = None
        result = optimizer.optimize_schedule(999)
        assert result == {}

    def test_no_tasks_returns_empty(self, optimizer, db_session):
        project = MagicMock()
        db_session.query.return_value.get.return_value = project
        db_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = optimizer.optimize_schedule(1)
        assert result == {}

    def test_basic_schedule_structure(self, optimizer, db_session):
        project = MagicMock()
        project.id = 1
        db_session.query.return_value.get.return_value = project

        tasks = [_make_task(i, f"1.{i}", duration_days=5) for i in range(1, 4)]
        db_session.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = tasks
        db_session.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = optimizer.optimize_schedule(1, start_date=date(2025, 1, 1))

        assert result["project_id"] == 1
        assert "gantt_data" in result
        assert "critical_path" in result
        assert "recommendations" in result
        assert "optimization_summary" in result
        assert result["optimization_summary"]["total_tasks"] == 3
