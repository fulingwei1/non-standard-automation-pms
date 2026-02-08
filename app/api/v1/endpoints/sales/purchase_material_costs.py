# -*- coding: utf-8 -*-
"""
成本管理 - 采购物料成本清单管理

包含采购物料成本的CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.sales import PurchaseMaterialCost
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.schemas.sales import (
    PurchaseMaterialCostCreate,
    PurchaseMaterialCostResponse,
    PurchaseMaterialCostUpdate,
)

router = APIRouter()


@router.get("/purchase-material-costs", response_model=PaginatedResponse[PurchaseMaterialCostResponse])
def get_purchase_material_costs(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    material_name: Optional[str] = Query(None, description="物料名称搜索"),
    material_type: Optional[str] = Query(None, description="物料类型筛选"),
    is_standard_part: Optional[bool] = Query(None, description="是否标准件"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取采购物料成本清单列表（采购部维护的标准件成本信息）
    """
    query = db.query(PurchaseMaterialCost)

    if material_name:
        query = query.filter(PurchaseMaterialCost.material_name.like(f"%{material_name}%"))
    if material_type:
        query = query.filter(PurchaseMaterialCost.material_type == material_type)
    if is_standard_part is not None:
        query = query.filter(PurchaseMaterialCost.is_standard_part == is_standard_part)
    if is_active is not None:
        query = query.filter(PurchaseMaterialCost.is_active == is_active)

    total = query.count()
    costs = query.order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for cost in costs:
        cost_dict = {
            **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
            "submitter_name": cost.submitter.real_name if cost.submitter else None
        }
        items.append(PurchaseMaterialCostResponse(**cost_dict))

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.get("/purchase-material-costs/{cost_id}", response_model=PurchaseMaterialCostResponse)
def get_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取采购物料成本详情
    """
    cost = db.query(PurchaseMaterialCost).filter(PurchaseMaterialCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="采购物料成本不存在")

    cost_dict = {
        **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
        "submitter_name": cost.submitter.real_name if cost.submitter else None
    }
    return PurchaseMaterialCostResponse(**cost_dict)


@router.post("/purchase-material-costs", response_model=PurchaseMaterialCostResponse, status_code=201)
def create_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_in: PurchaseMaterialCostCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建采购物料成本（采购部提交）
    """
    cost = PurchaseMaterialCost(
        **cost_in.model_dump(),
        submitted_by=current_user.id
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)

    cost_dict = {
        **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
        "submitter_name": cost.submitter.real_name if cost.submitter else None
    }
    return PurchaseMaterialCostResponse(**cost_dict)


@router.put("/purchase-material-costs/{cost_id}", response_model=PurchaseMaterialCostResponse)
def update_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    cost_in: PurchaseMaterialCostUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新采购物料成本
    """
    cost = db.query(PurchaseMaterialCost).filter(PurchaseMaterialCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="采购物料成本不存在")

    update_data = cost_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(cost, field):
            setattr(cost, field, value)

    db.add(cost)
    db.commit()
    db.refresh(cost)

    cost_dict = {
        **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
        "submitter_name": cost.submitter.real_name if cost.submitter else None
    }
    return PurchaseMaterialCostResponse(**cost_dict)


@router.delete("/purchase-material-costs/{cost_id}", status_code=200)
def delete_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除采购物料成本
    """
    cost = db.query(PurchaseMaterialCost).filter(PurchaseMaterialCost.id == cost_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="采购物料成本不存在")

    db.delete(cost)
    db.commit()

    return ResponseModel(code=200, message="删除成功")
