# -*- coding: utf-8 -*-
"""向后兼容入口: app.services.notification_queue."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

QUEUE_KEY = "notification:dispatch:queue"


def enqueue_notification(payload: Dict[str, Any]) -> bool:
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
            result = redis_client.blpop(QUEUE_KEY, timeout)
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


__all__ = ["QUEUE_KEY", "get_redis_client", "enqueue_notification", "dequeue_notification"]
