# -*- coding: utf-8 -*-
"""
费用分摊服务
"""

from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.rd_project import RdCost, RdCostAllocationRule, RdProject


def query_allocatable_costs(
    db: Session,
    rule: RdCostAllocationRule,
    cost_ids: Optional[List[int]]
) -> List[RdCost]:
    """
    查询需要分摊的费用

    Returns:
        List[RdCost]: 费用列表
    """
    query = db.query(RdCost).filter(
        RdCost.status == 'APPROVED',
        RdCost.is_allocated == False
    )

    if cost_ids:
        query = query.filter(RdCost.id.in_(cost_ids))
    else:
        if rule.cost_type_ids:
            query = query.filter(RdCost.cost_type_id.in_(rule.cost_type_ids))

    return query.all()


def get_target_project_ids(
    db: Session,
    rule: RdCostAllocationRule
) -> List[int]:
    """
    获取目标项目ID列表

    Returns:
        List[int]: 项目ID列表
    """
    target_project_ids = rule.project_ids if rule.project_ids else []

    if not target_project_ids:
        projects = db.query(RdProject).filter(
            RdProject.status.in_(['APPROVED', 'IN_PROGRESS'])
        ).all()
        target_project_ids = [p.id for p in projects]

    return target_project_ids


def calculate_allocation_rates_by_hours(
    db: Session,
    target_project_ids: List[int]
) -> Dict[int, float]:
    """
    按工时分摊计算分摊比例

    Returns:
        Dict[int, float]: 项目ID到分摊比例的映射
    """
    total_hours = Decimal(0)
    project_hours = {}

    for project_id in target_project_ids:
        project = db.query(RdProject).filter(RdProject.id == project_id).first()
        if project and project.total_hours:
            hours = Decimal(str(project.total_hours))
            project_hours[project_id] = hours
            total_hours += hours

    allocation_rates = {}

    if total_hours > 0:
        for project_id, hours in project_hours.items():
            allocation_rates[project_id] = float(hours / total_hours * 100)
    else:
        rate = 100.0 / len(target_project_ids)
        for project_id in target_project_ids:
            allocation_rates[project_id] = rate

    return allocation_rates


def calculate_allocation_rates_by_headcount(
    db: Session,
    target_project_ids: List[int]
) -> Dict[int, float]:
    """
    按人数分摊计算分摊比例

    Returns:
        Dict[int, float]: 项目ID到分摊比例的映射
    """
    total_participants = 0
    project_participants = {}

    for project_id in target_project_ids:
        project = db.query(RdProject).filter(RdProject.id == project_id).first()
        if project and project.participant_count:
            participants = project.participant_count
            project_participants[project_id] = participants
            total_participants += participants

    allocation_rates = {}

    if total_participants > 0:
        for project_id, participants in project_participants.items():
            allocation_rates[project_id] = float(participants / total_participants * 100)
    else:
        rate = 100.0 / len(target_project_ids)
        for project_id in target_project_ids:
            allocation_rates[project_id] = rate

    return allocation_rates


def calculate_allocation_rates(
    db: Session,
    rule: RdCostAllocationRule,
    target_project_ids: List[int]
) -> Dict[int, float]:
    """
    根据分摊依据计算分摊比例

    Returns:
        Dict[int, float]: 项目ID到分摊比例的映射
    """
    if rule.allocation_basis == 'HOURS':
        return calculate_allocation_rates_by_hours(db, target_project_ids)
    elif rule.allocation_basis == 'REVENUE':
        # 按收入分摊：暂时使用平均分摊
        rate = 100.0 / len(target_project_ids)
        return {project_id: rate for project_id in target_project_ids}
    elif rule.allocation_basis == 'HEADCOUNT':
        return calculate_allocation_rates_by_headcount(db, target_project_ids)
    else:
        # 默认平均分摊
        rate = 100.0 / len(target_project_ids)
        return {project_id: rate for project_id in target_project_ids}


def create_allocated_cost(
    db: Session,
    cost: RdCost,
    project_id: int,
    rate: float,
    rule_id: int,
    generate_cost_no
) -> RdCost:
    """
    创建分摊后的费用记录

    Returns:
        RdCost: 分摊后的费用记录
    """
    allocated_amount = cost.cost_amount * Decimal(str(rate)) / 100

    allocated_cost = RdCost(
        cost_no=generate_cost_no(db),
        rd_project_id=project_id,
        cost_type_id=cost.cost_type_id,
        cost_date=cost.cost_date,
        cost_amount=allocated_amount,
        cost_description=f"{cost.cost_description or ''}（分摊自费用{cost.cost_no}）",
        source_type='ALLOCATED',
        source_id=cost.id,
        is_allocated=True,
        allocation_rule_id=rule_id,
        allocation_rate=Decimal(str(rate)),
        deductible_amount=allocated_amount * (cost.deductible_amount / cost.cost_amount) if cost.deductible_amount and cost.cost_amount > 0 else None,
        status='APPROVED',
        remark=f"由规则{rule_id}自动分摊"
    )

    db.add(allocated_cost)

    # 更新目标项目的总费用
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if project:
        project.total_cost = (project.total_cost or 0) + allocated_amount

    return allocated_cost
