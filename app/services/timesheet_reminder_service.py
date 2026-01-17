# -*- coding: utf-8 -*-
"""
工时提醒服务
提供工时填报提醒、异常工时预警、审批超时提醒等功能
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models.alert import AlertLevelEnum, AlertRecord, AlertRule, AlertRuleTypeEnum
from app.models.notification import Notification
from app.models.timesheet import Timesheet, TimesheetApprovalLog
from app.models.user import User
from app.services.notification_service import AlertNotificationService
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
    extra_data: Optional[dict] = None
) -> Notification:
    """
    创建工时相关通知
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type=source_type,
        source_id=source_id,
        link_url=link_url or "/timesheet",
        priority=priority,
        extra_data=extra_data or {}
    )
    db.add(notification)
    return notification


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
    engineer_roles = db.query(Role).filter(
        Role.role_name.in_(['engineer', 'mechanical_engineer', 'test_engineer', 'plc_engineer', 'rd_engineer', 'electrical_engineer', 'software_engineer'])
    ).all()
    engineer_role_ids = [r.id for r in engineer_roles]

    # 查找技术相关部门的ID
    tech_departments = db.query(Department).filter(
        Department.name.in_(['技术部', '研发部', '工程部', '研发中心'])
    ).all()
    tech_dept_ids = [d.id for d in tech_departments]

    # 查询用户：通过角色或部门
    user_ids_by_role = []
    if engineer_role_ids:
        user_roles = db.query(UserRole).filter(UserRole.role_id.in_(engineer_role_ids)).all()
        user_ids_by_role = [ur.user_id for ur in user_roles]

    engineers = db.query(User).filter(
        User.is_active == True,
        or_(
            User.id.in_(user_ids_by_role) if user_ids_by_role else False,
            User.department_id.in_(tech_dept_ids) if tech_dept_ids else False
        )
    ).all()

    reminder_count = 0
    today = datetime.now().date()

    for engineer in engineers:
        # 检查该日期是否已有工时记录
        existing = db.query(Timesheet).filter(
            Timesheet.user_id == engineer.id,
            Timesheet.work_date == target_date
        ).first()

        if existing:
            continue

        # 检查今天是否已发送过提醒
        # 使用JSON字段查询需要特殊处理
        from sqlalchemy import String, cast
        existing_notification = db.query(Notification).filter(
            Notification.user_id == engineer.id,
            Notification.notification_type == "TIMESHEET_MISSING",
            Notification.created_at >= datetime.combine(today, datetime.min.time())
        ).first()

        # 进一步检查extra_data中的target_date
        if existing_notification:
            extra_data = existing_notification.extra_data or {}
            if extra_data.get('target_date') == target_date.isoformat():
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
                "user_name": engineer.real_name or engineer.username
            }
        )
        reminder_count += 1

    db.commit()
    logger.info(f"工时填报提醒完成: 发送 {reminder_count} 条提醒（目标日期: {target_date}）")

    return reminder_count


