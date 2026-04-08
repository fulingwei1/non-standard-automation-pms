# -*- coding: utf-8 -*-
"""
进度服务单元测试 - 覆盖率提升版
"""
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List, Optional

from app.services.progress_service import (
    progress_error_to_http,
    apply_task_progress_update,
    aggregate_task_progress,
    get_project_progress_summary,
)
from app.models.task_center import TaskUnified
from app.models.progress import Task, ProgressLog
from fastapi import HTTPException


class TestProgressErrorToHttp:
    """测试错误转换"""

    def test_task_not_found(self):
        """测试任务不存在错误"""
        exc = ValueError("任务不存在: 123")
        http_exc = progress_error_to_http(exc)
        
        assert http_exc.status_code == 404
        assert "任务不存在" in http_exc.detail

    def test_permission_denied(self):
        """测试权限错误"""
        exc = ValueError("无权操作此任务")
        http_exc = progress_error_to_http(exc)
        
        assert http_exc.status_code == 403
        assert "无权" in http_exc.detail

    def test_invalid_progress(self):
        """测试无效进度错误"""
        exc = ValueError("进度值必须为 0-100")
        http_exc = progress_error_to_http(exc)
        
        assert http_exc.status_code == 400

    def test_other_error(self):
        """测试其他错误"""
        exc = ValueError("未知错误")
        http_exc = progress_error_to_http(exc)
        
        assert http_exc.status_code == 400


class TestApplyTaskProgressUpdate:
    """测试进度更新应用"""

    def test_apply_progress_zero(self):
        """测试进度为0"""
        task = Mock(spec=TaskUnified)
        task.progress = 50
        task.status = "IN_PROGRESS"
        task.assignee_id = 1
        
        apply_task_progress_update(
            task=task,
            progress=0,
            updater_id=1,
            enforce_assignee=False
        )
        
        assert task.progress == 0

    def test_apply_progress_complete(self):
        """测试进度完成"""
        task = Mock(spec=TaskUnified)
        task.progress = 80
        task.status = "IN_PROGRESS"
        task.assignee_id = 1
        task.actual_hours = Decimal("10")
        
        apply_task_progress_update(
            task=task,
            progress=100,
            updater_id=1,
            reject_completed=False,
            enforce_assignee=False
        )
        
        assert task.progress == 100

    def test_apply_progress_with_actual_hours(self):
        """测试带实际工时的进度更新"""
        task = Mock(spec=TaskUnified)
        task.progress = 50
        task.status = "IN_PROGRESS"
        task.assignee_id = 1
        task.actual_hours = Decimal("8")
        
        apply_task_progress_update(
            task=task,
            progress=60,
            updater_id=1,
            actual_hours=Decimal("12"),
            enforce_assignee=False
        )
        
        assert task.progress == 60
        assert task.actual_hours == Decimal("12")


class TestAggregateTaskProgress:
    """测试进度聚合"""

    def test_aggregate_task_progress_method_exists(self):
        """测试进度聚合方法存在"""
        assert callable(aggregate_task_progress)

    def test_aggregate_task_progress_signature(self):
        """测试进度聚合方法签名"""
        import inspect
        sig = inspect.signature(aggregate_task_progress)
        params = list(sig.parameters.keys())
        assert 'db' in params
        assert 'task_id' in params


class TestGetProjectProgressSummary:
    """测试项目进度摘要"""

    def test_get_project_progress_summary_method_exists(self):
        """测试项目进度摘要方法存在"""
        assert callable(get_project_progress_summary)

    def test_get_project_progress_summary_signature(self):
        """测试项目进度摘要方法签名"""
        import inspect
        sig = inspect.signature(get_project_progress_summary)
        params = list(sig.parameters.keys())
        assert 'db' in params
        assert 'project_id' in params


class TestProgressServiceConstants:
    """测试常量"""

    def test_module_exists(self):
        """测试模块存在"""
        import app.services.progress_service as ps
        assert hasattr(ps, 'progress_error_to_http')
        assert hasattr(ps, 'apply_task_progress_update')
        assert hasattr(ps, 'aggregate_task_progress')