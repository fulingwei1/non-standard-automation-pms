# -*- coding: utf-8 -*-
"""
定时任务 - 预警与通知相关任务
包含：预警升级、消息推送、通知重试、响应指标计算
"""
import logging
from datetime import datetime

from sqlalchemy import or_

from app.dependencies import get_db_session
from app.models.alert import AlertNotification, AlertRecord, AlertRule
from app.services.notification.notification_dispatcher import NotificationDispatcher
from app.utils.scheduled_tasks.base import (
    enqueue_or_dispatch_notification,
    send_notification_for_alert,
)

logger = logging.getLogger(__name__)


def _get_or_create_sla_alert_rule(db) -> AlertRule:
    rule = db.query(AlertRule).filter(AlertRule.rule_code == "SLA_WARNING").first()
    if rule:
        return rule

    rule = AlertRule(
        rule_code="SLA_WARNING",
        rule_name="SLA 工单预警",
        rule_type="SLA",
        target_type="SLA_MONITOR",
        target_field="status",
        condition_type="CUSTOM",
        condition_expr="response_status == WARNING or resolve_status == WARNING",
        alert_level="WARNING",
        notify_channels=["SYSTEM"],
        enforcement_mode="WARN",
        check_frequency="HOURLY",
        is_enabled=True,
        is_system=True,
        is_active=True,
        description="服务工单 SLA 响应/解决时限预警。",
    )
    db.add(rule)
    db.flush()
    return rule


def _sla_warning_deadline(monitor, warning_type: str):
    if warning_type == "response":
        return monitor.response_deadline
    return monitor.resolve_deadline


def _create_sla_warning_alert(db, monitor, warning_type: str, now: datetime) -> bool:
    ticket = getattr(monitor, "ticket", None)
    title = "SLA 响应预警" if warning_type == "response" else "SLA 解决预警"
    existing_alert = (
        db.query(AlertRecord)
        .filter(
            AlertRecord.target_type == "SLA_MONITOR",
            AlertRecord.target_id == monitor.id,
            AlertRecord.alert_title == title,
            AlertRecord.status.in_(["PENDING", "OPEN"]),
        )
        .first()
    )
    if existing_alert:
        return False

    rule = _get_or_create_sla_alert_rule(db)
    deadline = _sla_warning_deadline(monitor, warning_type)
    ticket_no = getattr(ticket, "ticket_no", None) or f"Ticket-{monitor.ticket_id}"
    target_name = getattr(ticket, "problem_desc", None) or ticket_no
    if len(target_name) > 200:
        target_name = f"{target_name[:197]}..."

    alert = AlertRecord(
        alert_no=f"ALT-SLA-{warning_type.upper()}-{monitor.id}-{now.strftime('%Y%m%d%H%M%S')}",
        rule_id=rule.id,
        target_type="SLA_MONITOR",
        target_id=monitor.id,
        target_no=ticket_no,
        target_name=target_name,
        project_id=getattr(ticket, "project_id", None),
        alert_level="WARNING",
        severity="WARNING",
        alert_title=title,
        alert_content=(
            f"服务工单 {ticket_no} 已达到 {title} 阈值，"
            f"截止时间：{deadline.strftime('%Y-%m-%d %H:%M') if deadline else '未设置'}。"
        ),
        alert_data={
            "monitor_id": monitor.id,
            "ticket_id": monitor.ticket_id,
            "warning_type": warning_type,
            "response_status": monitor.response_status,
            "resolve_status": monitor.resolve_status,
            "response_deadline": monitor.response_deadline.isoformat()
            if monitor.response_deadline
            else None,
            "resolve_deadline": monitor.resolve_deadline.isoformat()
            if monitor.resolve_deadline
            else None,
        },
        triggered_at=now,
        trigger_value=warning_type,
        threshold_value=str(deadline) if deadline else None,
        status="PENDING",
        handler_id=getattr(ticket, "assigned_to_id", None),
    )
    db.add(alert)
    db.flush()
    send_notification_for_alert(db, alert, logger_instance=logger)
    return True


