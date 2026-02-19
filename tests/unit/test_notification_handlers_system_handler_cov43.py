# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/notification_handlers/system_handler.py
"""
import pytest

pytest.importorskip("app.services.notification_handlers.system_handler")

from unittest.mock import MagicMock, patch
from app.services.notification_handlers.system_handler import SystemNotificationHandler


def make_handler():
    db = MagicMock()
    return SystemNotificationHandler(db=db)


def make_objects(user_id=10, has_existing=False):
    notification = MagicMock()
    notification.notify_user_id = user_id

    alert = MagicMock()
    alert.id = 1

    user = MagicMock()
    user.id = user_id

    existing = MagicMock() if has_existing else None

    return notification, alert, user, existing


# ── 1. 缺少 notify_user_id 时抛出 ValueError ────────────────────────────────
def test_send_no_user_id():
    h = make_handler()
    notification = MagicMock()
    notification.notify_user_id = None
    alert = MagicMock()

    with pytest.raises(ValueError, match="notify_user_id"):
        h.send(notification, alert)


# ── 2. 已有相同通知时直接返回（不重复创建） ──────────────────────────────────
def test_send_duplicate_notification_returns_early():
    h = make_handler()
    notification, alert, user, _ = make_objects()
    h.db.query.return_value.filter.return_value.first.return_value = MagicMock()

    with patch("app.services.notification_handlers.system_handler.send_alert_via_unified") as mock_send:
        h.send(notification, alert, user=user)
        mock_send.assert_not_called()


# ── 3. 无重复时调用 send_alert_via_unified ──────────────────────────────────
def test_send_calls_unified_adapter():
    h = make_handler()
    notification, alert, user, _ = make_objects()
    h.db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.notification_handlers.system_handler.send_alert_via_unified") as mock_send:
        h.send(notification, alert, user=user)
        mock_send.assert_called_once()


# ── 4. user 参数可为 None ─────────────────────────────────────────────────
def test_send_user_none():
    h = make_handler()
    notification = MagicMock()
    notification.notify_user_id = 5
    alert = MagicMock()
    alert.id = 2
    h.db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.services.notification_handlers.system_handler.send_alert_via_unified") as mock_send:
        h.send(notification, alert, user=None)
        mock_send.assert_called_once()


# ── 5. 父引用（parent）存储正确 ───────────────────────────────────────────
def test_handler_stores_parent():
    db = MagicMock()
    parent = MagicMock()
    h = SystemNotificationHandler(db=db, parent=parent)
    assert h._parent is parent
    assert h.db is db


# ── 6. 构造函数：parent 默认为 None ─────────────────────────────────────────
def test_handler_default_parent():
    db = MagicMock()
    h = SystemNotificationHandler(db=db)
    assert h._parent is None
