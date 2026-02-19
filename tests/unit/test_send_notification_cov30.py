# -*- coding: utf-8 -*-
"""
Unit tests for SendNotificationMixin (第三十批)
"""
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.approval_engine.notify.send_notification import SendNotificationMixin
from app.services.channel_handlers.base import NotificationPriority


class ConcreteNotifier(SendNotificationMixin):
    """Concrete implementation for testing the mixin"""

    def __init__(self, db):
        self.db = db
        self._notification_dispatcher = None


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def notifier(mock_db):
    return ConcreteNotifier(db=mock_db)


# ---------------------------------------------------------------------------
# _get_dispatcher
# ---------------------------------------------------------------------------

class TestGetDispatcher:
    def test_creates_dispatcher_if_none(self, notifier, mock_db):
        with patch("app.services.approval_engine.notify.send_notification.NotificationDispatcher") as MockDispatcher:
            instance = MagicMock()
            MockDispatcher.return_value = instance

            dispatcher = notifier._get_dispatcher()
            assert dispatcher is instance
            MockDispatcher.assert_called_once_with(mock_db)

    def test_reuses_existing_dispatcher(self, notifier):
        existing = MagicMock()
        notifier._notification_dispatcher = existing

        dispatcher = notifier._get_dispatcher()
        assert dispatcher is existing


# ---------------------------------------------------------------------------
# _map_notification_type
# ---------------------------------------------------------------------------

class TestMapNotificationType:
    @pytest.mark.parametrize("input_type,expected", [
        ("APPROVAL_PENDING", "APPROVAL_PENDING"),
        ("APPROVAL_APPROVED", "APPROVAL_RESULT"),
        ("APPROVAL_REJECTED", "APPROVAL_RESULT"),
        ("APPROVAL_CC", "APPROVAL_CC"),
        ("APPROVAL_TIMEOUT_WARNING", "APPROVAL_PENDING"),
        ("APPROVAL_WITHDRAWN", "APPROVAL_RESULT"),
        ("UNKNOWN_TYPE", "APPROVAL_PENDING"),
    ])
    def test_maps_type_correctly(self, notifier, input_type, expected):
        result = notifier._map_notification_type(input_type)
        assert result == expected


# ---------------------------------------------------------------------------
# _map_urgency_to_priority
# ---------------------------------------------------------------------------

class TestMapUrgencyToPriority:
    def test_maps_urgent(self, notifier):
        result = notifier._map_urgency_to_priority("URGENT")
        assert result == NotificationPriority.URGENT

    def test_maps_high(self, notifier):
        result = notifier._map_urgency_to_priority("HIGH")
        assert result == NotificationPriority.HIGH

    def test_maps_normal(self, notifier):
        result = notifier._map_urgency_to_priority("NORMAL")
        assert result == NotificationPriority.NORMAL

    def test_maps_low(self, notifier):
        result = notifier._map_urgency_to_priority("LOW")
        assert result == NotificationPriority.LOW

    def test_maps_lowercase_input(self, notifier):
        result = notifier._map_urgency_to_priority("urgent")
        assert result == NotificationPriority.URGENT

    def test_maps_unknown_to_normal(self, notifier):
        result = notifier._map_urgency_to_priority("UNKNOWN")
        assert result == NotificationPriority.NORMAL

    def test_handles_none_input(self, notifier):
        result = notifier._map_urgency_to_priority(None)
        assert result == NotificationPriority.NORMAL


# ---------------------------------------------------------------------------
# _send_notification
# ---------------------------------------------------------------------------

class TestSendNotification:
    def test_skips_when_no_receiver_id(self, notifier):
        notification = {"type": "APPROVAL_PENDING", "content": "test"}
        # Should not raise and should not create dispatcher
        notifier._notification_dispatcher = None
        notifier._send_notification(notification)
        # Dispatcher was never set (since we short-circuit on missing receiver_id)
        assert notifier._notification_dispatcher is None

    def test_sends_via_dispatcher_on_success(self, notifier):
        dispatcher = MagicMock()
        dispatcher.send_notification_request.return_value = {
            "success": True,
            "channels_sent": ["SYSTEM"],
        }
        notifier._notification_dispatcher = dispatcher

        notification = {
            "type": "APPROVAL_PENDING",
            "receiver_id": 10,
            "title": "审批待处理",
            "content": "请审批",
            "urgency": "HIGH",
            "instance_id": 100,
        }
        notifier._send_notification(notification)
        dispatcher.send_notification_request.assert_called_once()

    def test_logs_warning_when_send_fails(self, notifier):
        dispatcher = MagicMock()
        dispatcher.send_notification_request.return_value = {
            "success": False,
            "message": "User opted out",
        }
        notifier._notification_dispatcher = dispatcher

        notification = {
            "type": "APPROVAL_REJECTED",
            "receiver_id": 5,
            "urgency": "NORMAL",
        }
        # Should not raise
        notifier._send_notification(notification)
        dispatcher.send_notification_request.assert_called_once()

    def test_handles_dispatcher_exception_gracefully(self, notifier):
        dispatcher = MagicMock()
        dispatcher.send_notification_request.side_effect = Exception("Connection error")
        notifier._notification_dispatcher = dispatcher

        notification = {
            "receiver_id": 1,
            "type": "APPROVAL_PENDING",
        }
        # Should not raise
        notifier._send_notification(notification)