def notify_weekly_timesheet_missing(db: Session, week_start: Optional[date] = None) -> int:
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
    engineer_roles = db.query(Role).filter(
        Role.role_name.in_(['engineer', 'mechanical_engineer', 'test_engineer', 'plc_engineer', 'rd_engineer', 'electrical_engineer', 'software_engineer'])
    ).all()
    engineer_role_ids = [r.id for r in engineer_roles]

    # 查找技术相关部门的ID
    tech_departments = db.query(Department).filter(
        Department.name.in_(['技术部', '研发部', '工程部', '研发中心'])
    ).all()
    tech_dept_ids = [d.id for d in tech_departments]

    # 查询用户：通过角色或部门
    user_ids_by_role = []
    if engineer_role_ids:
        user_roles = db.query(UserRole).filter(UserRole.role_id.in_(engineer_role_ids)).all()
        user_ids_by_role = [ur.user_id for ur in user_roles]

    engineers = db.query(User).filter(
        User.is_active == True,
        or_(
            User.id.in_(user_ids_by_role) if user_ids_by_role else False,
            User.department_id.in_(tech_dept_ids) if tech_dept_ids else False
        )
    ).all()

    reminder_count = 0
    today = datetime.now().date()

    for engineer in engineers:
        # 检查该周是否有工时记录
        timesheet_count = db.query(Timesheet).filter(
            Timesheet.user_id == engineer.id,
            Timesheet.work_date >= week_start,
            Timesheet.work_date <= week_end
        ).count()

        # 如果该周有5天以上有工时记录，认为已填报
        if timesheet_count >= 5:
            continue

        # 检查今天是否已发送过提醒
        existing_notification = db.query(Notification).filter(
            Notification.user_id == engineer.id,
            Notification.notification_type == "TIMESHEET_WEEKLY_MISSING",
            Notification.created_at >= datetime.combine(today, datetime.min.time())
        ).first()

        # 进一步检查extra_data中的week_start
        if existing_notification:
            extra_data = existing_notification.extra_data or {}
            if extra_data.get('week_start') == week_start.isoformat():
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
                "user_name": engineer.real_name or engineer.username
            }
        )
        reminder_count += 1

    db.commit()
    logger.info(f"周工时填报提醒完成: 发送 {reminder_count} 条提醒（周: {week_start} ~ {week_end}）")

    return reminder_count


def notify_timesheet_anomaly(db: Session, days: int = 1) -> int:
    """
    提醒异常工时记录

    Args:
        db: 数据库会话
        days: 检查最近几天的数据（默认1天）

    Returns:
        发送的提醒数量
    """
    target_date = date.today() - timedelta(days=days)

    # 使用质量服务检测异常
    quality_service = TimesheetQualityService(db)
    anomalies = quality_service.detect_anomalies(
        start_date=target_date,
        end_date=date.today()
    )

    reminder_count = 0
    notified_users = set()

    for anomaly in anomalies:
        # 获取工时记录
        timesheet = db.query(Timesheet).filter(Timesheet.id == anomaly.get('timesheet_id')).first()
        if not timesheet:
            continue

        user_id = timesheet.user_id
        # 避免重复通知同一用户
        if user_id in notified_users:
            continue

        # 检查今天是否已发送过提醒
        existing_notification = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.notification_type == "TIMESHEET_ANOMALY",
            Notification.source_id == timesheet.id,
            Notification.created_at >= datetime.combine(date.today(), datetime.min.time())
        ).first()

        if existing_notification:
            continue

        # 创建异常提醒通知
        create_timesheet_notification(
            db=db,
            user_id=user_id,
            notification_type="TIMESHEET_ANOMALY",
            title=f"异常工时预警：{anomaly.get('anomaly_type', '未知异常')}",
            content=f"您的工时记录（{timesheet.work_date}）存在异常：{anomaly.get('description', '')}，请检查并修正。",
            source_id=timesheet.id,
            priority="HIGH",
            extra_data={
                "timesheet_id": timesheet.id,
                "anomaly_type": anomaly.get('anomaly_type'),
                "description": anomaly.get('description'),
                "work_date": timesheet.work_date.isoformat()
            }
        )
        notified_users.add(user_id)
        reminder_count += 1

    db.commit()
    logger.info(f"异常工时预警完成: 发送 {reminder_count} 条提醒")

    return reminder_count


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
    pending_timesheets = db.query(Timesheet).filter(
        Timesheet.status == "PENDING",
        Timesheet.created_at <= timeout_threshold
    ).all()

    reminder_count = 0
    notified_approvers = {}  # {approver_id: [timesheet_ids]}

    for timesheet in pending_timesheets:
        # 获取审批人（通常是部门经理或项目经理）
        approver_id = None

        # 尝试从用户部门获取部门经理
        user = db.query(User).filter(User.id == timesheet.user_id).first()
        if user and hasattr(user, 'department_id') and user.department_id:
            from app.models.organization import Department
            department = db.query(Department).filter(Department.id == user.department_id).first()
            if department and department.manager_id:
                approver_id = department.manager_id

        # 如果没有部门经理，尝试从项目获取项目经理
        if not approver_id and timesheet.project_id:
            from app.models.project import Project
            project = db.query(Project).filter(Project.id == timesheet.project_id).first()
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
        existing_notification = db.query(Notification).filter(
            Notification.user_id == approver_id,
            Notification.notification_type == "TIMESHEET_APPROVAL_TIMEOUT",
            Notification.created_at >= datetime.combine(date.today(), datetime.min.time())
        ).first()

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
                "count": len(timesheet_ids)
            }
        )
        reminder_count += 1

    db.commit()
    logger.info(f"审批超时提醒完成: 发送 {reminder_count} 条提醒（{len(pending_timesheets)} 条待审批记录）")

    return reminder_count


