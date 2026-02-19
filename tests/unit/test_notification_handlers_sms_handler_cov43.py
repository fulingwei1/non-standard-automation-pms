# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/notification_handlers/sms_handler.py
"""
import pytest

pytest.importorskip("app.services.notification_handlers.sms_handler")

from unittest.mock import MagicMock, patch
from app.services.notification_handlers.sms_handler import SMSNotificationHandler
from app.models.enums import AlertLevelEnum


def make_handler():
    db = MagicMock()
    return SMSNotificationHandler(db=db)


def make_alert(level=AlertLevelEnum.URGENT.value):
    alert = MagicMock()
    alert.alert_level = level
    alert.alert_title = "测试预警标题"
    alert.id = 1
    return alert


def make_notification(target="13812345678", user_id=5):
    notif = MagicMock()
    notif.notify_target = target
    notif.notify_user_id = user_id
    notif.notify_title = "通知标题"
    return notif


# ── 1. 非 URGENT 级别时抛出 ValueError ──────────────────────────────────────
def test_send_non_urgent_raises():
    h = make_handler()
    alert = make_alert(level="INFO")
    with pytest.raises(ValueError, match="URGENT"):
        h.send(make_notification(), alert)


# ── 2. SMS 未启用时抛出 ValueError ──────────────────────────────────────────
def test_send_sms_disabled():
    h = make_handler()
    alert = make_alert()
    with patch("app.services.notification_handlers.sms_handler.settings") as s:
        s.SMS_ENABLED = False
        with pytest.raises(ValueError, match="disabled"):
            h.send(make_notification(), alert)


# ── 3. 无接收方时抛出 ValueError ────────────────────────────────────────────
def test_send_no_recipient():
    h = make_handler()
    alert = make_alert()
    notif = MagicMock()
    notif.notify_target = None
    notif.notify_user_id = None
    notif.notify_title = "test"

    with patch("app.services.notification_handlers.sms_handler.settings") as s:
        s.SMS_ENABLED = True
        s.SMS_MAX_PER_DAY = 100
        s.SMS_MAX_PER_HOUR = 20
        user = MagicMock()
        user.phone = None
        with pytest.raises(ValueError, match="phone"):
            h.send(notif, alert, user=user)


# ── 4. 超过日限额时抛出 ValueError ──────────────────────────────────────────
def test_send_daily_limit_exceeded():
    h = make_handler()
    alert = make_alert()
    notif = make_notification()

    import datetime
    today = datetime.date.today().isoformat()
    h._sms_count["today"][today] = 10

    with patch("app.services.notification_handlers.sms_handler.settings") as s:
        s.SMS_ENABLED = True
        s.SMS_MAX_PER_DAY = 10
        s.SMS_MAX_PER_HOUR = 20
        with pytest.raises(ValueError, match="daily limit"):
            h.send(notif, alert)


# ── 5. 超过小时限额时抛出 ValueError ────────────────────────────────────────
def test_send_hourly_limit_exceeded():
    h = make_handler()
    alert = make_alert()
    notif = make_notification()

    import datetime
    hour_key = datetime.datetime.now().strftime("%Y-%m-%d-%H")
    h._sms_count["hour"][hour_key] = 5

    with patch("app.services.notification_handlers.sms_handler.settings") as s:
        s.SMS_ENABLED = True
        s.SMS_MAX_PER_DAY = 100
        s.SMS_MAX_PER_HOUR = 5
        with pytest.raises(ValueError, match="hourly limit"):
            h.send(notif, alert)


# ── 6. 发送成功时计数增加 ───────────────────────────────────────────────────
def test_send_success_increments_count():
    h = make_handler()
    alert = make_alert()
    notif = make_notification(target="13911112222")

    with patch("app.services.notification_handlers.sms_handler.settings") as s, \
         patch("app.services.notification_handlers.sms_handler.send_alert_via_unified") as mock_send:
        s.SMS_ENABLED = True
        s.SMS_MAX_PER_DAY = 100
        s.SMS_MAX_PER_HOUR = 20
        s.CORS_ORIGINS = ["http://localhost:3000"]

        import datetime
        today = datetime.date.today().isoformat()
        h.send(notif, alert)
        assert h._sms_count["today"][today] == 1
        mock_send.assert_called_once()


# ── 7. _send_aliyun: SDK 未安装时抛出 ValueError ────────────────────────────
def test_send_aliyun_no_sdk():
    h = make_handler()
    import builtins
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name.startswith("aliyunsdkcore"):
            raise ImportError("no aliyun sdk")
        return original_import(name, *args, **kwargs)

    import builtins
    with patch("builtins.__import__", side_effect=mock_import):
        with pytest.raises(ValueError, match="SDK not installed"):
            h._send_aliyun("13800000000", "test message")


# ── 8. _send_tencent 总是抛出 ValueError ────────────────────────────────────
def test_send_tencent_not_implemented():
    h = make_handler()
    with pytest.raises(ValueError, match="not implemented"):
        h._send_tencent("13900000000", "content")
