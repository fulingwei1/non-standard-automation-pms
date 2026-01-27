# -*- coding: utf-8 -*-
"""
progress_auto_service 单元测试

测试进度跟踪自动化服务的各个方法
"""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.progress import DependencyIssue, TaskForecastItem
from app.services.progress_auto_service import ProgressAutoService


@pytest.mark.unit
class TestProgressAutoServiceInit:
    """测试服务初始化"""

    def test_init(self):
        """测试初始化"""
        mock_db = MagicMock()
        service = ProgressAutoService(mock_db)
        assert service.db == mock_db


@pytest.mark.unit
class TestApplyForecastToTasks:
    """测试 apply_forecast_to_tasks 方法"""

    def test_apply_forecast_empty_items(self):
        """测试空预测列表"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ProgressAutoService(mock_db)
        result = service.apply_forecast_to_tasks(
        project_id=1,
        forecast_items=[]
        )

        assert result["total"] == 0
        assert result["blocked"] == 0
        assert result["risk_tagged"] == 0

    def test_apply_forecast_auto_block_exceeds_threshold(self):
        """测试自动阻塞超过延迟阈值的任务"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.task_name = "Test Task"
        mock_task.status = "IN_PROGRESS"
        mock_task.progress_percent = 50

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        forecast_item = TaskForecastItem(
        task_id=1,
        task_name="Test Task",
        progress_percent=50,
        predicted_finish_date=date.today() + timedelta(days=10),
        plan_end=date.today(),
        delay_days=5,
        status="Delayed",
        critical=True
        )

        service = ProgressAutoService(mock_db)
        result = service.apply_forecast_to_tasks(
        project_id=1,
        forecast_items=[forecast_item],
        auto_block=True,
        delay_threshold=3
        )

        assert result["blocked"] == 1
        assert mock_task.status == "BLOCKED"
        assert "预测延迟 5 天" in mock_task.block_reason

    def test_apply_forecast_skip_done_task(self):
        """测试跳过已完成任务"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "DONE"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        forecast_item = TaskForecastItem(
        task_id=1,
        task_name="Test Task",
        progress_percent=100,
        predicted_finish_date=date.today(),
        delay_days=5,
        status="Delayed",
        critical=True
        )

        service = ProgressAutoService(mock_db)
        result = service.apply_forecast_to_tasks(
        project_id=1,
        forecast_items=[forecast_item],
        auto_block=True,
        delay_threshold=3
        )

        assert result["blocked"] == 0
        assert mock_task.status == "DONE"  # Unchanged

    def test_apply_forecast_skip_cancelled_task(self):
        """测试跳过已取消任务"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = "CANCELLED"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        forecast_item = TaskForecastItem(
        task_id=1,
        task_name="Test Task",
        progress_percent=0,
        predicted_finish_date=date.today(),
        delay_days=10,
        status="Delayed",
        critical=True
        )

        service = ProgressAutoService(mock_db)
        result = service.apply_forecast_to_tasks(
        project_id=1,
        forecast_items=[forecast_item],
        auto_block=True,
        delay_threshold=3
        )

        assert result["blocked"] == 0

    def test_apply_forecast_risk_tagged(self):
        """测试为高风险任务添加进度日志"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.task_name = "Test Task"
        mock_task.status = "IN_PROGRESS"
        mock_task.progress_percent = 30

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        forecast_item = TaskForecastItem(
        task_id=1,
        task_name="Test Task",
        progress_percent=30,
        predicted_finish_date=date.today() + timedelta(days=10),
        delay_days=5,
        status="Delayed",
        critical=True
        )

        service = ProgressAutoService(mock_db)
        result = service.apply_forecast_to_tasks(
        project_id=1,
        forecast_items=[forecast_item],
        auto_block=False
        )

        assert result["risk_tagged"] == 1
        assert mock_db.add.called

    def test_apply_forecast_no_matching_task(self):
        """测试预测项没有匹配的任务"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 2  # Different ID

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        forecast_item = TaskForecastItem(
        task_id=1,  # No match
        task_name="Test Task",
        progress_percent=30,
        predicted_finish_date=date.today(),
        delay_days=5,
        status="Delayed"
        )

        service = ProgressAutoService(mock_db)
        result = service.apply_forecast_to_tasks(
        project_id=1,
        forecast_items=[forecast_item]
        )

        assert result["blocked"] == 0
        assert result["risk_tagged"] == 0


