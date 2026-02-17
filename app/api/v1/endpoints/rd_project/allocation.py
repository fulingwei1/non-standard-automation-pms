# -*- coding: utf-8 -*-
"""
费用分摊规则管理
"""
from datetime import date
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.rd_project import RdCostAllocationRule, RdProject
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.rd_project import RdCostAllocationRuleResponse

from .utils import generate_cost_no

router = APIRouter()

# ==================== 费用分摊规则 ====================

@router.get("/rd-cost-allocation-rules", response_model=ResponseModel)
def get_rd_cost_allocation_rules(
    db: Session = Depends(deps.get_db),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    获取费用分摊规则列表
    """
    query = db.query(RdCostAllocationRule)

    if is_active is not None:
        query = query.filter(RdCostAllocationRule.is_active == is_active)

    rules = query.order_by(desc(RdCostAllocationRule.created_at)).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[RdCostAllocationRuleResponse.model_validate(rule) for rule in rules]
    )


@router.post("/rd-costs/apply-allocation", response_model=ResponseModel)
def apply_cost_allocation(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int = Query(..., description="分摊规则ID"),
    cost_ids: Optional[List[int]] = Query(None, description="费用ID列表（不提供则应用规则范围内的所有费用）"),
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    应用费用分摊规则
    根据分摊规则将共享费用分摊到多个研发项目
    """
    from app.services.cost_allocation_service import (
        calculate_allocation_rates,
        create_allocated_cost,
        get_target_project_ids,
        query_allocatable_costs,
    )

    # 验证分摊规则是否存在
    rule = db.query(RdCostAllocationRule).filter(RdCostAllocationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="分摊规则不存在")

    if not rule.is_active:
        raise HTTPException(status_code=400, detail="分摊规则未启用")

    # 查询需要分摊的费用
    costs = query_allocatable_costs(db, rule, cost_ids)

    if not costs:
        return ResponseModel(
            code=200,
            message="没有需要分摊的费用",
            data={"allocated_count": 0}
        )

    # 获取目标项目列表
    target_project_ids = get_target_project_ids(db, rule)

    if not target_project_ids:
        return ResponseModel(
            code=400,
            message="没有可分摊的目标项目",
            data={"allocated_count": 0}
        )

    # 计算分摊比例
    allocation_rates = calculate_allocation_rates(db, rule, target_project_ids)

    # 应用分摊规则
    allocated_count = 0

    for cost in costs:
        # 为每个目标项目创建分摊后的费用记录
        for project_id, rate in allocation_rates.items():
            create_allocated_cost(db, cost, project_id, rate, rule_id, generate_cost_no)

        # 标记原费用为已分摊
        cost.is_allocated = True
        cost.allocation_rule_id = rule_id
        db.add(cost)
        allocated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"费用分摊成功，共分摊{allocated_count}条费用到{len(target_project_ids)}个项目",
        data={
            "allocated_count": allocated_count,
            "target_projects": len(target_project_ids),
            "allocation_rates": allocation_rates
        }
    )


@router.get("/{project_id}/timesheet-summary", response_model=ResponseModel)
def get_rd_project_timesheet_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    获取研发项目工时汇总
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")

    # 查询关联的非标项目
    linked_project_ids = []
    if project.linked_project_id:
        linked_project_ids.append(project.linked_project_id)

    # 如果没有关联的非标项目，无法统计工时
    if not linked_project_ids:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "rd_project_id": project_id,
                "rd_project_name": project.project_name,
                "total_hours": 0,
                "total_participants": 0,
                "by_user": [],
                "by_date": {},
                "note": "研发项目未关联非标项目，无法统计工时"
            }
        )

    # 查询工时记录（从关联的非标项目）
    query = db.query(Timesheet).filter(
        Timesheet.project_id.in_(linked_project_ids),
        Timesheet.status == 'APPROVED'
    )

    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)

    timesheets = query.all()

    # 统计汇总
    total_hours = Decimal(0)
    by_user = {}
    by_date = {}
    participants = set()

    for ts in timesheets:
        hours = Decimal(str(ts.hours or 0))
        total_hours += hours
        participants.add(ts.user_id)

        # 按用户统计
        user = db.query(User).filter(User.id == ts.user_id).first()
        user_name = user.real_name or user.username if user else f"用户{ts.user_id}"
        if user_name not in by_user:
            by_user[user_name] = {
                'user_id': ts.user_id,
                'user_name': user_name,
                'total_hours': Decimal(0),
                'days': 0
            }
        by_user[user_name]['total_hours'] += hours
        by_user[user_name]['days'] += 1

        # 按日期统计
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal(0)
        by_date[date_str] += hours

    # 更新研发项目的总工时和参与人数
    project.total_hours = total_hours
    project.participant_count = len(participants)
    db.add(project)
    db.commit()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "rd_project_id": project_id,
            "rd_project_name": project.project_name,
            "total_hours": float(total_hours),
            "total_participants": len(participants),
            "by_user": list(by_user.values()),
            "by_date": {k: float(v) for k, v in by_date.items()},
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    )



