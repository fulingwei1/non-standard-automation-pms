# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：工时相关 (timesheet_tasks.py)
J2组覆盖率提升
"""
import sys
from unittest.mock import MagicMock, patch

sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


def _make_db():
    return MagicMock()


# ================================================================
#  daily_timesheet_reminder_task
# ================================================================

class TestDailyTimesheetReminderTask:

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_returns_reminder_count(self, mock_db_ctx):
        """正常执行返回 reminder_count"""
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_timesheet_missing",
            return_value=5,
        ) as mock_notify:
            from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_reminder_task
            result = daily_timesheet_reminder_task()

        assert result["reminder_count"] == 5
        assert "timestamp" in result

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        """service 抛异常时返回 error 键"""
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_timesheet_missing",
            side_effect=Exception("DB error"),
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_reminder_task
            result = daily_timesheet_reminder_task()

        assert "error" in result

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_zero_reminders(self, mock_db_ctx):
        """没有需要提醒的用户时返回 0"""
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_timesheet_missing",
            return_value=0,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_reminder_task
            result = daily_timesheet_reminder_task()

        assert result["reminder_count"] == 0


# ================================================================
#  weekly_timesheet_reminder_task
# ================================================================

class TestWeeklyTimesheetReminderTask:

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_returns_reminder_count(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_weekly_timesheet_missing",
            return_value=3,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import weekly_timesheet_reminder_task
            result = weekly_timesheet_reminder_task()

        assert result["reminder_count"] == 3

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_weekly_timesheet_missing",
            side_effect=RuntimeError("weekly error"),
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import weekly_timesheet_reminder_task
            result = weekly_timesheet_reminder_task()

        assert "error" in result


# ================================================================
#  timesheet_approval_timeout_reminder_task
# ================================================================

class TestTimesheetApprovalTimeoutReminderTask:

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_returns_reminder_count(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_approval_timeout",
            return_value=7,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import timesheet_approval_timeout_reminder_task
            result = timesheet_approval_timeout_reminder_task()

        assert result["reminder_count"] == 7

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_approval_timeout",
            side_effect=Exception("approval error"),
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import timesheet_approval_timeout_reminder_task
            result = timesheet_approval_timeout_reminder_task()

        assert "error" in result


# ================================================================
#  timesheet_sync_failure_alert_task
# ================================================================

class TestTimesheetSyncFailureAlertTask:

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_returns_alert_count(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_sync_failure",
            return_value=2,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import timesheet_sync_failure_alert_task
            result = timesheet_sync_failure_alert_task()

        assert result["alert_count"] == 2

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_reminder.notify_sync_failure",
            side_effect=Exception("sync error"),
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import timesheet_sync_failure_alert_task
            result = timesheet_sync_failure_alert_task()

        assert "error" in result


# ================================================================
#  daily_timesheet_aggregation_task
# ================================================================

class TestDailyTimesheetAggregationTask:

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_returns_aggregation_result(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        mock_service = MagicMock()
        mock_service.aggregate_monthly_timesheet.return_value = {
            "message": "汇总完成",
            "total_hours": 800.5,
        }

        with patch(
            "app.services.timesheet_aggregation_service.TimesheetAggregationService",
            return_value=mock_service,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_aggregation_task
            result = daily_timesheet_aggregation_task()

        assert result.get("message") == "汇总完成"

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_aggregation_service.TimesheetAggregationService",
            side_effect=Exception("agg error"),
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import daily_timesheet_aggregation_task
            result = daily_timesheet_aggregation_task()

        assert "error" in result


# ================================================================
#  monthly_timesheet_aggregation_task
# ================================================================

class TestMonthlyTimesheetAggregationTask:

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_calculates_previous_month(self, mock_db_ctx):
        """确认调用了正确的 aggregate_monthly_timesheet"""
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        mock_service = MagicMock()
        mock_service.aggregate_monthly_timesheet.return_value = {"message": "月度汇总完成"}

        with patch(
            "app.services.timesheet_aggregation_service.TimesheetAggregationService",
            return_value=mock_service,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import monthly_timesheet_aggregation_task
            result = monthly_timesheet_aggregation_task()

        assert mock_service.aggregate_monthly_timesheet.called

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.timesheet_aggregation_service.TimesheetAggregationService",
            side_effect=Exception("month error"),
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import monthly_timesheet_aggregation_task
            result = monthly_timesheet_aggregation_task()

        assert "error" in result


# ================================================================
#  calculate_monthly_labor_cost_task
# ================================================================

class TestCalculateMonthlyLaborCostTask:

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_returns_cost_result(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        mock_service = MagicMock()
        mock_service.calculate_monthly_costs.return_value = {
            "message": "成本计算完成",
            "total_cost": 50000,
        }

        with patch(
            "app.services.labor_cost_service.LaborCostCalculationService",
            return_value=mock_service,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import calculate_monthly_labor_cost_task
            result = calculate_monthly_labor_cost_task()

        assert mock_service.calculate_monthly_costs.called

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        with patch(
            "app.services.labor_cost_service.LaborCostCalculationService",
            side_effect=Exception("cost error"),
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import calculate_monthly_labor_cost_task
            result = calculate_monthly_labor_cost_task()

        assert "error" in result


# ================================================================
#  timesheet_anomaly_alert_task
# ================================================================

class TestTimesheetAnomalyAlertTask:

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_no_anomalies(self, mock_db_ctx):
        """无异常工时时 reminder_count=0"""
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        mock_detector = MagicMock()
        mock_detector.detect_all_anomalies.return_value = []
        mock_manager = MagicMock()
        mock_sender = MagicMock()
        mock_reminder_type = MagicMock()

        with patch(
            "app.services.timesheet_reminder.anomaly_detector.TimesheetAnomalyDetector",
            return_value=mock_detector,
        ), patch(
            "app.services.timesheet_reminder.notification_sender.NotificationSender",
            return_value=mock_sender,
        ), patch(
            "app.services.timesheet_reminder.reminder_manager.TimesheetReminderManager",
            return_value=mock_manager,
        ), patch(
            "app.models.timesheet_reminder.ReminderTypeEnum",
            mock_reminder_type,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import timesheet_anomaly_alert_task
            result = timesheet_anomaly_alert_task()

        assert result["anomaly_count"] == 0
        assert result["reminder_count"] == 0

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_with_anomalies(self, mock_db_ctx):
        """有异常工时时为每条创建提醒"""
        db = _make_db()
        mock_db_ctx.return_value.__enter__.return_value = db
        mock_db_ctx.return_value.__exit__.return_value = False

        anomaly = MagicMock()
        anomaly.user_id = 1
        anomaly.user_name = "张三"
        anomaly.anomaly_type.value = "OVER_HOURS"
        anomaly.description = "超时工作"
        anomaly.id = 100
        anomaly.anomaly_data = {}

        mock_detector = MagicMock()
        mock_detector.detect_all_anomalies.return_value = [anomaly]
        mock_manager = MagicMock()
        mock_manager.create_reminder_record.return_value = MagicMock(id=1)
        mock_sender = MagicMock()
        mock_reminder_type = MagicMock()

        with patch(
            "app.services.timesheet_reminder.anomaly_detector.TimesheetAnomalyDetector",
            return_value=mock_detector,
        ), patch(
            "app.services.timesheet_reminder.notification_sender.NotificationSender",
            return_value=mock_sender,
        ), patch(
            "app.services.timesheet_reminder.reminder_manager.TimesheetReminderManager",
            return_value=mock_manager,
        ), patch(
            "app.models.timesheet_reminder.ReminderTypeEnum",
            mock_reminder_type,
        ):
            from app.utils.scheduled_tasks.timesheet_tasks import timesheet_anomaly_alert_task
            result = timesheet_anomaly_alert_task()

        assert result["anomaly_count"] == 1
        assert result["reminder_count"] == 1

    @patch("app.utils.scheduled_tasks.timesheet_tasks.get_db_session")
    def test_exception_returns_error(self, mock_db_ctx):
        mock_db_ctx.return_value.__enter__.side_effect = Exception("异常检测失败")

        from app.utils.scheduled_tasks.timesheet_tasks import timesheet_anomaly_alert_task
        result = timesheet_anomaly_alert_task()

        assert "error" in result
