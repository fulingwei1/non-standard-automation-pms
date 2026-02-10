# -*- coding: utf-8 -*-
"""
Tests for notification_dispatcher service
"""

import pytest
from datetime import datetime
from unittest.mock import patch, Mock
from sqlalchemy.orm import Session

from app.models.alert import AlertNotification, AlertRecord
from app.models.user import User


class TestNotificationDispatcher:
    """Test suite for NotificationDispatcher class."""

    @pytest.fixture
    def db_session(self):
        return Mock(spec=Session)

    @pytest.fixture
    def mock_alert(self):
        alert = Mock(spec=AlertRecord)
        alert.id = 1
        alert.alert_level = "WARNING"
        alert.message = "Test alert"
        return alert

    @pytest.fixture
    def mock_notification(self):
        notification = Mock(spec=AlertNotification)
        notification.id = 1
        notification.notify_channel = "SYSTEM"
        notification.notify_target = "user_1"
        notification.status = "PENDING"
        notification.retry_count = 0
        notification.next_retry_at = None
        return notification

    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        return user

    def test_init_dispatcher(self, db_session):
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_service = Mock()
        with patch(
            "app.services.notification_dispatcher.get_notification_service",
            return_value=mock_service,
        ):
            dispatcher = NotificationDispatcher(db_session)

        assert dispatcher.db == db_session
        assert dispatcher.unified_service == mock_service

    def test_compute_next_retry_schedule(self, db_session):
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_service = Mock()
        with patch(
            "app.services.notification_dispatcher.get_notification_service",
            return_value=mock_service,
        ):
            dispatcher = NotificationDispatcher(db_session)

        result_0 = dispatcher._compute_next_retry(0)
        assert isinstance(result_0, datetime)

    def test_dispatch_system_channel_success(
        self, db_session, mock_notification, mock_alert, mock_user
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_service = Mock()
        mock_service.send_notification.return_value = {"success": True}
        with patch(
            "app.services.notification_dispatcher.get_notification_service",
            return_value=mock_service,
        ):
            dispatcher = NotificationDispatcher(db_session)
        mock_notification.notify_channel = "SYSTEM"

        result = dispatcher.dispatch(mock_notification, mock_alert, mock_user)

        assert result is True
        assert mock_notification.status == "SENT"
        assert mock_service.send_notification.called

    def test_dispatch_email_channel_success(
        self, db_session, mock_notification, mock_alert, mock_user
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_service = Mock()
        mock_service.send_notification.return_value = {"success": True}
        with patch(
            "app.services.notification_dispatcher.get_notification_service",
            return_value=mock_service,
        ):
            dispatcher = NotificationDispatcher(db_session)
        mock_notification.notify_channel = "EMAIL"

        result = dispatcher.dispatch(mock_notification, mock_alert, mock_user)

        assert result is True
        assert mock_notification.status == "SENT"
        assert mock_service.send_notification.called

    def test_dispatch_unsupported_channel(
        self, db_session, mock_notification, mock_alert, mock_user
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_service = Mock()
        mock_service.send_notification.return_value = {"success": True}
        with patch(
            "app.services.notification_dispatcher.get_notification_service",
            return_value=mock_service,
        ):
            dispatcher = NotificationDispatcher(db_session)
        mock_notification.notify_channel = "UNSUPPORTED"

        result = dispatcher.dispatch(mock_notification, mock_alert, mock_user)

        assert result is True
        assert mock_notification.status == "SENT"
        assert mock_service.send_notification.called

    def test_dispatch_with_exception(
        self, db_session, mock_notification, mock_alert, mock_user
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        mock_service = Mock()
        mock_service.send_notification.side_effect = Exception("Test error")
        with patch(
            "app.services.notification_dispatcher.get_notification_service",
            return_value=mock_service,
        ):
            dispatcher = NotificationDispatcher(db_session)
        mock_notification.notify_channel = "EMAIL"

        result = dispatcher.dispatch(mock_notification, mock_alert, mock_user)

        assert result is False
        assert mock_notification.status == "FAILED"
        assert mock_notification.retry_count == 1