@pytest.mark.unit
class TestAutoFixDependencyIssues:
    """测试 auto_fix_dependency_issues 方法"""

    def test_empty_issues(self):
        """测试空问题列表"""
        mock_db = MagicMock()
        service = ProgressAutoService(mock_db)

        result = service.auto_fix_dependency_issues(
        project_id=1,
        issues=[]
        )

        assert result["total_issues"] == 0
        assert result["timing_fixed"] == 0
        assert result["missing_removed"] == 0

    def test_skip_cycle_dependency(self):
        """测试跳过循环依赖"""
        mock_db = MagicMock()
        service = ProgressAutoService(mock_db)

        issue = DependencyIssue(
        issue_type="CYCLE",
        severity="HIGH",
        task_id=1,
        task_name="Task 1",
        detail="循环依赖: Task 1 -> Task 2 -> Task 1"
        )

        result = service.auto_fix_dependency_issues(
        project_id=1,
        issues=[issue]
        )

        assert result["cycles_skipped"] == 1
        assert result["timing_fixed"] == 0

    def test_fix_timing_conflict(self):
        """测试修复时序冲突"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.task_name = "Task 1"
        mock_task.plan_start = date.today()
        mock_task.plan_end = date.today() + timedelta(days=5)
        mock_task.progress_percent = 0

        mock_pred_task = MagicMock()
        mock_pred_task.id = 2
        mock_pred_task.actual_end = date.today() + timedelta(days=3)
        mock_pred_task.plan_end = date.today() + timedelta(days=3)

        mock_dependency = MagicMock()
        mock_dependency.task_id = 1
        mock_dependency.depends_on_task_id = 2
        mock_dependency.lag_days = 1

        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Task':
        def filter_side_effect(*args):
            filter_mock = MagicMock()
            filter_mock.first.return_value = mock_task if mock_task.id == 1 else mock_pred_task
            filter_mock.all.return_value = []
            return filter_mock
            query_mock.filter.side_effect = filter_side_effect
        elif model.__name__ == 'TaskDependency':
            query_mock.filter.return_value.all.return_value = [mock_dependency]
            return query_mock

            mock_db.query.side_effect = query_side_effect

            service = ProgressAutoService(mock_db)

            with patch.object(service, '_fix_timing_conflict', return_value=True):
                issue = DependencyIssue(
                issue_type="TIMING_CONFLICT",
                severity="MEDIUM",
                task_id=1,
                task_name="Task 1",
                detail="时序冲突"
                )

                result = service.auto_fix_dependency_issues(
                project_id=1,
                issues=[issue],
                auto_fix_timing=True
                )

                assert result["timing_fixed"] == 1

    def test_fix_missing_dependency(self):
        """测试移除缺失依赖"""
        mock_db = MagicMock()
        service = ProgressAutoService(mock_db)

        with patch.object(service, '_remove_missing_dependency', return_value=True):
            issue = DependencyIssue(
            issue_type="MISSING_PREDECESSOR",
            severity="LOW",
            task_id=1,
            detail="依赖任务不存在"
            )

            result = service.auto_fix_dependency_issues(
            project_id=1,
            issues=[issue],
            auto_fix_missing=True
            )

            assert result["missing_removed"] == 1

    def test_error_handling(self):
        """测试错误处理"""
        mock_db = MagicMock()
        service = ProgressAutoService(mock_db)

        with patch.object(service, '_fix_timing_conflict', side_effect=Exception("Test error")):
            issue = DependencyIssue(
            issue_type="TIMING_CONFLICT",
            severity="MEDIUM",
            task_id=1,
            detail="时序冲突"
            )

            result = service.auto_fix_dependency_issues(
            project_id=1,
            issues=[issue],
            auto_fix_timing=True
            )

            assert result["errors"] == 1


@pytest.mark.unit
class TestFixTimingConflict:
    """测试 _fix_timing_conflict 方法"""

    def test_task_not_found(self):
        """测试任务不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProgressAutoService(mock_db)

        issue = DependencyIssue(
        issue_type="TIMING_CONFLICT",
        severity="MEDIUM",
        task_id=999,
        detail="任务不存在"
        )

        result = service._fix_timing_conflict(issue)
        assert result is False

    def test_no_dependencies(self):
        """测试没有依赖"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 1

        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Task':
                query_mock.filter.return_value.first.return_value = mock_task
        elif model.__name__ == 'TaskDependency':
            query_mock.filter.return_value.all.return_value = []
            return query_mock

            mock_db.query.side_effect = query_side_effect

            service = ProgressAutoService(mock_db)

            issue = DependencyIssue(
            issue_type="TIMING_CONFLICT",
            severity="MEDIUM",
            task_id=1,
            detail="无依赖"
            )

            result = service._fix_timing_conflict(issue)
            assert result is False

    def test_successful_timing_fix(self):
        """测试成功修复时序"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.task_name = "Task 1"
        mock_task.plan_start = date(2024, 1, 1)
        mock_task.plan_end = date(2024, 1, 5)
        mock_task.progress_percent = 0

        mock_pred_task = MagicMock()
        mock_pred_task.id = 2
        mock_pred_task.actual_end = date(2024, 1, 10)
        mock_pred_task.plan_end = date(2024, 1, 8)

        mock_dependency = MagicMock()
        mock_dependency.depends_on_task_id = 2
        mock_dependency.lag_days = 2

        call_count = 0

        def query_side_effect(model):
            nonlocal call_count
            query_mock = MagicMock()
            if model.__name__ == 'Task':
                call_count += 1
                if call_count == 1:
                    query_mock.filter.return_value.first.return_value = mock_task
        else:
            query_mock.filter.return_value.first.return_value = mock_pred_task
        elif model.__name__ == 'TaskDependency':
            query_mock.filter.return_value.all.return_value = [mock_dependency]
            return query_mock

            mock_db.query.side_effect = query_side_effect

            service = ProgressAutoService(mock_db)

            issue = DependencyIssue(
            issue_type="TIMING_CONFLICT",
            severity="MEDIUM",
            task_id=1,
            detail="时序冲突"
            )

            result = service._fix_timing_conflict(issue)

            assert result is True
            # Plan start should be updated based on predecessor end + lag
            assert mock_task.plan_start == date(2024, 1, 10) + timedelta(days=2)
            assert mock_db.add.called

    def test_pred_task_not_found(self):
        """测试前置任务不存在"""
        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.task_name = "Task 1"

        mock_dependency = MagicMock()
        mock_dependency.depends_on_task_id = 999
        mock_dependency.lag_days = 0

        call_count = 0

        def query_side_effect(model):
            nonlocal call_count
            query_mock = MagicMock()
            if model.__name__ == 'Task':
                call_count += 1
                if call_count == 1:
                    query_mock.filter.return_value.first.return_value = mock_task
        else:
            query_mock.filter.return_value.first.return_value = None
        elif model.__name__ == 'TaskDependency':
            query_mock.filter.return_value.all.return_value = [mock_dependency]
            return query_mock

            mock_db.query.side_effect = query_side_effect

            service = ProgressAutoService(mock_db)

            issue = DependencyIssue(
            issue_type="TIMING_CONFLICT",
            severity="MEDIUM",
            task_id=1,
            detail="时序冲突"
            )

            result = service._fix_timing_conflict(issue)
            assert result is False


