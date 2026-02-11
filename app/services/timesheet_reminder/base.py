# -*- coding: utf-8 -*-
"""
工时提醒服务 - 基础工具

提供创建通知等基础功能
"""

"""
工时提醒服务
提供工时填报提醒、异常工时预警、审批超时提醒等功能
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.notification_dispatcher import NotificationDispatcher
from app.services.timesheet_quality_service import TimesheetQualityService

logger = logging.getLogger(__name__)



def create_timesheet_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    content: str,
    source_type: str = "timesheet",
    source_id: Optional[int] = None,
    link_url: Optional[str] = None,
    priority: str = "NORMAL",
    extra_data: Optional[dict] = None,
) -> object:
    """
    创建工时相关通知
    """
    dispatcher = NotificationDispatcher(db)
    return dispatcher.create_system_notification(
        recipient_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type=source_type,
        source_id=source_id,
        link_url=link_url or "/timesheet",
        priority=priority,
        extra_data=extra_data or {},
    )

