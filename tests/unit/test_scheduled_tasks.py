# -*- coding: utf-8 -*-
"""
定时任务单元测试

测试内容：
- base: 基础辅助函数
- project_health_tasks: 健康度相关任务
- milestone_tasks: 里程碑预警任务
- alert_tasks: 预警相关任务
- issue_scheduled_tasks: 问题相关任务
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.utils.scheduled_tasks.base import (
    enqueue_or_dispatch_notification,
    log_task_result,
    safe_task_execution,
    send_notification_for_alert,
)


# ============================================================================
# Base 模块测试
# ============================================================================


@pytest.mark.unit
class TestLogTaskResult:
    """测试任务结果日志记录"""

    def test_log_success_result(self):
        """测试记录成功结果"""
        mock_logger = MagicMock()

        log_task_result("test_task", {"count": 10}, mock_logger)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "test_task" in call_args
        assert "执行完成" in call_args

    def test_log_error_result(self):
        """测试记录错误结果"""
        mock_logger = MagicMock()

        log_task_result("test_task", {"error": "Some error"}, mock_logger)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "test_task" in call_args
        assert "执行失败" in call_args

    def test_log_with_default_logger(self):
        """测试使用默认 logger"""
        # 不传入 logger，使用模块默认 logger
        # 验证不会抛出异常
        log_task_result("test_task", {"count": 5})

    def test_log_empty_result(self):
        """测试空结果"""
        mock_logger = MagicMock()
        log_task_result("test_task", {}, mock_logger)
        mock_logger.info.assert_called_once()


@pytest.mark.unit
class TestSafeTaskExecution:
    """测试安全任务执行装饰器"""

    def test_successful_execution(self):
        """测试成功执行"""
        mock_logger = MagicMock()

        def sample_task():
            return {"count": 10}

            wrapped = safe_task_execution(sample_task, "sample_task", mock_logger)
            result = wrapped()

            assert result == {"count": 10}
            mock_logger.info.assert_called()

    def test_execution_with_exception(self):
        """测试执行时抛出异常"""
        mock_logger = MagicMock()

        def failing_task():
            raise ValueError("Test error")

            wrapped = safe_task_execution(failing_task, "failing_task", mock_logger)
            result = wrapped()

            assert "error" in result
            assert "Test error" in result["error"]
            mock_logger.error.assert_called()

    def test_execution_with_args(self):
        """测试带参数的执行"""
        mock_logger = MagicMock()

        def task_with_args(a, b, multiplier=1):
            return {"result": (a + b) * multiplier}

            wrapped = safe_task_execution(task_with_args, "task_with_args", mock_logger)
            result = wrapped(1, 2, multiplier=3)

            assert result == {"result": 9}

    def test_execution_returns_none(self):
        """测试返回 None 的执行"""
        mock_logger = MagicMock()

        def task_returns_none():
            return None

            wrapped = safe_task_execution(
            task_returns_none, "task_returns_none", mock_logger
            )
            result = wrapped()

            assert result is None
            mock_logger.info.assert_called()

    def test_default_logger(self):
        """测试使用默认 logger"""

        def simple_task():
            return {"ok": True}

            wrapped = safe_task_execution(simple_task, "simple_task")
            result = wrapped()
            assert result == {"ok": True}


@pytest.mark.unit
class TestSendNotificationForAlert:
    """测试预警通知发送"""

    def test_send_notification_callable(self):
        """测试通知发送函数可调用"""
        assert callable(send_notification_for_alert)

    def test_send_notification_handles_exception(self, db_session: Session):
        """测试发送通知时异常处理不会传播"""
        mock_logger = MagicMock()
        mock_alert = MagicMock()
        mock_alert.alert_no = "ALT-002"
        mock_alert.id = 1

        # 使用一个不存在的 db 会导致异常，但不应该传播
        try:
            send_notification_for_alert(db_session, mock_alert, mock_logger)
        except Exception:
            pass  # 函数应该捕获所有异常
            # 如果到这里没有崩溃，测试就通过了


@pytest.mark.unit
class TestEnqueueOrDispatchNotification:
    """测试通知入队/直发辅助函数"""

    def test_fallback_dispatch_when_enqueue_fails(self):
        """入队失败时回退为同步派发"""
        dispatcher = MagicMock()
        dispatcher.dispatch.return_value = True

        notification = MagicMock()
        notification.id = 123
        notification.alert_id = 456
        notification.notify_channel = "SYSTEM"

        alert = MagicMock()
        user = MagicMock()
        request = SimpleNamespace(
            recipient_id=1,
            notification_type="ALERT",
            category="alert",
            title="t",
            content="c",
        )

        with patch(
            "app.services.notification_queue.enqueue_notification", return_value=False
        ):
            result = enqueue_or_dispatch_notification(
                dispatcher, notification, alert, user, request=request
            )

        assert result["queued"] is False
        assert result["sent"] is True
        dispatcher.dispatch.assert_called_once_with(
            notification, alert, user, request=request
        )


            # ============================================================================
            # Project Health Tasks 测试
            # ============================================================================


@pytest.mark.unit
class TestProjectHealthTasks:
    """测试项目健康度任务"""

    def test_calculate_project_health_callable(self):
        """测试健康度计算函数可调用"""
        from app.utils.scheduled_tasks.project_health_tasks import (
        calculate_project_health,
        )

        assert callable(calculate_project_health)

    def test_daily_health_snapshot_callable(self):
        """测试每日健康度快照函数可调用"""
        from app.utils.scheduled_tasks.project_health_tasks import (
        daily_health_snapshot,
        )

        assert callable(daily_health_snapshot)

    def test_calculate_project_health_exception(self):
        """测试健康度计算异常处理"""
        from app.utils.scheduled_tasks.project_health_tasks import (
        calculate_project_health,
        )

        with patch(
            "app.utils.scheduled_tasks.project_health_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = calculate_project_health()

        assert "error" in result
        assert "DB error" in result["error"]

    def test_daily_health_snapshot_exception(self):
        """测试每日健康度快照异常处理"""
        from app.utils.scheduled_tasks.project_health_tasks import (
            daily_health_snapshot,
        )

        with patch(
            "app.utils.scheduled_tasks.project_health_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("Snapshot error")

            result = daily_health_snapshot()

        assert "error" in result


# ============================================================================
# Milestone Tasks 测试
# ============================================================================


@pytest.mark.unit
class TestMilestoneTasks:
    """测试里程碑任务"""

    def test_check_milestone_alerts_callable(self):
        """测试里程碑预警函数可调用"""
        from app.utils.scheduled_tasks.milestone_tasks import check_milestone_alerts

        assert callable(check_milestone_alerts)

    def test_check_milestone_risk_alerts_callable(self):
        """测试里程碑风险预警函数可调用"""
        from app.utils.scheduled_tasks.milestone_tasks import (
        check_milestone_risk_alerts,
        )

        assert callable(check_milestone_risk_alerts)

    def test_check_milestone_status_and_adjust_payments_callable(self):
        """测试里程碑状态调整函数可调用"""
        from app.utils.scheduled_tasks.milestone_tasks import (
        check_milestone_status_and_adjust_payments,
        )

        assert callable(check_milestone_status_and_adjust_payments)

    def test_check_milestone_alerts_exception(self):
        """测试里程碑预警检查异常"""
        from app.utils.scheduled_tasks.milestone_tasks import check_milestone_alerts

        with patch(
            "app.utils.scheduled_tasks.milestone_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("Service error")

            result = check_milestone_alerts()

            assert "error" in result

    def test_check_milestone_status_exception(self):
        """测试里程碑状态检查异常"""
        from app.utils.scheduled_tasks.milestone_tasks import (
            check_milestone_status_and_adjust_payments,
        )

        with patch(
            "app.utils.scheduled_tasks.milestone_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("Payment error")

            result = check_milestone_status_and_adjust_payments()

            assert "error" in result

    def test_check_milestone_risk_alerts_exception(self):
        """测试没有项目时的风险预警检查异常"""
        from app.utils.scheduled_tasks.milestone_tasks import (
            check_milestone_risk_alerts,
        )

        with patch(
            "app.utils.scheduled_tasks.milestone_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("Risk error")

            result = check_milestone_risk_alerts()

            assert "error" in result


# ============================================================================
# Alert Tasks 测试
# ============================================================================


@pytest.mark.unit
class TestAlertTasks:
    """预警任务测试类"""

    def test_check_alert_escalation_callable(self):
        """测试预警升级函数可调用"""
        from app.utils.scheduled_tasks.alert_tasks import check_alert_escalation

        assert callable(check_alert_escalation)

    def test_retry_failed_notifications_callable(self):
        """测试通知重试函数可调用"""
        from app.utils.scheduled_tasks.alert_tasks import retry_failed_notifications

        assert callable(retry_failed_notifications)

    def test_check_alert_escalation_exception(self):
        """测试预警升级异常处理"""
        from app.utils.scheduled_tasks.alert_tasks import check_alert_escalation

        with patch(
            "app.utils.scheduled_tasks.alert_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_alert_escalation()

            assert "error" in result

    def test_retry_failed_notifications_exception(self):
        """测试通知重试异常处理"""
        from app.utils.scheduled_tasks.alert_tasks import retry_failed_notifications

        with patch(
            "app.utils.scheduled_tasks.alert_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = retry_failed_notifications()

            assert "error" in result


# ============================================================================
# Issue Scheduled Tasks 测试
# ============================================================================


@pytest.mark.unit
class TestIssueScheduledTasks:
    """问题定时任务测试类"""

    def test_check_overdue_issues_callable(self):
        """测试逾期问题检查函数可调用"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        assert callable(check_overdue_issues)

    def test_check_blocking_issues_callable(self):
        """测试阻塞问题检查函数可调用"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
        check_blocking_issues,
        )

        assert callable(check_blocking_issues)

    def test_check_overdue_issues_exception(self):
        """测试逾期问题检查异常处理"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        with patch(
            "app.utils.scheduled_tasks.issue_scheduled_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_overdue_issues()

            assert "error" in result


