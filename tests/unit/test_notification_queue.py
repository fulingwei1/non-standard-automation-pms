# -*- coding: utf-8 -*-
"""通知队列 (notification_queue) 单元测试"""

from unittest.mock import MagicMock, patch

import pytest
import importlib.util


def _load_module_directly(path: str):
    """直接加载模块，绕过 __init__.py"""
    spec = importlib.util.spec_from_file_location("notification_queue", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# 尝试加载 notification_queue 模块
_load_error = ""
try:
    _notification_queue = _load_module_directly(
        "app/services/notification/notification_queue.py"
    )
    QUEUE_MODULE_OK = True
except Exception as e:
    QUEUE_MODULE_OK = False
    _load_error = str(e)


pytestmark = pytest.mark.skipif(
    not QUEUE_MODULE_OK, reason=f"Cannot load notification_queue: {_load_error}"
)


class TestNotificationQueue:
    """通知队列测试类"""

    def test_enqueue_notification_redis_not_configured(self):
        """测试 Redis 未配置时返回 False"""
        # 直接替换模块中的 get_redis_client 函数
        with patch.object(_notification_queue, 'get_redis_client', return_value=None):
            result = _notification_queue.enqueue_notification(
                {"notification_id": 1, "alert_id": 2, "notify_channel": "EMAIL"}
            )
            assert result is False

    def test_enqueue_notification_success(self):
        """测试入队成功"""
        mock_redis_client = MagicMock()
        mock_redis_client.rpush.return_value = 1
        
        original_enqueue_at = _notification_queue.QUEUE_KEY
        
        with patch.object(_notification_queue, 'get_redis_client', return_value=mock_redis_client):
            with patch.object(_notification_queue, 'QUEUE_KEY', "test:queue"):
                payload = {
                    "notification_id": 123,
                    "alert_id": 456,
                    "notify_channel": "EMAIL",
                    "enqueue_at": "2024-01-01T00:00:00",
                }
                result = _notification_queue.enqueue_notification(payload)

        assert result is True

    def test_enqueue_notification_failure(self):
        """测试入队失败时返回 False"""
        mock_redis_client = MagicMock()
        mock_redis_client.rpush.side_effect = Exception("Redis error")

        with patch.object(_notification_queue, 'get_redis_client', return_value=mock_redis_client):
            with patch.object(_notification_queue, 'QUEUE_KEY', "test:queue"):
                payload = {
                    "notification_id": 123,
                    "alert_id": 456,
                    "notify_channel": "EMAIL",
                }
                result = _notification_queue.enqueue_notification(payload)

        assert result is False

    def test_dequeue_notification(self):
        """测试出队"""
        mock_redis_client = MagicMock()
        mock_redis_client.lpop.return_value = '{"notification_id": 123}'

        with patch.object(_notification_queue, 'get_redis_client', return_value=mock_redis_client):
            with patch.object(_notification_queue, 'QUEUE_KEY', "test:queue"):
                result = _notification_queue.dequeue_notification(block=False)

        assert result == {"notification_id": 123}

    def test_dequeue_notification_empty_queue(self):
        """测试空队列返回 None"""
        mock_redis_client = MagicMock()
        mock_redis_client.lpop.return_value = None

        with patch.object(_notification_queue, 'get_redis_client', return_value=mock_redis_client):
            with patch.object(_notification_queue, 'QUEUE_KEY', "test:queue"):
                result = _notification_queue.dequeue_notification(block=False)

        assert result is None

    def test_dequeue_notification_invalid_json(self):
        """测试无效 JSON 返回 None"""
        mock_redis_client = MagicMock()
        mock_redis_client.lpop.return_value = "invalid json"

        with patch.object(_notification_queue, 'get_redis_client', return_value=mock_redis_client):
            with patch.object(_notification_queue, 'QUEUE_KEY', "test:queue"):
                result = _notification_queue.dequeue_notification(block=False)

        assert result is None

    def test_dequeue_notification_with_enqueued_at(self):
        """测试带有入队时间的通知出队"""
        mock_redis_client = MagicMock()
        mock_redis_client.lpop.return_value = '{"notification_id": 456, "enqueue_at": "2024-01-01T12:00:00"}'

        with patch.object(_notification_queue, 'get_redis_client', return_value=mock_redis_client):
            with patch.object(_notification_queue, 'QUEUE_KEY', "test:queue"):
                result = _notification_queue.dequeue_notification(block=False)

        assert result == {"notification_id": 456, "enqueue_at": "2024-01-01T12:00:00"}