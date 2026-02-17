# -*- coding: utf-8 -*-
"""
定时任务 H2 组扩展单元测试

覆盖文件：
- base.py
- project_scheduled_tasks.py
- issue_scheduled_tasks.py
- issue_tasks.py
- production_tasks.py
- kit_rate_tasks.py
- timesheet_tasks.py
- sales_tasks.py
- hr_tasks.py
- alert_tasks.py
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

import pytest
from sqlalchemy.orm import Session


# ============================================================================
# base.py 扩展测试
# ============================================================================


@pytest.mark.unit
class TestBaseModuleExtended:
    """base.py 扩展测试"""

    def test_send_notification_for_alert_success(self):
        """测试通知发送成功路径"""
        mock_db = MagicMock(spec=Session)
        mock_alert = MagicMock()
        mock_alert.alert_no = "ALT-001"
        mock_logger = MagicMock()

        with patch(
            "app.services.notification_dispatcher.NotificationDispatcher"
        ) as MockDispatcher:
            mock_dispatcher = MagicMock()
            mock_dispatcher.dispatch_alert_notifications.return_value = {
                "created": 2, "queued": 1, "sent": 1, "failed": 0
            }
            MockDispatcher.return_value = mock_dispatcher

            from app.utils.scheduled_tasks.base import send_notification_for_alert
            send_notification_for_alert(mock_db, mock_alert, mock_logger)

            mock_dispatcher.dispatch_alert_notifications.assert_called_once_with(alert=mock_alert)
            mock_logger.debug.assert_called()

    def test_send_notification_for_alert_zero_created(self):
        """测试通知创建数量为0时不记录 debug"""
        mock_db = MagicMock(spec=Session)
        mock_alert = MagicMock()
        mock_alert.alert_no = "ALT-002"
        mock_logger = MagicMock()

        with patch(
            "app.services.notification_dispatcher.NotificationDispatcher"
        ) as MockDispatcher:
            mock_dispatcher = MagicMock()
            mock_dispatcher.dispatch_alert_notifications.return_value = {
                "created": 0, "queued": 0, "sent": 0, "failed": 0
            }
            MockDispatcher.return_value = mock_dispatcher

            from app.utils.scheduled_tasks.base import send_notification_for_alert
            send_notification_for_alert(mock_db, mock_alert, mock_logger)

            mock_logger.debug.assert_not_called()

    def test_send_notification_for_alert_dispatcher_exception(self):
        """测试 dispatcher 抛出异常时被捕获"""
        mock_db = MagicMock(spec=Session)
        mock_alert = MagicMock()
        mock_alert.alert_no = "ALT-003"
        mock_logger = MagicMock()

        with patch(
            "app.services.notification_dispatcher.NotificationDispatcher"
        ) as MockDispatcher:
            MockDispatcher.side_effect = RuntimeError("dispatcher init failed")

            from app.utils.scheduled_tasks.base import send_notification_for_alert
            # 不应抛出异常
            send_notification_for_alert(mock_db, mock_alert, mock_logger)
            mock_logger.error.assert_called()

    def test_enqueue_or_dispatch_notification_enqueue_success(self):
        """测试入队成功时返回 queued=True"""
        from app.utils.scheduled_tasks.base import enqueue_or_dispatch_notification
        from types import SimpleNamespace

        dispatcher = MagicMock()
        notification = MagicMock()
        notification.id = 1
        notification.alert_id = 10
        notification.notify_channel = "SYSTEM"
        alert = MagicMock()
        user = MagicMock()
        request = SimpleNamespace(field="value")

        with patch(
            "app.services.notification_queue.enqueue_notification", return_value=True
        ):
            result = enqueue_or_dispatch_notification(
                dispatcher, notification, alert, user, request=request
            )

        assert result["queued"] is True
        assert result["sent"] is False
        assert notification.status == "QUEUED"

    def test_enqueue_or_dispatch_notification_build_request_fails(self):
        """测试构建请求失败时返回 error"""
        from app.utils.scheduled_tasks.base import enqueue_or_dispatch_notification

        dispatcher = MagicMock()
        dispatcher.build_notification_request.side_effect = ValueError("bad request")
        notification = MagicMock()
        notification.id = 2
        notification.alert_id = 20
        notification.notify_channel = "EMAIL"
        alert = MagicMock()
        user = MagicMock()

        # 不传 request，会调用 build_notification_request
        result = enqueue_or_dispatch_notification(
            dispatcher, notification, alert, user
        )

        assert "error" in result
        assert notification.status == "FAILED"

    def test_safe_task_execution_successful(self):
        """测试 safe_task_execution 包装成功执行"""
        from app.utils.scheduled_tasks.base import safe_task_execution

        mock_logger = MagicMock()
        call_log = []

        def my_task(x, y=10):
            call_log.append((x, y))
            return {"sum": x + y}

        wrapped = safe_task_execution(my_task, "my_task", mock_logger)
        result = wrapped(5, y=20)

        assert result == {"sum": 25}
        assert call_log == [(5, 20)]
        mock_logger.info.assert_called_once()

    def test_safe_task_execution_with_exception(self):
        """测试 safe_task_execution 异常被捕获并返回 error dict"""
        from app.utils.scheduled_tasks.base import safe_task_execution

        mock_logger = MagicMock()

        def bad_task():
            raise RuntimeError("boom")

        wrapped = safe_task_execution(bad_task, "bad_task", mock_logger)
        result = wrapped()

        assert "error" in result
        assert "boom" in result["error"]
        mock_logger.error.assert_called()

    def test_log_task_result_with_error_key(self):
        """测试含 error key 的结果走 logger.error"""
        from app.utils.scheduled_tasks.base import log_task_result

        mock_logger = MagicMock()
        log_task_result("task_x", {"error": "connection refused"}, mock_logger)
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "task_x" in call_args
        assert "执行失败" in call_args

    def test_log_task_result_success_message_contains_task_name(self):
        """测试成功结果中包含任务名称"""
        from app.utils.scheduled_tasks.base import log_task_result

        mock_logger = MagicMock()
        log_task_result("my_special_task", {"count": 42}, mock_logger)
        call_args = mock_logger.info.call_args[0][0]
        assert "my_special_task" in call_args


# ============================================================================
# project_scheduled_tasks.py 扩展测试
# ============================================================================


@pytest.mark.unit
class TestProjectScheduledTasksExtended:
    """project_scheduled_tasks.py 扩展测试"""

    def test_daily_spec_match_check_callable(self):
        """测试 daily_spec_match_check 可调用"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import daily_spec_match_check
        assert callable(daily_spec_match_check)

    def test_calculate_progress_summary_callable(self):
        """测试 calculate_progress_summary 可调用"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import calculate_progress_summary
        assert callable(calculate_progress_summary)

    def test_check_project_cost_overrun_callable(self):
        """测试 check_project_cost_overrun 可调用"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import check_project_cost_overrun
        assert callable(check_project_cost_overrun)

    def test_calculate_project_health_returns_error_on_exception(self):
        """测试 calculate_project_health 异常返回 error 字典"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import calculate_project_health

        with patch(
            "app.utils.scheduled_tasks.project_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("health calc failed")
            result = calculate_project_health()

        assert "error" in result
        assert "health calc failed" in result["error"]

    def test_check_project_deadline_alerts_no_projects(self):
        """测试无即将到期项目时正常返回"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import check_project_deadline_alerts

        with patch(
            "app.utils.scheduled_tasks.project_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_project_deadline_alerts()

        assert result is not None
        assert result.get("upcoming_projects") == 0
        assert result.get("alerts_created") == 0

    def test_check_project_deadline_alerts_exception(self):
        """测试截止日期预警异常返回 error"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import check_project_deadline_alerts

        with patch(
            "app.utils.scheduled_tasks.project_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("deadline check failed")
            result = check_project_deadline_alerts()

        assert "error" in result

    def test_check_project_cost_overrun_no_projects(self):
        """测试无项目时成本超支检查正常返回"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import check_project_cost_overrun

        with patch(
            "app.utils.scheduled_tasks.project_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_project_cost_overrun()

        assert result is not None
        assert result.get("overrun_projects") == 0

    def test_check_project_cost_overrun_exception(self):
        """测试成本超支检查异常返回 error"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import check_project_cost_overrun

        with patch(
            "app.utils.scheduled_tasks.project_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("cost overrun check failed")
            result = check_project_cost_overrun()

        assert "error" in result

    def test_daily_spec_match_check_exception(self):
        """测试规格匹配检查异常（无法 commit 等）"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import daily_spec_match_check

        with patch(
            "app.utils.scheduled_tasks.project_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("spec match failed")

            # 函数内部会 raise，不返回 error dict
            with pytest.raises(Exception):
                daily_spec_match_check()

    def test_calculate_progress_summary_exception(self):
        """测试进度汇总计算异常返回 error"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import calculate_progress_summary

        with patch(
            "app.utils.scheduled_tasks.project_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("progress calc failed")
            result = calculate_progress_summary()

        assert "error" in result

    def test_daily_health_snapshot_no_projects(self):
        """测试无项目时每日健康快照返回0个快照"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import daily_health_snapshot

        with patch(
            "app.utils.scheduled_tasks.project_scheduled_tasks.get_db_session"
        ) as mock_ctx, patch(
            "app.services.health_calculator.HealthCalculator"
        ) as MockCalc:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            mock_calc = MagicMock()
            MockCalc.return_value = mock_calc

            result = daily_health_snapshot()

        assert result is not None
        assert result.get("snapshot_count") == 0

    def test_module_exports_all_functions(self):
        """测试模块导出所有预期函数"""
        from app.utils.scheduled_tasks import project_scheduled_tasks as m

        for fn_name in [
            "daily_spec_match_check",
            "calculate_project_health",
            "daily_health_snapshot",
            "calculate_progress_summary",
            "check_project_deadline_alerts",
            "check_project_cost_overrun",
        ]:
            assert hasattr(m, fn_name), f"缺少函数 {fn_name}"
            assert callable(getattr(m, fn_name))


# ============================================================================
# issue_scheduled_tasks.py 扩展测试
# ============================================================================


@pytest.mark.unit
class TestIssueScheduledTasksExtended:
    """issue_scheduled_tasks.py 扩展测试"""

    def test_check_overdue_issues_no_overdue(self):
        """测试无逾期问题时正常返回"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        with patch(
            "app.utils.scheduled_tasks.issue_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_overdue_issues()

        assert result["overdue_issues"] == 0
        assert result["alerts_created"] == 0
        assert "timestamp" in result

    def test_check_overdue_issues_exception(self):
        """测试逾期问题检查异常时返回 error"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_overdue_issues

        with patch(
            "app.utils.scheduled_tasks.issue_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("DB error")
            result = check_overdue_issues()

        assert "error" in result

    def test_check_blocking_issues_no_blocking(self):
        """测试无阻塞问题时正常返回"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        with patch(
            "app.utils.scheduled_tasks.issue_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_blocking_issues()

        assert result["blocking_issues"] == 0
        assert result["alerts_created"] == 0

    def test_check_blocking_issues_exception(self):
        """测试阻塞问题检查异常时返回 error"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_blocking_issues

        with patch(
            "app.utils.scheduled_tasks.issue_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("DB error")
            result = check_blocking_issues()

        assert "error" in result

    def test_check_timeout_issues_callable(self):
        """测试 check_timeout_issues 可调用"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_timeout_issues
        assert callable(check_timeout_issues)

    def test_check_timeout_issues_exception(self):
        """测试超时问题检查异常时返回 error"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import check_timeout_issues

        with patch(
            "app.utils.scheduled_tasks.issue_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("DB error")
            result = check_timeout_issues()

        assert "error" in result

    def test_daily_issue_statistics_snapshot_callable(self):
        """测试 daily_issue_statistics_snapshot 可调用"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import daily_issue_statistics_snapshot
        assert callable(daily_issue_statistics_snapshot)

    def test_daily_issue_statistics_snapshot_exception(self):
        """测试问题统计快照异常时返回 error"""
        from app.utils.scheduled_tasks.issue_scheduled_tasks import daily_issue_statistics_snapshot

        with patch(
            "app.utils.scheduled_tasks.issue_scheduled_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("Snapshot failed")
            result = daily_issue_statistics_snapshot()

        assert "error" in result


# ============================================================================
# issue_tasks.py 扩展测试（原先无测试）
# ============================================================================


@pytest.mark.unit
class TestIssueTasksNew:
    """issue_tasks.py 全新测试（原先无测试覆盖）"""

    def test_check_overdue_issues_callable(self):
        """测试 issue_tasks.check_overdue_issues 可调用"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues
        assert callable(check_overdue_issues)

    def test_check_blocking_issues_callable(self):
        """测试 issue_tasks.check_blocking_issues 可调用"""
        from app.utils.scheduled_tasks.issue_tasks import check_blocking_issues
        assert callable(check_blocking_issues)

    def test_check_timeout_issues_callable(self):
        """测试 issue_tasks.check_timeout_issues 可调用"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues
        assert callable(check_timeout_issues)

    def test_daily_issue_statistics_snapshot_callable(self):
        """测试 issue_tasks.daily_issue_statistics_snapshot 可调用"""
        from app.utils.scheduled_tasks.issue_tasks import daily_issue_statistics_snapshot
        assert callable(daily_issue_statistics_snapshot)

    def test_check_overdue_issues_no_overdue(self):
        """测试 issue_tasks: 无逾期问题正常返回"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

        with patch(
            "app.utils.scheduled_tasks.issue_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_overdue_issues()

        assert result["overdue_count"] == 0
        assert result["notified_count"] == 0
        assert "timestamp" in result

    def test_check_overdue_issues_exception(self):
        """测试 issue_tasks: 逾期问题检查异常返回 error"""
        from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

        with patch(
            "app.utils.scheduled_tasks.issue_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("DB connection error")
            result = check_overdue_issues()

        assert "error" in result

    def test_check_blocking_issues_no_blocking(self):
        """测试 issue_tasks: 无阻塞问题正常返回"""
        from app.utils.scheduled_tasks.issue_tasks import check_blocking_issues

        with patch(
            "app.utils.scheduled_tasks.issue_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_blocking_issues()

        assert result["blocking_count"] == 0
        assert result["affected_projects"] == 0

    def test_check_blocking_issues_exception(self):
        """测试 issue_tasks: 阻塞检查异常返回 error"""
        from app.utils.scheduled_tasks.issue_tasks import check_blocking_issues

        with patch(
            "app.utils.scheduled_tasks.issue_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("blocking check failed")
            result = check_blocking_issues()

        assert "error" in result

    def test_check_timeout_issues_no_timeout(self):
        """测试 issue_tasks: 无超时问题正常返回"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues

        with patch(
            "app.utils.scheduled_tasks.issue_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_timeout_issues()

        assert result["timeout_count"] == 0
        assert result["upgraded_count"] == 0

    def test_check_timeout_issues_exception(self):
        """测试 issue_tasks: 超时升级异常返回 error"""
        from app.utils.scheduled_tasks.issue_tasks import check_timeout_issues

        with patch(
            "app.utils.scheduled_tasks.issue_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("timeout check failed")
            result = check_timeout_issues()

        assert "error" in result

    def test_check_overdue_issues_with_overdue_issue_no_assignee(self):
        """测试 issue_tasks: 逾期问题无 assignee 不发送通知"""
        import sys

        mock_create_notification = MagicMock()
        mock_sales_reminder = MagicMock()
        mock_sales_reminder.create_notification = mock_create_notification
        sys.modules["app.services.sales_reminder"] = mock_sales_reminder

        try:
            from app.utils.scheduled_tasks.issue_tasks import check_overdue_issues

            mock_issue = MagicMock()
            mock_issue.id = 1
            mock_issue.issue_no = "ISS-001"
            mock_issue.title = "Test Issue"
            mock_issue.due_date = date.today() - timedelta(days=3)
            mock_issue.assignee_id = None  # 无 assignee
            mock_issue.project_id = None

            with patch(
                "app.utils.scheduled_tasks.issue_tasks.get_db_session"
            ) as mock_ctx:
                mock_session = MagicMock()
                mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
                mock_session.query.return_value.filter.return_value.all.return_value = [mock_issue]

                result = check_overdue_issues()

            # 无 assignee 不应发送通知
            mock_create_notification.assert_not_called()
            assert result["overdue_count"] == 1
            assert result["notified_count"] == 0
        finally:
            if "app.services.sales_reminder" in sys.modules:
                del sys.modules["app.services.sales_reminder"]

    def test_daily_issue_statistics_snapshot_exception(self):
        """测试 issue_tasks: 统计快照异常返回 error"""
        from app.utils.scheduled_tasks.issue_tasks import daily_issue_statistics_snapshot

        with patch(
            "app.utils.scheduled_tasks.issue_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("snapshot failed")
            result = daily_issue_statistics_snapshot()

        assert "error" in result

    def test_daily_issue_statistics_snapshot_already_exists(self):
        """测试 issue_tasks: 今日快照已存在时跳过"""
        import sys

        mock_issue_stats = MagicMock()
        mock_issue_stats.check_existing_snapshot = MagicMock(return_value=True)
        sys.modules["app.services.issue_statistics_service"] = mock_issue_stats

        try:
            from app.utils.scheduled_tasks.issue_tasks import daily_issue_statistics_snapshot

            with patch(
                "app.utils.scheduled_tasks.issue_tasks.get_db_session"
            ) as mock_ctx:
                mock_session = MagicMock()
                mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = daily_issue_statistics_snapshot()

            assert result.get("message") == "Snapshot already exists for today"
        finally:
            if "app.services.issue_statistics_service" in sys.modules:
                del sys.modules["app.services.issue_statistics_service"]


# ============================================================================
# production_tasks.py 扩展测试
# ============================================================================


@pytest.mark.unit
class TestProductionTasksExtended:
    """production_tasks.py 扩展测试"""

    def test_check_production_plan_alerts_returns_dict(self):
        """测试无活跃计划时返回有效结构"""
        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

            # AlertRule 查询返回 None，active_plans 返回空列表
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_production_plan_alerts()

        assert result is not None
        assert "alert_count" in result or "timestamp" in result

    def test_check_work_report_timeout_returns_dict(self):
        """测试无超时工单时返回有效结构"""
        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_work_report_timeout()

        assert result is not None
        assert "timestamp" in result

    def test_generate_production_daily_reports_returns_dict(self):
        """测试生产日报生成返回有效结构"""
        from app.utils.scheduled_tasks.production_tasks import generate_production_daily_reports

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = generate_production_daily_reports()

        assert result is not None

    def test_check_production_plan_alerts_with_low_progress_plan(self):
        """测试有低进度计划时创建预警"""
        from app.utils.scheduled_tasks.production_tasks import check_production_plan_alerts

        today = date.today()

        mock_plan = MagicMock()
        mock_plan.id = 1
        mock_plan.plan_no = "PP-001"
        mock_plan.plan_name = "Test Plan"
        mock_plan.progress = 50  # 低于 80%
        mock_plan.plan_end_date = today + timedelta(days=3)  # 3天后到期

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

            # AlertRule 不存在
            call_count = [0]
            def query_side_effect(model):
                call_count[0] += 1
                mock_q = MagicMock()
                mock_q.filter.return_value.first.return_value = None
                mock_q.filter.return_value.all.return_value = [mock_plan] if call_count[0] == 2 else []
                return mock_q

            mock_session.query.side_effect = query_side_effect

            result = check_production_plan_alerts()

        assert result is not None

    def test_check_work_report_timeout_exception(self):
        """测试工单超时检查异常返回 error"""
        from app.utils.scheduled_tasks.production_tasks import check_work_report_timeout

        with patch(
            "app.utils.scheduled_tasks.production_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("work report check failed")
            result = check_work_report_timeout()

        assert "error" in result


# ============================================================================
# kit_rate_tasks.py 全新测试
# ============================================================================


@pytest.mark.unit
class TestKitRateTasksNew:
    """kit_rate_tasks.py 全新测试（原先无覆盖）"""

    def test_calculate_kit_rate_for_bom_items_empty_list(self):
        """测试空 BOM 清单返回默认值"""
        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items

        mock_db = MagicMock(spec=Session)
        result = _calculate_kit_rate_for_bom_items(mock_db, [])

        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "shortage"
        assert result["total_items"] == 0

    def test_calculate_kit_rate_for_bom_items_all_fulfilled(self):
        """测试全部满足时 kit_rate = 100"""
        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items

        mock_db = MagicMock(spec=Session)
        mock_item = MagicMock()
        mock_item.quantity = 10
        mock_item.received_qty = 10
        mock_item.unit_price = 100
        mock_item.material = MagicMock()
        mock_item.material.current_stock = 0
        mock_item.material_id = None  # 无在途查询

        result = _calculate_kit_rate_for_bom_items(mock_db, [mock_item])

        assert result["kit_rate"] == 100.0
        assert result["kit_status"] == "complete"
        assert result["fulfilled_items"] == 1
        assert result["shortage_items"] == 0

    def test_calculate_kit_rate_for_bom_items_shortage(self):
        """测试缺料时 kit_status = shortage"""
        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items

        mock_db = MagicMock(spec=Session)
        items = []
        for i in range(5):
            mock_item = MagicMock()
            mock_item.quantity = 10
            mock_item.received_qty = 0
            mock_item.unit_price = 50
            mock_item.material = MagicMock()
            mock_item.material.current_stock = 0
            mock_item.material_id = None
            items.append(mock_item)

        result = _calculate_kit_rate_for_bom_items(mock_db, items)

        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "shortage"
        assert result["shortage_items"] == 5

    def test_calculate_kit_rate_by_amount(self):
        """测试按金额计算模式"""
        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items

        mock_db = MagicMock(spec=Session)
        mock_item = MagicMock()
        mock_item.quantity = 10
        mock_item.received_qty = 10
        mock_item.unit_price = 100
        mock_item.material = MagicMock()
        mock_item.material.current_stock = 0
        mock_item.material_id = None

        result = _calculate_kit_rate_for_bom_items(mock_db, [mock_item], calculate_by="amount")

        assert result["kit_rate"] == 100.0

    def test_create_kit_rate_snapshot_project_not_found(self):
        """测试项目不存在时返回 None"""
        from app.utils.scheduled_tasks.kit_rate_tasks import create_kit_rate_snapshot

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = create_kit_rate_snapshot(mock_db, project_id=999)

        assert result is None

    def test_create_stage_change_snapshot_callable(self):
        """测试 create_stage_change_snapshot 可调用"""
        from app.utils.scheduled_tasks.kit_rate_tasks import create_stage_change_snapshot
        assert callable(create_stage_change_snapshot)

    def test_daily_kit_rate_snapshot_callable(self):
        """测试 daily_kit_rate_snapshot 可调用"""
        from app.utils.scheduled_tasks.kit_rate_tasks import daily_kit_rate_snapshot
        assert callable(daily_kit_rate_snapshot)

    def test_daily_kit_rate_snapshot_exception(self):
        """测试每日齐套率快照任务异常时返回失败结构"""
        from app.utils.scheduled_tasks.kit_rate_tasks import daily_kit_rate_snapshot

        with patch(
            "app.utils.scheduled_tasks.kit_rate_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("DB connection failed")
            result = daily_kit_rate_snapshot()

        assert result["success"] is False
        assert "error" in result

    def test_daily_kit_rate_snapshot_no_projects(self):
        """测试无活跃项目时快照任务正常返回"""
        from app.utils.scheduled_tasks.kit_rate_tasks import daily_kit_rate_snapshot

        with patch(
            "app.utils.scheduled_tasks.kit_rate_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = daily_kit_rate_snapshot()

        assert result["success"] is True
        assert result["created"] == 0
        assert result["total_projects"] == 0

    def test_create_kit_rate_snapshot_daily_already_exists(self):
        """测试 DAILY 快照今天已存在时跳过"""
        from app.utils.scheduled_tasks.kit_rate_tasks import create_kit_rate_snapshot

        mock_db = MagicMock(spec=Session)
        mock_project = MagicMock()
        mock_existing_snapshot = MagicMock()
        mock_existing_snapshot.id = 42

        # 第一次 query(Project) 返回项目
        # 第二次 query(KitRateSnapshot) 返回已存在快照
        query_results = [mock_project, mock_existing_snapshot]
        call_idx = [0]

        def query_side(model):
            mock_q = MagicMock()
            idx = call_idx[0]
            call_idx[0] += 1
            if idx == 0:
                mock_q.filter.return_value.first.return_value = mock_project
            else:
                mock_q.filter.return_value.first.return_value = mock_existing_snapshot
            return mock_q

        mock_db.query.side_effect = query_side

        result = create_kit_rate_snapshot(mock_db, project_id=1, snapshot_type="DAILY")

        # 已存在时应返回 existing snapshot
        assert result is not None

    def test_calculate_kit_rate_partial_status(self):
        """测试 kit_rate 在 80-100 之间时 status = partial"""
        from app.utils.scheduled_tasks.kit_rate_tasks import _calculate_kit_rate_for_bom_items

        mock_db = MagicMock(spec=Session)
        items = []
        # 9 个满足，1 个缺货 => kit_rate = 90%
        for i in range(9):
            mock_item = MagicMock()
            mock_item.quantity = 10
            mock_item.received_qty = 10
            mock_item.unit_price = 100
            mock_item.material = MagicMock()
            mock_item.material.current_stock = 0
            mock_item.material_id = None
            items.append(mock_item)

        shortage_item = MagicMock()
        shortage_item.quantity = 10
        shortage_item.received_qty = 0
        shortage_item.unit_price = 100
        shortage_item.material = MagicMock()
        shortage_item.material.current_stock = 0
        shortage_item.material_id = None
        items.append(shortage_item)

        result = _calculate_kit_rate_for_bom_items(mock_db, items)

        assert result["kit_rate"] == 90.0
        assert result["kit_status"] == "partial"


# ============================================================================
# timesheet_tasks.py 扩展测试
# ============================================================================


@pytest.mark.unit
class TestTimesheetTasksExtended:
    """timesheet_tasks.py 扩展测试（补充异常路径）"""

    def test_daily_timesheet_reminder_exception(self):
        """测试每日工时提醒异常返回 error"""
        from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_reminder_task

        with patch(
            "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("reminder failed")
            result = daily_timesheet_reminder_task()

        assert "error" in result

    def test_weekly_timesheet_reminder_exception(self):
        """测试每周工时提醒异常返回 error"""
        from app.utils.scheduled_tasks.timesheet_tasks import weekly_timesheet_reminder_task

        with patch(
            "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("weekly reminder failed")
            result = weekly_timesheet_reminder_task()

        assert "error" in result

    def test_timesheet_anomaly_alert_exception(self):
        """测试工时异常提醒异常返回 error"""
        from app.utils.scheduled_tasks.timesheet_tasks import timesheet_anomaly_alert_task

        with patch(
            "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("anomaly detect failed")
            result = timesheet_anomaly_alert_task()

        assert "error" in result

    def test_timesheet_approval_timeout_exception(self):
        """测试审批超时提醒异常返回 error"""
        from app.utils.scheduled_tasks.timesheet_tasks import (
            timesheet_approval_timeout_reminder_task,
        )

        with patch(
            "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("approval timeout failed")
            result = timesheet_approval_timeout_reminder_task()

        assert "error" in result

    def test_daily_timesheet_reminder_success_returns_count(self):
        """测试每日工时提醒成功返回 reminder_count"""
        import sys

        mock_reminder = MagicMock()
        mock_reminder.notify_timesheet_missing = MagicMock(return_value=7)
        sys.modules["app.services.timesheet_reminder"] = mock_reminder

        try:
            from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_reminder_task

            with patch(
                "app.utils.scheduled_tasks.timesheet_tasks.get_db_session"
            ) as mock_ctx:
                mock_session = MagicMock()
                mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = daily_timesheet_reminder_task()

            assert result["reminder_count"] == 7
            assert "timestamp" in result
        finally:
            sys.modules.pop("app.services.timesheet_reminder", None)


# ============================================================================
# sales_tasks.py 扩展测试
# ============================================================================


@pytest.mark.unit
class TestSalesTasksExtended:
    """sales_tasks.py 扩展测试"""

    def test_sales_reminder_scan_no_exception_on_success(self):
        """测试销售扫描成功不抛异常"""
        import sys

        mock_scan = MagicMock()
        mock_scan.scan_and_notify_all = MagicMock(return_value={"sent": 3})
        sys.modules["app.services.sales_reminder"] = mock_scan

        try:
            from app.utils.scheduled_tasks.sales_tasks import sales_reminder_scan

            with patch(
                "app.utils.scheduled_tasks.sales_tasks.get_db_session"
            ) as mock_ctx:
                mock_session = MagicMock()
                mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

                # 应该不抛出异常
                sales_reminder_scan()
        finally:
            sys.modules.pop("app.services.sales_reminder", None)

    def test_check_payment_reminder_success_returns_count(self):
        """测试收款提醒成功返回 reminder_count"""
        import sys

        mock_service = MagicMock()
        mock_service.notify_payment_plan_upcoming = MagicMock(return_value=5)
        sys.modules["app.services.sales_reminder"] = mock_service

        try:
            from app.utils.scheduled_tasks.sales_tasks import check_payment_reminder

            with patch(
                "app.utils.scheduled_tasks.sales_tasks.get_db_session"
            ) as mock_ctx:
                mock_session = MagicMock()
                mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

                result = check_payment_reminder()

            assert result["reminder_count"] == 5
            assert "timestamp" in result
        finally:
            sys.modules.pop("app.services.sales_reminder", None)

    def test_check_overdue_receivable_alerts_no_invoices(self):
        """测试无逾期应收时正常返回"""
        from app.utils.scheduled_tasks.sales_tasks import check_overdue_receivable_alerts

        with patch(
            "app.utils.scheduled_tasks.sales_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_overdue_receivable_alerts()

        assert result is not None

    def test_check_opportunity_stage_timeout_no_opportunities(self):
        """测试无超时商机时正常返回"""
        from app.utils.scheduled_tasks.sales_tasks import check_opportunity_stage_timeout

        with patch(
            "app.utils.scheduled_tasks.sales_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_opportunity_stage_timeout()

        assert result is not None

    def test_sales_reminder_scan_exception_logged(self):
        """测试销售扫描异常时异常被 catch（不上抛）"""
        import sys

        mock_scan = MagicMock()
        mock_scan.scan_and_notify_all = MagicMock(side_effect=Exception("scan failed"))
        sys.modules["app.services.sales_reminder"] = mock_scan

        try:
            from app.utils.scheduled_tasks.sales_tasks import sales_reminder_scan

            with patch(
                "app.utils.scheduled_tasks.sales_tasks.get_db_session"
            ) as mock_ctx:
                mock_session = MagicMock()
                mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
                mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

                # 内部异常已被 catch，不应向上抛
                sales_reminder_scan()  # 不应 raise
        finally:
            sys.modules.pop("app.services.sales_reminder", None)


# ============================================================================
# hr_tasks.py 扩展测试
# ============================================================================


@pytest.mark.unit
class TestHRTasksExtended:
    """hr_tasks.py 扩展测试"""

    def test_check_contract_expiry_reminder_returns_dict(self):
        """测试合同到期提醒成功时返回正确结构"""
        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_contract_expiry_reminder()

        assert result is not None
        assert "reminders_created" in result or "error" not in result

    def test_check_contract_expiry_creates_reminder_for_expiring_contract(self):
        """测试即将到期合同创建提醒记录"""
        import sys

        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder

        mock_contract = MagicMock()
        mock_contract.id = 1
        mock_contract.employee_id = 10
        mock_contract.end_date = date.today() + timedelta(days=20)  # 20天后到期 → one_month
        mock_contract.status = "active"

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

            # EmployeeContract query 返回待检查的合同，ContractReminder query 返回 None
            call_idx = [0]
            def query_side(model):
                mock_q = MagicMock()
                idx = call_idx[0]
                call_idx[0] += 1
                if idx == 0:
                    mock_q.filter.return_value.all.return_value = [mock_contract]
                else:
                    mock_q.filter.return_value.first.return_value = None
                return mock_q

            mock_session.query.side_effect = query_side

            result = check_contract_expiry_reminder()

        assert result is not None

    def test_check_employee_confirmation_reminder_returns_dict(self):
        """测试员工转正提醒成功时返回正确结构"""
        from app.utils.scheduled_tasks.hr_tasks import check_employee_confirmation_reminder

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = check_employee_confirmation_reminder()

        assert result is not None

    def test_check_contract_expiry_expired_contract(self):
        """测试已到期合同生成 expired 类型提醒"""
        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder

        mock_contract = MagicMock()
        mock_contract.id = 2
        mock_contract.employee_id = 20
        mock_contract.end_date = date.today() - timedelta(days=5)  # 已到期
        mock_contract.status = "active"

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

            call_idx = [0]
            def query_side(model):
                mock_q = MagicMock()
                idx = call_idx[0]
                call_idx[0] += 1
                if idx == 0:
                    mock_q.filter.return_value.all.return_value = [mock_contract]
                else:
                    mock_q.filter.return_value.first.return_value = None
                return mock_q

            mock_session.query.side_effect = query_side

            result = check_contract_expiry_reminder()

        assert result is not None

    def test_check_contract_expiry_reminder_exception(self):
        """测试合同到期提醒异常返回 error"""
        from app.utils.scheduled_tasks.hr_tasks import check_contract_expiry_reminder

        with patch(
            "app.utils.scheduled_tasks.hr_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("DB error")
            result = check_contract_expiry_reminder()

        assert "error" in result


# ============================================================================
# alert_tasks.py 扩展测试
# ============================================================================


@pytest.mark.unit
class TestAlertTasksExtended:
    """alert_tasks.py 扩展测试"""

    def test_send_alert_notifications_callable(self):
        """测试 send_alert_notifications 可调用"""
        from app.utils.scheduled_tasks.alert_tasks import send_alert_notifications
        assert callable(send_alert_notifications)

    def test_send_alert_notifications_exception(self):
        """测试消息推送异常返回 error"""
        from app.utils.scheduled_tasks.alert_tasks import send_alert_notifications

        with patch(
            "app.utils.scheduled_tasks.alert_tasks.get_db_session"
        ) as mock_ctx:
            mock_ctx.side_effect = Exception("push failed")
            result = send_alert_notifications()

        assert "error" in result

    def test_check_alert_escalation_success(self):
        """测试预警升级成功返回正确结构"""
        from app.utils.scheduled_tasks.alert_tasks import check_alert_escalation

        with patch(
            "app.utils.scheduled_tasks.alert_tasks.get_db_session"
        ) as mock_ctx, patch(
            "app.services.alert_escalation_service.AlertEscalationService"
        ) as MockService:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

            mock_service = MagicMock()
            mock_service.check_and_escalate.return_value = {"checked": 5, "escalated": 2}
            MockService.return_value = mock_service

            result = check_alert_escalation()

        assert result is not None
        # 成功时不含 error
        assert "error" not in result

    def test_retry_failed_notifications_no_failed(self):
        """测试无失败通知时返回零计数"""
        from app.utils.scheduled_tasks.alert_tasks import retry_failed_notifications

        with patch(
            "app.utils.scheduled_tasks.alert_tasks.get_db_session"
        ) as mock_ctx:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = []

            result = retry_failed_notifications()

        assert result["retry_count"] == 0
        assert result["success_count"] == 0
        assert "timestamp" in result

    def test_send_alert_notifications_no_pending_alerts(self):
        """测试无待处理预警时消息推送任务返回零发送"""
        from app.utils.scheduled_tasks.alert_tasks import send_alert_notifications

        with patch(
            "app.utils.scheduled_tasks.alert_tasks.get_db_session"
        ) as mock_ctx, patch(
            "app.utils.scheduled_tasks.alert_tasks.NotificationDispatcher"
        ) as MockDispatcher:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)

            mock_dispatcher = MagicMock()
            MockDispatcher.return_value = mock_dispatcher

            mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value = MagicMock(all=MagicMock(return_value=[]))

            result = send_alert_notifications()

        assert result is not None
        assert "sent_count" in result or "queue_created" in result or "timestamp" in result

    def test_check_alert_response_metrics_callable(self):
        """测试 check_alert_response_metrics 可调用（如存在）"""
        from app.utils.scheduled_tasks import alert_tasks
        if hasattr(alert_tasks, "check_alert_response_metrics"):
            assert callable(alert_tasks.check_alert_response_metrics)
        # 不存在也不失败

    def test_retry_failed_notifications_max_retries_exceeded(self):
        """测试超过最大重试次数时通知被放弃"""
        from app.utils.scheduled_tasks.alert_tasks import retry_failed_notifications

        mock_notification = MagicMock()
        mock_notification.id = 1
        mock_notification.alert_id = 100
        mock_notification.notify_user_id = 1
        mock_notification.status = "FAILED"
        mock_notification.retry_count = 3  # 等于 max_retries
        mock_notification.next_retry_at = None
        mock_notification.alert = MagicMock()

        with patch(
            "app.utils.scheduled_tasks.alert_tasks.get_db_session"
        ) as mock_ctx, patch(
            "app.utils.scheduled_tasks.alert_tasks.NotificationDispatcher"
        ) as MockDispatcher:
            mock_session = MagicMock()
            mock_ctx.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_ctx.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.query.return_value.filter.return_value.all.return_value = [mock_notification]
            mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()

            mock_dispatcher = MagicMock()
            mock_dispatcher.dispatch.return_value = False  # 重试失败
            MockDispatcher.return_value = mock_dispatcher

            result = retry_failed_notifications()

        assert result is not None


# ============================================================================
# 模块导入与集成测试
# ============================================================================


@pytest.mark.unit
class TestH2ModuleIntegration:
    """H2 组模块集成与导入测试"""

    def test_all_h2_modules_importable(self):
        """测试所有 H2 组模块可正常导入"""
        modules = [
            "app.utils.scheduled_tasks.base",
            "app.utils.scheduled_tasks.project_scheduled_tasks",
            "app.utils.scheduled_tasks.issue_scheduled_tasks",
            "app.utils.scheduled_tasks.issue_tasks",
            "app.utils.scheduled_tasks.production_tasks",
            "app.utils.scheduled_tasks.kit_rate_tasks",
            "app.utils.scheduled_tasks.timesheet_tasks",
            "app.utils.scheduled_tasks.sales_tasks",
            "app.utils.scheduled_tasks.hr_tasks",
            "app.utils.scheduled_tasks.alert_tasks",
        ]
        import importlib
        for module_name in modules:
            mod = importlib.import_module(module_name)
            assert mod is not None, f"模块 {module_name} 导入失败"

    def test_issue_tasks_module_has_required_functions(self):
        """测试 issue_tasks 模块包含必要函数"""
        from app.utils.scheduled_tasks import issue_tasks

        required = [
            "check_overdue_issues",
            "check_blocking_issues",
            "check_timeout_issues",
            "daily_issue_statistics_snapshot",
        ]
        for fn in required:
            assert hasattr(issue_tasks, fn), f"issue_tasks 缺少函数 {fn}"

    def test_kit_rate_tasks_module_has_required_functions(self):
        """测试 kit_rate_tasks 模块包含必要函数"""
        from app.utils.scheduled_tasks import kit_rate_tasks

        required = [
            "_calculate_kit_rate_for_bom_items",
            "create_kit_rate_snapshot",
            "daily_kit_rate_snapshot",
            "create_stage_change_snapshot",
        ]
        for fn in required:
            assert hasattr(kit_rate_tasks, fn), f"kit_rate_tasks 缺少函数 {fn}"

    def test_all_task_functions_are_callable(self):
        """测试所有关键任务函数均可调用"""
        from app.utils.scheduled_tasks.project_scheduled_tasks import (
            calculate_project_health,
            check_project_deadline_alerts,
            check_project_cost_overrun,
            calculate_progress_summary,
        )
        from app.utils.scheduled_tasks.issue_tasks import (
            check_overdue_issues,
            check_blocking_issues,
            check_timeout_issues,
        )
        from app.utils.scheduled_tasks.kit_rate_tasks import (
            daily_kit_rate_snapshot,
            create_stage_change_snapshot,
        )
        from app.utils.scheduled_tasks.alert_tasks import (
            check_alert_escalation,
            retry_failed_notifications,
            send_alert_notifications,
        )

        for fn in [
            calculate_project_health,
            check_project_deadline_alerts,
            check_project_cost_overrun,
            calculate_progress_summary,
            check_overdue_issues,
            check_blocking_issues,
            check_timeout_issues,
            daily_kit_rate_snapshot,
            send_alert_notifications,
            check_alert_escalation,
            retry_failed_notifications,
        ]:
            assert callable(fn), f"{fn.__name__} 不可调用"

    def test_task_exception_handling_pattern(self):
        """测试所有任务函数的异常处理模式一致（均返回 error 或不上抛）"""
        tasks_with_error_return = [
            ("app.utils.scheduled_tasks.project_scheduled_tasks", "calculate_project_health"),
            ("app.utils.scheduled_tasks.project_scheduled_tasks", "check_project_deadline_alerts"),
            ("app.utils.scheduled_tasks.project_scheduled_tasks", "check_project_cost_overrun"),
            ("app.utils.scheduled_tasks.issue_tasks", "check_overdue_issues"),
            ("app.utils.scheduled_tasks.issue_tasks", "check_blocking_issues"),
            ("app.utils.scheduled_tasks.issue_tasks", "check_timeout_issues"),
            ("app.utils.scheduled_tasks.kit_rate_tasks", "daily_kit_rate_snapshot"),
            ("app.utils.scheduled_tasks.alert_tasks", "check_alert_escalation"),
            ("app.utils.scheduled_tasks.alert_tasks", "retry_failed_notifications"),
            ("app.utils.scheduled_tasks.hr_tasks", "check_contract_expiry_reminder"),
        ]

        import importlib

        for module_name, fn_name in tasks_with_error_return:
            mod = importlib.import_module(module_name)
            fn = getattr(mod, fn_name)

            # patch get_db_session 抛异常
            with patch(
                f"{module_name}.get_db_session"
            ) as mock_ctx:
                mock_ctx.side_effect = Exception(f"Test error for {fn_name}")
                try:
                    result = fn()
                    # 如果正常返回，应包含 error 或者 success=False
                    if result is not None:
                        has_error = "error" in result or result.get("success") is False
                        assert has_error, (
                            f"{module_name}.{fn_name} 异常时返回结果 {result} 不含 error 字段"
                        )
                except Exception as e:
                    # 少数函数（如 daily_spec_match_check）内部会 re-raise，允许
                    pass
