# -*- coding: utf-8 -*-
"""旧路径兼容：app.services.timesheet_reminder.anomaly_reminders"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.timesheet import Timesheet
from app.services.timesheet.timesheet_quality_service import TimesheetQualityService
from app.services.timesheet.reminder.base import create_timesheet_notification

logger = logging.getLogger(__name__)


def notify_timesheet_anomaly(db: Session, days: int = 1) -> int:
    target_date = date.today() - timedelta(days=days)

    quality_service = TimesheetQualityService(db)
    anomalies = quality_service.detect_anomalies(start_date=target_date, end_date=date.today())

    reminder_count = 0
    notified_users = set()

    for anomaly in anomalies:
        timesheet = db.query(Timesheet).filter(Timesheet.id == anomaly.get("timesheet_id")).first()
        if not timesheet:
            continue

        user_id = timesheet.user_id
        if user_id in notified_users:
            continue

        existing_notification = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.notification_type == "TIMESHEET_ANOMALY",
                Notification.source_id == timesheet.id,
                Notification.created_at >= datetime.combine(date.today(), datetime.min.time()),
            )
            .first()
        )

        if existing_notification:
            continue

        create_timesheet_notification(
            db=db,
            user_id=user_id,
            notification_type="TIMESHEET_ANOMALY",
            title=f"异常工时预警：{anomaly.get('anomaly_type', '未知异常')}",
            content=f"您的工时记录（{timesheet.work_date}）存在异常：{anomaly.get('description', '')}，请检查并修正。",
            source_id=timesheet.id,
            priority="HIGH",
            extra_data={
                "timesheet_id": timesheet.id,
                "anomaly_type": anomaly.get("anomaly_type"),
                "description": anomaly.get("description"),
                "work_date": timesheet.work_date.isoformat(),
            },
        )
        notified_users.add(user_id)
        reminder_count += 1

    db.commit()
    logger.info(f"异常工时预警完成: 发送 {reminder_count} 条提醒")
    return reminder_count


__all__ = ["notify_timesheet_anomaly", "TimesheetQualityService", "create_timesheet_notification"]
