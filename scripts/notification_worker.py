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

from app.utils.redis_client import get_redis_client
from app.services.notification_queue import dequeue_notification
from app.services.notification_dispatcher import NotificationDispatcher, is_quiet_hours, next_quiet_resume
from app.utils.scheduler_metrics import record_notification_failure, record_notification_success
from app.models.base import get_db_session
from app.models.alert import AlertNotification
from app.models.user import User
from app.models.notification import NotificationSettings

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
            settings = None
            if notification.notify_user_id:
                user = db.query(User).filter(User.id == notification.notify_user_id).first()
                settings = db.query(NotificationSettings).filter(
                    NotificationSettings.user_id == notification.notify_user_id
                ).first()
            if is_quiet_hours(settings, alert.triggered_at or alert.created_at or alert.updated_at or alert.created_at):
                notification.status = 'PENDING'
                notification.next_retry_at = next_quiet_resume(settings, alert.triggered_at or alert.created_at or notification.created_at)
                notification.error_message = "Delayed due to quiet hours (worker)"
                db.commit()
                continue

            dispatcher = NotificationDispatcher(db)
            success = dispatcher.dispatch(notification, alert, user)
            db.commit()
            channel = notification.notify_channel.upper()
            if success:
                record_notification_success(channel)
            else:
                record_notification_failure(channel)


if __name__ == "__main__":
    asyncio.run(main())
