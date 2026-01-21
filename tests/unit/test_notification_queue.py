# -*- coding: utf-8 -*-
"""
Tests for notification_queue service
Covers: app/services/notification_queue.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
Batch: P3 - 扩展服务模块测试
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Mock the module to avoid dependency issues
QUEUE_KEY = "notification:dispatch:queue"


class TestNotificationQueue:
    """Test suite for notification queue functions."""

    @patch('app.services.notification_queue.get_redis_client')
    def test_enqueue_notification_success(self, mock_redis):
        """Test successful notification enqueue."""
        mock_redis.return_value = MagicMock()
        mock_redis.return_value.rpush.return_value = True
        
        from app.services.notification_queue import enqueue_notification
        
        payload = {
            "notification_id": 123,
            "alert_id": 456,
            "notify_channel": "EMAIL",
        }
        
        result = enqueue_notification(payload)
        
        # Verify payload was updated with enqueue_at
        assert "enqueue_at" in payload
        assert result is True
        mock_redis.return_value.rpush.assert_called_once()

    @patch('app.services.notification_queue.get_redis_client')
    def test_enqueue_notification_no_redis(self, mock_redis):
        """Test enqueue when Redis is not configured."""
        mock_redis.return_value = None
        
        from app.services.notification_queue import enqueue_notification
        
        result = enqueue_notification({"test": "payload"})
        
        assert result is False

    @patch('app.services.notification_queue.get_redis_client')
    def test_enqueue_notification_adds_timestamp(self, mock_redis):
        """Test that enqueue_notification adds timestamp."""
        mock_redis.return_value = MagicMock()
        mock_redis.return_value.rpush.return_value = True
        
        from app.services.notification_queue import enqueue_notification
        
        payload = {"test": "data"}
        
        enqueue_notification(payload)
        
        # Verify timestamp was added
        assert "enqueue_at" in payload
        try:
            datetime.fromisoformat(payload["enqueue_at"])
        except:
            pytest.fail("enqueue_at should be a valid ISO format timestamp")

    @patch('app.services.notification_queue.get_redis_client')
    def test_dequeue_notification_blocking(self, mock_redis):
        """Test blocking dequeue."""
        mock_redis.return_value = MagicMock()
        mock_redis.return_value.blpop.return_value = (None, b'{"test": "data"}')
        
        from app.services.notification_queue import dequeue_notification
        
        result = dequeue_notification(block=True, timeout=5)
        
        assert result == {"test": "data"}
        mock_redis.return_value.blpop.assert_called_once()

    @patch('app.services.notification_queue.get_redis_client')
    def test_dequeue_notification_non_blocking(self, mock_redis):
        """Test non-blocking dequeue."""
        mock_redis.return_value = MagicMock()
        mock_redis.return_value.lpop.return_value = b'{"test": "data"}'
        
        from app.services.notification_queue import dequeue_notification
        
        result = dequeue_notification(block=False)
        
        assert result == {"test": "data"}
        mock_redis.return_value.lpop.assert_called_once()

    @patch('app.services.notification_queue.get_redis_client')
    def test_dequeue_notification_no_redis(self, mock_redis):
        """Test dequeue when Redis is not configured."""
        mock_redis.return_value = None
        
        from app.services.notification_queue import dequeue_notification
        
        result = dequeue_notification(block=True)
        
        assert result is None

    @patch('app.services.notification_queue.get_redis_client')
    def test_queue_constants(self, mock_redis):
        """Test queue key constant."""
        from app.services.notification_queue import QUEUE_KEY
        
        assert QUEUE_KEY == "notification:dispatch:queue"
        assert isinstance(QUEUE_KEY, str)
        assert len(QUEUE_KEY) > 0
