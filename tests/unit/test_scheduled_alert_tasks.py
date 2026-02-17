# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：预警与通知相关 (alert_tasks.py)
L2组覆盖率提升
"""
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


def make_mock_db_ctx(return_data=None):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = return_data or []
    mock_db.query.return_value.all.return_value = return_data or []
    mock_db.query.return_value.filter.return_value.first.return_value = (
        return_data[0] if return_data else None
    )

    @contextmanager
    def ctx():
        yield mock_db

    return ctx, mock_db


# ================================================================
#  check_alert_escalation
# ================================================================

class TestCheckAlertEscalation:

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_empty_result(self, mock_get_db):
        """escalation service 返回空结果"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert_escalation_service.AlertEscalationService"
        ) as MockSvc:
            instance = MagicMock()
            instance.check_and_escalate.return_value = {"checked": 0, "escalated": 0}
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.alert_tasks import check_alert_escalation
            result = check_alert_escalation()

        assert result.get("checked") == 0
        assert result.get("escalated") == 0

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_with_escalations(self, mock_get_db):
        """escalation service 返回有升级数据"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert_escalation_service.AlertEscalationService"
        ) as MockSvc:
            instance = MagicMock()
            instance.check_and_escalate.return_value = {"checked": 10, "escalated": 3}
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.alert_tasks import check_alert_escalation
            result = check_alert_escalation()

        assert result.get("escalated") == 3

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """异常时返回 error 字段"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert_escalation_service.AlertEscalationService",
            side_effect=Exception("escalation error"),
        ):
            from app.utils.scheduled_tasks.alert_tasks import check_alert_escalation
            result = check_alert_escalation()

        assert "error" in result


# ================================================================
#  retry_failed_notifications
# ================================================================

class TestRetryFailedNotifications:

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_no_failed_notifications(self, mock_get_db):
        """无需重试的通知 → retry_count=0"""
        ctx, mock_db = make_mock_db_ctx()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_get_db.side_effect = ctx

        with patch("app.services.notification_dispatcher.NotificationDispatcher"):
            from app.utils.scheduled_tasks.alert_tasks import retry_failed_notifications
            result = retry_failed_notifications()

        assert result["retry_count"] == 0
        assert result["success_count"] == 0

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_successful_retry(self, mock_get_db):
        """重试成功 → success_count 增加"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        notification = MagicMock()
        notification.id = 1
        notification.notify_user_id = 10
        notification.retry_count = 1
        notification.alert = MagicMock()

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            notification
        ]

        user = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = user

        with patch(
            "app.services.notification_dispatcher.NotificationDispatcher"
        ) as MockDisp:
            instance = MagicMock()
            instance.dispatch.return_value = True
            MockDisp.return_value = instance

            from app.utils.scheduled_tasks.alert_tasks import retry_failed_notifications
            result = retry_failed_notifications()

        assert result["retry_count"] >= 1
        assert result["success_count"] >= 1

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_notification_missing_alert_abandoned(self, mock_get_db):
        """通知关联的 alert 不存在 → abandoned"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        notification = MagicMock()
        notification.id = 2
        notification.notify_user_id = None
        notification.retry_count = 0
        notification.alert = None  # alert 不存在

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
            notification
        ]

        with patch("app.services.notification_dispatcher.NotificationDispatcher"):
            from app.utils.scheduled_tasks.alert_tasks import retry_failed_notifications
            result = retry_failed_notifications()

        assert result["abandoned_count"] >= 1

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """DB session 异常 → 返回 error"""
        @contextmanager
        def bad_ctx():
            raise Exception("db error")
            yield  # noqa

        mock_get_db.side_effect = bad_ctx

        from app.utils.scheduled_tasks.alert_tasks import retry_failed_notifications
        result = retry_failed_notifications()

        assert "error" in result


# ================================================================
#  send_alert_notifications
# ================================================================

class TestSendAlertNotifications:

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_no_pending_alerts_or_notifications(self, mock_get_db):
        """无待处理预警或通知 → 返回 0 统计"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        # 两次 all() 都返回空
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        with patch("app.services.notification_dispatcher.NotificationDispatcher") as MockDisp:
            instance = MagicMock()
            instance.dispatch_alert_notifications.return_value = {
                "created": 0, "queued": 0, "sent": 0, "failed": 0
            }
            MockDisp.return_value = instance

            from app.utils.scheduled_tasks.alert_tasks import send_alert_notifications
            result = send_alert_notifications()

        assert result["queue_created"] == 0
        assert result["sent_count"] == 0

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_pending_alerts_dispatched(self, mock_get_db):
        """有 PENDING 预警 → dispatch_alert_notifications 被调用"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        alert = MagicMock()
        alert.id = 1
        alert.status = "PENDING"

        # pending_alerts 查询
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [alert]
        # pending_notifications 查询（or_ filter）
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        with patch("app.services.notification_dispatcher.NotificationDispatcher") as MockDisp:
            instance = MagicMock()
            instance.dispatch_alert_notifications.return_value = {
                "created": 1, "queued": 1, "sent": 0, "failed": 0
            }
            MockDisp.return_value = instance

            from app.utils.scheduled_tasks.alert_tasks import send_alert_notifications
            result = send_alert_notifications()

        assert result["queue_created"] == 1

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """异常时返回 error"""
        @contextmanager
        def bad_ctx():
            raise Exception("send error")
            yield  # noqa

        mock_get_db.side_effect = bad_ctx

        from app.utils.scheduled_tasks.alert_tasks import send_alert_notifications
        result = send_alert_notifications()

        assert "error" in result


# ================================================================
#  calculate_response_metrics
# ================================================================

class TestCalculateResponseMetrics:

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_returns_metrics(self, mock_get_db):
        """响应指标计算成功"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert_response_service.AlertResponseService"
        ) as MockSvc:
            instance = MagicMock()
            instance.calculate_daily_metrics.return_value = {"avg_response_time": 3.5}
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.alert_tasks import calculate_response_metrics
            result = calculate_response_metrics()

        assert result.get("avg_response_time") == 3.5

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_empty_metrics(self, mock_get_db):
        """响应指标为空"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert_response_service.AlertResponseService"
        ) as MockSvc:
            instance = MagicMock()
            instance.calculate_daily_metrics.return_value = {}
            MockSvc.return_value = instance

            from app.utils.scheduled_tasks.alert_tasks import calculate_response_metrics
            result = calculate_response_metrics()

        assert result == {}

    @patch("app.utils.scheduled_tasks.alert_tasks.get_db_session")
    def test_exception_returns_error(self, mock_get_db):
        """异常时返回 error"""
        ctx, mock_db = make_mock_db_ctx()
        mock_get_db.side_effect = ctx

        with patch(
            "app.services.alert_response_service.AlertResponseService",
            side_effect=Exception("metrics error"),
        ):
            from app.utils.scheduled_tasks.alert_tasks import calculate_response_metrics
            result = calculate_response_metrics()

        assert "error" in result
