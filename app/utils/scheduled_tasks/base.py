# -*- coding: utf-8 -*-
"""
定时任务 - 基础模块
通用辅助函数和共享依赖
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.alert import AlertRecord
from app.models.base import get_db_session

# 模块级 logger
logger = logging.getLogger(__name__)


def send_notification_for_alert(db: Session, alert: AlertRecord, logger_instance=None):
    """
    为预警发送通知的辅助函数
    通知发送失败不影响预警记录创建

    注意：实际通知发送由 send_alert_notifications 定时任务批量处理
    此函数用于创建通知并尝试入队，队列不可用时直接发送

    Args:
        db: 数据库会话
        alert: 预警记录
        logger_instance: 日志记录器（可选）
    """
    if logger_instance is None:
        logger_instance = logger

    try:
        # 延迟导入避免循环依赖
        from app.models.alert import AlertNotification
        from app.services.notification_dispatcher import (
            NotificationDispatcher,
            channel_allowed,
            resolve_channel_target,
            resolve_channels,
            resolve_recipients,
        )

        dispatcher = NotificationDispatcher(db)
        recipients = resolve_recipients(db, alert)

        if not recipients:
            logger_instance.debug(f"No recipients found for alert {alert.alert_no}")
            return

        channels = resolve_channels(alert)
        notifications_created = 0
        created_notifications = []
        queued_count = 0
        sent_count = 0

        for user_id, recipient_info in recipients.items():
            user = recipient_info.get("user")
            settings = recipient_info.get("settings")

            if not user:
                continue

            for channel in channels:
                if not channel_allowed(channel, settings):
                    continue

                target = resolve_channel_target(channel, user)
                if not target:
                    continue

                # 检查是否已存在相同通知
                existing = db.query(AlertNotification).filter(
                    AlertNotification.alert_id == alert.id,
                    AlertNotification.notify_channel == channel,
                    AlertNotification.notify_target == target
                ).first()

                if existing:
                    continue

                # 创建通知记录
                notification = AlertNotification(
                    alert_id=alert.id,
                    notify_channel=channel,
                    notify_target=target,
                    notify_user_id=user.id,
                    notify_title=alert.alert_title,
                    notify_content=alert.alert_content,
                    status='PENDING'
                )
                db.add(notification)
                notifications_created += 1
                created_notifications.append((notification, user))

        if notifications_created > 0:
            db.flush()
            for notification, user in created_notifications:
                result = enqueue_or_dispatch_notification(
                    dispatcher,
                    notification,
                    alert,
                    user,
                    logger_instance=logger_instance,
                )
                if result.get("queued"):
                    queued_count += 1
                elif result.get("sent"):
                    sent_count += 1

            logger_instance.debug(
                f"Created {notifications_created} notifications for alert {alert.alert_no} "
                f"(queued={queued_count}, sent={sent_count})"
            )

    except Exception as notif_err:
        # 通知发送失败不影响预警记录创建
        logger_instance.error(
            f"Error creating notification for alert {alert.alert_no}: {str(notif_err)}",
            exc_info=True
        )


def enqueue_or_dispatch_notification(
    dispatcher,
    notification,
    alert: AlertRecord,
    user: Optional[object],
    logger_instance=None,
    request=None,
) -> dict:
    """Build request, enqueue notification, and fallback to synchronous dispatch."""
    if logger_instance is None:
        logger_instance = logger

    from app.services.notification_queue import enqueue_notification

    try:
        if request is None:
            request = dispatcher.build_notification_request(
                notification, alert, user
            )
        request_payload = request.__dict__
    except Exception as exc:
        notification.status = "FAILED"
        notification.error_message = str(exc)
        logger_instance.debug(f"Failed to build notification request: {exc}")
        return {"queued": False, "sent": False, "error": str(exc)}

    enqueued = enqueue_notification({
        "notification_id": notification.id,
        "alert_id": notification.alert_id,
        "notify_channel": notification.notify_channel,
        "request": request_payload,
    })

    if enqueued:
        notification.status = 'QUEUED'
        notification.next_retry_at = None
        return {"queued": True, "sent": False}

    success = dispatcher.dispatch(notification, alert, user, request=request)
    return {"queued": False, "sent": success}

def log_task_result(task_name: str, result: dict, logger_instance=None):
    """
    记录任务执行结果

    Args:
        task_name: 任务名称
        result: 执行结果
        logger_instance: 日志记录器
    """
    if logger_instance is None:
        logger_instance = logger

    if 'error' in result:
        logger_instance.error(f"[{datetime.now()}] {task_name} 执行失败: {result['error']}")
    else:
        logger_instance.info(f"[{datetime.now()}] {task_name} 执行完成: {result}")


def safe_task_execution(task_func, task_name: str, logger_instance=None):
    """
    安全执行任务的装饰器辅助函数

    Args:
        task_func: 任务函数
        task_name: 任务名称
        logger_instance: 日志记录器
    """
    if logger_instance is None:
        logger_instance = logger

    def wrapper(*args, **kwargs):
        try:
            result = task_func(*args, **kwargs)
            log_task_result(task_name, result or {}, logger_instance)
            return result
        except Exception as e:
            logger_instance.error(f"[{datetime.now()}] {task_name} 执行异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    return wrapper
