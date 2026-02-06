# -*- coding: utf-8 -*-
"""
TaskProgressService 单元测试

验证任务进度更新统一服务的校验、状态转换与聚合调用。
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.task_progress_service import update_task_progress


@pytest.mark.unit
class TestTaskProgressService:
    """任务进度更新服务"""

    def _make_task(
        self,
        task_id=1,
        assignee_id=10,
        status="ACCEPTED",
        progress=0,
        actual_start_date=None,
        actual_end_date=None,
    ):
        task = MagicMock()
        task.id = task_id
        task.assignee_id = assignee_id
        task.status = status
        task.progress = progress
        task.actual_start_date = actual_start_date
        task.actual_end_date = actual_end_date
        task.actual_hours = None
        task.updated_by = None
        task.updated_at = None
        return task

    def test_task_not_found_raises(self):
        """任务不存在时抛出 ValueError"""
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="任务不存在"):
            update_task_progress(db, task_id=999, progress=50, updater_id=1)

    def test_wrong_assignee_raises(self):
        """非任务负责人更新时抛出 ValueError"""
        db = MagicMock()
        task = self._make_task(assignee_id=10)
        db.query.return_value.filter.return_value.first.return_value = task

        with pytest.raises(ValueError, match="只能更新分配给自己的任务"):
            update_task_progress(db, task_id=1, progress=50, updater_id=99)

    def test_completed_task_reject_raises(self):
        """已完成任务在 reject_completed=True 时抛出 ValueError"""
        db = MagicMock()
        task = self._make_task(assignee_id=10, status="COMPLETED")
        db.query.return_value.filter.return_value.first.return_value = task

        with pytest.raises(ValueError, match="无法更新进度"):
            update_task_progress(
                db, task_id=1, progress=50, updater_id=10, reject_completed=True
            )

    def test_progress_below_zero_raises(self):
        """进度 < 0 时抛出 ValueError"""
        db = MagicMock()
        task = self._make_task(assignee_id=10)
        db.query.return_value.filter.return_value.first.return_value = task

        with pytest.raises(ValueError, match="进度必须在0到100之间"):
            update_task_progress(db, task_id=1, progress=-1, updater_id=10)

    def test_progress_over_100_raises(self):
        """进度 > 100 时抛出 ValueError"""
        db = MagicMock()
        task = self._make_task(assignee_id=10)
        db.query.return_value.filter.return_value.first.return_value = task

        with pytest.raises(ValueError, match="进度必须在0到100之间"):
            update_task_progress(db, task_id=1, progress=101, updater_id=10)

    def test_success_updates_fields_and_commits(self):
        """成功时更新进度、updated_by/updated_at 并 commit"""
        db = MagicMock()
        task = self._make_task(assignee_id=10, status="ACCEPTED")
        db.query.return_value.filter.return_value.first.return_value = task

        with patch(
            "app.services.progress_aggregation_service.aggregate_task_progress",
            return_value={"project_progress_updated": False, "stage_progress_updated": False},
        ):
            out_task, agg = update_task_progress(
                db,
                task_id=1,
                progress=50,
                updater_id=10,
                run_aggregation=True,
                create_progress_log=False,
            )

        assert out_task is task
        assert task.progress == 50
        assert task.updated_by == 10
        assert task.updated_at is not None
        db.add.assert_called_once_with(task)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(task)

    def test_progress_gt_zero_sets_in_progress_and_start_date(self):
        """进度 > 0 且状态为 ACCEPTED 时设为 IN_PROGRESS 并设置 actual_start_date"""
        db = MagicMock()
        task = self._make_task(assignee_id=10, status="ACCEPTED", actual_start_date=None)
        db.query.return_value.filter.return_value.first.return_value = task

        with patch(
            "app.services.progress_aggregation_service.aggregate_task_progress",
            return_value={},
        ), patch("app.services.task_progress_service.date") as mdate:
            mdate.today.return_value = date(2026, 1, 30)
            update_task_progress(
                db, task_id=1, progress=10, updater_id=10,
                create_progress_log=False, run_aggregation=False,
            )

        assert task.status == "IN_PROGRESS"
        assert task.actual_start_date == date(2026, 1, 30)

    def test_progress_100_sets_completed_and_end_date(self):
        """进度 100 时设为 COMPLETED 并设置 actual_end_date"""
        db = MagicMock()
        task = self._make_task(assignee_id=10, status="IN_PROGRESS", actual_end_date=None)
        db.query.return_value.filter.return_value.first.return_value = task

        with patch(
            "app.services.progress_aggregation_service.aggregate_task_progress",
            return_value={},
        ), patch("app.services.task_progress_service.date") as mdate:
            mdate.today.return_value = date(2026, 1, 30)
            update_task_progress(
                db, task_id=1, progress=100, updater_id=10,
                create_progress_log=False, run_aggregation=False,
            )

        assert task.status == "COMPLETED"
        assert task.actual_end_date == date(2026, 1, 30)

    def test_actual_hours_updated_when_provided(self):
        """传入 actual_hours 时更新任务工时"""
        db = MagicMock()
        task = self._make_task(assignee_id=10)
        task.actual_hours = None
        db.query.return_value.filter.return_value.first.return_value = task

        with patch(
            "app.services.progress_aggregation_service.aggregate_task_progress",
            return_value={},
        ):
            update_task_progress(
                db,
                task_id=1,
                progress=50,
                updater_id=10,
                actual_hours=Decimal("3.5"),
                create_progress_log=False,
                run_aggregation=False,
            )

        assert task.actual_hours == Decimal("3.5")
