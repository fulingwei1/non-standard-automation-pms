# -*- coding: utf-8 -*-
"""
通知服务兼容层

统一入口，re-export 统一通知服务的核心接口，并提供旧代码所需的
AlertNotificationService 和 NotificationPriority。

通知系统架构：
- app.services.unified_notification_service: 主通知服务 (canonical)
- app.services.notification_service (本模块): 兼容层
- app.services.notification_dispatcher: 预警通知调度协调器
- app.services.notification_queue: Redis 通知队列
- app.services.notification_utils: 工具函数
- app.services.channel_handlers/: 渠道处理器
- app.services.notification_handlers/: 旧版通知处理器 (通过 unified_adapter 桥接)

新代码请直接使用:
    from app.services.unified_notification_service import get_notification_service
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence

from sqlalchemy.orm import Session

# ── Re-exports from unified service ──────────────────────────────────
from app.services.unified_notification_service import (  # noqa: F401
    NotificationService,
    get_notification_service,
    notification_service,
)
from app.services.channel_handlers.base import (  # noqa: F401
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
    NotificationResult,
)
from app.services.notification_dispatcher import NotificationDispatcher  # noqa: F401

logger = logging.getLogger(__name__)


class AlertNotificationService:
    """预警通知服务 — 对 NotificationDispatcher 的薄包装。

    旧代码通过本类发送预警通知:
        service = AlertNotificationService(db)
        service.send_alert_notification(alert=alert, user_ids=[...], channels=[...])
    """

    def __init__(self, db: Session):
        self.db = db
        self._dispatcher = NotificationDispatcher(db)

    def get_user_notifications(
        self,
        user_id: int,
        is_read: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """获取用户的预警通知列表（stub）。"""
        return {"success": True, "items": [], "total": 0}

    def get_unread_count(self, user_id: int) -> int:
        """获取用户未读通知数量（stub）。"""
        return 0

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """标记通知为已读（stub）。"""
        return True

    def batch_mark_read(self, notification_ids: list, user_id: int) -> Dict[str, Any]:
        """批量标记通知为已读（stub）。"""
        return {"success": True, "success_count": len(notification_ids)}

    def send_alert_notification(
        self,
        alert,
        user_ids: Optional[Sequence[int]] = None,
        channels: Optional[Sequence[str]] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
        force_send: bool = False,
    ) -> Dict[str, Any]:
        """发送预警通知（委托给 NotificationDispatcher）。"""
        return self._dispatcher.dispatch_alert_notifications(
            alert=alert,
            user_ids=user_ids,
            channels=channels,
            title=title,
            content=content,
            force_send=force_send,
        )


__all__ = [
    "AlertNotificationService",
    "NotificationService",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationRequest",
    "NotificationResult",
    "NotificationDispatcher",
    "get_notification_service",
    "notification_service",
]
