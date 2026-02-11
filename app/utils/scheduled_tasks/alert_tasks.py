# -*- coding: utf-8 -*-
"""
定时任务 - 预警与通知相关任务
包含：预警升级、消息推送、通知重试、响应指标计算
"""
import logging
from datetime import datetime

from sqlalchemy import or_

from app.models.alert import AlertNotification, AlertRecord
from app.models.base import get_db_session
from app.services.notification_dispatcher import NotificationDispatcher
from app.utils.scheduled_tasks.base import enqueue_or_dispatch_notification

logger = logging.getLogger(__name__)


def check_alert_escalation():
    """
    S.10: 预警升级服务
    每小时执行一次，检查超时未处理的预警并自动升级
    """
    try:
        with get_db_session() as db:
            from app.services.alert_escalation_service import AlertEscalationService

            service = AlertEscalationService(db)
            result = service.check_and_escalate()

            logger.info(
                f"[{datetime.now()}] 预警升级检查完成: "
                f"检查 {result.get('checked', 0)} 个预警, "
                f"升级 {result.get('escalated', 0)} 个"
            )

            return result
    except Exception as e:
        logger.error(f"[{datetime.now()}] 预警升级检查失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def retry_failed_notifications():
    """
    通知重试机制
    每小时执行一次，重试发送失败的通知
    """
    try:
        with get_db_session() as db:
            from app.models.user import User

            current_time = datetime.now()
            max_retries = 3

            # 查询需要重试的通知
            failed_notifications = db.query(AlertNotification).filter(
                AlertNotification.status == 'FAILED',
                AlertNotification.retry_count < max_retries,
                or_(
                    AlertNotification.next_retry_at.is_(None),
                    AlertNotification.next_retry_at <= current_time
                )
            ).all()

            retry_count = 0
            success_count = 0
            failed_count = 0
            abandoned_count = 0

            dispatcher = NotificationDispatcher(db)

            for notification in failed_notifications:
                # 获取预警和用户信息
                alert = notification.alert
                user = None
                if notification.notify_user_id:
                    user = db.query(User).filter(User.id == notification.notify_user_id).first()

                if not alert or not user:
                    notification.status = 'ABANDONED'
                    notification.error_message = "Alert or user not found"
                    abandoned_count += 1
                    continue

                # 尝试重新发送
                retry_count += 1
                success = dispatcher.dispatch(notification, alert, user)

                if success:
                    success_count += 1
                    logger.info(f"Retry successful for notification {notification.id}")
                else:
                    failed_count += 1
                    if notification.retry_count >= max_retries:
                        notification.status = 'ABANDONED'
                        notification.error_message = f"Max retries ({max_retries}) exceeded"
                        abandoned_count += 1
                    logger.warning(
                        f"Retry failed for notification {notification.id}: "
                        f"{notification.error_message}"
                    )

            db.commit()

            logger.info(
                f"通知重试完成: 重试 {retry_count} 个, 成功 {success_count} 个, "
                f"失败 {failed_count} 个, 放弃 {abandoned_count} 个"
            )

            return {
                'retry_count': retry_count,
                'success_count': success_count,
                'failed_count': failed_count,
                'abandoned_count': abandoned_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] 通知重试失败: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def send_alert_notifications():
    """
    S.12: 消息推送服务
    - 为新预警生成通知队列
    - 根据通知渠道发送消息（站内信、企业微信、邮件）
    - 失败任务支持重试策略
    """
    try:
        with get_db_session() as db:
            dispatcher = NotificationDispatcher(db)
            from app.models.user import User

            # 1) 生成通知队列
            pending_alerts = db.query(AlertRecord).filter(
                AlertRecord.status == 'PENDING'
            ).order_by(AlertRecord.triggered_at.desc().nulls_last()).limit(50).all()

            queue_created = 0
            queued_from_alerts = 0
            sent_from_alerts = 0
            failed_from_alerts = 0

            for alert in pending_alerts:
                result = dispatcher.dispatch_alert_notifications(alert=alert)
                queue_created += result.get("created", 0)
                queued_from_alerts += result.get("queued", 0)
                sent_from_alerts += result.get("sent", 0)
                failed_from_alerts += result.get("failed", 0)

            # 2) 发送通知（包含失败重试）
            now = datetime.now()
            pending_notifications = db.query(AlertNotification).filter(
                AlertNotification.status.in_(["PENDING", "FAILED"]),
                or_(AlertNotification.next_retry_at.is_(None), AlertNotification.next_retry_at <= now)
            ).order_by(AlertNotification.created_at.asc()).limit(100).all()

            sent_count = 0
            queued_notifications = 0

            for notification in pending_notifications:
                alert = notification.alert
                user = None
                if notification.notify_user_id:
                    user = db.query(User).filter(User.id == notification.notify_user_id).first()

                result = enqueue_or_dispatch_notification(
                    dispatcher,
                    notification,
                    alert,
                    user,
                    logger_instance=logger,
                )
                if result.get("queued"):
                    queued_notifications += 1
                elif result.get("sent"):
                    sent_count += 1

            db.commit()

            logger.info(
                f"[{datetime.now()}] 消息推送服务完成: "
                f"新建 {queue_created} 条通知(入队 {queued_from_alerts}，直发 {sent_from_alerts}，失败 {failed_from_alerts}), "
                f"处理 {len(pending_notifications)} 条通知, "
                f"入队 {queued_notifications} 条, 直接发送 {sent_count} 条"
            )

            return {
                'queued_alerts': len(pending_alerts),
                'queue_created': queue_created,
                'queued_from_alerts': queued_from_alerts,
                'sent_from_alerts': sent_from_alerts,
                'failed_from_alerts': failed_from_alerts,
                'processed_notifications': len(pending_notifications),
                'queued_notifications': queued_notifications,
                'sent_count': sent_count,
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] 消息推送服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def calculate_response_metrics():
    """
    计算预警响应指标
    每天执行一次，统计预警响应时间等指标
    """
    try:
        with get_db_session() as db:
            from app.services.alert_response_service import AlertResponseService

            service = AlertResponseService(db)
            result = service.calculate_daily_metrics()

            logger.info(f"[{datetime.now()}] 预警响应指标计算完成: {result}")

            return result
    except Exception as e:
        logger.error(f"[{datetime.now()}] 预警响应指标计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
