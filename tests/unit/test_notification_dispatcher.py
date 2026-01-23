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

        dispatcher = NotificationDispatcher(db_session)

        assert dispatcher.db == db_session

    def test_compute_next_retry_schedule(self, db_session):
        from app.services.notification_dispatcher import NotificationDispatcher

        dispatcher = NotificationDispatcher(db_session)

        result_0 = dispatcher._compute_next_retry(0)
        assert isinstance(result_0, datetime)

    def test_dispatch_system_channel_success(
        self, db_session, mock_notification, mock_alert, mock_user
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        dispatcher = NotificationDispatcher(db_session)
        mock_notification.notify_channel = "SYSTEM"

        result = dispatcher.dispatch(mock_notification, mock_alert, mock_user)

        assert result is True

    def test_dispatch_email_channel_success(
        self, db_session, mock_notification, mock_alert, mock_user
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        dispatcher = NotificationDispatcher(db_session)
        mock_notification.notify_channel = "EMAIL"

        result = dispatcher.dispatch(mock_notification, mock_alert, mock_user)

        assert result is True

    def test_dispatch_unsupported_channel(
        self, db_session, mock_notification, mock_alert, mock_user
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        dispatcher = NotificationDispatcher(db_session)
        mock_notification.notify_channel = "UNSUPPORTED"

        result = dispatcher.dispatch(mock_notification, mock_alert, mock_user)

        assert result is False
        assert mock_notification.status == "FAILED"
        assert mock_notification.error_message is not None

    def test_dispatch_with_exception(
        self, db_session, mock_notification, mock_alert, mock_user
    ):
        from app.services.notification_dispatcher import NotificationDispatcher

        dispatcher = NotificationDispatcher(db_session)
        mock_notification.notify_channel = "EMAIL"

        with patch.object(
            dispatcher.email_handler, "send", side_effect=Exception("Test error")
        ):
            result = dispatcher.dispatch(mock_notification, mock_alert, mock_user)

        assert result is False
        assert mock_notification.status == "FAILED"
        assert mock_notification.retry_count == 1
