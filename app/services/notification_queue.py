# -*- coding: utf-8 -*-
"""
Redis-backed notification queue for async dispatch.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

QUEUE_KEY = "notification:dispatch:queue"


def enqueue_notification(payload: Dict[str, Any]) -> bool:
    """
    Push notification payload to Redis queue.
    Payload example:
    {
        "notification_id": 123,
        "alert_id": 456,
        "notify_channel": "EMAIL",
        "enqueue_at": "...",
    }
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.warning("Redis未配置，无法使用通知队列")
        return False
    try:
        if "enqueue_at" not in payload:
            payload["enqueue_at"] = datetime.now(timezone.utc).isoformat()
        redis_client.rpush(QUEUE_KEY, json.dumps(payload, ensure_ascii=False))
        return True
    except Exception as exc:
        logger.error(f"写入通知队列失败: {exc}")
        return False


def dequeue_notification(block: bool = True, timeout: int = 5) -> Optional[Dict[str, Any]]:
    redis_client = get_redis_client()
    if not redis_client:
        return None
    try:
        if block:
            result = redis_client.blpop(QUEUE_KEY, timeout=timeout)
            if not result:
                return None
            _, data = result
        else:
            data = redis_client.lpop(QUEUE_KEY)
            if data is None:
                return None
        return json.loads(data)
    except Exception as exc:
        logger.error(f"读取通知队列失败: {exc}")
        return None
