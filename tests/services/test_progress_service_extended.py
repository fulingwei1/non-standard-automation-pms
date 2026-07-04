# -*- coding: utf-8 -*-
"""扩展进度服务测试 - 覆盖 0% 覆盖率的方法"""
from datetime import date, datetime
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
        db.query.return_value.filter.return_value.scalar.return_value = 0

        _check_and_update_health(db, 10)

    def test_health_updates_based_on_delayed_ratio(self):
        """测试根据延期比例更新健康度"""
        db = _make_db()
        project = _make_project(health="H1")

        db.query.return_value.filter.return_value.scalar.side_effect = [100, 30, 0]
        db.query.return_value.filter.return_value.first.return_value = project

        _check_and_update_health(db, 10)

        assert project.health == "H3"

    def test_health_h2_mid_risk(self):
        """测试健康度为 H2（中等风险）"""
        db = _make_db()
        project = _make_project(health="H1")

        db.query.return_value.filter.return_value.scalar.side_effect = [100, 15, 0]
        db.query.return_value.filter.return_value.first.return_value = project

        _check_and_update_health(db, 10)

        assert project.health == "H2"


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


# --- ProgressAutoServiceRunAutoProcessing ---


class TestProgressAutoServiceRunAutoProcessing:
    """测试自动处理流程"""

    def test_run_auto_processing_no_project(self):
        """项目不存在"""
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None

        svc = ProgressAutoService(db)
        result = svc.run_auto_processing(1)

        assert result["success"] is False
        assert "error" in result


# --- get_project_progress_summary 扩展测试 ---


class TestGetProjectProgressSummaryExtended:
    """扩展测试项目进度汇总"""

    def test_summary_with_all_statuses(self):
        """测试所有状态统计"""
        db = _make_db()

        db.query.return_value.filter.return_value.scalar.side_effect = [20, 5, 3, 55.0]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("COMPLETED", 10),
            ("IN_PROGRESS", 5),
            ("ACCEPTED", 3),
            ("PENDING_APPROVAL", 2),
        ]

        result = get_project_progress_summary(db, 1)

        assert result["total_tasks"] == 20
        assert result["completed_tasks"] == 10
        assert result["delayed_tasks"] == 5
        assert result["overdue_tasks"] == 3
        assert result["overall_progress"] == 55.0
        assert result["completion_rate"] == 50.0
