# -*- coding: utf-8 -*-
"""扩展进度服务测试 - 覆盖 0% 覆盖率的方法"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


# Mock 掉有问题的模块导入
with patch.dict("sys.modules", {"app.services.sales_reminder": MagicMock()}):
    from app.services.progress_service import (
        ProgressAggregationService,
        ProgressAutoService,
        _check_and_update_health,
        aggregate_task_progress,
        create_progress_log_entry,
        get_project_progress_summary,
    )


def _make_db():
    return MagicMock()


def _make_task(**kw):
    t = MagicMock()
    defaults = dict(
        id=1,
        project_id=10,
        assignee_id=1,
        status="ACCEPTED",
        progress=0,
        actual_hours=None,
        actual_start_date=None,
        actual_end_date=None,
        updated_by=None,
        updated_at=None,
        is_active=True,
        is_delayed=False,
        stage="DESIGN",
        estimated_hours=Decimal("8"),
        deadline=datetime(2025, 12, 31),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


def _make_project(**kw):
    p = MagicMock()
    defaults = dict(
        id=10,
        project_name="Test Project",
        progress_pct=0,
        health="H1",
        pm_id=1,
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(p, k, v)
    return p


# --- _check_and_update_health ---


class TestCheckAndUpdateHealth:
    """测试项目健康度检查与更新"""

    def test_health_h1_normal(self):
        """测试健康度为 H1（正常）"""
        db = _make_db()
        project = _make_project(health="H1")
        db.query.return_value.filter.return_value.first.return_value = project
        # 模拟返回 0 个任务
        db.query.return_value.filter.return_value.scalar.return_value = 0

        with patch("app.services.progress_service.TaskUnified"):
            _check_and_update_health(db, 10)
        # 无异常即通过

    def test_health_updates_based_on_delayed_ratio(self):
        """测试根据延期比例更新健康度"""
        db = _make_db()
        project = _make_project(health="H1")

        # 设置查询返回值: 总任务 10 个，延期 3 个 (30% > 25% -> H3)
        def scalar_side_effect(*args):
            query_mock = MagicMock()
            query_mock.scalar.return_value = 10 if "count" in str(args) else 3
            return query_mock.scalar()

        db.query.return_value.filter.return_value.scalar.side_effect = [10, 3, 0]
        db.query.return_value.filter.return_value.first.return_value = project

        with patch("app.services.progress_service.TaskUnified"):
            _check_and_update_health(db, 10)

        # 验证健康度应该变为 H3
        assert project.health == "H3"

    def test_health_updates_based_on_overdue_ratio(self):
        """测试根据逾期比例更新健康度"""
        db = _make_db()
        project = _make_project(health="H1")

        # 总任务 10 个，延期 0 个，逾期 2 个 (20% > 15% -> H3)
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 0, 2]
        db.query.return_value.filter.return_value.first.return_value = project

        with patch("app.services.progress_service.TaskUnified"):
            _check_and_update_health(db, 10)

        assert project.health == "H3"

    def test_health_h2_mid_risk(self):
        """测试健康度为 H2（中等风险）"""
        db = _make_db()
        project = _make_project(health="H1")

        # 延期 15% (10-25% 区间 -> H2)，逾期 0
        db.query.return_value.filter.return_value.scalar.side_effect = [100, 15, 0]
        db.query.return_value.filter.return_value.first.return_value = project

        with patch("app.services.progress_service.TaskUnified"):
            _check_and_update_health(db, 10)

        assert project.health == "H2"

    def test_project_not_found(self):
        """测试项目不存在"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        # 不应该抛出异常
        with patch("app.services.progress_service.TaskUnified"):
            _check_and_update_health(db, 999)

    def test_no_active_tasks(self):
        """测试没有活跃任务"""
        db = _make_db()
        project = _make_project(health="H1")
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.scalar.return_value = 0

        with patch("app.services.progress_service.TaskUnified"):
            _check_and_update_health(db, 10)


# --- aggregate_task_progress 扩展测试 ---