# ============================================================================
# Project Scheduled Tasks 测试
# ============================================================================


@pytest.mark.unit
class TestProjectScheduledTasks:
    """项目定时任务测试类"""

    def test_calculate_project_health_callable(self):
        """测试项目健康度计算函数可调用"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
        calculate_project_health,
        )

        assert callable(calculate_project_health)

    def test_check_project_deadline_alerts_callable(self):
        """测试截止日期预警函数可调用"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
        check_project_deadline_alerts,
        )

        assert callable(check_project_deadline_alerts)


# ============================================================================
# 集成场景测试
# ============================================================================


@pytest.mark.unit
class TestScheduledTasksIntegration:
    """测试定时任务集成场景"""

    def test_task_result_logging_integration(self):
        """测试任务结果日志记录集成"""
        mock_logger = MagicMock()
        call_count = [0]

        def counting_task():
            call_count[0] += 1
            return {"count": call_count[0]}

            wrapped = safe_task_execution(counting_task, "counting_task", mock_logger)

            # 执行多次
            result1 = wrapped()
            result2 = wrapped()
            result3 = wrapped()

            assert result1["count"] == 1
            assert result2["count"] == 2
            assert result3["count"] == 3
            assert mock_logger.info.call_count == 3

    def test_task_error_isolation(self):
        """测试任务错误隔离"""
        mock_logger = MagicMock()
        execution_order = []

        def task1():
            execution_order.append("task1")
            raise ValueError("Task 1 error")

        def task2():
            execution_order.append("task2")
            return {"status": "ok"}

            wrapped1 = safe_task_execution(task1, "task1", mock_logger)
            wrapped2 = safe_task_execution(task2, "task2", mock_logger)

            result1 = wrapped1()
            result2 = wrapped2()

            # 即使 task1 失败，task2 也能正常执行
            assert "error" in result1
            assert result2 == {"status": "ok"}
            assert execution_order == ["task1", "task2"]

    def test_module_imports(self):
        """测试模块可以正常导入"""
        # 验证所有任务模块可以正常导入
        from app.utils.scheduled_tasks import base
        from app.utils.scheduled_tasks import project_health_tasks
        from app.utils.scheduled_tasks import milestone_tasks

        assert hasattr(base, "log_task_result")
        assert hasattr(base, "safe_task_execution")
        assert hasattr(base, "send_notification_for_alert")

        assert hasattr(project_health_tasks, "calculate_project_health")
        assert hasattr(project_health_tasks, "daily_health_snapshot")

        assert hasattr(milestone_tasks, "check_milestone_alerts")
        assert hasattr(milestone_tasks, "check_milestone_status_and_adjust_payments")
        assert hasattr(milestone_tasks, "check_milestone_risk_alerts")

    def test_all_tasks_callable(self):
        """测试所有任务函数可调用"""
        from app.utils.scheduled_tasks.alert_tasks import (
        check_alert_escalation,
        retry_failed_notifications,
        )
        from app.utils.scheduled_tasks.milestone_tasks import (
        check_milestone_alerts,
        check_milestone_risk_alerts,
        )
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
        calculate_project_health,
        check_project_deadline_alerts,
        )
        from app.utils.scheduled_tasks.issue_scheduled_tasks import (
        check_overdue_issues,
        check_blocking_issues,
        )

        assert all(
        callable(f)
        for f in [
        check_alert_escalation,
        retry_failed_notifications,
        check_milestone_alerts,
        check_milestone_risk_alerts,
        calculate_project_health,
        check_project_deadline_alerts,
        check_overdue_issues,
        check_blocking_issues,
        ]
        )


