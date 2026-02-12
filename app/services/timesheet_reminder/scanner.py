# -*- coding: utf-8 -*-
"""
工时提醒扫描器

提供扫描所有需要提醒的事项并发送通知的功能
"""

"""
工时提醒服务
提供工时填报提醒、异常工时预警、审批超时提醒等功能
"""

import logging
from typing import Dict

from sqlalchemy.orm import Session

from app.services.timesheet_reminder.missing_reminders import notify_timesheet_missing, notify_weekly_timesheet_missing
from app.services.timesheet_reminder.anomaly_reminders import notify_timesheet_anomaly
from app.services.timesheet_reminder.approval_reminders import notify_approval_timeout
from app.services.timesheet_reminder.sync_reminders import notify_sync_failure

logger = logging.getLogger(__name__)



def scan_and_notify_all(db: Session) -> Dict[str, int]:
    """
    扫描所有需要提醒的事项并发送通知

    Returns:
        统计信息字典
    """
    stats = {
        "daily_missing": 0,
        "weekly_missing": 0,
        "anomaly": 0,
        "approval_timeout": 0,
        "sync_failure": 0,
    }

    try:
        # 每日工时填报提醒（提醒昨天的）
        stats["daily_missing"] = notify_timesheet_missing(db)

        # 周工时填报提醒（提醒上周的）
        stats["weekly_missing"] = notify_weekly_timesheet_missing(db)

        # 异常工时预警
        stats["anomaly"] = notify_timesheet_anomaly(db, days=1)

        # 审批超时提醒
        stats["approval_timeout"] = notify_approval_timeout(db, timeout_hours=24)

        # 数据同步失败提醒
        stats["sync_failure"] = notify_sync_failure(db)

        db.commit()

    except Exception as e:
        logger.error(f"工时提醒服务扫描失败: {str(e)}")
        import traceback

        traceback.print_exc()
        db.rollback()

    return stats
