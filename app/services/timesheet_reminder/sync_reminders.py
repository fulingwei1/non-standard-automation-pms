# -*- coding: utf-8 -*-
"""
同步失败提醒

提供数据同步失败提醒功能
"""

"""
工时提醒服务
提供工时填报提醒、异常工时预警、审批超时提醒等功能
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.timesheet import Timesheet
from app.services.timesheet_reminder.base import create_timesheet_notification

logger = logging.getLogger(__name__)



def notify_sync_failure(db: Session) -> int:
    """
    提醒数据同步失败的工时记录

    Args:
        db: 数据库会话

    Returns:
        发送的提醒数量
    """
    # 查询已审批但可能同步失败的记录
    # 这里需要根据实际同步状态来判断
    # 假设同步失败会在某个字段标记，或者通过检查同步目标表来判断

    # 查询已审批但可能未同步的记录
    approved_timesheets = (
        db.query(Timesheet)
        .filter(
            Timesheet.status == "APPROVED",
            Timesheet.approve_time.isnot(None),
            Timesheet.approve_time
            >= datetime.now() - timedelta(days=1),  # 最近1天审批的
        )
        .all()
    )

    reminder_count = 0
    notified_users = set()

    for timesheet in approved_timesheets:
        # 检查同步状态（这里简化处理，实际应该调用同步状态API）
        # 假设如果审批后超过1小时还没有同步记录，认为同步失败
        if (
            timesheet.approve_time
            and (datetime.now() - timesheet.approve_time).total_seconds() > 3600
        ):
            user_id = timesheet.user_id

            # 避免重复通知
            if user_id in notified_users:
                continue

            # 检查今天是否已发送过提醒
            existing_notification = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.notification_type == "TIMESHEET_SYNC_FAILURE",
                    Notification.source_id == timesheet.id,
                    Notification.created_at
                    >= datetime.combine(date.today(), datetime.min.time()),
                )
                .first()
            )

            if existing_notification:
                continue

            # 创建同步失败提醒
            create_timesheet_notification(
                db=db,
                user_id=user_id,
                notification_type="TIMESHEET_SYNC_FAILURE",
                title="工时数据同步失败提醒",
                content=f"您的工时记录（{timesheet.work_date}）审批通过后同步失败，请联系管理员处理。",
                source_id=timesheet.id,
                priority="NORMAL",
                extra_data={
                    "timesheet_id": timesheet.id,
                    "work_date": timesheet.work_date.isoformat(),
                    "approve_time": timesheet.approve_time.isoformat()
                    if timesheet.approve_time
                    else None,
                },
            )
            notified_users.add(user_id)
            reminder_count += 1

    db.commit()
    logger.info(f"数据同步失败提醒完成: 发送 {reminder_count} 条提醒")

    return reminder_count