@pytest.mark.unit
class TestRemoveMissingDependency:
    """测试 _remove_missing_dependency 方法"""

    def test_no_dependencies_to_remove(self):
        """测试没有依赖需要移除"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ProgressAutoService(mock_db)

        issue = DependencyIssue(
        issue_type="MISSING_PREDECESSOR",
        severity="LOW",
        task_id=1,
        detail="无依赖"
        )

        result = service._remove_missing_dependency(issue)
        assert result is False

    def test_dependency_exists(self):
        """测试依赖任务存在（不需要移除）"""
        mock_db = MagicMock()

        mock_dep = MagicMock()
        mock_dep.depends_on_task_id = 2

        mock_pred_task = MagicMock()
        mock_pred_task.id = 2

        call_count = 0

        def query_side_effect(model):
            nonlocal call_count
            query_mock = MagicMock()
            if model.__name__ == 'TaskDependency':
                query_mock.filter.return_value.all.return_value = [mock_dep]
        elif model.__name__ == 'Task':
            call_count += 1
            query_mock.filter.return_value.first.return_value = mock_pred_task
            return query_mock

            mock_db.query.side_effect = query_side_effect

            service = ProgressAutoService(mock_db)

            issue = DependencyIssue(
            issue_type="MISSING_PREDECESSOR",
            severity="LOW",
            task_id=1,
            detail="缺失依赖"
            )

            result = service._remove_missing_dependency(issue)
            assert result is False  # Nothing removed


@pytest.mark.unit
class TestSendForecastNotifications:
    """测试 send_forecast_notifications 方法"""

    def test_no_critical_tasks(self):
        """测试没有高风险任务"""
        mock_db = MagicMock()
        mock_project = MagicMock()
        mock_project.pm_id = 1

        service = ProgressAutoService(mock_db)

        forecast_items = [
        TaskForecastItem(
        task_id=1,
        task_name="Task 1",
        progress_percent=80,
        predicted_finish_date=date.today(),
        delay_days=0,
        status="OnTrack",
        critical=False
        )
        ]

        result = service.send_forecast_notifications(
        project_id=1,
        project=mock_project,
        forecast_items=forecast_items
        )

        assert result["total"] == 0
        assert result["sent"] == 0
        assert result["skipped"] == "no_critical_tasks"

    @patch('app.services.progress_auto_service.create_notification')
    def test_send_notifications_to_pm(self, mock_create_notification):
        """测试向项目经理发送通知"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing notification

        mock_project = MagicMock()
        mock_project.pm_id = 1
        mock_project.project_name = "Test Project"

        mock_task = MagicMock()
        mock_task.owner_id = 2

        # Make query return task when asked
        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Notification':
                query_mock.filter.return_value.first.return_value = None
        elif model.__name__ == 'Task':
            query_mock.filter.return_value.first.return_value = mock_task
            return query_mock

            mock_db.query.side_effect = query_side_effect

            service = ProgressAutoService(mock_db)

            forecast_items = [
            TaskForecastItem(
            task_id=1,
            task_name="Critical Task",
            progress_percent=30,
            predicted_finish_date=date.today() + timedelta(days=10),
            delay_days=5,
            status="Delayed",
            critical=True
            )
            ]

            result = service.send_forecast_notifications(
            project_id=1,
            project=mock_project,
            forecast_items=forecast_items
            )

            assert result["total"] == 2  # PM + task owner
            assert result["sent"] == 2
            assert result["critical_task_count"] == 1

    @patch('app.services.progress_auto_service.create_notification')
    def test_skip_duplicate_notification(self, mock_create_notification):
        """测试跳过重复通知"""
        mock_db = MagicMock()

        existing_notification = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_notification

        mock_project = MagicMock()
        mock_project.pm_id = 1
        mock_project.project_name = "Test Project"

        service = ProgressAutoService(mock_db)

        forecast_items = [
        TaskForecastItem(
        task_id=1,
        task_name="Critical Task",
        progress_percent=30,
        predicted_finish_date=date.today() + timedelta(days=10),
        delay_days=5,
        status="Delayed",
        critical=True
        )
        ]

        result = service.send_forecast_notifications(
        project_id=1,
        project=mock_project,
        forecast_items=forecast_items
        )

        assert result["sent"] == 0  # Notification skipped due to duplicate


