# -*- coding: utf-8 -*-
"""
成本分摊规则管理端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.budget import ProjectCostAllocationRule
from app.models.user import User
from app.schemas.budget import (
    ProjectCostAllocationRuleCreate,
    ProjectCostAllocationRuleResponse,
    ProjectCostAllocationRuleUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.query_filters import apply_pagination

router = APIRouter()


@router.get("/allocation-rules", response_model=PaginatedResponse[ProjectCostAllocationRuleResponse])
def list_allocation_rules(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    获取成本分摊规则列表
    """
    query = db.query(ProjectCostAllocationRule)

    if is_active is not None:
        query = query.filter(ProjectCostAllocationRule.is_active == is_active)

    total = query.count()
    rules = apply_pagination(query.order_by(desc(ProjectCostAllocationRule.created_at)), pagination.offset, pagination.limit).all()

    items = [ProjectCostAllocationRuleResponse(**{c.name: getattr(rule, c.name) for c in rule.__table__.columns})
             for rule in rules]

    return pagination.to_response(items, total)


@router.post("/allocation-rules", response_model=ProjectCostAllocationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_allocation_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_in: ProjectCostAllocationRuleCreate,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    创建成本分摊规则
    """
    rule_data = rule_in.model_dump()
    rule_data['created_by'] = current_user.id

    rule = ProjectCostAllocationRule(**rule_data)
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ProjectCostAllocationRuleResponse(**{c.name: getattr(rule, c.name) for c in rule.__table__.columns})


@router.get("/allocation-rules/{rule_id}", response_model=ProjectCostAllocationRuleResponse)
def get_allocation_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    获取成本分摊规则详情
    """
    rule = db.query(ProjectCostAllocationRule).filter(ProjectCostAllocationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="分摊规则不存在")

    return ProjectCostAllocationRuleResponse(**{c.name: getattr(rule, c.name) for c in rule.__table__.columns})


@router.put("/allocation-rules/{rule_id}", response_model=ProjectCostAllocationRuleResponse)
def update_allocation_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    rule_in: ProjectCostAllocationRuleUpdate,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    更新成本分摊规则
    """
    rule = db.query(ProjectCostAllocationRule).filter(ProjectCostAllocationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="分摊规则不存在")

    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(rule, field):
            setattr(rule, field, value)

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ProjectCostAllocationRuleResponse(**{c.name: getattr(rule, c.name) for c in rule.__table__.columns})


@router.delete("/allocation-rules/{rule_id}", status_code=status.HTTP_200_OK)
def delete_allocation_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.require_permission("budget:read")),
) -> Any:
    """
    删除成本分摊规则
    """
    rule = db.query(ProjectCostAllocationRule).filter(ProjectCostAllocationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="分摊规则不存在")

    db.delete(rule)
    db.commit()

    return ResponseModel(code=200, message="分摊规则已删除")
