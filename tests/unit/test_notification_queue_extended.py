# -*- coding: utf-8 -*-
"""
Tests for notification_queue - Redis notification queue
Additional coverage for edge cases.
"""

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

import pytest
import json


class TestNotificationQueue:
    """Test suite for notification_queue module."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            client = Mock()
            mock.return_value = client
            yield client

    # --- Test enqueue_notification ---

    def test_enqueue_notification_success(self, mock_redis_client):
        """Test enqueue_notification successful write."""
        from app.services.notification.notification_queue import enqueue_notification
        
        payload = {
            "notification_id": 123,
            "alert_id": 456,
            "notify_channel": "EMAIL"
        }
        
        result = enqueue_notification(payload)
        
        assert result is True
        mock_redis_client.rpush.assert_called_once()
        call_args = mock_redis_client.rpush.call_args
        assert "notification:dispatch:queue" in str(call_args)

    def test_enqueue_notification_adds_timestamp(self, mock_redis_client):
        """Test enqueue_notification adds enqueue_at timestamp."""
        from app.services.notification.notification_queue import enqueue_notification
        
        payload = {"notification_id": 1}
        enqueue_notification(payload)
        
        # Check that rpush was called with JSON containing enqueue_at
        call_args = mock_redis_client.rpush.call_args[0]
        pushed_data = json.loads(call_args[1])
        assert "enqueue_at" in pushed_data

    def test_enqueue_notification_redis_not_configured(self):
        """Test enqueue_notification when Redis is not configured."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = None
            from app.services.notification.notification_queue import enqueue_notification
            
            result = enqueue_notification({"notification_id": 1})
            
            assert result is False

    def test_enqueue_notification_handles_exception(self, mock_redis_client):
        """Test enqueue_notification handles exception."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = mock_redis_client
            mock_redis_client.rpush.side_effect = Exception("Redis error")
            
            from app.services.notification.notification_queue import enqueue_notification
            
            result = enqueue_notification({"notification_id": 1})
            
            assert result is False

    def test_enqueue_notification_with_complex_payload(self, mock_redis_client):
        """Test enqueue_notification with complex payload."""
        from app.services.notification.notification_queue import enqueue_notification
        
        payload = {
            "notification_id": 123,
            "alert_id": 456,
            "notify_channel": "EMAIL",
            "request": {
                "recipient_id": 100,
                "title": "Test",
                "content": "Content",
                "priority": "HIGH",
                "channels": ["EMAIL"],
                "extra_data": {
                    "alert_no": "ALERT-001",
                    "alert_level": "WARNING"
                }
            }
        }
        
        result = enqueue_notification(payload)
        
        assert result is True

    # --- Test dequeue_notification ---

    def test_dequeue_notification_blocking_success(self, mock_redis_client):
        """Test dequeue_notification with blocking mode."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = mock_redis_client
            mock_redis_client.blpop.return_value = (
                "notification:dispatch:queue",
                json.dumps({"notification_id": 123, "alert_id": 456})
            )
            
            from app.services.notification.notification_queue import dequeue_notification
            
            result = dequeue_notification(block=True, timeout=5)
            
            assert result is not None
            assert result["notification_id"] == 123
            assert result["alert_id"] == 456

    def test_dequeue_notification_non_blocking_success(self, mock_redis_client):
        """Test dequeue_notification with non-blocking mode."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = mock_redis_client
            mock_redis_client.lpop.return_value = json.dumps({"notification_id": 123})
            
            from app.services.notification.notification_queue import dequeue_notification
            
            result = dequeue_notification(block=False)
            
            assert result is not None
            assert result["notification_id"] == 123

    def test_dequeue_notification_empty_queue_blocking(self, mock_redis_client):
        """Test dequeue_notification returns None when queue is empty (blocking)."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = mock_redis_client
            mock_redis_client.blpop.return_value = None
            
            from app.services.notification.notification_queue import dequeue_notification
            
            result = dequeue_notification(block=True, timeout=5)
            
            assert result is None

    def test_dequeue_notification_empty_queue_non_blocking(self, mock_redis_client):
        """Test dequeue_notification returns None when queue is empty (non-blocking)."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = mock_redis_client
            mock_redis_client.lpop.return_value = None
            
            from app.services.notification.notification_queue import dequeue_notification
            
            result = dequeue_notification(block=False)
            
            assert result is None

    def test_dequeue_notification_redis_not_configured(self):
        """Test dequeue_notification when Redis is not configured."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = None
            
            from app.services.notification.notification_queue import dequeue_notification
            
            result = dequeue_notification()
            
            assert result is None

    def test_dequeue_notification_handles_exception(self, mock_redis_client):
        """Test dequeue_notification handles exception."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = mock_redis_client
            mock_redis_client.blpop.side_effect = Exception("Redis error")
            
            from app.services.notification.notification_queue import dequeue_notification
            
            result = dequeue_notification(block=True)
            
            assert result is None

    def test_dequeue_notification_invalid_json(self, mock_redis_client):
        """Test dequeue_notification handles invalid JSON."""
        with patch("app.services.notification.notification_queue.get_redis_client") as mock:
            mock.return_value = mock_redis_client
            mock_redis_client.blpop.return_value = (
                "notification:dispatch:queue",
                "invalid json"
            )
            
            from app.services.notification.notification_queue import dequeue_notification
            
            result = dequeue_notification(block=True)
            
            assert result is None

    # --- Test QUEUE_KEY constant ---
    
    def test_queue_key_defined(self):
        """Test QUEUE_KEY is properly defined."""
        from app.services.notification.notification_queue import QUEUE_KEY
        assert QUEUE_KEY == "notification:dispatch:queue"