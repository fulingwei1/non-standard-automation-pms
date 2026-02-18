# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - progress_service"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime
from decimal import Decimal

pytest.importorskip("app.services.progress_service")

from app.services.progress_service import (
    progress_error_to_http,
    apply_task_progress_update,
    update_task_progress,
    aggregate_task_progress,
    create_progress_log_entry,
    get_project_progress_summary,
    ProgressAutoService,
)


def make_task(**kwargs):
    t = MagicMock()
    t.id = kwargs.get("id", 1)
    t.assignee_id = kwargs.get("assignee_id", 10)
    t.status = kwargs.get("status", "IN_PROGRESS")
    t.progress = kwargs.get("progress", 50)
    t.actual_hours = kwargs.get("actual_hours", None)
    t.updated_by = None
    t.updated_at = None
    t.actual_start_date = kwargs.get("actual_start_date", None)
    t.actual_end_date = kwargs.get("actual_end_date", None)
    t.project_id = kwargs.get("project_id", 1)
    t.stage = kwargs.get("stage", None)
    t.is_delayed = False
    t.deadline = kwargs.get("deadline", datetime(2099, 1, 1))
    t.estimated_hours = kwargs.get("estimated_hours", 8.0)
    return t


def make_db():
    return MagicMock()


class TestProgressErrorToHttp:
    def test_task_not_found(self):
        exc = ValueError("任务不存在")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 404

    def test_forbidden(self):
        exc = ValueError("只能更新分配给自己的任务")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 403

    def test_bad_request(self):
        exc = ValueError("进度必须在0到100之间")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 400


class TestApplyTaskProgressUpdate:
    def test_basic_update(self):
        task = make_task(assignee_id=5, status="IN_PROGRESS")
        apply_task_progress_update(task, 60, 5, enforce_assignee=True)
        assert task.progress == 60

    def test_wrong_assignee_raises(self):
        task = make_task(assignee_id=5)
        with pytest.raises(ValueError, match="只能更新"):
            apply_task_progress_update(task, 60, 99, enforce_assignee=True)

    def test_completed_status_raises(self):
        task = make_task(assignee_id=5, status="COMPLETED")
        with pytest.raises(ValueError, match="无法更新进度"):
            apply_task_progress_update(task, 60, 5)

    def test_progress_100_sets_completed(self):
        task = make_task(assignee_id=5, status="IN_PROGRESS")
        apply_task_progress_update(task, 100, 5)
        assert task.status == "COMPLETED"

    def test_progress_out_of_range(self):
        task = make_task(assignee_id=5)
        with pytest.raises(ValueError, match="0到100"):
            apply_task_progress_update(task, 150, 5, enforce_assignee=False)

    def test_accepted_status_to_in_progress(self):
        task = make_task(assignee_id=5, status="ACCEPTED", actual_start_date=None)
        apply_task_progress_update(task, 30, 5)
        assert task.status == "IN_PROGRESS"


class TestUpdateTaskProgress:
    def test_task_not_found_raises(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="任务不存在"):
            update_task_progress(db, 999, 50, 10)

    def test_successful_update(self):
        db = make_db()
        task = make_task(assignee_id=10)
        db.query.return_value.filter.return_value.first.return_value = task

        with patch("app.services.progress_service.save_obj"), \
             patch("app.services.progress_service.aggregate_task_progress", return_value={}):
            result_task, agg = update_task_progress(
                db, 1, 60, 10, run_aggregation=True
            )
        assert result_task is task

    def test_creates_progress_log(self):
        db = make_db()
        task = make_task(assignee_id=10)
        db.query.return_value.filter.return_value.first.return_value = task

        with patch("app.services.progress_service.save_obj"), \
             patch("app.services.progress_service.aggregate_task_progress", return_value={}), \
             patch("app.services.progress_service.create_progress_log_entry") as mock_log:
            update_task_progress(
                db, 1, 60, 10,
                progress_note="正在进行",
                create_progress_log=True,
                run_aggregation=False,
            )
        mock_log.assert_called_once()


class TestAggregateTaskProgress:
    def test_no_task_returns_default(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        result = aggregate_task_progress(db, 999)
        assert result["project_progress_updated"] is False

    def test_with_task_no_project_id(self):
        db = make_db()
        task = MagicMock()
        task.project_id = None
        db.query.return_value.filter.return_value.first.return_value = task
        result = aggregate_task_progress(db, 1)
        assert result["project_progress_updated"] is False


class TestCreateProgressLogEntry:
    def test_creates_log(self):
        db = make_db()
        with patch("app.services.progress_service.save_obj") as mock_save:
            log = create_progress_log_entry(db, 1, 50, 2.0, "note", 10)
        assert log is not None

    def test_handles_exception(self):
        db = make_db()
        with patch("app.services.progress_service.save_obj", side_effect=Exception("DB error")):
            log = create_progress_log_entry(db, 1, 50, None, None, 10)
        assert log is None


class TestProgressAutoService:
    def test_apply_forecast_auto_block(self):
        db = make_db()
        svc = ProgressAutoService(db)

        from app.schemas.progress import TaskForecastItem
        forecast_item = MagicMock(spec=TaskForecastItem)
        forecast_item.task_id = 1
        forecast_item.delay_days = 10
        forecast_item.critical = True
        forecast_item.status = "Delayed"

        task = MagicMock()
        task.id = 1
        task.status = "IN_PROGRESS"
        db.query.return_value.filter.return_value.all.return_value = [task]

        result = svc.apply_forecast_to_tasks(
            1, [forecast_item], auto_block=True, delay_threshold=3
        )
        assert result["blocked"] == 1

    def test_apply_forecast_no_block_when_disabled(self):
        db = make_db()
        svc = ProgressAutoService(db)

        from app.schemas.progress import TaskForecastItem
        forecast_item = MagicMock(spec=TaskForecastItem)
        forecast_item.task_id = 1
        forecast_item.delay_days = 10
        forecast_item.critical = False
        forecast_item.status = "OnTrack"

        task = MagicMock()
        task.id = 1
        task.status = "IN_PROGRESS"
        db.query.return_value.filter.return_value.all.return_value = [task]

        result = svc.apply_forecast_to_tasks(
            1, [forecast_item], auto_block=False, delay_threshold=3
        )
        assert result["blocked"] == 0

    def test_auto_fix_dependency_cycles_skipped(self):
        db = make_db()
        svc = ProgressAutoService(db)

        issue = MagicMock()
        issue.issue_type = "CYCLE"

        result = svc.auto_fix_dependency_issues(1, [issue], auto_fix_timing=True)
        assert result["cycles_skipped"] == 1
        assert result["timing_fixed"] == 0

    def test_send_forecast_notifications_no_critical(self):
        db = make_db()
        svc = ProgressAutoService(db)
        project = MagicMock()
        project.pm_id = 1

        forecast_item = MagicMock()
        forecast_item.critical = False
        forecast_item.delay_days = 0

        result = svc.send_forecast_notifications(1, project, [forecast_item])
        assert result["total"] == 0
