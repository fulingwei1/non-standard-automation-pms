# -*- coding: utf-8 -*-
"""Tests for notification_handlers/unified_adapter.py"""
import pytest
from unittest.mock import MagicMock, patch


class TestMapAlertLevelToPriority:
    def test_none(self):
        from app.services.notification_handlers.unified_adapter import map_alert_level_to_priority
        from app.services.channel_handlers.base import NotificationPriority
        assert map_alert_level_to_priority(None) == NotificationPriority.NORMAL

    def test_urgent(self):
        from app.services.notification_handlers.unified_adapter import map_alert_level_to_priority
        from app.services.channel_handlers.base import NotificationPriority
        assert map_alert_level_to_priority("URGENT") == NotificationPriority.URGENT

    def test_warning(self):
        from app.services.notification_handlers.unified_adapter import map_alert_level_to_priority
        from app.services.channel_handlers.base import NotificationPriority
        assert map_alert_level_to_priority("WARNING") == NotificationPriority.HIGH

    def test_unknown(self):
        from app.services.notification_handlers.unified_adapter import map_alert_level_to_priority
        from app.services.channel_handlers.base import NotificationPriority
        assert map_alert_level_to_priority("RANDOM") == NotificationPriority.NORMAL


class TestResolveRecipientId:
    def test_from_notification(self):
        from app.services.notification_handlers.unified_adapter import resolve_recipient_id
        db = MagicMock()
        notification = MagicMock(notify_user_id=42)
        assert resolve_recipient_id(db, notification, None) == 42

    def test_from_user(self):
        from app.services.notification_handlers.unified_adapter import resolve_recipient_id
        db = MagicMock()
        notification = MagicMock(spec=[])
        user = MagicMock(id=10)
        assert resolve_recipient_id(db, notification, user) == 10

    def test_none(self):
        from app.services.notification_handlers.unified_adapter import resolve_recipient_id
        db = MagicMock()
        notification = MagicMock(spec=[])
        assert resolve_recipient_id(db, notification, None) is None


class TestSendAlertViaUnified:
    def test_success(self):
        from app.services.notification_handlers.unified_adapter import send_alert_via_unified
        db = MagicMock()
        notification = MagicMock(notify_user_id=1, notify_title="Alert", notify_content="Content")
        alert = MagicMock(id=5, alert_level="HIGH", alert_no="A001", alert_title=None, alert_content=None, target_type="project", target_name="P1")
        with patch('app.services.unified_notification_service.get_notification_service') as mock_get_svc:
            mock_svc = MagicMock()
            mock_svc.send_notification.return_value = {"success": True}
            mock_get_svc.return_value = mock_svc
            result = send_alert_via_unified(db, notification, alert, None, "IN_APP")
            assert result['success'] is True

    def test_no_recipient_raises(self):
        from app.services.notification_handlers.unified_adapter import send_alert_via_unified
        db = MagicMock()
        notification = MagicMock(spec=[])
        alert = MagicMock()
        with pytest.raises(ValueError):
            send_alert_via_unified(db, notification, alert, None, "IN_APP")
