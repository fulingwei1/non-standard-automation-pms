# -*- coding: utf-8 -*-
"""
预算明细管理端点
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.budget import ProjectBudget, ProjectBudgetItem
from app.models.user import User
from app.schemas.budget import (
    ProjectBudgetItemCreate,
    ProjectBudgetItemResponse,
    ProjectBudgetItemUpdate,
)
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/{budget_id}/items", response_model=List[ProjectBudgetItemResponse])
def get_budget_items(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    获取预算明细列表
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    items = db.query(ProjectBudgetItem).filter(
        ProjectBudgetItem.budget_id == budget_id
    ).order_by(ProjectBudgetItem.item_no).all()

    return [ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})
            for item in items]


@router.post("/{budget_id}/items", response_model=ProjectBudgetItemResponse, status_code=status.HTTP_201_CREATED)
def create_budget_item(
    *,
    db: Session = Depends(deps.get_db),
    budget_id: int,
    item_in: ProjectBudgetItemCreate,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    创建预算明细
    """
    budget = db.query(ProjectBudget).filter(ProjectBudget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="预算不存在")

    if budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能为草稿状态的预算添加明细")

    item = ProjectBudgetItem(budget_id=budget_id, **item_in.model_dump())
    db.add(item)

    # 更新预算总额
    budget.total_amount = (budget.total_amount or 0) + item.budget_amount
    db.add(budget)

    db.commit()
    db.refresh(item)

    return ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.put("/items/{item_id}", response_model=ProjectBudgetItemResponse)
def update_budget_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    item_in: ProjectBudgetItemUpdate,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    更新预算明细
    """
    item = db.query(ProjectBudgetItem).filter(ProjectBudgetItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="预算明细不存在")

    if item.budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能更新草稿状态预算的明细")

    old_amount = item.budget_amount
    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(item, field):
            setattr(item, field, value)

    # 更新预算总额
    if item_in.budget_amount is not None:
        budget = item.budget
        budget.total_amount = (budget.total_amount or 0) - old_amount + item.budget_amount
        db.add(budget)

    db.add(item)
    db.commit()
    db.refresh(item)

    return ProjectBudgetItemResponse(**{c.name: getattr(item, c.name) for c in item.__table__.columns})


@router.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
def delete_budget_item(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    删除预算明细
    """
    item = db.query(ProjectBudgetItem).filter(ProjectBudgetItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="预算明细不存在")

    if item.budget.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能删除草稿状态预算的明细")

    budget = item.budget
    budget.total_amount = max(0, (budget.total_amount or 0) - item.budget_amount)
    db.add(budget)

    db.delete(item)
    db.commit()

    return ResponseModel(code=200, message="预算明细已删除")
