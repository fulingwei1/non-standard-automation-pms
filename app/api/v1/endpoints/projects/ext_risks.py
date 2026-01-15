# -*- coding: utf-8 -*-
"""
风险管理 API
从 projects/extended.py 拆分
"""

from typing import Any, List, Optional, Dict

from datetime import date, datetime, timedelta

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, status

from sqlalchemy.orm import Session, joinedload

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.project import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/risks",
    tags=["risks"]
)

# ==================== 路由定义 ====================
# 共 1 个路由

    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_type).all()

    type_summary = [
        {
            "cost_type": stat.cost_type,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        }
        for stat in type_stats
    ]

    # 按成本分类统计
    category_stats = db.query(
        ProjectCost.cost_category,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_category).all()

    category_summary = [
        {
            "cost_category": stat.cost_category,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        }
        for stat in category_stats
    ]

    # 预算对比
    budget_amount = float(project.budget_amount or 0)
    actual_cost = float(project.actual_cost or 0)
    cost_variance = actual_cost - budget_amount
    cost_variance_pct = (cost_variance / budget_amount * 100) if budget_amount > 0 else 0

    # 合同对比
    contract_amount = float(project.contract_amount or 0)
    profit = contract_amount - actual_cost
    profit_margin = (profit / contract_amount * 100) if contract_amount > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "budget_info": {
                "budget_amount": round(budget_amount, 2),
                "actual_cost": round(actual_cost, 2),
                "cost_variance": round(cost_variance, 2),
                "cost_variance_pct": round(cost_variance_pct, 2),
                "is_over_budget": cost_variance > 0
            },
            "contract_info": {
                "contract_amount": round(contract_amount, 2),
                "profit": round(profit, 2),
                "profit_margin": round(profit_margin, 2)
            },
            "cost_summary": {
                "total_amount": round(total_amount, 2),
                "total_tax": round(total_tax, 2),
                "total_with_tax": round(total_amount + total_tax, 2),
                "total_count": total_count
            },
            "by_type": type_summary,
            "by_category": category_summary,
        }
    )


@router.get("/projects/{project_id}/cost-details", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_cost_details(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    cost_type: Optional[str] = Query(None, description="成本类型筛选"),
    cost_category: Optional[str] = Query(None, description="成本分类筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本明细列表
    获取项目的成本明细记录列表，支持分页和筛选
    """
    from app.models.project import ProjectCost
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)

    if machine_id:
        query = query.filter(ProjectCost.machine_id == machine_id)
    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)
    if cost_category:
        query = query.filter(ProjectCost.cost_category == cost_category)
    if start_date:
        query = query.filter(ProjectCost.cost_date >= start_date)
    if end_date:
        query = query.filter(ProjectCost.cost_date <= end_date)

    total = query.count()
    offset = (page - 1) * page_size
    costs = query.order_by(desc(ProjectCost.cost_date), desc(ProjectCost.created_at)).offset(offset).limit(page_size).all()

    cost_details = []
    for cost in costs:
        machine = None
        if cost.machine_id:
            machine = db.query(Machine).filter(Machine.id == cost.machine_id).first()

        cost_details.append({
            "id": cost.id,
            "cost_no": cost.cost_no,
            "cost_date": cost.cost_date.isoformat() if cost.cost_date else None,
            "cost_type": cost.cost_type,
            "cost_category": cost.cost_category,
            "amount": float(cost.amount) if cost.amount else 0,
            "tax_amount": float(cost.tax_amount) if cost.tax_amount else 0,
            "total_amount": float(cost.amount or 0) + float(cost.tax_amount or 0),
            "machine_id": cost.machine_id,
            "machine_code": machine.machine_code if machine else None,
            "machine_name": machine.machine_name if machine else None,
            "description": cost.description,
            "remark": cost.remark,
        })

    return PaginatedResponse(
        items=cost_details,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )

