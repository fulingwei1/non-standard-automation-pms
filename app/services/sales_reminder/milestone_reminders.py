# -*- coding: utf-8 -*-
"""
销售提醒服务 - 里程碑提醒
"""

from datetime import date, datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.project import ProjectMilestone
from app.services.sales_reminder.base import create_notification


def notify_milestone_upcoming(db: Session, days_before: int = 7) -> int:
    """
    提醒即将到期的里程碑
    """
    today = date.today()
    target_date = today + timedelta(days=days_before)

    # 查找即将到期的里程碑
    milestones = db.query(ProjectMilestone).filter(
        and_(
            ProjectMilestone.status == "PENDING",
            ProjectMilestone.planned_date <= target_date,
            ProjectMilestone.planned_date >= today
        )
    ).all()

    count = 0
    for milestone in milestones:
        if milestone.owner_id:
            # 检查是否已发送过提醒
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == milestone.owner_id,
                    Notification.source_type == "milestone",
                    Notification.source_id == milestone.id,
                    Notification.notification_type == "MILESTONE_UPCOMING",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                )
            ).first()

            if not existing:
                create_notification(
                    db=db,
                    user_id=milestone.owner_id,
                    notification_type="MILESTONE_UPCOMING",
                    title=f"里程碑即将到期：{milestone.milestone_name}",
                    content=f"里程碑 {milestone.milestone_code} 将在 {milestone.planned_date} 到期，请及时处理。",
                    source_type="milestone",
                    source_id=milestone.id,
                    link_url=f"/projects/{milestone.project_id}/milestones/{milestone.id}",
                    priority="HIGH" if days_before <= 3 else "NORMAL",
                    extra_data={
                        "milestone_code": milestone.milestone_code,
                        "planned_date": milestone.planned_date.isoformat(),
                        "days_left": (milestone.planned_date - today).days
                    }
                )
                count += 1

    return count


def notify_milestone_overdue(db: Session) -> int:
    """
    提醒已逾期的里程碑
    """
    today = date.today()

    # 查找已逾期的里程碑
    milestones = db.query(ProjectMilestone).filter(
        and_(
            ProjectMilestone.status == "PENDING",
            ProjectMilestone.planned_date < today
        )
    ).all()

    count = 0
    for milestone in milestones:
        if milestone.owner_id:
            # 检查今天是否已发送过提醒
            existing = db.query(Notification).filter(
                and_(
                    Notification.user_id == milestone.owner_id,
                    Notification.source_type == "milestone",
                    Notification.source_id == milestone.id,
                    Notification.notification_type == "MILESTONE_OVERDUE",
                    Notification.created_at >= datetime.combine(today, datetime.min.time())
                )
            ).first()

            if not existing:
                overdue_days = (today - milestone.planned_date).days
                create_notification(
                    db=db,
                    user_id=milestone.owner_id,
                    notification_type="MILESTONE_OVERDUE",
                    title=f"里程碑已逾期：{milestone.milestone_name}",
                    content=f"里程碑 {milestone.milestone_code} 已逾期 {overdue_days} 天，请尽快处理。",
                    source_type="milestone",
                    source_id=milestone.id,
                    link_url=f"/projects/{milestone.project_id}/milestones/{milestone.id}",
                    priority="URGENT",
                    extra_data={
                        "milestone_code": milestone.milestone_code,
                        "planned_date": milestone.planned_date.isoformat(),
                        "overdue_days": overdue_days
                    }
                )
                count += 1

    return count
