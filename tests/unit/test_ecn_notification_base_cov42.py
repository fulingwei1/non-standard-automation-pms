# -*- coding: utf-8 -*-
"""第四十二批：ecn_notification/base.py 单元测试"""
import pytest

pytest.importorskip("app.services.ecn_notification.base")

from unittest.mock import MagicMock, patch
from app.services.ecn_notification.base import (
    create_ecn_notification,
    _map_priority_to_unified,
)
from app.services.channel_handlers.base import NotificationPriority


# ------------------------------------------------------------------ tests ---

def test_map_priority_urgent():
    result = _map_priority_to_unified("URGENT")
    assert result == NotificationPriority.URGENT


def test_map_priority_high():
    result = _map_priority_to_unified("HIGH")
    assert result == NotificationPriority.HIGH


def test_map_priority_normal():
    result = _map_priority_to_unified("NORMAL")
    assert result == NotificationPriority.NORMAL


def test_map_priority_low():
    result = _map_priority_to_unified("LOW")
    assert result == NotificationPriority.LOW


def test_map_priority_unknown_defaults_to_normal():
    result = _map_priority_to_unified("SUPER_HIGH")
    assert result == NotificationPriority.NORMAL


def test_map_priority_none_defaults_to_normal():
    result = _map_priority_to_unified(None)
    assert result == NotificationPriority.NORMAL


def test_create_ecn_notification_calls_dispatcher():
    db = MagicMock()
    with patch("app.services.ecn_notification.base.NotificationDispatcher") as MockDisp:
        mock_disp = MagicMock()
        mock_disp.send_notification_request.return_value = {"success": True}
        MockDisp.return_value = mock_disp
        result = create_ecn_notification(
            db=db,
            user_id=1,
            notification_type="ECN_CREATED",
            title="ECN通知",
            content="ECN已创建",
            ecn_id=42,
            priority="HIGH",
        )
    mock_disp.send_notification_request.assert_called_once()
    assert result["success"] is True


def test_create_ecn_notification_extra_data():
    db = MagicMock()
    with patch("app.services.ecn_notification.base.NotificationDispatcher") as MockDisp:
        mock_disp = MagicMock()
        mock_disp.send_notification_request.return_value = {"success": True}
        MockDisp.return_value = mock_disp
        create_ecn_notification(
            db=db, user_id=2, notification_type="ECN_UPDATED",
            title="标题", content="内容", ecn_id=10,
            extra_data={"field": "value"},
        )
    request = mock_disp.send_notification_request.call_args[0][0]
    assert request.extra_data.get("field") == "value"


def test_create_ecn_notification_link_url_contains_ecn_id():
    db = MagicMock()
    with patch("app.services.ecn_notification.base.NotificationDispatcher") as MockDisp:
        mock_disp = MagicMock()
        mock_disp.send_notification_request.return_value = {}
        MockDisp.return_value = mock_disp
        create_ecn_notification(
            db=db, user_id=1, notification_type="T",
            title="T", content="C", ecn_id=99,
        )
    request = mock_disp.send_notification_request.call_args[0][0]
    assert "99" in request.link_url
