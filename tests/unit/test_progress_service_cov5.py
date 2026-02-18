# -*- coding: utf-8 -*-
"""第五批：progress_service.py 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date
from decimal import Decimal

try:
    from app.services.progress_service import (
        progress_error_to_http,
        apply_task_progress_update,
    )
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="progress_service not importable")


def make_task(**kwargs):
    t = MagicMock()
    t.assignee_id = kwargs.get("assignee_id", 1)
    t.status = kwargs.get("status", "ACCEPTED")
    t.progress = kwargs.get("progress", 0)
    t.actual_hours = kwargs.get("actual_hours", None)
    t.updated_by = None
    t.updated_at = None
    return t


class TestProgressErrorToHttp:
    def test_task_not_found(self):
        exc = ValueError("任务不存在")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 404

    def test_permission_error(self):
        exc = ValueError("只能更新分配给自己的任务")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 403

    def test_no_permission(self):
        exc = ValueError("无权操作")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 403

    def test_bad_request(self):
        exc = ValueError("进度无效")
        http_exc = progress_error_to_http(exc)
        assert http_exc.status_code == 400


class TestApplyTaskProgressUpdate:
    def test_basic_update(self):
        task = make_task()
        apply_task_progress_update(task, 50, 1)
        assert task.progress == 50

    def test_wrong_assignee(self):
        task = make_task(assignee_id=2)
        with pytest.raises(ValueError, match="只能更新"):
            apply_task_progress_update(task, 50, 1)

    def test_completed_task_rejected(self):
        task = make_task(status="COMPLETED")
        with pytest.raises(ValueError, match="已完成"):
            apply_task_progress_update(task, 80, 1)

    def test_invalid_progress_negative(self):
        task = make_task()
        with pytest.raises(ValueError, match="进度必须在"):
            apply_task_progress_update(task, -1, 1)

    def test_invalid_progress_over_100(self):
        task = make_task()
        with pytest.raises(ValueError, match="进度必须在"):
            apply_task_progress_update(task, 101, 1)

    def test_progress_100_marks_completed(self):
        task = make_task(status="IN_PROGRESS")
        apply_task_progress_update(task, 100, 1)
        assert task.progress == 100

    def test_actual_hours_updated(self):
        task = make_task()
        apply_task_progress_update(task, 30, 1, actual_hours=Decimal("5.5"))
        assert task.actual_hours == Decimal("5.5")

    def test_skip_assignee_check(self):
        task = make_task(assignee_id=99)
        apply_task_progress_update(task, 20, 1, enforce_assignee=False)
        assert task.progress == 20
