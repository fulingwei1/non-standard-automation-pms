# -*- coding: utf-8 -*-
"""
定时任务基础模块

包含公共导入、辅助函数和基础设施
"""

from typing import List, Optional
from sqlalchemy import or_, func
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from app.models.base import get_db_session
from app.models.project import Project, ProjectMilestone, ProjectCost
from app.models.technical_spec import TechnicalSpecRequirement, SpecMatchRecord
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.material import BomHeader, BomItem
from app.models.issue import Issue, IssueStatisticsSnapshot
from app.models.alert import AlertRecord, AlertRule, AlertNotification, AlertStatistics
from app.models.enums import AlertLevelEnum, AlertStatusEnum, AlertRuleTypeEnum

from app.services.notification_dispatcher import (
    NotificationDispatcher,
    resolve_channels,
    resolve_recipients,
    resolve_channel_target,
    channel_allowed,
    is_quiet_hours,
    next_quiet_resume,
)
from app.services.notification_queue import enqueue_notification
from app.services.notification_service import AlertNotificationService, send_alert_notification

logger = logging.getLogger(__name__)


# ==================== 预警通知集成辅助函数 ====================

def send_notification_for_alert(db: Session, alert: AlertRecord, logger_instance=None):
    """
    为预警发送通知的辅助函数
    通知发送失败不影响预警记录创建

    Args:
        db: 数据库会话
        alert: 预警记录
        logger_instance: 日志记录器（可选）
    """
    if logger_instance is None:
        logger_instance = logger

    try:
        notification_service = AlertNotificationService(db)
        notification_result = notification_service.send_alert_notification(alert)
        if notification_result.get('success'):
            logger_instance.debug(
                f"Notification sent for alert {alert.alert_no}: "
                f"created={notification_result.get('notifications_created', 0)}, "
                f"sent={notification_result.get('notifications_sent', 0)}"
            )
        else:
            logger_instance.warning(
                f"Failed to send notification for alert {alert.alert_no}: "
                f"{notification_result.get('message')}"
            )
    except Exception as notif_err:
        # 通知发送失败不影响预警记录创建
        logger_instance.error(
            f"Error sending notification for alert {alert.alert_no}: {str(notif_err)}",
            exc_info=True
        )


def generate_alert_no(db: Session, prefix: str = "ALT") -> str:
    """生成预警编号"""
    today = datetime.now().strftime("%Y%m%d")
    # 查询今天已有的预警数量
    count = db.query(AlertRecord).filter(
        AlertRecord.alert_no.like(f"{prefix}{today}%")
    ).count()
    return f"{prefix}{today}{count + 1:04d}"
