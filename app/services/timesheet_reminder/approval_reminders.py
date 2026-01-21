# -*- coding: utf-8 -*-
"""
审批超时提醒

提供工时审批超时提醒功能
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

from app.models.notification import Notification
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.timesheet_quality_service import TimesheetQualityService

logger = logging.getLogger(__name__)



def notify_approval_timeout(db: Session, timeout_hours: int = 24) -> int:
    """
    提醒审批超时的工时记录

    Args:
        db: 数据库会话
        timeout_hours: 超时时间（小时，默认24小时）

    Returns:
        发送的提醒数量
    """
    timeout_threshold = datetime.now() - timedelta(hours=timeout_hours)

    # 查询待审批且超过超时阈值的工时记录
    pending_timesheets = (
        db.query(Timesheet)
        .filter(
            Timesheet.status == "PENDING", Timesheet.created_at <= timeout_threshold
        )
        .all()
    )

    reminder_count = 0
    notified_approvers = {}  # {approver_id: [timesheet_ids]}

    for timesheet in pending_timesheets:
        # 获取审批人（通常是部门经理或项目经理）
        approver_id = None

        # 尝试从用户部门获取部门经理
        user = db.query(User).filter(User.id == timesheet.user_id).first()
        if user and hasattr(user, "department_id") and user.department_id:
            from app.models.organization import Department

            department = (
                db.query(Department).filter(Department.id == user.department_id).first()
            )
            if department and department.manager_id:
                approver_id = department.manager_id

        # 如果没有部门经理，尝试从项目获取项目经理
        if not approver_id and timesheet.project_id:
            from app.models.project import Project

            project = (
                db.query(Project).filter(Project.id == timesheet.project_id).first()
            )
            if project and project.manager_id:
                approver_id = project.manager_id

        if not approver_id:
            continue

        # 收集同一审批人的待审批记录
        if approver_id not in notified_approvers:
            notified_approvers[approver_id] = []
        notified_approvers[approver_id].append(timesheet.id)

    # 为每个审批人发送一条汇总通知
    for approver_id, timesheet_ids in notified_approvers.items():
        # 检查今天是否已发送过提醒
        existing_notification = (
            db.query(Notification)
            .filter(
                Notification.user_id == approver_id,
                Notification.notification_type == "TIMESHEET_APPROVAL_TIMEOUT",
                Notification.created_at
                >= datetime.combine(date.today(), datetime.min.time()),
            )
            .first()
        )

        if existing_notification:
            continue

        # 创建审批超时提醒
        create_timesheet_notification(
            db=db,
            user_id=approver_id,
            notification_type="TIMESHEET_APPROVAL_TIMEOUT",
            title=f"工时审批超时提醒：{len(timesheet_ids)} 条记录待审批",
            content=f"您有 {len(timesheet_ids)} 条工时记录超过 {timeout_hours} 小时未审批，请及时处理。",
            priority="HIGH",
            extra_data={
                "timesheet_ids": timesheet_ids,
                "timeout_hours": timeout_hours,
                "count": len(timesheet_ids),
            },
        )
        reminder_count += 1

    db.commit()
    logger.info(
        f"审批超时提醒完成: 发送 {reminder_count} 条提醒（{len(pending_timesheets)} 条待审批记录）"
    )

    return reminder_count


