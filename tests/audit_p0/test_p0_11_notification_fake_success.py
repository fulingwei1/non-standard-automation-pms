# -*- coding: utf-8 -*-
"""
P0-11: 通知触达假成功 + 预警积压饿死。

channels/email_handler.py:52-55 与 sms_handler.py:29-31 在无任何真实发送实现（无
smtplib / 无短信网关）的情况下，只 logger.info 就返回 success=True。

正确行为：未配置真实发送通道时，send() 必须返回 success=False（不能谎报已送达）。
附带：SELECT count(*) FROM alert_records WHERE status='PENDING' 佐证约 841 条积压。
"""
from unittest.mock import MagicMock

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
