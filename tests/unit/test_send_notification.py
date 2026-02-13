# -*- coding: utf-8 -*-
"""Tests for approval_engine/notify/send_notification.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestSendNotificationMixin:
    def _make_instance(self):
        from app.services.approval_engine.notify.send_notification import SendNotificationMixin
        obj = SendNotificationMixin()
        obj.db = MagicMock()
        return obj

    def test_map_notification_type(self):
        obj = self._make_instance()
        assert obj._map_notification_type("APPROVAL_PENDING") == "APPROVAL_PENDING"
        assert obj._map_notification_type("APPROVAL_APPROVED") == "APPROVAL_RESULT"
        assert obj._map_notification_type("UNKNOWN") == "APPROVAL_PENDING"

    def test_map_urgency_to_priority(self):
        from app.services.channel_handlers.base import NotificationPriority
        obj = self._make_instance()
        assert obj._map_urgency_to_priority("URGENT") == NotificationPriority.URGENT
        assert obj._map_urgency_to_priority("HIGH") == NotificationPriority.HIGH
        assert obj._map_urgency_to_priority(None) == NotificationPriority.NORMAL

    @patch('app.services.approval_engine.notify.send_notification.NotificationDispatcher')
    def test_send_notification_success(self, mock_dispatcher_cls):
        obj = self._make_instance()
        mock_dispatcher = MagicMock()
        mock_dispatcher.send_notification_request.return_value = {"success": True, "channels_sent": ["IN_APP"]}
        mock_dispatcher_cls.return_value = mock_dispatcher
        obj._send_notification({"receiver_id": 1, "type": "APPROVAL_PENDING", "title": "Test", "content": "", "instance_id": 10})
        mock_dispatcher.send_notification_request.assert_called_once()

    def test_send_notification_no_receiver(self):
        obj = self._make_instance()
        obj._send_notification({"type": "APPROVAL_PENDING"})
        # Should just log warning, no exception