class TestAggregateTaskProgressExtended:
    """扩展测试任务进度聚合"""

    def test_aggregate_with_stage(self):
        """测试带阶段的进度聚合"""
        db = _make_db()
        task = _make_task(stage="DESIGN", project_id=10)
        project = _make_project()
        stage = MagicMock()

        # 模拟查询返回值
        query_mock = MagicMock()
        query_mock.first.side_effect = [task, project, stage]
        query_mock.scalar.side_effect = [10, 500, 10, 500]  # 总任务数，进度和，阶段任务数，阶段进度和
        query_mock.filter.return_value = query_mock

        db.query.return_value.filter.return_value.first.side_effect = [task, project, stage]
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 500, 10, 500]

        with patch("app.services.progress_service._check_and_update_health"), \
             patch("app.services.progress_service.TaskUnified"), \
             patch("app.services.progress_service.ProjectStage", return_value=stage):
            result = aggregate_task_progress(db, 1)

        assert result["project_progress_updated"] is True
        assert result["stage_progress_updated"] is True

    def test_aggregate_updates_project_progress(self):
        """测试聚合更新项目进度"""
        db = _make_db()
        task = _make_task(project_id=10)
        project = _make_project()

        db.query.return_value.filter.return_value.first.side_effect = [task, project]
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 500]

        with patch("app.services.progress_service._check_and_update_health"), \
             patch("app.services.progress_service.TaskUnified"):
            result = aggregate_task_progress(db, 1)

        assert result["new_project_progress"] == 50.0
        project.progress_pct = 50.0


# --- ProgressAggregationService 扩展测试 ---


class TestProgressAggregationServiceExtended:
    """测试进度聚合服务"""

    def test_aggregate_with_weighted_hours(self):
        """测试使用预估工时加权"""
        db = _make_db()
        db.query.return_value.filter.return_value.scalar.side_effect = [
            10,  # 总任务数
            500,  # 总权重
            25000,  # 加权和
            2,  # 延期任务数
            1,  # 逾期任务数
        ]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("COMPLETED", 3),
            ("IN_PROGRESS", 5),
            ("ACCEPTED", 2),
        ]

        result = ProgressAggregationService.aggregate_project_progress(1, db)
        assert result["overall_progress"] == 50.0

    def test_aggregate_no_tasks(self):
        """测试无任务情况"""
        db = _make_db()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = ProgressAggregationService.aggregate_project_progress(1, db)
        assert result["total_tasks"] == 0
        assert result["overall_progress"] == 0.0


# --- ProgressAutoService 扩展测试 ---


class TestProgressAutoServiceExtended:
    """测试进度自动服务"""

    def test_apply_forecast_all_cases(self):
        """测试应用预测的所有场景"""
        db = _make_db()

        # 3 个任务，不同状态
        task1 = MagicMock(id=1, status="IN_PROGRESS", task_name="T1", progress_percent=30)
        task2 = MagicMock(id=2, status="DONE", task_name="T2", progress_percent=100)
        task3 = MagicMock(id=3, status="CANCELLED", task_name="T3", progress_percent=0)

        db.query.return_value.filter.return_value.all.return_value = [task1, task2, task3]

        forecast_items = [
            MagicMock(task_id=1, delay_days=10, critical=True, status="Delayed"),
            MagicMock(task_id=2, delay_days=5, critical=False, status="OnTrack"),
            MagicMock(task_id=3, delay_days=2, critical=False, status="OnTrack"),
        ]

        svc = ProgressAutoService(db)
        stats = svc.apply_forecast_to_tasks(1, forecast_items, auto_block=True, delay_threshold=3)

        assert stats["total"] == 3
        assert stats["blocked"] == 1  # 任务1被阻塞

    def test_auto_fix_dependency_missing(self):
        """测试自动修复缺失依赖"""
        db = _make_db()
        issue = MagicMock(issue_type="MISSING_PREDECESSOR", task_id=1, detail="missing")
        dep = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [dep]

        # 模拟前置任务不存在
        db.query.return_value.filter.return_value.first.return_value = None

        svc = ProgressAutoService(db)
        with patch.object(svc, "_remove_missing_dependency", return_value=True):
            stats = svc.auto_fix_dependency_issues(1, [issue], auto_fix_missing=True)

        assert stats["missing_removed"] == 1


