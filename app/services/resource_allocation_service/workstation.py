# -*- coding: utf-8 -*-
"""
资源分配服务 - 工位相关
"""
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import WorkOrder, Workstation

from .utils import calculate_workdays


def check_workstation_availability(
    db: Session,
    workstation_id: int,
    start_date: date,
    end_date: date,
    exclude_work_order_id: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    检查工位可用性

    Args:
        db: 数据库会话
        workstation_id: 工位ID
        start_date: 计划开始日期
        end_date: 计划结束日期
        exclude_work_order_id: 排除的工单ID（用于更新时检查）

    Returns:
        (是否可用, 不可用原因)
    """
    workstation = db.query(Workstation).filter(Workstation.id == workstation_id).first()
    if not workstation:
        return (False, "工位不存在")

    if not workstation.is_active:
        return (False, "工位已停用")

    # 检查工位状态
    if workstation.status not in ['IDLE', 'MAINTENANCE']:
        return (False, f"工位状态为：{workstation.status}")

    # 检查是否有冲突的工单
    conflicting_orders = db.query(WorkOrder).filter(
        WorkOrder.workstation_id == workstation_id,
        WorkOrder.status.in_(['PLANNED', 'IN_PROGRESS', 'PAUSED']),
        WorkOrder.plan_start_date <= end_date,
        WorkOrder.plan_end_date >= start_date
    )

    if exclude_work_order_id:
        conflicting_orders = conflicting_orders.filter(WorkOrder.id != exclude_work_order_id)

    conflicting_order = conflicting_orders.first()
    if conflicting_order:
        return (False, f"工位在 {conflicting_order.plan_start_date} 至 {conflicting_order.plan_end_date} 已被工单 {conflicting_order.work_order_no} 占用")

    return (True, None)


def find_available_workstations(
    db: Session,
    workshop_id: Optional[int] = None,
    start_date: date = None,
    end_date: date = None,
    required_capability: Optional[str] = None
) -> List[Dict]:
    """
    查找可用工位

    Args:
        db: 数据库会话
        workshop_id: 车间ID（可选）
        start_date: 计划开始日期（默认今天）
        end_date: 计划结束日期（默认start_date + 7天）
        required_capability: 所需能力（可选）

    Returns:
        可用工位列表
    """
    if not start_date:
        start_date = date.today()
    if not end_date:
        end_date = start_date + timedelta(days=7)

    # 查询工位
    query = db.query(Workstation).filter(
        Workstation.is_active == True,
        Workstation.status == 'IDLE'
    )

    if workshop_id:
        query = query.filter(Workstation.workshop_id == workshop_id)

    workstations = query.all()

    available_workstations = []
    for ws in workstations:
        is_available, reason = check_workstation_availability(
            db, ws.id, start_date, end_date
        )

        if is_available:
            available_workstations.append({
                'workstation_id': ws.id,
                'workstation_code': ws.workstation_code,
                'workstation_name': ws.workstation_name,
                'workshop_id': ws.workshop_id,
                'workshop_name': ws.workshop.name if ws.workshop else None,
                'status': ws.status,
                'available_from': start_date,
                'available_until': end_date
            })

    return available_workstations
