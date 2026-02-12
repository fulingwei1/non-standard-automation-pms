# -*- coding: utf-8 -*-
"""
ECN通知服务 - 基础通知创建（使用统一NotificationService）

向后兼容：保持原有函数接口，内部使用统一通知服务
"""

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.services.notification_dispatcher import NotificationDispatcher
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationPriority,
)


def _map_priority_to_unified(priority: str) -> str:
    """映射ECN优先级到统一服务优先级"""
    priority_upper = priority.upper() if priority else "NORMAL"
    mapping = {
        "URGENT": NotificationPriority.URGENT,
        "HIGH": NotificationPriority.HIGH,
        "NORMAL": NotificationPriority.NORMAL,
        "LOW": NotificationPriority.LOW,
    }
    return mapping.get(priority_upper, NotificationPriority.NORMAL)


def create_ecn_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    content: str,
    ecn_id: int,
    priority: str = "NORMAL",
    extra_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建ECN相关通知（使用统一通知服务）
    
    向后兼容：返回结果字典，包含 success 字段
    """
    dispatcher = NotificationDispatcher(db)
    
    request = NotificationRequest(
        recipient_id=user_id,
        notification_type=notification_type,
        category="ecn",
        title=title,
        content=content,
        priority=_map_priority_to_unified(priority),
        source_type="ecn",
        source_id=ecn_id,
        link_url=f"/ecns?ecnId={ecn_id}",
        extra_data=extra_data or {},
    )
    
    result = dispatcher.send_notification_request(request)
    
    # 为了向后兼容，返回包含 success 的结果
    # 如果调用方需要 Notification 对象，可以从数据库查询
    return result