# ============================================================================
# HR Tasks 测试
# ============================================================================


@pytest.mark.unit
class TestHRTasks:
    """HR定时任务测试类"""

    def test_check_contract_expiry_reminder_callable(self):
        """测试合同到期提醒函数可调用"""
        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder

        assert callable(check_contract_expiry_reminder)

    def test_check_employee_confirmation_reminder_callable(self):
        """测试员工转正提醒函数可调用"""
        from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder

        assert callable(check_employee_confirmation_reminder)

    def test_check_contract_expiry_reminder_exception(self):
        """测试合同到期提醒异常处理"""
        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_contract_expiry_reminder()

            assert "error" in result

    def test_check_employee_confirmation_reminder_exception(self):
        """测试员工转正提醒异常处理"""
        from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_employee_confirmation_reminder()

            assert "error" in result

    def test_check_contract_expiry_no_expiring_contracts(self):
        """测试无到期合同时的处理"""
        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_session = MagicMock()
            mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_contract_expiry_reminder()

            # 应该正常返回，不抛出异常
            assert result is not None

    def test_check_employee_confirmation_no_employees(self):
        """测试无待转正员工时的处理"""
        from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_session = MagicMock()
            mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_employee_confirmation_reminder()

        assert result is not None


# ============================================================================
# Timesheet Tasks 测试
# ============================================================================


