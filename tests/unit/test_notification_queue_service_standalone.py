# -*- coding: utf-8 -*-
"""
通知队列服务单元测试（独立版本，不依赖复杂模型）
"""

from unittest.mock import MagicMock, patch


class TestEnqueueNotification:
    """测试通知入队"""

    @patch("app.services.notification_queue.get_redis_client")
    def test_successfully_enqueues_notification(self, mock_get_redis):
        """成功将通知推入队列"""
        mock_redis = MagicMock()
        mock_redis.rpush.return_value = True
        mock_get_redis.return_value = mock_redis

        from app.services.notification_queue import enqueue_notification

        payload = {
        "notification_id": 123,
        "alert_id": 456,
        "notify_channel": "EMAIL",
        }

        result = enqueue_notification(payload)

        assert result is True
        assert mock_redis.rpush.called
        assert "enqueue_at" in payload
        assert isinstance(payload["enqueue_at"], str)

    @patch("app.services.notification_queue.get_redis_client")
    def test_redis_not_configured_returns_false(self, mock_get_redis):
        """Redis 未配置时返回 False"""
        mock_get_redis.return_value = None

        from app.services.notification_queue import enqueue_notification

        payload = {"notification_id": 123}

        result = enqueue_notification(payload)

        assert result is False
        assert not mock_get_redis.return_value

    @patch("app.services.notification_queue.get_redis_client")
    def test_handles_json_serialize_error(self, mock_get_redis, caplog):
        """处理 JSON 序列化错误"""
        mock_redis = MagicMock()
        mock_redis.rpush.side_effect = Exception("JSON encode error")
        mock_get_redis.return_value = mock_redis

        from app.services.notification_queue import enqueue_notification

        payload = {"notification_id": 123, "invalid_data": object()}

        result = enqueue_notification(payload)

        assert result is False


class TestDequeueNotification:
    """测试通知出队"""

    @patch("app.services.notification_queue.get_redis_client")
    def test_dequeue_blocking(self, mock_get_redis):
        """阻塞模式出队"""
        mock_redis = MagicMock()
        mock_redis.blpop.return_value = [
        b"notification:dispatch:queue",
        b'{"notification_id": 123}',
        ]

        mock_get_redis.return_value = mock_redis

        from app.services.notification_queue import dequeue_notification

        result = dequeue_notification(block=True, timeout=5)

        assert result is not None
        assert isinstance(result, dict)
        assert result["notification_id"] == 123
        mock_redis.blpop.assert_called_once_with("notification:dispatch:queue", 5)

    @patch("app.services.notification_queue.get_redis_client")
    def test_dequeue_non_blocking(self, mock_get_redis):
        """非阻塞模式出队"""
        mock_redis = MagicMock()
        mock_redis.lpop.return_value = b'{"notification_id": 456}'

        mock_get_redis.return_value = mock_redis

        from app.services.notification_queue import dequeue_notification

        result = dequeue_notification(block=False)

        assert result is not None
        assert isinstance(result, dict)
        assert result["notification_id"] == 456
        mock_redis.lpop.assert_called_once()

    @patch("app.services.notification_queue.get_redis_client")
    def test_empty_queue_returns_none(self, mock_get_redis):
        """空队列返回 None"""
        mock_redis = MagicMock()
        mock_redis.lpop.return_value = None
        mock_redis.blpop.return_value = [None]

        mock_get_redis.return_value = mock_redis

        from app.services.notification_queue import dequeue_notification

        result_blocking = dequeue_notification(block=True)
        result_non_blocking = dequeue_notification(block=False)

        assert result_blocking is None
        assert result_non_blocking is None

    @patch("app.services.notification_queue.get_redis_client")
    def test_redis_not_configured_dequeue(self, mock_get_redis):
        """Redis 未配置时出队返回 None"""
        mock_get_redis.return_value = None

        from app.services.notification_queue import dequeue_notification

        result = dequeue_notification(block=True)

        assert result is None

    @patch("app.services.notification_queue.get_redis_client")
    def test_custom_timeout_param(self, mock_get_redis):
        """自定义超时参数"""
        mock_redis = MagicMock()
        mock_redis.blpop.return_value = [
        b"notification:dispatch:queue",
        b'{"notification_id": 123}',
        ]

        mock_get_redis.return_value = mock_redis

        from app.services.notification_queue import dequeue_notification

        result = dequeue_notification(block=True, timeout=10)

        assert result is not None
        mock_redis.blpop.assert_called_once_with("notification:dispatch:queue", 10)
