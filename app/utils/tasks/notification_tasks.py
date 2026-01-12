# -*- coding: utf-8 -*-
"""
通知和杂项定时任务

包含通知重试、消息推送、响应时效计算、设备保养提醒、员工确认提醒等
"""

import logging
from datetime import datetime, date, timedelta

from sqlalchemy import or_

from app.models.base import get_db_session
from app.models.alert import AlertRecord, AlertRule, AlertNotification
from app.models.enums import AlertLevelEnum, AlertStatusEnum
from app.services.notification_dispatcher import (
    NotificationDispatcher,
    is_quiet_hours,
    next_quiet_resume,
)

logger = logging.getLogger(__name__)


def check_alert_escalation():
    """
    S.10: 预警升级服务
    每小时执行一次，检查超时未处理的预警并自动升级
    """
    from app.utils.alert_escalation_task import check_alert_timeout_escalation
    return check_alert_timeout_escalation()


def retry_failed_notifications():
    """
    Issue 1.3: 通知重试机制
    每小时执行一次，重试发送失败的通知
    """
    try:
        with get_db_session() as db:
            from app.models.user import User
            from app.models.notification import NotificationSettings

            current_time = datetime.now()
            max_retries = 3

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

            dispatcher = NotificationDispatcher(db)

            for notification in failed_notifications:
                settings = None
                if notification.notify_user_id:
                    settings = db.query(NotificationSettings).filter(
                        NotificationSettings.user_id == notification.notify_user_id
                    ).first()

                if is_quiet_hours(settings, current_time):
                    notification.next_retry_at = next_quiet_resume(settings, current_time)
                    notification.error_message = "Delayed due to quiet hours"
                    continue

                alert = notification.alert
                user = None
                if notification.notify_user_id:
                    user = db.query(User).filter(User.id == notification.notify_user_id).first()

                if not alert or not user:
                    notification.status = 'ABANDONED'
                    notification.error_message = "Alert or user not found"
                    continue

                try:
                    notification.retry_count += 1
                    retry_count += 1

                    result = dispatcher.send_notification(
                        alert=alert,
                        user=user,
                        channel=notification.channel
                    )

                    if result.get('success'):
                        notification.status = 'SENT'
                        notification.sent_at = datetime.now()
                        notification.error_message = None
                        success_count += 1
                    else:
                        notification.status = 'FAILED'
                        notification.error_message = result.get('error', 'Unknown error')
                        notification.next_retry_at = current_time + timedelta(minutes=30 * notification.retry_count)
                        failed_count += 1
                except Exception as e:
                    notification.status = 'FAILED'
                    notification.error_message = str(e)
                    notification.next_retry_at = current_time + timedelta(minutes=30 * notification.retry_count)
                    failed_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 通知重试完成: 重试 {retry_count} 条, 成功 {success_count} 条, 失败 {failed_count} 条")

            return {
                'retry_count': retry_count,
                'success_count': success_count,
                'failed_count': failed_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 通知重试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def send_alert_notifications():
    """
    消息推送服务
    每10分钟执行一次，发送待发送的预警通知
    """
    try:
        with get_db_session() as db:
            from app.models.user import User

            pending_notifications = db.query(AlertNotification).filter(
                AlertNotification.status == 'PENDING'
            ).limit(100).all()

            sent_count = 0
            failed_count = 0

            dispatcher = NotificationDispatcher(db)

            for notification in pending_notifications:
                alert = notification.alert
                user = None
                if notification.notify_user_id:
                    user = db.query(User).filter(User.id == notification.notify_user_id).first()

                if not alert or not user:
                    notification.status = 'ABANDONED'
                    continue

                try:
                    result = dispatcher.send_notification(
                        alert=alert,
                        user=user,
                        channel=notification.channel
                    )

                    if result.get('success'):
                        notification.status = 'SENT'
                        notification.sent_at = datetime.now()
                        sent_count += 1
                    else:
                        notification.status = 'FAILED'
                        notification.error_message = result.get('error', 'Unknown error')
                        notification.retry_count = 0
                        notification.next_retry_at = datetime.now() + timedelta(minutes=30)
                        failed_count += 1
                except Exception as e:
                    notification.status = 'FAILED'
                    notification.error_message = str(e)
                    failed_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 消息推送完成: 发送 {sent_count} 条, 失败 {failed_count} 条")

            return {
                'sent_count': sent_count,
                'failed_count': failed_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 消息推送失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def calculate_response_metrics():
    """
    计算响应时效指标
    每天凌晨执行，计算各类响应时效统计
    """
    try:
        with get_db_session() as db:
            from sqlalchemy import func

            today = date.today()
            yesterday = today - timedelta(days=1)

            # 计算预警响应时效
            alerts = db.query(AlertRecord).filter(
                AlertRecord.triggered_at >= datetime.combine(yesterday, datetime.min.time()),
                AlertRecord.triggered_at < datetime.combine(today, datetime.min.time()),
                AlertRecord.status.in_(['RESOLVED', 'IGNORED'])
            ).all()

            total_response_time = 0
            resolved_count = 0

            for alert in alerts:
                if alert.resolved_at and alert.triggered_at:
                    response_time = (alert.resolved_at - alert.triggered_at).total_seconds() / 3600
                    total_response_time += response_time
                    resolved_count += 1

            avg_response_time = total_response_time / resolved_count if resolved_count > 0 else 0

            logger.info(f"[{datetime.now()}] 响应时效计算完成: 平均响应时间 {avg_response_time:.2f} 小时")

            return {
                'date': yesterday.isoformat(),
                'total_alerts': len(alerts),
                'resolved_count': resolved_count,
                'avg_response_time_hours': round(avg_response_time, 2),
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 响应时效计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_equipment_maintenance_reminder():
    """
    S.16: 设备保养提醒服务
    每天上午8:30执行，检查设备保养计划并发送提醒
    """
    try:
        with get_db_session() as db:
            from app.models.production import Equipment
            from app.models.notification import Notification
            from app.models.user import User
            from app.services.sales_reminder_service import create_notification

            today = date.today()
            target_date = today + timedelta(days=7)

            equipment_list = db.query(Equipment).filter(
                Equipment.is_active == True,
                Equipment.next_maintenance_date.isnot(None),
                Equipment.next_maintenance_date >= today,
                Equipment.next_maintenance_date <= target_date
            ).all()

            reminder_count = 0

            for equipment in equipment_list:
                if not equipment.next_maintenance_date:
                    continue

                days_until_maintenance = (equipment.next_maintenance_date - today).days

                existing = db.query(Notification).filter(
                    Notification.source_type == "equipment",
                    Notification.source_id == equipment.id,
                    Notification.notification_type == "EQUIPMENT_MAINTENANCE_REMINDER",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                ).first()

                if existing:
                    continue

                if days_until_maintenance <= 1:
                    priority = "URGENT"
                elif days_until_maintenance <= 3:
                    priority = "HIGH"
                else:
                    priority = "NORMAL"

                # 发送给管理员
                recipients = db.query(User).filter(
                    User.is_active == True,
                    User.is_superuser == True
                ).limit(3).all()

                for recipient in recipients:
                    create_notification(
                        db=db,
                        user_id=recipient.id,
                        notification_type="EQUIPMENT_MAINTENANCE_REMINDER",
                        title=f"设备保养提醒：{equipment.equipment_name}",
                        content=f"设备 {equipment.equipment_code}（{equipment.equipment_name}）将在 {days_until_maintenance} 天后进行保养，保养日期：{equipment.next_maintenance_date}，请提前安排。",
                        source_type="equipment",
                        source_id=equipment.id,
                        link_url=f"/production/equipment/{equipment.id}",
                        priority=priority
                    )
                    reminder_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 设备保养提醒服务完成: 检查 {len(equipment_list)} 台设备, 发送 {reminder_count} 条提醒")

            return {
                'checked_count': len(equipment_list),
                'reminder_count': reminder_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 设备保养提醒服务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def check_employee_confirmation_reminder():
    """
    员工转正提醒服务
    每天执行，检查即将转正的员工
    """
    try:
        with get_db_session() as db:
            from app.models.user import User
            from app.models.notification import Notification
            from app.services.sales_reminder_service import create_notification

            today = date.today()
            warning_date = today + timedelta(days=7)

            # 查询即将转正的员工
            employees = db.query(User).filter(
                User.is_active == True,
                User.confirmation_date.isnot(None),
                User.confirmation_date >= today,
                User.confirmation_date <= warning_date
            ).all()

            reminder_count = 0

            for emp in employees:
                days_to_confirm = (emp.confirmation_date - today).days

                existing = db.query(Notification).filter(
                    Notification.source_type == "employee",
                    Notification.source_id == emp.id,
                    Notification.notification_type == "EMPLOYEE_CONFIRMATION_REMINDER",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                ).first()

                if not existing:
                    # 发送给HR和部门经理
                    hr_users = db.query(User).filter(
                        User.is_active == True,
                        User.is_superuser == True
                    ).limit(3).all()

                    for hr in hr_users:
                        create_notification(
                            db=db,
                            user_id=hr.id,
                            notification_type="EMPLOYEE_CONFIRMATION_REMINDER",
                            title=f"员工转正提醒：{emp.real_name or emp.username}",
                            content=f"员工 {emp.real_name or emp.username} 将在 {days_to_confirm} 天后（{emp.confirmation_date}）到达转正日期，请及时处理转正事宜。",
                            source_type="employee",
                            source_id=emp.id,
                            link_url=f"/hr/employees/{emp.id}",
                            priority="HIGH" if days_to_confirm <= 3 else "NORMAL"
                        )
                        reminder_count += 1

            db.commit()

            logger.info(f"[{datetime.now()}] 员工转正提醒完成: 检查 {len(employees)} 名员工, 发送 {reminder_count} 条提醒")

            return {
                'checked_count': len(employees),
                'reminder_count': reminder_count,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"[{datetime.now()}] 员工转正提醒失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}
