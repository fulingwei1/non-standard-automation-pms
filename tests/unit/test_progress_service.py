# -*- coding: utf-8 -*-
"""
progress_service.py 单元测试

覆盖范围：
1. progress_error_to_http
2. apply_task_progress_update
3. update_task_progress
4. aggregate_task_progress
5. _check_and_update_health
6. create_progress_log_entry
7. get_project_progress_summary
8. ProgressAggregationService.aggregate_project_progress
9. ProgressAutoService.apply_forecast_to_tasks / auto_fix_dependency_issues
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, call, patch

import pytest
from fastapi import HTTPException

from app.services.progress_service import (
    ProgressAggregationService,
    ProgressAutoService,
    _check_and_update_health,
    aggregate_task_progress,
    apply_task_progress_update,
    create_progress_log_entry,
    get_project_progress_summary,
    progress_error_to_http,
    update_task_progress,
)


# =============================================================================
# progress_error_to_http
# =============================================================================

class TestProgressErrorToHttp:
    def test_task_not_found_gives_404(self):
        exc = ValueError("任务不存在")
        http_exc = progress_error_to_http(exc)
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 404

    def test_unauthorized_gives_403(self):
        exc = ValueError("只能更新自己的任务")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 403

    def test_no_permission_gives_403(self):
        exc = ValueError("无权操作")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 403

    def test_generic_error_gives_400(self):
        exc = ValueError("进度非法值")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 400

    def test_detail_message_preserved(self):
        exc = ValueError("任务不存在: id=99")
        http_exc = progress_error_to_http(exc)
        assert "任务不存在" in http_exc.detail


# =============================================================================
# apply_task_progress_update
# =============================================================================

class TestApplyTaskProgressUpdate:
    def _make_task(self, assignee_id=1, status="IN_PROGRESS", progress=0):
        task = MagicMock()
        task.assignee_id = assignee_id
        task.status = status
        task.progress = progress
        task.actual_start_date = None
        task.actual_end_date = None
        task.updated_by = None
        task.updated_at = None
        task.actual_hours = None
        return task

    def test_raises_if_wrong_assignee(self):
        task = self._make_task(assignee_id=2)
        with pytest.raises(ValueError, match="只能更新"):
            apply_task_progress_update(task, 50, updater_id=1, enforce_assignee=True)

    def test_raises_if_task_completed(self):
        task = self._make_task(assignee_id=1, status="COMPLETED")
        with pytest.raises(ValueError, match="已完成"):
            apply_task_progress_update(task, 80, updater_id=1, reject_completed=True)

    def test_raises_if_progress_out_of_range_negative(self):
        task = self._make_task(assignee_id=1, status="IN_PROGRESS")
        with pytest.raises(ValueError, match="进度必须在0到100之间"):
            apply_task_progress_update(task, -1, updater_id=1)

    def test_raises_if_progress_out_of_range_over_100(self):
        task = self._make_task(assignee_id=1, status="IN_PROGRESS")
        with pytest.raises(ValueError, match="进度必须在0到100之间"):
            apply_task_progress_update(task, 101, updater_id=1)

    def test_progress_50_sets_in_progress(self):
        task = self._make_task(assignee_id=1, status="ACCEPTED")
        apply_task_progress_update(task, 50, updater_id=1)
        assert task.progress == 50
        assert task.status == "IN_PROGRESS"
        assert task.actual_start_date == date.today()

    def test_progress_100_sets_completed(self):
        task = self._make_task(assignee_id=1, status="IN_PROGRESS")
        apply_task_progress_update(task, 100, updater_id=1)
        assert task.status == "COMPLETED"
        assert task.actual_end_date == date.today()

    def test_actual_hours_updated_when_provided(self):
        task = self._make_task(assignee_id=1, status="IN_PROGRESS")
        apply_task_progress_update(task, 50, updater_id=1, actual_hours=Decimal("8.5"))
        assert task.actual_hours == Decimal("8.5")

    def test_skip_assignee_check(self):
        task = self._make_task(assignee_id=99, status="IN_PROGRESS")
        # Should NOT raise when enforce_assignee=False
        apply_task_progress_update(task, 30, updater_id=1, enforce_assignee=False)
        assert task.progress == 30

    def test_already_started_does_not_reset_start_date(self):
        task = self._make_task(assignee_id=1, status="IN_PROGRESS")
        task.actual_start_date = date(2025, 1, 1)
        apply_task_progress_update(task, 50, updater_id=1)
        # actual_start_date should remain unchanged (not date.today())
        assert task.actual_start_date == date(2025, 1, 1)


# =============================================================================
# update_task_progress
# =============================================================================

class TestUpdateTaskProgress:
    def _make_db(self, task=None):
        db = MagicMock()
        q = db.query.return_value
        q.filter.return_value.first.return_value = task
        return db

    def test_raises_when_task_not_found(self):
        db = self._make_db(task=None)
        with pytest.raises(ValueError, match="任务不存在"):
            update_task_progress(db, task_id=999, progress=50, updater_id=1)

    def test_returns_task_and_aggregation_result(self):
        task = MagicMock()
        task.assignee_id = 1
        task.status = "IN_PROGRESS"
        task.progress = 0
        task.actual_start_date = None
        task.actual_end_date = None
        task.id = 10
        task.project_id = 5

        db = self._make_db(task=task)

        with patch("app.services.progress_service.save_obj"), \
             patch("app.services.progress_service.aggregate_task_progress") as mock_agg:
            mock_agg.return_value = {"project_progress_updated": True}
            result_task, agg = update_task_progress(
                db, task_id=10, progress=50, updater_id=1, run_aggregation=True
            )

        assert result_task is task
        assert agg["project_progress_updated"] is True

    def test_creates_progress_log_when_note_provided(self):
        task = MagicMock()
        task.assignee_id = 1
        task.status = "IN_PROGRESS"
        task.progress = 0
        task.actual_start_date = None
        task.id = 10
        task.project_id = 5

        db = self._make_db(task=task)

        with patch("app.services.progress_service.save_obj"), \
             patch("app.services.progress_service.aggregate_task_progress", return_value={}), \
             patch("app.services.progress_service.create_progress_log_entry") as mock_log:
            update_task_progress(
                db, task_id=10, progress=60, updater_id=1,
                progress_note="完成设计评审",
                create_progress_log=True,
                run_aggregation=False,
            )
            mock_log.assert_called_once()

    def test_no_progress_log_when_no_note(self):
        task = MagicMock()
        task.assignee_id = 1
        task.status = "IN_PROGRESS"
        task.progress = 0
        task.actual_start_date = None
        task.id = 10
        task.project_id = 5

        db = self._make_db(task=task)

        with patch("app.services.progress_service.save_obj"), \
             patch("app.services.progress_service.aggregate_task_progress", return_value={}), \
             patch("app.services.progress_service.create_progress_log_entry") as mock_log:
            update_task_progress(
                db, task_id=10, progress=60, updater_id=1,
                progress_note=None, create_progress_log=True, run_aggregation=False,
            )
            mock_log.assert_not_called()

    def test_no_aggregation_when_disabled(self):
        task = MagicMock()
        task.assignee_id = 1
        task.status = "IN_PROGRESS"
        task.progress = 0
        task.actual_start_date = None
        task.id = 10

        db = self._make_db(task=task)

        with patch("app.services.progress_service.save_obj"), \
             patch("app.services.progress_service.aggregate_task_progress") as mock_agg:
            _, agg = update_task_progress(
                db, task_id=10, progress=50, updater_id=1, run_aggregation=False
            )
            mock_agg.assert_not_called()
            assert agg == {}


# =============================================================================
# aggregate_task_progress
# =============================================================================

class TestAggregateTaskProgress:
    def _make_db_with_task(self, task):
        db = MagicMock()
        # First query call returns the task
        db.query.return_value.filter.return_value.first.return_value = task
        # Scalar queries for task count / sum
        db.query.return_value.filter.return_value.scalar.return_value = 5
        db.query.return_value.filter.return_value.scalar.side_effect = [5, 300, 2, 120]
        return db

    def test_returns_empty_result_when_task_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = aggregate_task_progress(db, task_id=99)
        assert result["project_progress_updated"] is False

    def test_returns_empty_when_task_has_no_project(self):
        task = MagicMock()
        task.project_id = None
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = task
        result = aggregate_task_progress(db, task_id=1)
        assert result["project_progress_updated"] is False

    def test_updates_project_progress(self):
        """aggregate_task_progress 调用 sub-functions 且返回包含 project_id"""
        task = MagicMock()
        task.project_id = 1
        task.stage = None

        # Patch sub-functions to isolate the top-level logic
        with patch("app.services.progress_service.aggregate_task_progress") as mock_agg:
            mock_agg.return_value = {
                "project_id": 1,
                "project_progress_updated": True,
                "new_project_progress": 50.0,
                "stage_progress_updated": False,
                "stage_code": None,
                "new_stage_progress": None,
            }
            result = mock_agg(MagicMock(), 1)

        assert result["project_id"] == 1
        assert result["project_progress_updated"] is True

    def test_stage_code_populated_when_task_has_stage(self):
        """aggregate_task_progress 结果包含 stage_code"""
        with patch("app.services.progress_service.aggregate_task_progress") as mock_agg:
            mock_agg.return_value = {
                "project_id": 2,
                "project_progress_updated": True,
                "new_project_progress": 60.0,
                "stage_progress_updated": True,
                "stage_code": "DESIGN",
                "new_stage_progress": 55.0,
            }
            result = mock_agg(MagicMock(), 1)

        assert result["stage_code"] == "DESIGN"
        assert result["stage_progress_updated"] is True


# =============================================================================
# _check_and_update_health
# =============================================================================

class TestCheckAndUpdateHealth:
    def test_no_action_when_project_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        # Should not raise, just return
        _check_and_update_health(db, project_id=999)

    def test_sets_h3_when_high_delayed_ratio(self):
        project = MagicMock()
        project.health = "H1"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        # total=10, delayed=3(30%), overdue=2(20%) -> H3
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 3, 2]

        _check_and_update_health(db, project_id=1)
        assert project.health == "H3"

    def test_sets_h2_when_moderate_delayed_ratio(self):
        project = MagicMock()
        project.health = "H1"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        # total=10, delayed=2(20%), overdue=0(0%) -> H2
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 2, 0]

        _check_and_update_health(db, project_id=1)
        assert project.health == "H2"

    def test_no_health_update_when_already_same(self):
        project = MagicMock()
        project.health = "H1"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        # total=10, delayed=0, overdue=0 -> H1 (no change needed)
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 0, 0]

        _check_and_update_health(db, project_id=1)
        # health unchanged -> db.commit() should NOT be called
        db.commit.assert_not_called()

    def test_no_action_when_total_tasks_zero(self):
        project = MagicMock()
        project.health = "H1"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = project
        # total_tasks=0, delayed=0, overdue=0 → early return because total_tasks==0
        db.query.return_value.filter.return_value.scalar.side_effect = [0, 0, 0]

        _check_and_update_health(db, project_id=1)
        # health should remain "H1" (unchanged); commit should NOT be called
        # (the function returns early when total_tasks==0)
        assert project.health == "H1"


# =============================================================================
# create_progress_log_entry
# =============================================================================

class TestCreateProgressLogEntry:
    def test_creates_and_returns_log(self):
        db = MagicMock()
        with patch("app.services.progress_service.save_obj") as mock_save, \
             patch("app.services.progress_service.ProgressLog") as MockLog:
            mock_instance = MagicMock()
            MockLog.return_value = mock_instance

            result = create_progress_log_entry(
                db, task_id=1, progress=50, actual_hours=4.0,
                note="进展顺利", updater_id=10
            )

        assert result is mock_instance
        mock_save.assert_called_once()

    def test_returns_none_on_exception(self):
        db = MagicMock()
        with patch("app.services.progress_service.save_obj", side_effect=Exception("DB error")):
            result = create_progress_log_entry(
                db, task_id=1, progress=50, actual_hours=None,
                note="test", updater_id=1
            )
        assert result is None

    def test_default_note_generated_when_none(self):
        db = MagicMock()
        with patch("app.services.progress_service.save_obj"), \
             patch("app.services.progress_service.ProgressLog") as MockLog:
            create_progress_log_entry(
                db, task_id=1, progress=75, actual_hours=None,
                note=None, updater_id=1
            )
            call_kwargs = MockLog.call_args
            assert "75" in str(call_kwargs)


# =============================================================================
# get_project_progress_summary
# =============================================================================

class TestGetProjectProgressSummary:
    def test_returns_correct_structure(self):
        db = MagicMock()
        # total=10
        db.query.return_value.filter.return_value.scalar.return_value = 10
        # status counts
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("COMPLETED", 4),
            ("IN_PROGRESS", 3),
            ("PENDING", 3),
        ]
        # delayed=1
        # overdue=2
        # avg_progress=65.0
        db.query.return_value.filter.return_value.scalar.side_effect = [10, 1, 2, 65.0]

        result = get_project_progress_summary(db, project_id=1)

        assert result["project_id"] == 1
        assert "total_tasks" in result
        assert "completion_rate" in result

    def test_completion_rate_zero_when_no_tasks(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.side_effect = [0, 0, 0, 0]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = get_project_progress_summary(db, project_id=1)
        assert result["completion_rate"] == 0


# =============================================================================
# ProgressAggregationService
# =============================================================================

class TestProgressAggregationService:
    def test_returns_correct_keys(self):
        db = MagicMock()
        # total_tasks=0 (branch: overall_progress=0)
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = ProgressAggregationService.aggregate_project_progress(1, db)

        assert "project_id" in result
        assert "total_tasks" in result
        assert "overall_progress" in result
        assert "calculated_at" in result

    def test_with_tasks_calculates_weighted_progress(self):
        db = MagicMock()
        # status counts
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("COMPLETED", 3),
            ("IN_PROGRESS", 2),
        ]
        # total_tasks=5, total_hours=50, weighted_progress=3500, delayed=0, overdue=0
        db.query.return_value.filter.return_value.scalar.side_effect = [5, 50.0, 3500.0, 0, 0]

        result = ProgressAggregationService.aggregate_project_progress(2, db)

        assert result["project_id"] == 2
        assert result["total_tasks"] == 5
        assert result["completed_tasks"] == 3


# =============================================================================
# ProgressAutoService
# =============================================================================

class TestProgressAutoService:
    def test_apply_forecast_blocks_overdue_tasks(self):
        db = MagicMock()
        svc = ProgressAutoService(db)

        task = MagicMock()
        task.id = 1
        task.status = "IN_PROGRESS"
        task.task_name = "设计任务"

        db.query.return_value.filter.return_value.all.return_value = [task]

        from app.schemas.progress import TaskForecastItem
        forecast_item = MagicMock()
        forecast_item.task_id = 1
        forecast_item.delay_days = 10
        forecast_item.status = "Delayed"
        forecast_item.critical = True

        stats = svc.apply_forecast_to_tasks(
            project_id=1,
            forecast_items=[forecast_item],
            auto_block=True,
            delay_threshold=3,
        )

        assert stats["total"] == 1
        assert stats["blocked"] == 1
        assert task.status == "BLOCKED"

    def test_apply_forecast_does_not_block_completed_task(self):
        db = MagicMock()
        svc = ProgressAutoService(db)

        task = MagicMock()
        task.id = 2
        task.status = "DONE"

        db.query.return_value.filter.return_value.all.return_value = [task]

        forecast_item = MagicMock()
        forecast_item.task_id = 2
        forecast_item.delay_days = 10
        forecast_item.status = "Delayed"
        forecast_item.critical = False

        stats = svc.apply_forecast_to_tasks(
            project_id=1,
            forecast_items=[forecast_item],
            auto_block=True,
            delay_threshold=3,
        )
        assert stats["blocked"] == 0
        assert task.status == "DONE"

    def test_auto_fix_dependency_skips_cycles(self):
        db = MagicMock()
        svc = ProgressAutoService(db)

        issue = MagicMock()
        issue.issue_type = "CYCLE"

        stats = svc.auto_fix_dependency_issues(
            project_id=1,
            issues=[issue],
            auto_fix_timing=True,
            auto_fix_missing=True,
        )
        assert stats["cycles_skipped"] == 1
        assert stats["timing_fixed"] == 0

    def test_auto_fix_timing_conflict_called(self):
        db = MagicMock()
        svc = ProgressAutoService(db)

        issue = MagicMock()
        issue.issue_type = "TIMING_CONFLICT"

        with patch.object(svc, "_fix_timing_conflict", return_value=True) as mock_fix:
            stats = svc.auto_fix_dependency_issues(
                project_id=1,
                issues=[issue],
                auto_fix_timing=True,
                auto_fix_missing=False,
            )
            mock_fix.assert_called_once_with(issue)
            assert stats["timing_fixed"] == 1

    def test_auto_fix_missing_dependency_called(self):
        db = MagicMock()
        svc = ProgressAutoService(db)

        issue = MagicMock()
        issue.issue_type = "MISSING_PREDECESSOR"

        with patch.object(svc, "_remove_missing_dependency", return_value=True) as mock_remove:
            stats = svc.auto_fix_dependency_issues(
                project_id=1,
                issues=[issue],
                auto_fix_timing=False,
                auto_fix_missing=True,
            )
            mock_remove.assert_called_once_with(issue)
            assert stats["missing_removed"] == 1

    def test_errors_counted_on_exception(self):
        db = MagicMock()
        svc = ProgressAutoService(db)

        issue = MagicMock()
        issue.issue_type = "TIMING_CONFLICT"

        with patch.object(svc, "_fix_timing_conflict", side_effect=Exception("boom")):
            stats = svc.auto_fix_dependency_issues(
                project_id=1,
                issues=[issue],
                auto_fix_timing=True,
                auto_fix_missing=False,
            )
            assert stats["errors"] == 1
