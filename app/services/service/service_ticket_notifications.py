# -*- coding: utf-8 -*-
"""Notification helpers for service ticket lifecycle events."""
import logging
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.service import ServiceTicket
from app.models.user import User
from app.services.notification.channels.base import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
)
from app.services.notification.unified_notification_service import get_notification_service

logger = logging.getLogger(__name__)


def _as_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _recipient_ids(ticket: ServiceTicket, extra_user_ids: Optional[Iterable[int]] = None) -> set[int]:
    recipient_ids: set[int] = set()
    if getattr(ticket, "assigned_to_id", None):
        recipient_ids.add(ticket.assigned_to_id)

    reporter_id = _as_int(getattr(ticket, "reported_by", None))
    if reporter_id:
        recipient_ids.add(reporter_id)

    if extra_user_ids:
        for user_id in extra_user_ids:
            if isinstance(user_id, int):
                recipient_ids.add(user_id)

    for cc_user in getattr(ticket, "cc_users", []) or []:
        user_id = getattr(cc_user, "user_id", None)
        if isinstance(user_id, int):
            recipient_ids.add(user_id)

    return {user_id for user_id in recipient_ids if user_id}


def _action_label(action: str) -> str:
    labels = {
        "created": "新建",
        "assigned": "已分配",
        "closed": "已关闭",
    }
    if action.startswith("status_changed_to_"):
        return f"状态变更为 {action.removeprefix('status_changed_to_')}"
    return labels.get(action, action)


def send_service_ticket_notification(
    db: Session,
    ticket: ServiceTicket,
    action: str,
    *,
    actor: Optional[User] = None,
    extra_user_ids: Optional[Iterable[int]] = None,
) -> dict:
    """Send system notifications for a service ticket event.

    Returns a small delivery summary so callers can persist notified_at only
    after a real notification was created.
    """
    recipient_ids = _recipient_ids(ticket, extra_user_ids)
    if not recipient_ids:
        return {"sent": 0, "sent_user_ids": []}

    action_label = _action_label(action)
    actor_name = getattr(actor, "real_name", None) or getattr(actor, "username", None)
    content_lines = [
        f"工单编号: {ticket.ticket_no}",
        f"问题类型: {ticket.problem_type}",
        f"状态: {ticket.status}",
        f"描述: {ticket.problem_desc or ''}",
    ]
    if actor_name:
        content_lines.append(f"操作人: {actor_name}")

    service = get_notification_service(db)
    sent_user_ids: list[int] = []
    priority = (
        NotificationPriority.HIGH
        if getattr(ticket, "urgency", "") in {"HIGH", "URGENT"}
        else NotificationPriority.NORMAL
    )

    for recipient_id in sorted(recipient_ids):
        request = NotificationRequest(
            recipient_id=recipient_id,
            notification_type=f"SERVICE_TICKET_{action.upper()}",
            category="service",
            title=f"服务工单{action_label}: {ticket.ticket_no}",
            content="\n".join(content_lines),
            priority=priority,
            channels=[NotificationChannel.SYSTEM],
            source_type="service_ticket",
            source_id=ticket.id,
            link_url=f"/service/tickets/{ticket.id}",
            extra_data={"ticket_id": ticket.id, "action": action},
            force_send=True,
        )
        try:
            result = service.send_notification(request)
        except Exception as exc:
            logger.error(
                "服务工单通知发送失败 ticket_id=%s recipient_id=%s action=%s: %s",
                ticket.id,
                recipient_id,
                action,
                exc,
                exc_info=True,
            )
            continue
        if result.get("success"):
            sent_user_ids.append(recipient_id)

    return {"sent": len(sent_user_ids), "sent_user_ids": sent_user_ids}
