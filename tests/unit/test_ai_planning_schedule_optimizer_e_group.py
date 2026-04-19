# -*- coding: utf-8 -*-
"""
E组 - AI进度排期优化器 单元测试
覆盖: app/services/ai_planning/schedule_optimizer.py
"""
import json
from datetime import date
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def optimizer(mock_db):
    from app.services.ai_planning.schedule_optimizer import AIScheduleOptimizer

    return AIScheduleOptimizer(db=mock_db)


def _make_task(
    task_id,
    wbs_code,
    duration_days=5,
    dependencies=None,
    wbs_level=1,
    parent_wbs_id=None,
    risk_level="LOW",
):
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


class TestGetPredecessors:
    def test_no_dependencies_returns_empty(self, optimizer):
        task = _make_task(1, "1.0")
        task.dependencies = None
        assert optimizer._get_predecessors(task, {}) == []

    def test_valid_dependencies(self, optimizer):
        task_a = _make_task(1, "1.1")
        task_b = _make_task(2, "1.2", dependencies=[{"task_id": 1}])
        result = optimizer._get_predecessors(task_b, {1: task_a, 2: task_b})
        assert len(result) == 1 and result[0].id == 1

    def test_missing_predecessor_id_skipped(self, optimizer):
        task = _make_task(2, "1.2", dependencies=[{"task_id": 99}])
        assert optimizer._get_predecessors(task, {}) == []

    def test_invalid_json_dependencies_returns_empty(self, optimizer):
        task = _make_task(1, "1.1")
        task.dependencies = "invalid json {{"
        assert optimizer._get_predecessors(task, {}) == []


class TestGetSuccessors:
    def test_no_successors(self, optimizer):
        task_a = _make_task(1, "1.1")
        task_b = _make_task(2, "1.2")
        assert optimizer._get_successors(task_a, {1: task_a, 2: task_b}) == []

    def test_one_successor(self, optimizer):
        task_a = _make_task(1, "1.1")
        task_b = _make_task(2, "1.2", dependencies=[{"task_id": 1}])
        result = optimizer._get_successors(task_a, {1: task_a, 2: task_b})
        assert len(result) == 1 and result[0].id == 2

    def test_multiple_successors(self, optimizer):
        task_a = _make_task(1, "1.1")
        task_b = _make_task(2, "1.2", dependencies=[{"task_id": 1}])
        task_c = _make_task(3, "1.3", dependencies=[{"task_id": 1}])
        result = optimizer._get_successors(task_a, {1: task_a, 2: task_b, 3: task_c})
        assert len(result) == 2


class TestCalculateCPM:
    def test_single_task(self, optimizer):
        task = _make_task(1, "1.0", duration_days=10)
        result = optimizer._calculate_cpm([task], date(2025, 1, 1))
        assert result["total_duration"] == 10
        assert result["es"][1] == 0
        assert result["ef"][1] == 10

    def test_sequential_tasks(self, optimizer):
        task_a = _make_task(1, "1.1", duration_days=5)
        task_b = _make_task(2, "1.2", duration_days=3, dependencies=[{"task_id": 1}])
        task_c = _make_task(3, "1.3", duration_days=2, dependencies=[{"task_id": 2}])
        result = optimizer._calculate_cpm([task_a, task_b, task_c], date(2025, 1, 1))
        assert result["total_duration"] == 10
        assert result["ef"][3] == 10

    def test_parallel_tasks(self, optimizer):
        task_a = _make_task(1, "1.1", duration_days=5)
        task_b = _make_task(2, "1.2", duration_days=8)
        result = optimizer._calculate_cpm([task_a, task_b], date(2025, 1, 1))
        assert result["total_duration"] == 8

    def test_empty_task_list(self, optimizer):
        result = optimizer._calculate_cpm([], date(2025, 1, 1))
        assert result["total_duration"] == 0

    def test_slack_zero_on_critical_path(self, optimizer):
        task = _make_task(1, "1.0", duration_days=7)
        result = optimizer._calculate_cpm([task], date(2025, 1, 1))
        assert result["slack"][1] == 0


