# -*- coding: utf-8 -*-
"""
通知队列服务测试
"""

from datetime import datetime

from unittest.mock import MagicMock, patch

from app.services.notification_queue import (
    dequeue_notification,
    enqueue_notification,
)


class TestEnqueueNotification:
    """测试通知入队"""

    @patch("app.services.notification_queue.get_redis_client")
    def test_successfully_enqueues_notification(self, mock_get_redis):
        """成功将通知推入队列"""
        mock_redis = MagicMock()
        mock_redis.rpush.return_value = True
        mock_get_redis.return_value = mock_redis

        payload = {
            "notification_id": 123,
            "alert_id": 456,
            "notify_channel": "EMAIL",
        }

        result = enqueue_notification(payload)

        assert result is True
        mock_redis.rpush.assert_called_once()
        assert "enqueue_at" in payload
        assert isinstance(payload["enqueue_at"], str)

    @patch("app.services.notification_queue.get_redis_client")
    def test_redis_not_configured_returns_false(self, mock_get_redis):
        """Redis 未配置时返回 False"""
        mock_get_redis.return_value = None

        payload = {"notification_id": 123}

        result = enqueue_notification(payload)

        assert result is False

    @patch("app.services.notification_queue.get_redis_client")
    def test_handles_exception_during_enqueue(self, mock_get_redis, caplog):
        """处理入队过程中的异常"""
        mock_redis = MagicMock()
        mock_redis.rpush.side_effect = Exception("Redis error")
        mock_get_redis.return_value = mock_redis

        payload = {"notification_id": 123}

        result = enqueue_notification(payload)

        assert result is False

    @patch("app.services.notification_queue.get_redis_client")
    def test_adds_enqueue_at_timestamp(self, mock_get_redis):
        """添加入队时间戳"""
        mock_redis = MagicMock()
        mock_redis.rpush.return_value = True
        mock_get_redis.return_value = mock_redis

        payload = {"notification_id": 123, "alert_id": 456}

        before_time = datetime.now()
        result = enqueue_notification(payload)

        assert result is True
        assert "enqueue_at" in payload
        assert isinstance(payload["enqueue_at"], str)
        assert payload["enqueue_at"] >= before_time


class TestDequeueNotification:
    """测试通知出队"""

    @patch("app.services.notification_queue.get_redis_client")
    def test_dequeue_blocking(self, mock_get_redis):
        """阻塞模式出队"""
        mock_redis = MagicMock()
        mock_redis.blpop.return_value = [b'{"notification_id": 123}']

        mock_get_redis.return_value = mock_redis

        result = dequeue_notification(block=True, timeout=5)

        assert result is not None
        assert isinstance(result, dict)
        mock_redis.blpop.assert_called_once()

    @patch("app.services.notification_queue.get_redis_client")
    def test_dequeue_non_blocking(self, mock_get_redis):
        """非阻塞模式出队"""
        mock_redis = MagicMock()
        mock_redis.lpop.return_value = b'{"notification_id": 456}'

        mock_get_redis.return_value = mock_redis

        result = dequeue_notification(block=False)

        assert result is not None
        assert isinstance(result, dict)
        mock_redis.lpop.assert_called_once()

    @patch("app.services.notification_queue.get_redis_client")
    def test_redis_not_configured_returns_none(self, mock_get_redis):
        """Redis 未配置时返回 None"""
        mock_get_redis.return_value = None

        result = dequeue_notification(block=True)

        assert result is None

    @patch("app.services.notification_queue.get_redis_client")
    def test_empty_queue_returns_none(self, mock_get_redis):
        """空队列返回 None"""
        mock_redis = MagicMock()
        mock_redis.lpop.return_value = None
        mock_redis.blpop.return_value = [None]

        mock_get_redis.return_value = mock_redis

        result = dequeue_notification(block=False)

        assert result is None

    @patch("app.services.notification_queue.get_redis_client")
    def test_handles_exception_during_dequeue(self, mock_get_redis, caplog):
        """处理出队过程中的异常"""
        mock_redis = MagicMock()
        mock_redis.lpop.side_effect = Exception("Redis error")
        mock_get_redis.return_value = mock_redis

        result = dequeue_notification(block=False)

        assert result is None

    @patch("app.services.notification_queue.get_redis_client")
    def test_parse_json_data(self, mock_get_redis):
        """测试解析 JSON 数据"""
        mock_redis = MagicMock()
        test_data = {"notification_id": 123, "alert_id": 456, "type": "EMAIL"}
        mock_redis.lpop.return_value = test_data.encode("utf-8")

        mock_get_redis.return_value = mock_redis

        result = dequeue_notification(block=False)

        assert result is not None
        assert result["notification_id"] == 123
        assert result["alert_id"] == 456
        assert result["type"] == "EMAIL"
