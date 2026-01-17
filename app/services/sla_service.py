# -*- coding: utf-8 -*-
"""
SLA管理服务
包含：SLA策略匹配、SLA监控、SLA预警
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.service import ServiceTicket
from app.models.sla import SLAMonitor, SLAPolicy, SLAStatusEnum


def match_sla_policy(
    db: Session,
    problem_type: str,
    urgency: str
) -> Optional[SLAPolicy]:
    """
    匹配SLA策略

    匹配规则：
    1. 优先匹配问题类型和紧急程度都匹配的策略
    2. 其次匹配只匹配问题类型的策略
    3. 再次匹配只匹配紧急程度的策略
    4. 最后匹配通用策略（问题类型和紧急程度都为空）
    """
    # 1. 精确匹配（问题类型和紧急程度都匹配）
    policy = db.query(SLAPolicy).filter(
        and_(
            SLAPolicy.problem_type == problem_type,
            SLAPolicy.urgency == urgency,
            SLAPolicy.is_active == True
        )
    ).order_by(SLAPolicy.priority).first()

    if policy:
        return policy

    # 2. 匹配问题类型（紧急程度为空）
    policy = db.query(SLAPolicy).filter(
        and_(
            SLAPolicy.problem_type == problem_type,
            SLAPolicy.urgency.is_(None),
            SLAPolicy.is_active == True
        )
    ).order_by(SLAPolicy.priority).first()

    if policy:
        return policy

    # 3. 匹配紧急程度（问题类型为空）
    policy = db.query(SLAPolicy).filter(
        and_(
            SLAPolicy.urgency == urgency,
            SLAPolicy.problem_type.is_(None),
            SLAPolicy.is_active == True
        )
    ).order_by(SLAPolicy.priority).first()

    if policy:
        return policy

    # 4. 通用策略（问题类型和紧急程度都为空）
    policy = db.query(SLAPolicy).filter(
        and_(
            SLAPolicy.problem_type.is_(None),
            SLAPolicy.urgency.is_(None),
            SLAPolicy.is_active == True
        )
    ).order_by(SLAPolicy.priority).first()

    return policy


def create_sla_monitor(
    db: Session,
    ticket: ServiceTicket,
    policy: SLAPolicy
) -> SLAMonitor:
    """
    创建SLA监控记录
    """
    # 计算截止时间
    response_deadline = ticket.reported_time + timedelta(hours=policy.response_time_hours)
    resolve_deadline = ticket.reported_time + timedelta(hours=policy.resolve_time_hours)

    # 创建监控记录
    monitor = SLAMonitor(
        ticket_id=ticket.id,
        policy_id=policy.id,
        response_deadline=response_deadline,
        resolve_deadline=resolve_deadline,
        response_status='ON_TIME',
        resolve_status='ON_TIME',
    )

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    return monitor


def update_sla_monitor_status(
    db: Session,
    monitor: SLAMonitor,
    current_time: Optional[datetime] = None
) -> None:
    """
    更新SLA监控状态
    """
    if current_time is None:
        current_time = datetime.now()

    # 更新响应状态
    if monitor.actual_response_time:
        # 已响应，计算时间差
        time_diff = (monitor.actual_response_time - monitor.response_deadline).total_seconds() / 3600
        monitor.response_time_diff_hours = Decimal(str(time_diff))

        if time_diff <= 0:
            monitor.response_status = 'ON_TIME'
        else:
            monitor.response_status = 'OVERDUE'
    else:
        # 未响应，检查是否超时或预警
        time_remaining = (monitor.response_deadline - current_time).total_seconds() / 3600
        total_time = (monitor.response_deadline - monitor.ticket.reported_time).total_seconds() / 3600

        if time_remaining < 0:
            monitor.response_status = 'OVERDUE'
        elif monitor.policy and monitor.policy.warning_threshold_percent:
            # 检查是否达到预警阈值
            elapsed_percent = ((total_time - time_remaining) / total_time) * 100 if total_time > 0 else 0
            if elapsed_percent >= float(monitor.policy.warning_threshold_percent):
                monitor.response_status = 'WARNING'
            else:
                monitor.response_status = 'ON_TIME'
        else:
            monitor.response_status = 'ON_TIME'

    # 更新解决状态
    if monitor.actual_resolve_time:
        # 已解决，计算时间差
        time_diff = (monitor.actual_resolve_time - monitor.resolve_deadline).total_seconds() / 3600
        monitor.resolve_time_diff_hours = Decimal(str(time_diff))

        if time_diff <= 0:
            monitor.resolve_status = 'ON_TIME'
        else:
            monitor.resolve_status = 'OVERDUE'
    else:
        # 未解决，检查是否超时或预警
        time_remaining = (monitor.resolve_deadline - current_time).total_seconds() / 3600
        total_time = (monitor.resolve_deadline - monitor.ticket.reported_time).total_seconds() / 3600

        if time_remaining < 0:
            monitor.resolve_status = 'OVERDUE'
        elif monitor.policy and monitor.policy.warning_threshold_percent:
            # 检查是否达到预警阈值
            elapsed_percent = ((total_time - time_remaining) / total_time) * 100 if total_time > 0 else 0
            if elapsed_percent >= float(monitor.policy.warning_threshold_percent):
                monitor.resolve_status = 'WARNING'
            else:
                monitor.resolve_status = 'ON_TIME'
        else:
            monitor.resolve_status = 'ON_TIME'

    db.commit()


def sync_ticket_to_sla_monitor(
    db: Session,
    ticket: ServiceTicket
) -> Optional[SLAMonitor]:
    """
    同步工单状态到SLA监控记录
    """
    # 查找监控记录
    monitor = db.query(SLAMonitor).filter(SLAMonitor.ticket_id == ticket.id).first()

    if not monitor:
        # 如果没有监控记录，尝试创建
        policy = match_sla_policy(db, ticket.problem_type, ticket.urgency)
        if policy:
            monitor = create_sla_monitor(db, ticket, policy)
        else:
            return None

    # 更新实际时间
    if ticket.response_time and not monitor.actual_response_time:
        monitor.actual_response_time = ticket.response_time

    if ticket.resolved_time and not monitor.actual_resolve_time:
        monitor.actual_resolve_time = ticket.resolved_time

    # 更新状态
    update_sla_monitor_status(db, monitor)

    return monitor


def check_sla_warnings(
    db: Session,
    current_time: Optional[datetime] = None
) -> List[SLAMonitor]:
    """
    检查需要发送预警的SLA监控记录
    返回需要发送预警的监控记录列表
    """
    if current_time is None:
        current_time = datetime.now()

    # 查找需要预警的监控记录
    monitors = db.query(SLAMonitor).join(SLAPolicy).filter(
        and_(
            SLAPolicy.is_active == True,
            or_(
                # 响应预警：未响应且达到预警阈值且未发送过预警
                and_(
                    SLAMonitor.actual_response_time.is_(None),
                    SLAMonitor.response_status == 'WARNING',
                    SLAMonitor.response_warning_sent == False
                ),
                # 解决预警：未解决且达到预警阈值且未发送过预警
                and_(
                    SLAMonitor.actual_resolve_time.is_(None),
                    SLAMonitor.resolve_status == 'WARNING',
                    SLAMonitor.resolve_warning_sent == False
                )
            )
        )
    ).all()

    return monitors


def mark_warning_sent(
    db: Session,
    monitor: SLAMonitor,
    warning_type: str  # 'response' or 'resolve'
) -> None:
    """
    标记预警已发送
    """
    if warning_type == 'response':
        monitor.response_warning_sent = True
        monitor.response_warning_sent_at = datetime.now()
    elif warning_type == 'resolve':
        monitor.resolve_warning_sent = True
        monitor.resolve_warning_sent_at = datetime.now()

    db.commit()