@pytest.mark.unit
class TestRunAutoProcessing:
    """测试 run_auto_processing 方法"""

    def test_project_not_found(self):
        """测试项目不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ProgressAutoService(mock_db)
        result = service.run_auto_processing(project_id=999)

        assert result["success"] is False
        assert "项目不存在" in result.get("error", "")

    def test_no_tasks(self):
        """测试没有任务"""
        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1

        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model.__name__ == 'Task':
            query_mock.options.return_value.filter.return_value.all.return_value = []
            return query_mock

            mock_db.query.side_effect = query_side_effect

            service = ProgressAutoService(mock_db)
            result = service.run_auto_processing(project_id=1)

            assert result["success"] is True
            assert result["forecast_stats"] == {}

    def test_default_options(self):
        """测试默认选项"""
        mock_db = MagicMock()

        # Project query
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.pm_id = None

        def query_side_effect(model):
            query_mock = MagicMock()
            if model.__name__ == 'Project':
                query_mock.filter.return_value.first.return_value = mock_project
        elif model.__name__ == 'Task':
            query_mock.options.return_value.filter.return_value.all.return_value = []
            return query_mock

            mock_db.query.side_effect = query_side_effect

            service = ProgressAutoService(mock_db)
            result = service.run_auto_processing(project_id=1)

            assert result["success"] is True


@pytest.mark.unit
class TestProgressAutoIntegration:
    """集成测试"""

    def test_service_is_importable(self):
        """测试服务可导入"""
        from app.services.progress_auto_service import ProgressAutoService
        assert ProgressAutoService is not None

    def test_all_methods_exist(self):
        """测试所有方法存在"""
        mock_db = MagicMock()
        service = ProgressAutoService(mock_db)

        assert hasattr(service, 'apply_forecast_to_tasks')
        assert hasattr(service, 'auto_fix_dependency_issues')
        assert hasattr(service, '_fix_timing_conflict')
        assert hasattr(service, '_remove_missing_dependency')
        assert hasattr(service, 'send_forecast_notifications')
        assert hasattr(service, 'run_auto_processing')

    def test_multiple_forecast_items(self):
        """测试多个预测项目"""
        mock_db = MagicMock()

        mock_task1 = MagicMock()
        mock_task1.id = 1
        mock_task1.task_name = "Task 1"
        mock_task1.status = "IN_PROGRESS"
        mock_task1.progress_percent = 30

        mock_task2 = MagicMock()
        mock_task2.id = 2
        mock_task2.task_name = "Task 2"
        mock_task2.status = "IN_PROGRESS"
        mock_task2.progress_percent = 50

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task1, mock_task2]

        forecast_items = [
        TaskForecastItem(
        task_id=1,
        task_name="Task 1",
        progress_percent=30,
        predicted_finish_date=date.today() + timedelta(days=10),
        delay_days=10,
        status="Delayed",
        critical=True
        ),
        TaskForecastItem(
        task_id=2,
        task_name="Task 2",
        progress_percent=50,
        predicted_finish_date=date.today() + timedelta(days=5),
        delay_days=5,
        status="Delayed",
        critical=True
        )
        ]

        service = ProgressAutoService(mock_db)
        result = service.apply_forecast_to_tasks(
        project_id=1,
        forecast_items=forecast_items,
        auto_block=True,
        delay_threshold=3
        )

        assert result["total"] == 2
        assert result["blocked"] == 2

    def test_multiple_dependency_issues(self):
        """测试多个依赖问题"""
        mock_db = MagicMock()
        service = ProgressAutoService(mock_db)

        issues = [
        DependencyIssue(
        issue_type="CYCLE",
        severity="HIGH",
        task_id=1,
        detail="循环依赖"
        ),
        DependencyIssue(
        issue_type="TIMING_CONFLICT",
        severity="MEDIUM",
        task_id=2,
        detail="时序冲突"
        ),
        DependencyIssue(
        issue_type="MISSING_PREDECESSOR",
        severity="LOW",
        task_id=3,
        detail="缺失依赖"
        )
        ]

        with patch.object(service, '_fix_timing_conflict', return_value=True):
            with patch.object(service, '_remove_missing_dependency', return_value=True):
                result = service.auto_fix_dependency_issues(
                project_id=1,
                issues=issues,
                auto_fix_timing=True,
                auto_fix_missing=True
                )

                assert result["total_issues"] == 3
                assert result["cycles_skipped"] == 1
                assert result["timing_fixed"] == 1
                assert result["missing_removed"] == 1
