# -*- coding: utf-8 -*-
"""
P0-11: 通知触达假成功 + 预警积压饿死。

channels/email_handler.py:52-55 与 sms_handler.py:29-31 在无任何真实发送实现（无
smtplib / 无短信网关）的情况下，只 logger.info 就返回 success=True。

正确行为：未配置真实发送通道时，send() 必须返回 success=False（不能谎报已送达）。
附带：SELECT count(*) FROM alert_records WHERE status='PENDING' 佐证约 841 条积压。
"""
from unittest.mock import MagicMock
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.audit_p0


def _make_request():
    from app.services.notification.channels.base import NotificationRequest

    return NotificationRequest(
        recipient_id=1,
        notification_type="ALERT",
        category="SHORTAGE",
        title="audit-p0",
        content="reproduction",
    )


def _fake_db_with_contactable_user():
    """db.query(User).filter().first() -> 一个有 email/phone 的用户。"""
    user = MagicMock()
    user.email = "someone@example.com"
    user.phone = "13800000000"
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    return db


def test_email_channel_does_not_fake_success_without_smtp():
    from app.services.notification.channels.email_handler import EmailChannelHandler

    handler = EmailChannelHandler(db=_fake_db_with_contactable_user(), channel="EMAIL")
    handler.is_enabled = lambda: True  # 越过“功能未启用”短路，直击假桩发送体

    result = handler.send(_make_request())
    assert result.success is False, (
        "邮件渠道在无 SMTP 实现下仍返回 success=True（logger.info 即成功）——系统性谎报送达"
    )


def test_sms_channel_does_not_fake_success_without_gateway():
    from app.services.notification.channels.sms_handler import SMSChannelHandler

    handler = SMSChannelHandler(db=_fake_db_with_contactable_user(), channel="SMS")
    handler.is_enabled = lambda: True

    result = handler.send(_make_request())
    assert result.success is False, (
        "短信渠道在无网关实现下仍返回 success=True —— 假桩谎报送达"
    )


def test_alert_records_backlog_documented(sandbox_conn):
    """佐证性观察：PENDING 预警大量积压（报告称约 841 条）。"""
    n = sandbox_conn.execute(
        "SELECT count(*) FROM alert_records WHERE status='PENDING'"
    ).fetchone()[0]
    # 这是对现状的取证，不随修复消失；仅要求量级显著
    assert n > 500, f"预期 PENDING 预警大量积压，实际 {n}"


def test_notification_queue_defaults_to_sync_dispatch_even_when_redis_exists(monkeypatch):
    """未显式启用队列 worker 时，即使 Redis 存在也不能把通知丢进无人消费队列。"""
    from app.utils.scheduled_tasks.base import enqueue_or_dispatch_notification

    dispatcher = MagicMock()
    request = SimpleNamespace(recipient_id=1, channels=["EMAIL"])
    dispatcher.build_notification_request.return_value = request
    dispatcher.dispatch.return_value = True

    notification = MagicMock()
    notification.id = 1
    notification.alert_id = 2
    notification.notify_channel = "EMAIL"

    monkeypatch.setattr(
        "app.services.notification.notification_queue.get_redis_client",
        lambda: MagicMock(),
    )

    result = enqueue_or_dispatch_notification(
        dispatcher,
        notification,
        alert=MagicMock(),
        user=MagicMock(),
    )

    assert result == {"queued": False, "sent": True}
    dispatcher.dispatch.assert_called_once()


def test_notification_worker_script_imports_current_modules():
    """worker 脚本不能引用已不存在的 app.services.notification_queue 等旧路径。"""
    script_path = Path(__file__).parents[2] / "scripts" / "notification_worker.py"
    spec = importlib.util.spec_from_file_location("notification_worker_audit", script_path)
    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    assert hasattr(module, "main")


def test_alert_notification_task_moves_alert_out_of_pending_after_attempt(monkeypatch):
    """通知生成/发送已尝试后，AlertRecord 不能继续停在 PENDING 堵住后续窗口。"""
    from app.utils.scheduled_tasks import alert_tasks

    alert = MagicMock()
    alert.id = 1
    alert.status = "PENDING"
    alert.triggered_at = None

    db = MagicMock()
    pending_alert_query = MagicMock()
    pending_alert_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
        alert
    ]
    pending_notification_query = MagicMock()
    pending_notification_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    db.query.side_effect = [pending_alert_query, pending_notification_query]

    class _Ctx:
        def __enter__(self):
            return db

        def __exit__(self, exc_type, exc, tb):
            return False

    dispatcher = MagicMock()
    dispatcher.dispatch_alert_notifications.return_value = {
        "created": 1,
        "queued": 0,
        "sent": 1,
        "failed": 0,
    }

    monkeypatch.setattr(alert_tasks, "get_db_session", lambda: _Ctx())
    monkeypatch.setattr(alert_tasks, "NotificationDispatcher", lambda _db: dispatcher)

    result = alert_tasks.send_alert_notifications()

    assert result["opened_alerts"] == 1
    assert alert.status == "OPEN"
    db.commit.assert_called_once()


def test_alert_notification_task_prioritizes_oldest_pending_alerts(monkeypatch):
    """积压处理必须从最老 PENDING 开始，避免旧预警永久饿死。"""
    from app.models.alert import AlertRecord
    from app.utils.scheduled_tasks import alert_tasks

    captured_order_by = []

    class _PendingAlertQuery:
        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *clauses):
            captured_order_by.extend(str(clause) for clause in clauses)
            return self

        def limit(self, _limit):
            return self

        def all(self):
            return []

    class _PendingNotificationQuery(_PendingAlertQuery):
        pass

    db = MagicMock()
    db.query.side_effect = [_PendingAlertQuery(), _PendingNotificationQuery()]

    class _Ctx:
        def __enter__(self):
            return db

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(alert_tasks, "get_db_session", lambda: _Ctx())
    monkeypatch.setattr(alert_tasks, "NotificationDispatcher", lambda _db: MagicMock())

    alert_tasks.send_alert_notifications()

    assert any("triggered_at ASC" in clause for clause in captured_order_by), (
        f"预警积压查询应按最老优先，实际 order_by={captured_order_by}"
    )
