#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification queue worker
Continuously consumes Redis queue and dispatches notifications.
"""

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.alert import AlertNotification
from app.models.base import get_db_session
from app.models.user import User
from app.services.notification_dispatcher import (
    NotificationDispatcher,
)
from app.services.channel_handlers.base import NotificationRequest
from app.services.notification_queue import dequeue_notification
from app.utils.redis_client import get_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification_worker")


async def main():
    if not get_redis_client():
        logger.error("Redis 未配置，无法启动通知队列 worker")
        return
    logger.info("通知队列 worker 已启动")
    while True:
        payload = dequeue_notification()
        if not payload:
            await asyncio.sleep(1)
            continue
        notification_id = payload.get("notification_id")
        if not notification_id:
            logger.warning(f"队列数据缺失 notification_id: {payload}")
            continue

        with get_db_session() as db:
            notification = db.query(AlertNotification).filter(AlertNotification.id == notification_id).first()
            if not notification:
                logger.warning(f"通知记录 {notification_id} 不存在，跳过")
                continue
            alert = notification.alert
            user = None
            if notification.notify_user_id:
                user = db.query(User).filter(User.id == notification.notify_user_id).first()

            request = None
            request_payload = payload.get("request")
            if isinstance(request_payload, dict):
                try:
                    request = NotificationRequest(**request_payload)
                except Exception as exc:
                    logger.warning(f"通知请求数据无效，回退为即时构建: {exc}")

            dispatcher = NotificationDispatcher(db)
            dispatcher.dispatch(notification, alert, user, request=request)
            db.commit()


if __name__ == "__main__":
    asyncio.run(main())