class TestGenerateGanttData:
    def test_gantt_has_correct_structure(self, optimizer):
        task = _make_task(1, "1.1", duration_days=5)
        cpm_result = {"es": {1: 0}, "ef": {1: 5}, "slack": {1: 0}}
        result = optimizer._generate_gantt_data([task], cpm_result, date(2025, 1, 1))
        assert len(result) == 1
        assert result[0]["task_id"] == 1
        assert result[0]["start_date"] == "2025-01-01"
        assert result[0]["end_date"] == "2025-01-06"
        assert result[0]["is_critical"] is True

    def test_non_critical_task(self, optimizer):
        task = _make_task(1, "1.1", duration_days=3)
        cpm_result = {"es": {1: 2}, "ef": {1: 5}, "slack": {1: 2}}
        result = optimizer._generate_gantt_data([task], cpm_result, date(2025, 1, 1))
        assert result[0]["is_critical"] is False

    def test_multiple_tasks_in_gantt(self, optimizer):
        tasks = [_make_task(i, f"1.{i}", duration_days=i) for i in range(1, 4)]
        cpm_result = {"es": {1: 0, 2: 1, 3: 2}, "ef": {1: 1, 2: 3, 3: 5}, "slack": {1: 0, 2: 0, 3: 0}}
        assert len(optimizer._generate_gantt_data(tasks, cpm_result, date(2025, 1, 1))) == 3


class TestIdentifyCriticalPath:
    def test_all_tasks_critical(self, optimizer):
        tasks = [_make_task(i, f"1.{i}") for i in range(1, 4)]
        result = optimizer._identify_critical_path(tasks, {"slack": {1: 0, 2: 0, 3: 0}})
        assert len(result) == 3

    def test_some_non_critical(self, optimizer):
        tasks = [_make_task(i, f"1.{i}") for i in range(1, 4)]
        ids = [t["task_id"] for t in optimizer._identify_critical_path(tasks, {"slack": {1: 0, 2: 5, 3: 0}})]
        assert 2 not in ids

    def test_empty_returns_empty(self, optimizer):
        assert optimizer._identify_critical_path([], {"slack": {}}) == []


