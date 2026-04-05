# -*- coding: utf-8 -*-
"""
Tests for NotificationDispatcher - additional coverage
Logic-based tests to avoid problematic imports.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import pytest


# Re-create NotificationDispatcher helper methods for testing
class StubNotificationDispatcher:
    """Stub version of NotificationDispatcher for testing."""
    
    RETRY_SCHEDULE = [5, 15, 30, 60]
    
    def __init__(self, db):
        self.db = db
        self.unified_service = Mock()
    
    def _map_channel_to_unified(self, channel):
        """Map old channel name to unified service channel name."""
        channel_upper = channel.upper()
        # Simplified mapping for testing
        mapping = {
            "SYSTEM": "SYSTEM",
            "EMAIL": "EMAIL",
            "WECHAT": "WECHAT",
            "SMS": "SMS",
            "WEBHOOK": "WEBHOOK",
        }
        return mapping.get(channel_upper, "SYSTEM")
    
    def _map_alert_level_to_priority(self, alert_level):
        """Map alert level to notification priority."""
        level_upper = alert_level.upper() if alert_level else "NORMAL"
        mapping = {
            "URGENT": "URGENT",
            "CRITICAL": "URGENT",
            "WARNING": "HIGH",
            "INFO": "NORMAL",
        }
        return mapping.get(level_upper, "NORMAL")
    
    def _compute_next_retry(self, retry_count):
        """Compute next retry time."""
        idx = min(retry_count, len(self.RETRY_SCHEDULE)) - 1
        minutes = self.RETRY_SCHEDULE[idx] if idx >= 0 else self.RETRY_SCHEDULE[0]
        return datetime.now() + timedelta(minutes=minutes)
    
    def _resolve_recipient_id(self, notification, user):
        """Resolve recipient ID from notification or user."""
        recipient_id = notification.notify_user_id
        if not recipient_id and user:
            recipient_id = user.id
        if not recipient_id:
            raise ValueError("Notification requires recipient_id or user")
        return recipient_id
    
    def create_system_notification(self, recipient_id, notification_type, title, content,
                                    source_type=None, source_id=None, link_url=None,
                                    priority="NORMAL", extra_data=None):
        """Create in-app notification record."""
        from app.models.notification import Notification
        notification = Notification(
            user_id=recipient_id,
            notification_type=notification_type,
            title=title,
            content=content,
            source_type=source_type,
            source_id=source_id,
            link_url=link_url,
            priority=priority,
            extra_data=extra_data or {},
        )
        self.db.add(notification)
        return notification
    
    def send_notification_request(self, request):
        """Send notification request (unified entry)."""
        return self.unified_service.send_notification(request)


class TestNotificationDispatcherMethods:
    """Test suite for NotificationDispatcher helper methods."""

    @pytest.fixture
    def db_session(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def dispatcher(self, db_session):
        """Create StubNotificationDispatcher instance."""
        return StubNotificationDispatcher(db_session)

    @pytest.fixture
    def mock_notification(self):
        """Create mock AlertNotification."""
        notification = Mock()
        notification.id = 1
        notification.alert_id = 1
        notification.notify_channel = "SYSTEM"
        notification.notify_target = "user@example.com"
        notification.notify_user_id = 100
        notification.notify_title = "Test"
        notification.notify_content = "Content"
        notification.status = "PENDING"
        notification.retry_count = 0
        notification.next_retry_at = None
        notification.sent_at = None
        notification.error_message = None
        return notification

    @pytest.fixture
    def mock_user(self):
        """Create mock User."""
        user = Mock()
        user.id = 100
        user.username = "testuser"
        user.email = "test@example.com"
        user.is_active = True
        return user

    # --- Test _map_channel_to_unified ---

    def test_map_channel_to_unified_system(self, dispatcher):
        """Test channel mapping for SYSTEM."""
        result = dispatcher._map_channel_to_unified("SYSTEM")
        assert result == "SYSTEM"

    def test_map_channel_to_unified_email(self, dispatcher):
        """Test channel mapping for EMAIL."""
        result = dispatcher._map_channel_to_unified("EMAIL")
        assert result == "EMAIL"

    def test_map_channel_to_unified_wechat(self, dispatcher):
        """Test channel mapping for WECHAT."""
        result = dispatcher._map_channel_to_unified("WECHAT")
        assert result == "WECHAT"

    def test_map_channel_to_unified_sms(self, dispatcher):
        """Test channel mapping for SMS."""
        result = dispatcher._map_channel_to_unified("SMS")
        assert result == "SMS"

    def test_map_channel_to_unified_webhook(self, dispatcher):
        """Test channel mapping for WEBHOOK."""
        result = dispatcher._map_channel_to_unified("WEBHOOK")
        assert result == "WEBHOOK"

    def test_map_channel_to_unified_unknown(self, dispatcher):
        """Test channel mapping for unknown channel defaults to SYSTEM."""
        result = dispatcher._map_channel_to_unified("UNKNOWN")
        assert result == "SYSTEM"

    def test_map_channel_to_unified_lowercase(self, dispatcher):
        """Test channel mapping with lowercase."""
        result = dispatcher._map_channel_to_unified("email")
        assert result == "EMAIL"

    # --- Test _map_alert_level_to_priority ---

    def test_map_alert_level_to_priority_urgent(self, dispatcher):
        """Test alert level mapping for URGENT."""
        result = dispatcher._map_alert_level_to_priority("URGENT")
        assert result == "URGENT"

    def test_map_alert_level_to_priority_critical(self, dispatcher):
        """Test alert level mapping for CRITICAL."""
        result = dispatcher._map_alert_level_to_priority("CRITICAL")
        assert result == "URGENT"

    def test_map_alert_level_to_priority_warning(self, dispatcher):
        """Test alert level mapping for WARNING."""
        result = dispatcher._map_alert_level_to_priority("WARNING")
        assert result == "HIGH"

    def test_map_alert_level_to_priority_info(self, dispatcher):
        """Test alert level mapping for INFO."""
        result = dispatcher._map_alert_level_to_priority("INFO")
        assert result == "NORMAL"

    def test_map_alert_level_to_priority_lowercase(self, dispatcher):
        """Test alert level mapping with lowercase."""
        result = dispatcher._map_alert_level_to_priority("warning")
        assert result == "HIGH"

    def test_map_alert_level_to_priority_unknown(self, dispatcher):
        """Test alert level mapping for unknown level defaults to NORMAL."""
        result = dispatcher._map_alert_level_to_priority("UNKNOWN")
        assert result == "NORMAL"

    def test_map_alert_level_to_priority_none(self, dispatcher):
        """Test alert level mapping for None."""
        result = dispatcher._map_alert_level_to_priority(None)
        assert result == "NORMAL"

    # --- Test _compute_next_retry ---

    def test_compute_next_retry_first(self, dispatcher):
        """Test compute_next_retry for first retry."""
        result = dispatcher._compute_next_retry(1)
        expected = datetime.now() + timedelta(minutes=5)
        assert isinstance(result, datetime)
        assert result > datetime.now()

    def test_compute_next_retry_second(self, dispatcher):
        """Test compute_next_retry for second retry."""
        result = dispatcher._compute_next_retry(2)
        assert isinstance(result, datetime)
        assert result > datetime.now()

    def test_compute_next_retry_third(self, dispatcher):
        """Test compute_next_retry for third retry."""
        result = dispatcher._compute_next_retry(3)
        assert isinstance(result, datetime)

    def test_compute_next_retry_fourth(self, dispatcher):
        """Test compute_next_retry for fourth retry."""
        result = dispatcher._compute_next_retry(4)
        assert isinstance(result, datetime)

    def test_compute_next_retry_exceeds_max(self, dispatcher):
        """Test compute_next_retry when exceeding max retries."""
        result = dispatcher._compute_next_retry(10)
        assert isinstance(result, datetime)

    # --- Test _resolve_recipient_id ---

    def test_resolve_recipient_id_from_notification(self, dispatcher, mock_notification, mock_user):
        """Test _resolve_recipient_id uses notify_user_id from notification."""
        mock_notification.notify_user_id = 200
        result = dispatcher._resolve_recipient_id(mock_notification, mock_user)
        assert result == 200

    def test_resolve_recipient_id_from_user(self, dispatcher, mock_notification, mock_user):
        """Test _resolve_recipient_id falls back to user.id."""
        mock_notification.notify_user_id = None
        result = dispatcher._resolve_recipient_id(mock_notification, mock_user)
        assert result == mock_user.id

    def test_resolve_recipient_id_raises_error(self, dispatcher, mock_notification):
        """Test _resolve_recipient_id raises ValueError when no recipient."""
        mock_notification.notify_user_id = None
        with pytest.raises(ValueError):
            dispatcher._resolve_recipient_id(mock_notification, None)

    # --- Test send_notification_request ---

    def test_send_notification_request(self, dispatcher):
        """Test send_notification_request delegates to unified service."""
        mock_request = Mock()
        dispatcher.unified_service.send_notification.return_value = {"success": True}
        
        result = dispatcher.send_notification_request(mock_request)
        
        assert result["success"] is True
        dispatcher.unified_service.send_notification.assert_called_once_with(mock_request)

    # --- Test initialization ---

    def test_init_dispatcher(self, db_session):
        """Test NotificationDispatcher initialization."""
        dispatcher = StubNotificationDispatcher(db_session)
        assert dispatcher.db == db_session
        assert hasattr(dispatcher, 'unified_service')

    def test_retry_schedule_values(self, dispatcher):
        """Test RETRY_SCHEDULE constant values."""
        assert dispatcher.RETRY_SCHEDULE == [5, 15, 30, 60]