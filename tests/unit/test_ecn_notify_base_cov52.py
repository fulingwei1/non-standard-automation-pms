# -*- coding: utf-8 -*-
"""
Unit tests for app/services/ecn_notification/base.py (cov52)
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.ecn_notification.base import (
        _map_priority_to_unified,
        create_ecn_notification,
    )
    from app.services.channel_handlers.base import NotificationPriority
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ──────────────────────── _map_priority_to_unified ────────────────────────

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
    """未知优先级默认返回 NORMAL"""
    result = _map_priority_to_unified("UNKNOWN_LEVEL")
    assert result == NotificationPriority.NORMAL


def test_map_priority_none_defaults_to_normal():
    """None 优先级默认返回 NORMAL"""
    result = _map_priority_to_unified(None)
    assert result == NotificationPriority.NORMAL


# ──────────────────────── create_ecn_notification ────────────────────────

@patch("app.services.ecn_notification.base.NotificationDispatcher")
def test_create_ecn_notification_success(mock_dispatcher_cls):
    """正常创建通知，dispatcher 被调用一次"""
    db = MagicMock()
    mock_dispatcher = MagicMock()
    mock_dispatcher.send_notification_request.return_value = {"success": True, "notification_id": 1}
    mock_dispatcher_cls.return_value = mock_dispatcher

    result = create_ecn_notification(
        db=db,
        user_id=1,
        notification_type="ECN_CREATED",
        title="ECN通知",
        content="内容",
        ecn_id=10,
    )

    mock_dispatcher_cls.assert_called_once_with(db)
    mock_dispatcher.send_notification_request.assert_called_once()
    assert result.get("success") is True


@patch("app.services.ecn_notification.base.NotificationDispatcher")
def test_create_ecn_notification_with_extra_data(mock_dispatcher_cls):
    """传入 extra_data 时，request 中应包含该数据"""
    db = MagicMock()
    mock_dispatcher = MagicMock()
    mock_dispatcher.send_notification_request.return_value = {"success": True}
    mock_dispatcher_cls.return_value = mock_dispatcher

    extra = {"key": "value"}
    create_ecn_notification(
        db=db,
        user_id=2,
        notification_type="ECN_APPROVED",
        title="审批通知",
        content="ECN已审批",
        ecn_id=5,
        priority="HIGH",
        extra_data=extra,
    )

    call_args = mock_dispatcher.send_notification_request.call_args
    request_obj = call_args[0][0]
    assert request_obj.extra_data == extra


@patch("app.services.ecn_notification.base.NotificationDispatcher")
def test_create_ecn_notification_link_url(mock_dispatcher_cls):
    """link_url 应包含 ecn_id"""
    db = MagicMock()
    mock_dispatcher = MagicMock()
    mock_dispatcher.send_notification_request.return_value = {"success": True}
    mock_dispatcher_cls.return_value = mock_dispatcher

    create_ecn_notification(
        db=db,
        user_id=3,
        notification_type="ECN_UPDATED",
        title="更新通知",
        content="ECN已更新",
        ecn_id=42,
    )

    call_args = mock_dispatcher.send_notification_request.call_args
    request_obj = call_args[0][0]
    assert "42" in request_obj.link_url
