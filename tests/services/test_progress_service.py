# -*- coding: utf-8 -*-
"""进度服务单元测试"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.progress_service import (
    apply_task_progress_update,
    update_task_progress,
    aggregate_task_progress,
    create_progress_log_entry,
    get_project_progress_summary,
    ProgressAggregationService,
    ProgressAutoService,
    progress_error_to_http,
)


def _make_db():
    return MagicMock()


def _make_task(**kw):
    t = MagicMock()
    defaults = dict(
        id=1, project_id=10, assignee_id=1, status="ACCEPTED",
        progress=0, actual_hours=None, actual_start_date=None,
        actual_end_date=None, updated_by=None, updated_at=None,
        is_active=True, is_delayed=False, stage="DESIGN",
        estimated_hours=Decimal("8"), deadline=datetime(2025, 12, 31),
    )
    defaults.update(kw)
    for k, v in defaults.items():
        setattr(t, k, v)
    return t


# --- apply_task_progress_update ---

class TestApplyTaskProgressUpdate:
    def test_basic_update(self):
        task = _make_task()
        apply_task_progress_update(task, 50, 1)
        assert task.progress == 50
        assert task.status == "IN_PROGRESS"

    def test_complete(self):
        task = _make_task(status="IN_PROGRESS")
        apply_task_progress_update(task, 100, 1)
        assert task.status == "COMPLETED"
        assert task.actual_end_date == date.today()

    def test_wrong_assignee(self):
        task = _make_task(assignee_id=2)
        with pytest.raises(ValueError, match="只能更新"):
            apply_task_progress_update(task, 50, 1)

    def test_completed_task_rejected(self):
        task = _make_task(status="COMPLETED")
        with pytest.raises(ValueError, match="已完成"):
            apply_task_progress_update(task, 50, 1)

    def test_invalid_progress(self):
        task = _make_task()
        with pytest.raises(ValueError, match="0到100"):
            apply_task_progress_update(task, 150, 1)

    def test_negative_progress(self):
        task = _make_task()
        with pytest.raises(ValueError, match="0到100"):
            apply_task_progress_update(task, -1, 1)

    def test_sets_actual_start_date(self):
        task = _make_task(actual_start_date=None)
        apply_task_progress_update(task, 10, 1)
        assert task.actual_start_date == date.today()

    def test_actual_hours(self):
        task = _make_task()
        apply_task_progress_update(task, 50, 1, actual_hours=Decimal("4"))
        assert task.actual_hours == Decimal("4")


# --- progress_error_to_http ---

class TestProgressErrorToHttp:
    def test_not_found(self):
        exc = progress_error_to_http(ValueError("任务不存在"))
        assert exc.status_code == 404

    def test_forbidden(self):
        exc = progress_error_to_http(ValueError("只能更新自己的"))
        assert exc.status_code == 403

    def test_bad_request(self):
        exc = progress_error_to_http(ValueError("进度非法"))
        assert exc.status_code == 400


# --- update_task_progress ---

class TestUpdateTaskProgress:
    def test_success(self):
        db = _make_db()
        task = _make_task()
        db.query.return_value.filter.return_value.first.return_value = task

        with patch("app.services.progress_service.aggregate_task_progress", return_value={}), \
             patch("app.services.progress_service.create_progress_log_entry"):
            result_task, agg = update_task_progress(db, 1, 50, 1, progress_note="half done")
        assert result_task.progress == 50
        db.commit.assert_called()

    def test_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="任务不存在"):
            update_task_progress(db, 999, 50, 1)


# --- aggregate_task_progress ---

class TestAggregateTaskProgress:
    def test_no_task(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = aggregate_task_progress(db, 999)
        assert result["project_progress_updated"] is False

    def test_with_task(self):
        db = _make_db()
        task = _make_task(stage="DESIGN")
        project = MagicMock()

        def query_side_effect(model):
            m = MagicMock()
            return m

        db.query.return_value.filter.return_value.first.side_effect = [task, project, None]
        db.query.return_value.filter.return_value.scalar.return_value = 5

        with patch("app.services.progress_service._check_and_update_health"), \
             patch("app.services.progress_service.TaskUnified", MagicMock()), \
             patch("app.services.progress_service.and_", lambda *a: MagicMock()):
            result = aggregate_task_progress(db, 1)
        assert "project_id" in result


# --- create_progress_log_entry ---

class TestCreateProgressLogEntry:
    def test_creates_log(self):
        db = _make_db()
        with patch("app.services.progress_service.ProgressLog") as MockLog:
            instance = MagicMock()
            MockLog.return_value = instance
            result = create_progress_log_entry(db, 1, 50, 4.0, "halfway", 1)
        db.add.assert_called_once()
        db.commit.assert_called()

    def test_handles_error(self):
        db = _make_db()
        db.add.side_effect = Exception("db error")
        result = create_progress_log_entry(db, 1, 50, None, "note", 1)
        assert result is None


# --- get_project_progress_summary ---

class TestGetProjectProgressSummary:
    def test_basic(self):
        db = _make_db()
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 2, 1, 50.0]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("COMPLETED", 3), ("IN_PROGRESS", 5)
        ]
        result = get_project_progress_summary(db, 1)
        assert result["project_id"] == 1
        assert "total_tasks" in result


# --- ProgressAggregationService ---

class TestProgressAggregationService:
    def test_aggregate_empty_project(self):
        db = _make_db()
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        result = ProgressAggregationService.aggregate_project_progress(1, db)
        assert result["project_id"] == 1
        assert result["total_tasks"] == 0
        assert result["overall_progress"] == 0.0


# --- ProgressAutoService ---

class TestProgressAutoServiceApplyForecast:
    def test_apply_forecast_blocks_delayed(self):
        db = _make_db()
        task = MagicMock(id=1, status="IN_PROGRESS", task_name="T1")
        db.query.return_value.filter.return_value.all.return_value = [task]

        forecast_item = MagicMock(task_id=1, delay_days=10, critical=True, status="Delayed")

        svc = ProgressAutoService(db)
        stats = svc.apply_forecast_to_tasks(1, [forecast_item], auto_block=True, delay_threshold=3)
        assert stats["blocked"] == 1
        assert task.status == "BLOCKED"

    def test_apply_forecast_risk_tag(self):
        db = _make_db()
        task = MagicMock(id=1, status="IN_PROGRESS", task_name="T1", progress_percent=30)
        db.query.return_value.filter.return_value.all.return_value = [task]

        forecast_item = MagicMock(task_id=1, delay_days=5, critical=True, status="Delayed")

        svc = ProgressAutoService(db)
        with patch("app.services.progress_service.ProgressLog"):
            stats = svc.apply_forecast_to_tasks(1, [forecast_item], auto_block=False)
        assert stats["risk_tagged"] == 1


class TestProgressAutoServiceFixDependency:
    def test_skip_cycles(self):
        db = _make_db()
        issue = MagicMock(issue_type="CYCLE", task_id=1)
        svc = ProgressAutoService(db)
        stats = svc.auto_fix_dependency_issues(1, [issue])
        assert stats["cycles_skipped"] == 1

    def test_fix_timing(self):
        db = _make_db()
        issue = MagicMock(issue_type="TIMING_CONFLICT", task_id=1, detail="conflict")
        svc = ProgressAutoService(db)
        with patch.object(svc, "_fix_timing_conflict", return_value=True):
            stats = svc.auto_fix_dependency_issues(1, [issue], auto_fix_timing=True)
        assert stats["timing_fixed"] == 1


class TestProgressAutoServiceNotifications:
    def test_no_critical_tasks(self):
        db = _make_db()
        project = MagicMock(pm_id=1, project_name="P1")
        svc = ProgressAutoService(db)
        result = svc.send_forecast_notifications(1, project, [])
        assert result["total"] == 0

    def test_sends_to_pm(self):
        db = _make_db()
        project = MagicMock(pm_id=1, project_name="P1")
        task = MagicMock(owner_id=2)
        db.query.return_value.filter.return_value.first.side_effect = [task, None, None]
        
        forecast_item = MagicMock(task_id=1, critical=True, delay_days=5)

        svc = ProgressAutoService(db)
        with patch("app.services.progress_service.create_notification"):
            result = svc.send_forecast_notifications(1, project, [forecast_item])
        assert result["sent"] >= 0


class TestProgressAutoServiceRunAutoProcessing:
    def test_no_project(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ProgressAutoService(db)
        result = svc.run_auto_processing(1)
        assert result["success"] is False
        assert "error" in result

    def test_no_tasks(self):
        db = _make_db()
        project = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        db.query.return_value.filter.return_value.all.return_value = []
        svc = ProgressAutoService(db)
        result = svc.run_auto_processing(1)
        assert result["success"] is True