def check_sla_warnings_task(current_time: datetime | None = None):
    """
    AS-06: 同步服务工单 SLA 状态，并为达到阈值的 monitor 生成预警。
    """
    if current_time is None:
        current_time = datetime.now()

    try:
        with get_db_session() as db:
            from app.models.service import ServiceTicket, ServiceTicketStatusEnum
            from app.services.sla_service import (
                check_sla_warnings,
                mark_warning_sent,
                sync_ticket_to_sla_monitor,
            )

            open_tickets = (
                db.query(ServiceTicket)
                .filter(ServiceTicket.status != ServiceTicketStatusEnum.CLOSED.value)
                .order_by(ServiceTicket.reported_time.asc())
                .limit(500)
                .all()
            )

            synced_count = 0
            sync_error_count = 0
            for ticket in open_tickets:
                try:
                    if sync_ticket_to_sla_monitor(db, ticket, current_time=current_time):
                        synced_count += 1
                except Exception as exc:
                    sync_error_count += 1
                    logger.error(
                        f"SLA 工单同步失败 ticket_id={getattr(ticket, 'id', None)}: {exc}",
                        exc_info=True,
                    )

            warning_monitors = check_sla_warnings(db, current_time=current_time)
            alerts_created = 0
            response_warnings_sent = 0
            resolve_warnings_sent = 0

            for monitor in warning_monitors:
                if (
                    monitor.actual_response_time is None
                    and monitor.response_status == "WARNING"
                    and not monitor.response_warning_sent
                ):
                    if _create_sla_warning_alert(db, monitor, "response", current_time):
                        alerts_created += 1
                    mark_warning_sent(db, monitor, "response")
                    response_warnings_sent += 1

                if (
                    monitor.actual_resolve_time is None
                    and monitor.resolve_status == "WARNING"
                    and not monitor.resolve_warning_sent
                ):
                    if _create_sla_warning_alert(db, monitor, "resolve", current_time):
                        alerts_created += 1
                    mark_warning_sent(db, monitor, "resolve")
                    resolve_warnings_sent += 1

            db.commit()

            logger.info(
                "SLA 预警扫描完成: 扫描 %s 个工单, 同步 %s 个 monitor, "
                "发现 %s 个预警 monitor, 创建 %s 条预警",
                len(open_tickets),
                synced_count,
                len(warning_monitors),
                alerts_created,
            )

            return {
                "tickets_scanned": len(open_tickets),
                "monitors_synced": synced_count,
                "sync_errors": sync_error_count,
                "warning_monitors": len(warning_monitors),
                "alerts_created": alerts_created,
                "response_warnings_sent": response_warnings_sent,
                "resolve_warnings_sent": resolve_warnings_sent,
                "timestamp": current_time.isoformat(),
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] SLA 预警扫描失败: {str(e)}", exc_info=True)
        return {"error": str(e)}


def check_alert_escalation():
    """
    S.10: 预警升级服务
    每小时执行一次，检查超时未处理的预警并自动升级
    """
    try:
        with get_db_session() as db:
            from app.services.alert.alert_escalation_service import AlertEscalationService

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
        return {"error": str(e)}


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
            failed_notifications = (
                db.query(AlertNotification)
                .filter(
                    AlertNotification.status == "FAILED",
                    AlertNotification.retry_count < max_retries,
                    or_(
                        AlertNotification.next_retry_at.is_(None),
                        AlertNotification.next_retry_at <= current_time,
                    ),
                )
                .all()
            )

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
                    notification.status = "ABANDONED"
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
                        notification.status = "ABANDONED"
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
                "retry_count": retry_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "abandoned_count": abandoned_count,
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] 通知重试失败: {str(e)}", exc_info=True)
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


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
            pending_alerts = (
                db.query(AlertRecord)
                .filter(AlertRecord.status == "PENDING")
                .order_by(AlertRecord.triggered_at.asc().nulls_last())
                .limit(50)
                .all()
            )

            queue_created = 0
            queued_from_alerts = 0
            sent_from_alerts = 0
            failed_from_alerts = 0
            opened_alerts = 0

            for alert in pending_alerts:
                result = dispatcher.dispatch_alert_notifications(alert=alert)
                queue_created += result.get("created", 0)
                queued_from_alerts += result.get("queued", 0)
                sent_from_alerts += result.get("sent", 0)
                failed_from_alerts += result.get("failed", 0)
                if alert.status == "PENDING":
                    alert.status = "OPEN"
                    opened_alerts += 1

            # 2) 发送通知（包含失败重试）
            now = datetime.now()
            pending_notifications = (
                db.query(AlertNotification)
                .filter(
                    AlertNotification.status.in_(["PENDING", "FAILED"]),
                    or_(
                        AlertNotification.next_retry_at.is_(None),
                        AlertNotification.next_retry_at <= now,
                    ),
                )
                .order_by(AlertNotification.created_at.asc())
                .limit(100)
                .all()
            )

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
                f"打开 {opened_alerts} 条预警, "
                f"处理 {len(pending_notifications)} 条通知, "
                f"入队 {queued_notifications} 条, 直接发送 {sent_count} 条"
            )

            return {
                "queued_alerts": len(pending_alerts),
                "queue_created": queue_created,
                "queued_from_alerts": queued_from_alerts,
                "sent_from_alerts": sent_from_alerts,
                "failed_from_alerts": failed_from_alerts,
                "opened_alerts": opened_alerts,
                "processed_notifications": len(pending_notifications),
                "queued_notifications": queued_notifications,
                "sent_count": sent_count,
                "timestamp": datetime.now().isoformat(),
            }

    except Exception as e:
        logger.error(f"[{datetime.now()}] 消息推送服务失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}


def calculate_response_metrics():
    """
    计算预警响应指标
    每天执行一次，统计预警响应时间等指标
    """
    try:
        with get_db_session() as db:
            from app.services.alert.alert_response_service import AlertResponseService

            service = AlertResponseService(db)
            result = service.calculate_daily_metrics()

            logger.info(f"[{datetime.now()}] 预警响应指标计算完成: {result}")

            return result
    except Exception as e:
        logger.error(f"[{datetime.now()}] 预警响应指标计算失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}