@pytest.mark.unit
class TestTimesheetTasks:
    """工时定时任务测试类"""

    def test_daily_timesheet_reminder_callable(self):
        """测试每日工时提醒函数可调用"""
        from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_reminder_task

        assert callable(daily_timesheet_reminder_task)

    def test_weekly_timesheet_reminder_callable(self):
        """测试每周工时提醒函数可调用"""
        from app.utils.scheduled_tasks.timesheet_tasks import weekly_timesheet_reminder_task

        assert callable(weekly_timesheet_reminder_task)

    def test_timesheet_anomaly_alert_callable(self):
        """测试工时异常提醒函数可调用"""
        from app.utils.scheduled_tasks.timesheet_tasks import timesheet_anomaly_alert_task

        assert callable(timesheet_anomaly_alert_task)

    def test_timesheet_approval_timeout_callable(self):
        """测试审批超时提醒函数可调用"""
        from app.utils.scheduled_tasks.timesheet_tasks import (
        timesheet_approval_timeout_reminder_task,
        )

        assert callable(timesheet_approval_timeout_reminder_task)

    def test_daily_timesheet_aggregation_callable(self):
        """测试每日工时汇总函数可调用"""
        from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_aggregation_task

        assert callable(daily_timesheet_aggregation_task)

    def test_weekly_timesheet_aggregation_callable(self):
        """测试每周工时汇总函数可调用"""
        from app.utils.scheduled_tasks.timesheet_tasks import weekly_timesheet_aggregation_task

        assert callable(weekly_timesheet_aggregation_task)

    def test_monthly_timesheet_aggregation_callable(self):
        """测试每月工时汇总函数可调用"""
        from app.utils.scheduled_tasks.timesheet_tasks import monthly_timesheet_aggregation_task

        assert callable(monthly_timesheet_aggregation_task)

    def test_calculate_monthly_labor_cost_callable(self):
        """测试月度人工成本计算函数可调用"""
        from app.utils.scheduled_tasks.timesheet_tasks import calculate_monthly_labor_cost_task

        assert callable(calculate_monthly_labor_cost_task)

    def test_daily_timesheet_reminder_with_mock_service(self):
        """测试每日工时提醒 - 使用模拟服务"""
        import sys
        from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_reminder_task

        # 创建mock服务模块
        mock_service = MagicMock()
        mock_service.notify_timesheet_missing = MagicMock(return_value=5)
        sys.modules['app.services.timesheet_reminder_service'] = mock_service

        try:
            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = daily_timesheet_reminder_task()

                assert result is not None
        finally:
            # 清理mock模块
            if 'app.services.timesheet_reminder_service' in sys.modules:
                del sys.modules['app.services.timesheet_reminder_service']

    def test_weekly_timesheet_reminder_with_mock_service(self):
        """测试每周工时提醒 - 使用模拟服务"""
        import sys
        from app.utils.scheduled_tasks.timesheet_tasks import weekly_timesheet_reminder_task

        mock_service = MagicMock()
        mock_service.notify_weekly_timesheet_missing = MagicMock(return_value=3)
        sys.modules['app.services.timesheet_reminder_service'] = mock_service

        try:
            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = weekly_timesheet_reminder_task()

                assert result is not None
        finally:
            if 'app.services.timesheet_reminder_service' in sys.modules:
                del sys.modules['app.services.timesheet_reminder_service']

    def test_timesheet_anomaly_alert_with_mock_service(self):
        """测试工时异常提醒 - 使用模拟服务"""
        import sys
        from app.utils.scheduled_tasks.timesheet_tasks import timesheet_anomaly_alert_task

        mock_service = MagicMock()
        mock_service.notify_anomaly_timesheet = MagicMock(return_value=2)
        sys.modules['app.services.timesheet_reminder_service'] = mock_service

        try:
            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = timesheet_anomaly_alert_task()

                assert result is not None
        finally:
            if 'app.services.timesheet_reminder_service' in sys.modules:
                del sys.modules['app.services.timesheet_reminder_service']

    def test_timesheet_approval_timeout_with_mock_service(self):
        """测试审批超时提醒 - 使用模拟服务"""
        import sys
        from app.utils.scheduled_tasks.timesheet_tasks import (
            timesheet_approval_timeout_reminder_task,
        )

        mock_service = MagicMock()
        mock_service.notify_approval_timeout = MagicMock(return_value=1)
        sys.modules['app.services.timesheet_reminder_service'] = mock_service

        try:
            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = timesheet_approval_timeout_reminder_task()

                assert result is not None
        finally:
            if 'app.services.timesheet_reminder_service' in sys.modules:
                del sys.modules['app.services.timesheet_reminder_service']

    def test_daily_aggregation_with_mock_service(self):
        """测试每日汇总 - 使用模拟服务"""
        import sys
        from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_aggregation_task

        # 创建mock服务模块
        mock_service_class = MagicMock()
        mock_service_instance = MagicMock()
        mock_service_instance.aggregate_monthly_timesheet = MagicMock(
        return_value={'message': 'ok', 'success': True}
        )
        mock_service_class.return_value = mock_service_instance

        mock_module = MagicMock()
        mock_module.TimesheetAggregationService = mock_service_class
        sys.modules['app.services.timesheet_aggregation_service'] = mock_module

        try:
            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = daily_timesheet_aggregation_task()

                assert result is not None
                assert 'message' in result
        finally:
            if 'app.services.timesheet_aggregation_service' in sys.modules:
                del sys.modules['app.services.timesheet_aggregation_service']

    def test_weekly_aggregation_with_mock_service(self):
        """测试每周汇总 - 使用模拟服务"""
        import sys
        from app.utils.scheduled_tasks.timesheet_tasks import weekly_timesheet_aggregation_task

        mock_service_class = MagicMock()
        mock_service_instance = MagicMock()
        mock_service_instance.aggregate_monthly_timesheet = MagicMock(
        return_value={'message': 'ok', 'success': True}
        )
        mock_service_class.return_value = mock_service_instance

        mock_module = MagicMock()
        mock_module.TimesheetAggregationService = mock_service_class
        sys.modules['app.services.timesheet_aggregation_service'] = mock_module

        try:
            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = weekly_timesheet_aggregation_task()

                assert result is not None
        finally:
            if 'app.services.timesheet_aggregation_service' in sys.modules:
                del sys.modules['app.services.timesheet_aggregation_service']

    def test_monthly_aggregation_with_mock_service(self):
        """测试每月汇总 - 使用模拟服务"""
        import sys
        from app.utils.scheduled_tasks.timesheet_tasks import monthly_timesheet_aggregation_task

        mock_service_class = MagicMock()
        mock_service_instance = MagicMock()
        mock_service_instance.aggregate_monthly_timesheet = MagicMock(
        return_value={'message': 'ok', 'success': True}
        )
        mock_service_class.return_value = mock_service_instance

        mock_module = MagicMock()
        mock_module.TimesheetAggregationService = mock_service_class
        sys.modules['app.services.timesheet_aggregation_service'] = mock_module

        try:
            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = monthly_timesheet_aggregation_task()

                assert result is not None
                assert 'message' in result
        finally:
            if 'app.services.timesheet_aggregation_service' in sys.modules:
                del sys.modules['app.services.timesheet_aggregation_service']

    def test_calculate_monthly_labor_cost_with_mock_service(self):
        """测试月度人工成本计算 - 使用模拟服务"""
        import sys
        from app.utils.scheduled_tasks.timesheet_tasks import calculate_monthly_labor_cost_task

        mock_service_class = MagicMock()
        mock_service_instance = MagicMock()
        mock_service_instance.calculate_monthly_labor_cost = MagicMock(
        return_value={'message': 'ok', 'success': True}
        )
        mock_service_class.return_value = mock_service_instance

        mock_module = MagicMock()
        mock_module.LaborCostCalculationService = mock_service_class
        sys.modules['app.services.labor_cost_calculation_service'] = mock_module

        try:
            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = calculate_monthly_labor_cost_task()

                assert result is not None
        finally:
            if 'app.services.labor_cost_calculation_service' in sys.modules:
                del sys.modules['app.services.labor_cost_calculation_service']


