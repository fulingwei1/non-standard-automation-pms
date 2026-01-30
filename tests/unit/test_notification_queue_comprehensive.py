# -*- coding: utf-8 -*-
"""
notification_queue 模块综合单元测试

测试覆盖:
- enqueue_notification: 入队通知
- dequeue_notification: 出队通知
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import json

import pytest


class TestEnqueueNotification:
    """测试 enqueue_notification 函数"""

    def test_enqueues_notification_successfully(self):
        """测试成功入队通知"""
        from app.services.notification_queue import enqueue_notification

        mock_redis = MagicMock()

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            payload = {
                "notification_id": 123,
                "alert_id": 456,
                "notify_channel": "EMAIL",
            }

            result = enqueue_notification(payload)

            assert result is True
            mock_redis.rpush.assert_called_once()

    def test_returns_false_when_redis_not_configured(self):
        """测试 Redis 未配置时返回 False"""
        from app.services.notification_queue import enqueue_notification

        with patch('app.services.notification_queue.get_redis_client', return_value=None):
            payload = {
                "notification_id": 123,
                "alert_id": 456,
            }

            result = enqueue_notification(payload)

            assert result is False

    def test_adds_enqueue_at_if_not_present(self):
        """测试自动添加入队时间"""
        from app.services.notification_queue import enqueue_notification

        mock_redis = MagicMock()

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            payload = {
                "notification_id": 123,
            }

            result = enqueue_notification(payload)

            assert result is True
            call_args = mock_redis.rpush.call_args[0]
            pushed_data = json.loads(call_args[1])
            assert "enqueue_at" in pushed_data

    def test_preserves_existing_enqueue_at(self):
        """测试保留已有的入队时间"""
        from app.services.notification_queue import enqueue_notification

        mock_redis = MagicMock()
        existing_time = "2024-01-01T12:00:00+00:00"

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            payload = {
                "notification_id": 123,
                "enqueue_at": existing_time,
            }

            result = enqueue_notification(payload)

            call_args = mock_redis.rpush.call_args[0]
            pushed_data = json.loads(call_args[1])
            assert pushed_data["enqueue_at"] == existing_time

    def test_handles_redis_error(self):
        """测试处理 Redis 错误"""
        from app.services.notification_queue import enqueue_notification

        mock_redis = MagicMock()
        mock_redis.rpush.side_effect = Exception("Redis连接失败")

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            payload = {"notification_id": 123}

            result = enqueue_notification(payload)

            assert result is False

    def test_uses_correct_queue_key(self):
        """测试使用正确的队列键"""
        from app.services.notification_queue import enqueue_notification, QUEUE_KEY

        mock_redis = MagicMock()

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            payload = {"notification_id": 123}

            enqueue_notification(payload)

            call_args = mock_redis.rpush.call_args[0]
            assert call_args[0] == QUEUE_KEY


class TestDequeueNotification:
    """测试 dequeue_notification 函数"""

    def test_dequeues_notification_blocking(self):
        """测试阻塞模式出队通知"""
        from app.services.notification_queue import dequeue_notification

        mock_redis = MagicMock()
        payload = {"notification_id": 123, "alert_id": 456}
        mock_redis.blpop.return_value = ("queue_key", json.dumps(payload))

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            result = dequeue_notification(block=True, timeout=5)

            assert result == payload
            mock_redis.blpop.assert_called_once()

    def test_dequeues_notification_non_blocking(self):
        """测试非阻塞模式出队通知"""
        from app.services.notification_queue import dequeue_notification

        mock_redis = MagicMock()
        payload = {"notification_id": 123}
        mock_redis.lpop.return_value = json.dumps(payload)

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            result = dequeue_notification(block=False)

            assert result == payload
            mock_redis.lpop.assert_called_once()

    def test_returns_none_when_redis_not_configured(self):
        """测试 Redis 未配置时返回 None"""
        from app.services.notification_queue import dequeue_notification

        with patch('app.services.notification_queue.get_redis_client', return_value=None):
            result = dequeue_notification()

            assert result is None

    def test_returns_none_when_queue_empty_blocking(self):
        """测试阻塞模式队列为空时返回 None"""
        from app.services.notification_queue import dequeue_notification

        mock_redis = MagicMock()
        mock_redis.blpop.return_value = None

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            result = dequeue_notification(block=True, timeout=1)

            assert result is None

    def test_returns_none_when_queue_empty_non_blocking(self):
        """测试非阻塞模式队列为空时返回 None"""
        from app.services.notification_queue import dequeue_notification

        mock_redis = MagicMock()
        mock_redis.lpop.return_value = None

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            result = dequeue_notification(block=False)

            assert result is None

    def test_handles_redis_error(self):
        """测试处理 Redis 错误"""
        from app.services.notification_queue import dequeue_notification

        mock_redis = MagicMock()
        mock_redis.blpop.side_effect = Exception("Redis连接失败")

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            result = dequeue_notification(block=True)

            assert result is None

    def test_uses_correct_timeout(self):
        """测试使用正确的超时时间"""
        from app.services.notification_queue import dequeue_notification, QUEUE_KEY

        mock_redis = MagicMock()
        mock_redis.blpop.return_value = None

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            dequeue_notification(block=True, timeout=10)

            mock_redis.blpop.assert_called_once_with(QUEUE_KEY, timeout=10)

    def test_parses_json_payload(self):
        """测试解析 JSON 负载"""
        from app.services.notification_queue import dequeue_notification

        mock_redis = MagicMock()
        payload = {
            "notification_id": 123,
            "alert_id": 456,
            "notify_channel": "WECHAT",
            "data": {"key": "value"}
        }
        mock_redis.blpop.return_value = ("queue", json.dumps(payload))

        with patch('app.services.notification_queue.get_redis_client', return_value=mock_redis):
            result = dequeue_notification(block=True)

            assert result == payload
            assert result["data"]["key"] == "value"
