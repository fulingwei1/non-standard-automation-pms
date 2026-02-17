# -*- coding: utf-8 -*-
"""
单元测试 - 定时任务：基础模块 (base.py)
L2组覆盖率提升
"""
import sys
from unittest.mock import MagicMock, patch

sys.modules.setdefault("redis", MagicMock())
sys.modules.setdefault("redis.exceptions", MagicMock())

import pytest


def _make_db():
    return MagicMock()


# ================================================================
#  send_notification_for_alert
# ================================================================

class TestSendNotificationForAlert:

    def test_dispatches_and_logs_debug(self):
        """成功创建通知 → 记录 debug 日志"""
        db = _make_db()
        alert = MagicMock()
        alert.alert_no = "ALERT-001"

        with patch(
            "app.services.notification_dispatcher.NotificationDispatcher"
        ) as MockDisp:
            instance = MagicMock()
            instance.dispatch_alert_notifications.return_value = {
                "created": 2,
                "queued": 1,
                "sent": 1,
                "failed": 0,
            }
            MockDisp.return_value = instance

            mock_logger = MagicMock()

            from app.utils.scheduled_tasks.base import send_notification_for_alert
            send_notification_for_alert(db, alert, logger_instance=mock_logger)

        instance.dispatch_alert_notifications.assert_called_once_with(alert=alert)
        mock_logger.debug.assert_called_once()

    def test_zero_notifications_created_no_debug(self):
        """创建了 0 条通知 → 不调用 debug"""
        db = _make_db()
        alert = MagicMock()
        alert.alert_no = "ALERT-002"

        with patch(
            "app.services.notification_dispatcher.NotificationDispatcher"
        ) as MockDisp:
            instance = MagicMock()
            instance.dispatch_alert_notifications.return_value = {
                "created": 0,
                "queued": 0,
                "sent": 0,
                "failed": 0,
            }
            MockDisp.return_value = instance

            mock_logger = MagicMock()

            from app.utils.scheduled_tasks.base import send_notification_for_alert
            send_notification_for_alert(db, alert, logger_instance=mock_logger)

        mock_logger.debug.assert_not_called()

    def test_exception_logged_not_raised(self):
        """分发异常 → error 日志，不向外抛出"""
        db = _make_db()
        alert = MagicMock()
        alert.alert_no = "ALERT-ERR"

        with patch(
            "app.services.notification_dispatcher.NotificationDispatcher",
            side_effect=Exception("dispatch error"),
        ):
            mock_logger = MagicMock()

            from app.utils.scheduled_tasks.base import send_notification_for_alert
            # 不应抛出
            send_notification_for_alert(db, alert, logger_instance=mock_logger)

        mock_logger.error.assert_called_once()

    def test_uses_module_logger_when_none_provided(self):
        """未提供 logger_instance → 使用模块 logger"""
        db = _make_db()
        alert = MagicMock()
        alert.alert_no = "ALERT-003"

        with patch(
            "app.services.notification_dispatcher.NotificationDispatcher"
        ) as MockDisp:
            instance = MagicMock()
            instance.dispatch_alert_notifications.return_value = {"created": 0}
            MockDisp.return_value = instance

            from app.utils.scheduled_tasks.base import send_notification_for_alert
            # 不传 logger_instance，用模块默认 logger，不应抛出
            send_notification_for_alert(db, alert)


# ================================================================
#  enqueue_or_dispatch_notification
# ================================================================