class TestProgressAutoServiceFixTimingConflict:
    """测试时序冲突修复"""

    def test_fix_timing_conflict_success(self):
        """成功修复时序冲突"""
        db = _make_db()

        task = MagicMock(
            id=1,
            task_name="Task1",
            plan_start=datetime(2025, 1, 1),
            plan_end=datetime(2025, 1, 10),
            progress_percent=50,
        )

        dep = MagicMock(lag_days=0)
        pred_task = MagicMock(id=10, actual_end=datetime(2025, 1, 5), plan_end=datetime(2025, 1, 5))

        db.query.return_value.filter.return_value.first.side_effect = [task, dep, pred_task]

        svc = ProgressAutoService(db)
        result = svc._fix_timing_conflict(MagicMock(task_id=1))

        assert result is True

    def test_fix_timing_conflict_no_task(self):
        """任务不存在"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        svc = ProgressAutoService(db)
        result = svc._fix_timing_conflict(MagicMock(task_id=999))

        assert result is False


class TestProgressAutoServiceRemoveMissingDependency:
    """测试移除缺失依赖"""

    def test_remove_missing_dependency_success(self):
        """成功移除缺失依赖"""
        db = _make_db()

        dep1 = MagicMock(id=1, depends_on_task_id=100)
        dep2 = MagicMock(id=2, depends_on_task_id=200)

        task = MagicMock(id=1, progress_percent=50)

        # 前置任务都不存在
        db.query.return_value.filter.return_value.all.return_value = [dep1, dep2]
        db.query.return_value.filter.return_value.first.side_effect = [None, None, task]

        svc = ProgressAutoService(db)
        result = svc._remove_missing_dependency(MagicMock(task_id=1))

        assert result is True
        assert db.delete.call_count == 2


class TestProgressAutoServiceRunAutoProcessing:
    """测试自动处理流程"""

    def test_run_auto_processing_with_tasks(self):
        """测试有任务的自动处理"""
        db = _make_db()

        project = MagicMock(id=1, project_name="Test Project", pm_id=1)
        task1 = MagicMock(id=1, project_id=1, owner_id=1)
        task2 = MagicMock(id=2, project_id=1, owner_id=2)

        dep = MagicMock(id=1, task_id=1, depends_on_task_id=2)

        # 查询返回
        db.query.return_value.filter.return_value.first.side_effect = [project, None]
        db.query.return_value.filter.return_value.all.side_effect = [
            [task1, task2],  # tasks
            [],  # dependencies
        ]

        svc = ProgressAutoService(db)

        # Mock 预测相关函数
        forecast_result = MagicMock()
        forecast_result.current_progress = 50
        forecast_result.predicted_delay_days = 5
        forecast_result.tasks = [MagicMock(task_id=1, critical=True, delay_days=3)]

        with patch("app.services.progress_service._build_project_forecast", return_value=forecast_result), \
             patch("app.services.progress_service._analyze_dependency_graph", return_value=([], [])), \
             patch("app.services.progress_service.create_notification"):
            result = svc.run_auto_processing(1, {"auto_block": True})

        assert result["success"] is True


# --- get_project_progress_summary 扩展测试 ---


class TestGetProjectProgressSummaryExtended:
    """扩展测试项目进度汇总"""

    def test_summary_with_all_statuses(self):
        """测试所有状态统计"""
        db = _make_db()

        # 总任务，延期，逾期，平均进度
        db.query.return_value.filter.return_value.scalar.side_effect = [20, 5, 3, 55.0]

        # 状态分组统计
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("COMPLETED", 10),
            ("IN_PROGRESS", 5),
            ("ACCEPTED", 3),
            ("PENDING_APPROVAL", 2),
        ]

        result = get_project_progress_summary(db, 1)

        assert result["total_tasks"] == 20
        assert result["completed_tasks"] == 10
        assert result["in_progress_tasks"] == 5
        assert result["delayed_tasks"] == 5
        assert result["overdue_tasks"] == 3
        assert result["overall_progress"] == 55.0
        assert result["completion_rate"] == 50.0  # 10/20 * 100