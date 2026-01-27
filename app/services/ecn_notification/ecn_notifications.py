# -*- coding: utf-8 -*-
"""
ECN通知服务 - ECN提交和逾期通知（使用统一NotificationService）
包含：ECN提交通知、逾期提醒通知
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.ecn import Ecn
from app.models.project import ProjectMember

from app.services.unified_notification_service import get_notification_service
from app.services.channel_handlers.base import (
    NotificationRequest,
    NotificationChannel,
    NotificationPriority,
)


def notify_ecn_submitted(
    db: Session,
    ecn: Ecn
) -> None:
    """
    通知ECN提交
    通知申请人、项目相关人员和其他相关人员
    """
    unified_service = get_notification_service(db)
    # 通知申请人确认提交
    if ecn.applicant_id:
        title = f"ECN已提交：{ecn.ecn_no}"
        content = f"您的ECN {ecn.ecn_no} 已成功提交，已进入评估流程。"

        request = NotificationRequest(
            recipient_id=ecn.applicant_id,
            notification_type="ECN_SUBMITTED",
            category="ecn",
            title=title,
            content=content,
            priority=NotificationPriority.NORMAL,
            source_type="ecn",
            source_id=ecn.id,
            link_url=f"/ecns?ecnId={ecn.id}",
            extra_data={
                "ecn_no": ecn.ecn_no,
                "ecn_title": ecn.ecn_title
            }
        )
        unified_service.send_notification(request)

    # 抄送项目相关人员（如果ECN关联了项目）
    if ecn.project_id:
        # 查找项目成员（排除申请人，避免重复通知）
        project_members = db.query(ProjectMember).filter(
            ProjectMember.project_id == ecn.project_id,
            ProjectMember.is_active == True,
            ProjectMember.user_id != ecn.applicant_id
        ).all()

        project_user_ids = [pm.user_id for pm in project_members]

        if project_user_ids:
            title = f"ECN已提交（抄送）：{ecn.ecn_no}"
            content = f"项目相关的ECN {ecn.ecn_no} 已提交，已进入评估流程。\n\nECN标题：{ecn.ecn_title}\n变更类型：{ecn.ecn_type}\n变更原因：{ecn.change_reason}\n\n请关注项目变更情况。"

            for user_id in project_user_ids:
                request = NotificationRequest(
                    recipient_id=user_id,
                    notification_type="ECN_SUBMITTED",
                    category="ecn",
                    title=title,
                    content=content,
                    priority=NotificationPriority.NORMAL,
                    source_type="ecn",
                    source_id=ecn.id,
                    link_url=f"/ecns?ecnId={ecn.id}",
                    extra_data={
                        "ecn_no": ecn.ecn_no,
                        "ecn_title": ecn.ecn_title,
                        "is_cc": True  # 标记为抄送
                    }
                )
                unified_service.send_notification(request)


def notify_overdue_alert(
    db: Session,
    alert: Dict[str, Any],
    user_ids: List[int]
) -> None:
    """
    通知超时提醒（使用统一通知服务）
    """
    unified_service = get_notification_service(db)
    priority = NotificationPriority.URGENT if alert.get('overdue_days', 0) > 7 else NotificationPriority.HIGH
    
    for user_id in user_ids:
        title = f"ECN超时提醒：{alert.get('ecn_no', '')}"
        content = alert.get('message', '')

        request = NotificationRequest(
            recipient_id=user_id,
            notification_type="ECN_OVERDUE_ALERT",
            category="ecn",
            title=title,
            content=content,
            priority=priority,
            source_type="ecn",
            source_id=alert.get('ecn_id'),
            link_url=f"/ecns?ecnId={alert.get('ecn_id')}" if alert.get('ecn_id') else None,
            extra_data={
                "alert_type": alert.get('type'),
                "overdue_days": alert.get('overdue_days', 0),
                "ecn_no": alert.get('ecn_no')
            }
        )
        unified_service.send_notification(request)