class TestEnqueueOrDispatchNotification:

    def test_enqueued_successfully(self):
        """成功入队 → 返回 queued=True"""
        dispatcher = MagicMock()
        dispatcher.build_notification_request.return_value = MagicMock(__dict__={"key": "val"})

        notification = MagicMock()
        notification.id = 1
        notification.alert_id = 10
        notification.notify_channel = "WECHAT"

        alert = MagicMock()
        user = MagicMock()

        with patch(
            "app.services.notification_queue.enqueue_notification",
            return_value=True,
        ):
            from app.utils.scheduled_tasks.base import enqueue_or_dispatch_notification
            result = enqueue_or_dispatch_notification(dispatcher, notification, alert, user)

        assert result["queued"] is True
        assert result["sent"] is False
        assert notification.status == "QUEUED"

    def test_queue_full_falls_back_to_dispatch(self):
        """入队失败 → fallback 同步发送"""
        dispatcher = MagicMock()
        dispatcher.build_notification_request.return_value = MagicMock(__dict__={"key": "val"})
        dispatcher.dispatch.return_value = True

        notification = MagicMock()
        notification.id = 2
        notification.alert_id = 11
        notification.notify_channel = "EMAIL"

        alert = MagicMock()
        user = MagicMock()

        with patch(
            "app.services.notification_queue.enqueue_notification",
            return_value=False,
        ):
            from app.utils.scheduled_tasks.base import enqueue_or_dispatch_notification
            result = enqueue_or_dispatch_notification(dispatcher, notification, alert, user)

        assert result["queued"] is False
        assert result["sent"] is True

    def test_build_request_exception_returns_error(self):
        """build_notification_request 抛异常 → 返回 error"""
        dispatcher = MagicMock()
        dispatcher.build_notification_request.side_effect = Exception("build error")

        notification = MagicMock()
        notification.id = 3
        alert = MagicMock()
        user = MagicMock()

        from app.utils.scheduled_tasks.base import enqueue_or_dispatch_notification
        result = enqueue_or_dispatch_notification(dispatcher, notification, alert, user)

        assert result["queued"] is False
        assert result["sent"] is False
        assert "error" in result
        assert notification.status == "FAILED"

    def test_uses_provided_request(self):
        """传入预构建 request → 跳过 build"""
        dispatcher = MagicMock()
        dispatcher.dispatch.return_value = False

        notification = MagicMock()
        notification.id = 4
        notification.alert_id = 12
        notification.notify_channel = "SMS"

        alert = MagicMock()
        user = MagicMock()

        pre_built = MagicMock()
        pre_built.__dict__ = {"channel": "SMS"}

        with patch(
            "app.services.notification_queue.enqueue_notification",
            return_value=False,
        ):
            from app.utils.scheduled_tasks.base import enqueue_or_dispatch_notification
            result = enqueue_or_dispatch_notification(
                dispatcher, notification, alert, user, request=pre_built
            )

        dispatcher.build_notification_request.assert_not_called()


# ================================================================
#  log_task_result
# ================================================================

class TestLogTaskResult:

    def test_logs_error_when_error_key_present(self):
        """result 含 error → 调用 logger.error"""
        mock_logger = MagicMock()

        from app.utils.scheduled_tasks.base import log_task_result
        log_task_result("测试任务", {"error": "something went wrong"}, mock_logger)

        mock_logger.error.assert_called_once()

    def test_logs_info_on_success(self):
        """result 不含 error → 调用 logger.info"""
        mock_logger = MagicMock()

        from app.utils.scheduled_tasks.base import log_task_result
        log_task_result("成功任务", {"created": 5, "skipped": 0}, mock_logger)

        mock_logger.info.assert_called_once()

    def test_uses_module_logger_when_none(self):
        """未提供 logger → 使用模块 logger，不抛出"""
        from app.utils.scheduled_tasks.base import log_task_result
        # 不传 logger_instance，不应抛出
        log_task_result("默认日志任务", {"ok": True})


# ================================================================
#  safe_task_execution
# ================================================================

class TestSafeTaskExecution:

    def test_wraps_and_returns_result(self):
        """task_func 正常执行 → 返回结果"""
        mock_func = MagicMock(return_value={"count": 3})
        mock_logger = MagicMock()

        from app.utils.scheduled_tasks.base import safe_task_execution
        wrapped = safe_task_execution(mock_func, "正常任务", mock_logger)
        result = wrapped()

        assert result == {"count": 3}
        mock_logger.info.assert_called_once()

    def test_catches_exception_returns_error(self):
        """task_func 抛异常 → 返回 error 字典，不向外抛"""
        mock_func = MagicMock(side_effect=Exception("task failed"))
        mock_logger = MagicMock()

        from app.utils.scheduled_tasks.base import safe_task_execution
        wrapped = safe_task_execution(mock_func, "失败任务", mock_logger)
        result = wrapped()

        assert "error" in result
        mock_logger.error.assert_called_once()

    def test_passes_args_to_func(self):
        """wrapper 传递位置参数"""
        mock_func = MagicMock(return_value={"ok": True})
        mock_logger = MagicMock()

        from app.utils.scheduled_tasks.base import safe_task_execution
        wrapped = safe_task_execution(mock_func, "带参任务", mock_logger)
        wrapped(1, 2, key="value")

        mock_func.assert_called_once_with(1, 2, key="value")

    def test_result_none_handled(self):
        """task_func 返回 None → log_task_result 收到 {}，不抛出"""
        mock_func = MagicMock(return_value=None)
        mock_logger = MagicMock()

        from app.utils.scheduled_tasks.base import safe_task_execution
        wrapped = safe_task_execution(mock_func, "空结果任务", mock_logger)
        result = wrapped()

        assert result is None
        mock_logger.info.assert_called_once()