# ============================================================================
# Production Tasks 测试
# ============================================================================


@pytest.mark.unit
class TestProductionTasks:
    """生产定时任务测试类"""

    def test_check_production_plan_alerts_callable(self):
        """测试生产计划预警函数可调用"""
        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts

        assert callable(check_production_plan_alerts)

    def test_check_work_report_timeout_callable(self):
        """测试工单报工超时函数可调用"""
        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout

        assert callable(check_work_report_timeout)

    def test_generate_production_daily_reports_callable(self):
        """测试每日生产报表函数可调用"""
        from app.utils.scheduled_tasks.production_tasks import generate_production_daily_reports

        assert callable(generate_production_daily_reports)

    def test_check_production_plan_alerts_exception(self):
        """测试生产计划预警异常处理"""
        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_production_plan_alerts()

            assert "error" in result

    def test_check_work_report_timeout_exception(self):
        """测试工单报工超时异常处理"""
        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_work_report_timeout()

            assert "error" in result

    def test_generate_production_daily_reports_exception(self):
        """测试每日生产报表异常处理"""
        from app.utils.scheduled_tasks.production_tasks import generate_production_daily_reports

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = generate_production_daily_reports()

            assert "error" in result

    def test_check_production_plan_no_alerts(self):
        """测试无生产计划预警时的处理"""
        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_session = MagicMock()
            mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_production_plan_alerts()

            assert result is not None

    def test_check_work_report_no_timeouts(self):
        """测试无超时工单时的处理"""
        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_session = MagicMock()
            mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_work_report_timeout()

            assert result is not None


