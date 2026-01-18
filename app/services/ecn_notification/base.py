# -*- coding: utf-8 -*-
"""
ECN通知服务 - 基础通知创建
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification


def create_ecn_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    content: str,
    ecn_id: int,
    priority: str = "NORMAL",
    extra_data: Optional[Dict[str, Any]] = None
) -> Notification:
    """
    创建ECN相关通知
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type="ECN",
        source_id=ecn_id,
        link_url=f"/ecns?ecnId={ecn_id}",
        priority=priority,
        extra_data=extra_data or {}
    )
    db.add(notification)
    return notification
