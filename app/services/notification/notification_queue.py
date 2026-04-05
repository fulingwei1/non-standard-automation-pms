# -*- coding: utf-8 -*-
"""
Redis-backed notification queue for async dispatch.

通知系统架构：
- app.services.unified_notification_service: 主通知服务，提供 NotificationService 和 get_notification_service()
- app.services.notification_service: 兼容层，re-export 统一服务并提供旧接口的枚举和 AlertNotificationService
- app.services.notification_dispatcher: 预警通知调度协调器，内部使用统一服务
- app.services.notification_queue (本模块): Redis 通知队列（异步分发）
- app.services.notification_utils: 通知工具函数（渠道解析、接收者解析、免打扰判断等）
- app.services.channel_handlers/: 渠道处理器（System/Email/WeChat/SMS/Webhook）
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