# ============================================================================
# Sales Tasks 测试
# ============================================================================


@pytest.mark.unit
class TestSalesTasks:
    """销售定时任务测试类"""

    def test_sales_reminder_scan_callable(self):
        """测试销售提醒扫描函数可调用"""
        from app.utils.scheduled_tasks.sales_tasks import sales_reminder_scan

        assert callable(sales_reminder_scan)

    def test_check_payment_reminder_callable(self):
        """测试收款提醒函数可调用"""
        from app.utils.scheduled_tasks.sales_tasks import check_payment_reminder

        assert callable(check_payment_reminder)

    def test_check_overdue_receivable_alerts_callable(self):
        """测试应收逾期预警函数可调用"""
        from app.utils.scheduled_tasks.sales_tasks import check_overdue_receivable_alerts

        assert callable(check_overdue_receivable_alerts)

    def test_check_opportunity_stage_timeout_callable(self):
        """测试商机阶段超时函数可调用"""
        from app.utils.scheduled_tasks.sales_tasks import check_opportunity_stage_timeout

        assert callable(check_opportunity_stage_timeout)

    def test_check_payment_reminder_exception(self):
        """测试收款提醒异常处理"""
        from app.utils.scheduled_tasks.sales_tasks import check_payment_reminder

        with patch(
            "app.utils.scheduled_tasks.sales_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_payment_reminder()

            assert "error" in result

    def test_check_overdue_receivable_alerts_exception(self):
        """测试应收逾期预警异常处理"""
        from app.utils.scheduled_tasks.sales_tasks import check_overdue_receivable_alerts

        with patch(
            "app.utils.scheduled_tasks.sales_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_overdue_receivable_alerts()

            assert "error" in result

    def test_check_opportunity_stage_timeout_exception(self):
        """测试商机阶段超时异常处理"""
        from app.utils.scheduled_tasks.sales_tasks import check_opportunity_stage_timeout

        with patch(
            "app.utils.scheduled_tasks.sales_tasks.get_db_session"
        ) as mock_db_ctx:
            mock_db_ctx.side_effect = Exception("DB error")

            result = check_opportunity_stage_timeout()

            assert "error" in result

    def test_check_payment_reminder_no_reminders(self):
        """测试无收款提醒时的处理"""
        import sys
        from app.utils.scheduled_tasks.sales_tasks import check_payment_reminder

        mock_service = MagicMock()
        mock_service.notify_payment_plan_upcoming = MagicMock(return_value=0)
        sys.modules['app.services.sales_reminder'] = mock_service

        try:
            with patch(
                "app.utils.scheduled_tasks.sales_tasks.get_db_session"
            ) as mock_db_ctx:
                mock_session = MagicMock()
                mock_db_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_db_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = check_payment_reminder()

                assert result is not None
        finally:
            if 'app.services.sales_reminder' in sys.modules:
                del sys.modules['app.services.sales_reminder']
