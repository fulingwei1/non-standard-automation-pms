# -*- coding: utf-8 -*-
"""
项目成本管理
包含：成本记录CRUD、成本统计、成本分析
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.project import Project
from app.models.project.financial import ProjectCost
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/projects/{project_id}/costs", response_model=ResponseModel)
def get_project_costs(
    project_id: int,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    cost_type: Optional[str] = Query(None, description="成本类型"),
    cost_category: Optional[str] = Query(None, description="成本分类"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目成本列表

    Args:
        project_id: 项目ID
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        cost_type: 成本类型筛选
        cost_category: 成本分类筛选
        start_date: 开始日期
        end_date: 结束日期
        current_user: 当前用户

    Returns:
        ResponseModel: 成本列表
    """
    query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)

    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)
    if cost_category:
        query = query.filter(ProjectCost.cost_category == cost_category)
    if start_date:
        query = query.filter(ProjectCost.cost_date >= date.fromisoformat(start_date))
    if end_date:
        query = query.filter(ProjectCost.cost_date <= date.fromisoformat(end_date))

    total = query.count()
    costs = query.order_by(desc(ProjectCost.cost_date)).offset(skip).limit(limit).all()

    costs_data = [{
        "id": c.id,
        "cost_type": c.cost_type,
        "cost_category": c.cost_category,
        "source_module": c.source_module,
        "source_type": c.source_type,
        "source_no": c.source_no,
        "amount": float(c.amount) if c.amount else 0,
        "tax_amount": float(c.tax_amount) if c.tax_amount else 0,
        "cost_date": c.cost_date.isoformat() if c.cost_date else None,
        "description": c.description,
        "machine_id": c.machine_id,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    } for c in costs]

    # 计算汇总
    total_amount = sum(c.amount or Decimal('0') for c in costs)

    return ResponseModel(
        code=200,
        message="获取成本列表成功",
        data={
            "total": total,
            "total_amount": float(total_amount),
            "items": costs_data
        }
    )


@router.get("/projects/{project_id}/costs/summary", response_model=ResponseModel)
def get_project_cost_summary(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取项目成本汇总

    Args:
        project_id: 项目ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 成本汇总
    """
    # 按类型汇总
    by_type = db.query(
        ProjectCost.cost_type,
        func.sum(ProjectCost.amount).label("total")
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_type).all()

    # 按分类汇总
    by_category = db.query(
        ProjectCost.cost_category,
        func.sum(ProjectCost.amount).label("total")
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_category).all()

    # 按月份汇总
    by_month = db.query(
        func.strftime("%Y-%m", ProjectCost.cost_date).label("month"),
        func.sum(ProjectCost.amount).label("total")
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by("month").order_by("month").all()

    # 总计
    total = db.query(func.sum(ProjectCost.amount)).filter(
        ProjectCost.project_id == project_id
    ).scalar() or Decimal('0')

    return ResponseModel(
        code=200,
        message="获取成本汇总成功",
        data={
            "project_id": project_id,
            "total_cost": float(total),
            "by_type": [{"type": t.cost_type, "amount": float(t.total or 0)} for t in by_type],
            "by_category": [{"category": c.cost_category, "amount": float(c.total or 0)} for c in by_category],
            "by_month": [{"month": m.month, "amount": float(m.total or 0)} for m in by_month],
        }
    )


@router.post("/projects/{project_id}/costs", response_model=ResponseModel)
def create_project_cost(
    project_id: int,
    cost_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建项目成本记录

    Args:
        project_id: 项目ID
        cost_data: 成本数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    cost = ProjectCost(
        project_id=project_id,
        machine_id=cost_data.get("machine_id"),
        cost_type=cost_data.get("cost_type"),
        cost_category=cost_data.get("cost_category"),
        source_module=cost_data.get("source_module"),
        source_type=cost_data.get("source_type"),
        source_id=cost_data.get("source_id"),
        source_no=cost_data.get("source_no"),
        amount=Decimal(str(cost_data.get("amount", 0))),
        tax_amount=Decimal(str(cost_data.get("tax_amount", 0))),
        cost_date=date.fromisoformat(cost_data["cost_date"]) if cost_data.get("cost_date") else date.today(),
        description=cost_data.get("description"),
        created_by=current_user.id,
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)

    return ResponseModel(
        code=200,
        message="成本记录创建成功",
        data={"id": cost.id}
    )


@router.put("/projects/costs/{cost_id}", response_model=ResponseModel)
def update_project_cost(
    cost_id: int,
    cost_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新成本记录

    Args:
        cost_id: 成本ID
        cost_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在")

    updatable = ["cost_type", "cost_category", "description", "source_no"]
    for field in updatable:
        if field in cost_data:
            setattr(cost, field, cost_data[field])

    if "amount" in cost_data:
        cost.amount = Decimal(str(cost_data["amount"]))
    if "tax_amount" in cost_data:
        cost.tax_amount = Decimal(str(cost_data["tax_amount"]))
    if "cost_date" in cost_data:
        cost.cost_date = date.fromisoformat(cost_data["cost_date"]) if cost_data["cost_date"] else None

    db.commit()

    return ResponseModel(code=200, message="成本记录更新成功", data={"id": cost.id})


@router.delete("/projects/costs/{cost_id}", response_model=ResponseModel)
def delete_project_cost(
    cost_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除成本记录

    Args:
        cost_id: 成本ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    cost = db.query(ProjectCost).filter(ProjectCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="成本记录不存在")

    # 检查是否来自其他模块（不允许直接删除）
    if cost.source_module and cost.source_id:
        raise HTTPException(status_code=400, detail="来自其他模块的成本记录不能直接删除")

    db.delete(cost)
    db.commit()

    return ResponseModel(code=200, message="成本记录删除成功", data={"id": cost_id})
