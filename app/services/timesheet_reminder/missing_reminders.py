# -*- coding: utf-8 -*-
"""
工时缺失提醒

提供每日和周工时填报提醒功能
"""

"""
工时提醒服务
提供工时填报提醒、异常工时预警、审批超时提醒等功能
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from app.services.timesheet_reminder.base import create_timesheet_notification

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.timesheet import Timesheet
from app.models.user import User

logger = logging.getLogger(__name__)



def notify_timesheet_missing(db: Session, target_date: Optional[date] = None) -> int:
    """
    提醒未填报工时的用户

    Args:
        db: 数据库会话
        target_date: 目标日期（默认为昨天）

    Returns:
        发送的提醒数量
    """
    if target_date is None:
        target_date = date.today() - timedelta(days=1)

    # 获取所有活跃的工程师用户（需要填报工时的用户）
    # 通过UserRole关联查询，或者通过部门名称筛选
    from app.models.organization import Department
    from app.models.user import Role, UserRole

    # 查找工程师相关的角色ID
    engineer_roles = (
        db.query(Role)
        .filter(
            Role.role_name.in_(
                [
                    "engineer",
                    "mechanical_engineer",
                    "test_engineer",
                    "plc_engineer",
                    "rd_engineer",
                    "electrical_engineer",
                    "software_engineer",
                ]
            )
        )
        .all()
    )
    engineer_role_ids = [r.id for r in engineer_roles]

    # 查找技术相关部门的ID
    tech_departments = (
        db.query(Department)
        .filter(Department.dept_name.in_(["技术部", "研发部", "工程部", "研发中心"]))
        .all()
    )
    tech_dept_ids = [d.id for d in tech_departments]

    # 查询用户：通过角色或部门
    user_ids_by_role = []
    if engineer_role_ids:
        user_roles = (
            db.query(UserRole).filter(UserRole.role_id.in_(engineer_role_ids)).all()
        )
        user_ids_by_role = [ur.user_id for ur in user_roles]

    engineers = (
        db.query(User)
        .filter(
            User.is_active,
            or_(
                User.id.in_(user_ids_by_role) if user_ids_by_role else False,
                User.department_id.in_(tech_dept_ids) if tech_dept_ids else False,
            ),
        )
        .all()
    )

    reminder_count = 0
    today = datetime.now().date()

    for engineer in engineers:
        # 检查该日期是否已有工时记录
        existing = (
            db.query(Timesheet)
            .filter(
                Timesheet.user_id == engineer.id, Timesheet.work_date == target_date
            )
            .first()
        )

        if existing:
            continue

        # 检查今天是否已发送过提醒
        # 使用JSON字段查询需要特殊处理

        existing_notification = (
            db.query(Notification)
            .filter(
                Notification.user_id == engineer.id,
                Notification.notification_type == "TIMESHEET_MISSING",
                Notification.created_at >= datetime.combine(today, datetime.min.time()),
            )
            .first()
        )

        # 进一步检查extra_data中的target_date
        if existing_notification:
            extra_data = existing_notification.extra_data or {}
            if extra_data.get("target_date") == target_date.isoformat():
                continue

        if existing_notification:
            continue

        # 创建提醒通知
        create_timesheet_notification(
            db=db,
            user_id=engineer.id,
            notification_type="TIMESHEET_MISSING",
            title=f"工时填报提醒：{target_date.strftime('%Y-%m-%d')}",
            content=f"您还未填报 {target_date.strftime('%Y年%m月%d日')} 的工时，请及时填报。",
            priority="NORMAL",
            extra_data={
                "target_date": target_date.isoformat(),
                "user_name": engineer.real_name or engineer.username,
            },
        )
        reminder_count += 1

    db.commit()
    logger.info(
        f"工时填报提醒完成: 发送 {reminder_count} 条提醒（目标日期: {target_date}）"
    )

    return reminder_count


def notify_weekly_timesheet_missing(
    db: Session, week_start: Optional[date] = None
) -> int:
    """
    提醒未完成周工时填报的用户

    Args:
        db: 数据库会话
        week_start: 周开始日期（默认为上周一）

    Returns:
        发送的提醒数量
    """
    if week_start is None:
        today = date.today()
        # 计算上周一
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday + 7)

    week_end = week_start + timedelta(days=6)

    # 获取所有活跃的工程师用户
    from app.models.organization import Department
    from app.models.user import Role, UserRole

    # 查找工程师相关的角色ID
    engineer_roles = (
        db.query(Role)
        .filter(
            Role.role_name.in_(
                [
                    "engineer",
                    "mechanical_engineer",
                    "test_engineer",
                    "plc_engineer",
                    "rd_engineer",
                    "electrical_engineer",
                    "software_engineer",
                ]
            )
        )
        .all()
    )
    engineer_role_ids = [r.id for r in engineer_roles]

    # 查找技术相关部门的ID
    tech_departments = (
        db.query(Department)
        .filter(Department.dept_name.in_(["技术部", "研发部", "工程部", "研发中心"]))
        .all()
    )
    tech_dept_ids = [d.id for d in tech_departments]

    # 查询用户：通过角色或部门
    user_ids_by_role = []
    if engineer_role_ids:
        user_roles = (
            db.query(UserRole).filter(UserRole.role_id.in_(engineer_role_ids)).all()
        )
        user_ids_by_role = [ur.user_id for ur in user_roles]

    engineers = (
        db.query(User)
        .filter(
            User.is_active,
            or_(
                User.id.in_(user_ids_by_role) if user_ids_by_role else False,
                User.department_id.in_(tech_dept_ids) if tech_dept_ids else False,
            ),
        )
        .all()
    )

    reminder_count = 0
    today = datetime.now().date()

    for engineer in engineers:
        # 检查该周是否有工时记录
        timesheet_count = (
            db.query(Timesheet)
            .filter(
                Timesheet.user_id == engineer.id,
                Timesheet.work_date >= week_start,
                Timesheet.work_date <= week_end,
            )
            .count()
        )

        # 如果该周有5天以上有工时记录，认为已填报
        if timesheet_count >= 5:
            continue

        # 检查今天是否已发送过提醒
        existing_notification = (
            db.query(Notification)
            .filter(
                Notification.user_id == engineer.id,
                Notification.notification_type == "TIMESHEET_WEEKLY_MISSING",
                Notification.created_at >= datetime.combine(today, datetime.min.time()),
            )
            .first()
        )

        # 进一步检查extra_data中的week_start
        if existing_notification:
            extra_data = existing_notification.extra_data or {}
            if extra_data.get("week_start") == week_start.isoformat():
                continue

        if existing_notification:
            continue

        # 创建提醒通知
        create_timesheet_notification(
            db=db,
            user_id=engineer.id,
            notification_type="TIMESHEET_WEEKLY_MISSING",
            title=f"周工时填报提醒：{week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}",
            content=f"您还未完成上周（{week_start.strftime('%m月%d日')} ~ {week_end.strftime('%m月%d日')}）的工时填报，请及时补填。",
            priority="HIGH",
            extra_data={
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
                "timesheet_count": timesheet_count,
                "user_name": engineer.real_name or engineer.username,
            },
        )
        reminder_count += 1

    db.commit()
    logger.info(
        f"周工时填报提醒完成: 发送 {reminder_count} 条提醒（周: {week_start} ~ {week_end}）"
    )

    return reminder_count