class TestAnalyzeResourceLoad:
    def test_no_allocations_returns_empty(self, optimizer, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        assert optimizer._analyze_resource_load(1, {}) == {}

    def test_one_allocation(self, optimizer, mock_db):
        alloc = MagicMock(user_id=1, allocated_hours=80, wbs_suggestion_id=10, overall_match_score=85)
        mock_db.query.return_value.filter.return_value.all.return_value = [alloc]
        result = optimizer._analyze_resource_load(1, {})
        assert 1 in result and result[1]["total_hours"] == 80

    def test_same_user_multiple_allocations(self, optimizer, mock_db):
        alloc1 = MagicMock(user_id=1, allocated_hours=40, wbs_suggestion_id=10, overall_match_score=80)
        alloc2 = MagicMock(user_id=1, allocated_hours=60, wbs_suggestion_id=11, overall_match_score=75)
        mock_db.query.return_value.filter.return_value.all.return_value = [alloc1, alloc2]
        result = optimizer._analyze_resource_load(1, {})
        assert result[1]["total_hours"] == 100
        assert result[1]["task_count"] == 2


class TestDetectConflicts:
    def test_overloaded_user_detected(self, optimizer):
        tasks = [_make_task(i, f"1.{i}") for i in range(1, 3)]
        conflicts = optimizer._detect_conflicts(tasks, {"slack": {1: 0, 2: 0}}, {1: {"total_hours": 600, "task_count": 5, "tasks": []}})
        assert "RESOURCE_OVERLOAD" in [c["type"] for c in conflicts]

    def test_too_many_critical_tasks(self, optimizer):
        tasks = [_make_task(i, f"1.{i}") for i in range(1, 11)]
        conflicts = optimizer._detect_conflicts(tasks, {"slack": {i: 0 for i in range(1, 11)}}, {})
        assert "TOO_MANY_CRITICAL_TASKS" in [c["type"] for c in conflicts]

    def test_long_task_flagged(self, optimizer):
        task = _make_task(1, "1.1", duration_days=90)
        conflicts = optimizer._detect_conflicts([task], {"slack": {1: 0}}, {})
        assert "TASK_TOO_LONG" in [c["type"] for c in conflicts]

    def test_normal_scenario_no_conflicts(self, optimizer):
        tasks = [_make_task(i, f"1.{i}", duration_days=5) for i in range(1, 3)]
        conflicts = optimizer._detect_conflicts(tasks, {"slack": {1: 0, 2: 5}}, {1: {"total_hours": 80, "task_count": 1, "tasks": []}})
        assert all(c["type"] != "RESOURCE_OVERLOAD" for c in conflicts)


class TestGenerateRecommendations:
    def test_critical_path_recommendation(self, optimizer):
        result = optimizer._generate_recommendations([], [{"task_id": 1, "task_name": "T1"}], [], {})
        assert "CRITICAL_PATH" in [r["category"] for r in result]

    def test_unbalanced_resource_recommendation(self, optimizer):
        resource_load = {1: {"total_hours": 600, "task_count": 3, "tasks": []}, 2: {"total_hours": 20, "task_count": 1, "tasks": []}}
        result = optimizer._generate_recommendations([], [], [], resource_load)
        assert "RESOURCE_BALANCE" in [r["category"] for r in result]

    def test_high_risk_task_recommendation(self, optimizer):
        result = optimizer._generate_recommendations([_make_task(1, "1.1", risk_level="HIGH")], [], [], {})
        assert "RISK_MANAGEMENT" in [r["category"] for r in result]

    def test_empty_inputs_no_crash(self, optimizer):
        assert isinstance(optimizer._generate_recommendations([], [], [], {}), list)


class TestCalculateResourceUtilization:
    def test_empty_load_returns_zero(self, optimizer):
        assert optimizer._calculate_resource_utilization({}) == 0.0

    def test_full_utilization(self, optimizer):
        assert optimizer._calculate_resource_utilization({1: {"total_hours": 480, "task_count": 5, "tasks": []}}) == pytest.approx(100.0)

    def test_half_utilization(self, optimizer):
        assert optimizer._calculate_resource_utilization({1: {"total_hours": 240, "task_count": 3, "tasks": []}}) == pytest.approx(50.0)

    def test_capped_at_100(self, optimizer):
        assert optimizer._calculate_resource_utilization({1: {"total_hours": 10000, "task_count": 10, "tasks": []}}) == 100.0


class TestOptimizeSchedule:
    def test_project_not_found_returns_empty(self, optimizer, mock_db):
        query1 = MagicMock()
        query1.get.return_value = None
        mock_db.query.side_effect = [query1]
        assert optimizer.optimize_schedule(999) == {}

    def test_no_tasks_returns_empty(self, optimizer, mock_db):
        project = MagicMock()
        query1 = MagicMock()
        query1.get.return_value = project
        query2 = MagicMock()
        query2.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.side_effect = [query1, query2]
        assert optimizer.optimize_schedule(1) == {}

    def test_basic_schedule_structure(self, optimizer, mock_db):
        project = MagicMock()
        project.id = 1
        tasks = [_make_task(i, f"1.{i}", duration_days=5) for i in range(1, 4)]
        query1 = MagicMock(); query1.get.return_value = project
        query2 = MagicMock(); query2.filter.return_value.order_by.return_value.all.return_value = tasks
        query3 = MagicMock(); query3.filter.return_value.all.return_value = []
        mock_db.query.side_effect = [query1, query2, query3]

        result = optimizer.optimize_schedule(1, start_date=date(2025, 1, 1))
        assert result["project_id"] == 1
        assert "gantt_data" in result
        assert "critical_path" in result
        assert "recommendations" in result
        assert "optimization_summary" in result
        assert result["optimization_summary"]["total_tasks"] == 3
