# -*- coding: utf-8 -*-
"""第十五批: notification_queue 单元测试"""
import pytest

pytest.importorskip("app.services.notification_queue")

import json
from unittest.mock import MagicMock, patch
from app.services.notification_queue import (
    enqueue_notification,
    dequeue_notification,
    QUEUE_KEY,
)


def test_enqueue_no_redis():
    with patch("app.services.notification_queue.get_redis_client", return_value=None):
        result = enqueue_notification({"notification_id": 1})
        assert result is False


def test_enqueue_success():
    mock_redis = MagicMock()
    mock_redis.rpush.return_value = 1
    with patch("app.services.notification_queue.get_redis_client", return_value=mock_redis):
        payload = {"notification_id": 2, "notify_channel": "EMAIL"}
        result = enqueue_notification(payload)
        assert result is True
        mock_redis.rpush.assert_called_once()
        # enqueue_at should be added
        assert "enqueue_at" in payload


def test_enqueue_preserves_existing_enqueue_at():
    mock_redis = MagicMock()
    mock_redis.rpush.return_value = 1
    with patch("app.services.notification_queue.get_redis_client", return_value=mock_redis):
        payload = {"notification_id": 3, "enqueue_at": "2025-01-01T00:00:00Z"}
        enqueue_notification(payload)
        assert payload["enqueue_at"] == "2025-01-01T00:00:00Z"


def test_enqueue_exception():
    mock_redis = MagicMock()
    mock_redis.rpush.side_effect = Exception("Redis error")
    with patch("app.services.notification_queue.get_redis_client", return_value=mock_redis):
        result = enqueue_notification({"notification_id": 4})
        assert result is False


def test_dequeue_no_redis():
    with patch("app.services.notification_queue.get_redis_client", return_value=None):
        result = dequeue_notification()
        assert result is None


def test_dequeue_blocking_success():
    payload = {"notification_id": 5, "notify_channel": "SYSTEM"}
    mock_redis = MagicMock()
    mock_redis.blpop.return_value = (QUEUE_KEY, json.dumps(payload))
    with patch("app.services.notification_queue.get_redis_client", return_value=mock_redis):
        result = dequeue_notification(block=True, timeout=5)
        assert result["notification_id"] == 5


def test_dequeue_blocking_timeout():
    mock_redis = MagicMock()
    mock_redis.blpop.return_value = None
    with patch("app.services.notification_queue.get_redis_client", return_value=mock_redis):
        result = dequeue_notification(block=True, timeout=1)
        assert result is None


def test_dequeue_non_blocking():
    payload = {"notification_id": 6}
    mock_redis = MagicMock()
    mock_redis.lpop.return_value = json.dumps(payload)
    with patch("app.services.notification_queue.get_redis_client", return_value=mock_redis):
        result = dequeue_notification(block=False)
        assert result["notification_id"] == 6