def notify_sync_failure(db: Session) -> int:
    """
    提醒数据同步失败的工时记录

    Args:
        db: 数据库会话

    Returns:
        发送的提醒数量
    """
    # 查询已审批但可能同步失败的记录
    # 这里需要根据实际同步状态来判断
    # 假设同步失败会在某个字段标记，或者通过检查同步目标表来判断

    # 查询已审批但可能未同步的记录
    approved_timesheets = db.query(Timesheet).filter(
        Timesheet.status == "APPROVED",
        Timesheet.approve_time.isnot(None),
        Timesheet.approve_time >= datetime.now() - timedelta(days=1)  # 最近1天审批的
    ).all()

    reminder_count = 0
    notified_users = set()

    for timesheet in approved_timesheets:
        # 检查同步状态（这里简化处理，实际应该调用同步状态API）
        # 假设如果审批后超过1小时还没有同步记录，认为同步失败
        if timesheet.approve_time and (datetime.now() - timesheet.approve_time).total_seconds() > 3600:
            user_id = timesheet.user_id

            # 避免重复通知
            if user_id in notified_users:
                continue

            # 检查今天是否已发送过提醒
            existing_notification = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.notification_type == "TIMESHEET_SYNC_FAILURE",
                Notification.source_id == timesheet.id,
                Notification.created_at >= datetime.combine(date.today(), datetime.min.time())
            ).first()

            if existing_notification:
                continue

            # 创建同步失败提醒
            create_timesheet_notification(
                db=db,
                user_id=user_id,
                notification_type="TIMESHEET_SYNC_FAILURE",
                title="工时数据同步失败提醒",
                content=f"您的工时记录（{timesheet.work_date}）审批通过后同步失败，请联系管理员处理。",
                source_id=timesheet.id,
                priority="NORMAL",
                extra_data={
                    "timesheet_id": timesheet.id,
                    "work_date": timesheet.work_date.isoformat(),
                    "approve_time": timesheet.approve_time.isoformat() if timesheet.approve_time else None
                }
            )
            notified_users.add(user_id)
            reminder_count += 1

    db.commit()
    logger.info(f"数据同步失败提醒完成: 发送 {reminder_count} 条提醒")

    return reminder_count


def scan_and_notify_all(db: Session) -> Dict[str, int]:
    """
    扫描所有需要提醒的事项并发送通知

    Returns:
        统计信息字典
    """
    stats = {
        "daily_missing": 0,
        "weekly_missing": 0,
        "anomaly": 0,
        "approval_timeout": 0,
        "sync_failure": 0
    }

    try:
        # 每日工时填报提醒（提醒昨天的）
        stats["daily_missing"] = notify_timesheet_missing(db)

        # 周工时填报提醒（提醒上周的）
        stats["weekly_missing"] = notify_weekly_timesheet_missing(db)

        # 异常工时预警
        stats["anomaly"] = notify_timesheet_anomaly(db, days=1)

        # 审批超时提醒
        stats["approval_timeout"] = notify_approval_timeout(db, timeout_hours=24)

        # 数据同步失败提醒
        stats["sync_failure"] = notify_sync_failure(db)

        db.commit()

    except Exception as e:
        logger.error(f"工时提醒服务扫描失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()

    return stats
