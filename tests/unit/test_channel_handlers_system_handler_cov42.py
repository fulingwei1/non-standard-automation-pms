# -*- coding: utf-8 -*-
"""第四十二批：channel_handlers/system_handler.py 单元测试"""
import pytest

pytest.importorskip("app.services.channel_handlers.system_handler")

from unittest.mock import MagicMock, patch
from app.services.channel_handlers.system_handler import SystemChannelHandler
from app.services.channel_handlers.base import NotificationRequest


def make_request(**kw):
    defaults = dict(
        recipient_id=10, notification_type="TASK_UPDATE", category="task",
        title="任务更新", content="您的任务已更新",
        source_type="task", source_id=42, link_url="/tasks/42",
        extra_data={"key": "val"},
    )
    defaults.update(kw)
    return NotificationRequest(**defaults)


def make_handler():
    db = MagicMock()
    return SystemChannelHandler(db, "system"), db


# ------------------------------------------------------------------ tests ---

def test_handler_channel_is_system():
    h, _ = make_handler()
    assert h.channel == "system"


def test_send_calls_save_obj():
    h, db = make_handler()
    with patch("app.services.channel_handlers.system_handler.save_obj") as mock_save:
        with patch("app.services.channel_handlers.system_handler.Notification") as MockNotif:
            mock_notif_instance = MagicMock()
            MockNotif.return_value = mock_notif_instance
            result = h.send(make_request())
        mock_save.assert_called_once()


def test_send_returns_success():
    h, db = make_handler()
    with patch("app.services.channel_handlers.system_handler.save_obj"):
        with patch("app.services.channel_handlers.system_handler.Notification") as MockNotif:
            MockNotif.return_value = MagicMock()
            result = h.send(make_request())
    assert result.success is True
    assert result.channel == "system"


def test_send_sets_sent_at():
    h, db = make_handler()
    with patch("app.services.channel_handlers.system_handler.save_obj"):
        with patch("app.services.channel_handlers.system_handler.Notification") as MockNotif:
            MockNotif.return_value = MagicMock()
            result = h.send(make_request())
    assert result.sent_at is not None


def test_notification_built_with_request_fields():
    h, db = make_handler()
    req = make_request()
    with patch("app.services.channel_handlers.system_handler.save_obj"):
        with patch("app.services.channel_handlers.system_handler.Notification") as MockNotif:
            MockNotif.return_value = MagicMock()
            h.send(req)
        call_kwargs = MockNotif.call_args[1]
        assert call_kwargs["user_id"] == req.recipient_id
        assert call_kwargs["title"] == req.title
        assert call_kwargs["content"] == req.content


def test_extra_data_defaults_to_empty_dict():
    h, db = make_handler()
    req = make_request(extra_data=None)
    with patch("app.services.channel_handlers.system_handler.save_obj"):
        with patch("app.services.channel_handlers.system_handler.Notification") as MockNotif:
            MockNotif.return_value = MagicMock()
            h.send(req)
        call_kwargs = MockNotif.call_args[1]
        assert call_kwargs["extra_data"] == {}
