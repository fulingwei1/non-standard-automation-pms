# -*- coding: utf-8 -*-
"""
成本管理 - 采购物料成本清单管理

包含采购物料成本的CRUD操作
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.sales import PurchaseMaterialCost
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sales import (
    PurchaseMaterialCostCreate,
    PurchaseMaterialCostResponse,
    PurchaseMaterialCostUpdate,
)
from app.services.sales.operation_log_service import SalesOperationLogService
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _audit_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _material_cost_audit_value(cost: PurchaseMaterialCost) -> dict[str, Any]:
    return {
        "cost_id": cost.id,
        "material_code": cost.material_code,
        "material_name": cost.material_name,
        "specification": cost.specification,
        "brand": cost.brand,
        "unit": cost.unit,
        "material_type": cost.material_type,
        "is_standard_part": cost.is_standard_part,
        "unit_cost": _audit_value(cost.unit_cost),
        "currency": cost.currency,
        "supplier_id": cost.supplier_id,
        "supplier_name": cost.supplier_name,
        "purchase_date": _audit_value(cost.purchase_date),
        "purchase_order_no": cost.purchase_order_no,
        "purchase_quantity": _audit_value(cost.purchase_quantity),
        "lead_time_days": cost.lead_time_days,
        "is_active": cost.is_active,
        "match_priority": cost.match_priority,
        "match_keywords": cost.match_keywords,
        "usage_count": cost.usage_count,
        "last_used_at": _audit_value(cost.last_used_at),
        "remark": cost.remark,
        "submitted_by": cost.submitted_by,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def _log_material_cost_operation(
    db: Session,
    cost: PurchaseMaterialCost,
    operation_type: str,
    operator: User,
    *,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    operation_desc: str,
    remark: str | None = None,
) -> None:
    old_snapshot = old_value or {}
    new_snapshot = new_value or {}
    SalesOperationLogService.log_operation(
        db,
        entity_type=SalesEntityType.PURCHASE_MATERIAL_COST,
        entity_id=cost.id,
        entity_code=cost.material_code,
        operation_type=operation_type,
        operator=operator,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=remark or cost.material_name,
    )


def _build_material_cost_response(cost: PurchaseMaterialCost) -> PurchaseMaterialCostResponse:
    cost_dict = {
        **{c.name: getattr(cost, c.name) for c in cost.__table__.columns},
        "submitter_name": cost.submitter.real_name if cost.submitter else None,
    }
    return PurchaseMaterialCostResponse(**cost_dict)


@router.get(
    "/purchase-material-costs", response_model=PaginatedResponse[PurchaseMaterialCostResponse]
)
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

    query = apply_keyword_filter(
        query, PurchaseMaterialCost, material_name, "material_name", use_ilike=False
    )
    if material_type:
        query = query.filter(PurchaseMaterialCost.material_type == material_type)
    if is_standard_part is not None:
        query = query.filter(PurchaseMaterialCost.is_standard_part == is_standard_part)
    if is_active is not None:
        query = query.filter(PurchaseMaterialCost.is_active == is_active)

    total = query.count()
    costs = apply_pagination(
        query.order_by(
            desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.created_at)
        ),
        pagination.offset,
        pagination.limit,
    ).all()

    items = [_build_material_cost_response(cost) for cost in costs]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
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
    cost = get_or_404(db, PurchaseMaterialCost, cost_id, detail="采购物料成本不存在")

    return _build_material_cost_response(cost)


@router.post(
    "/purchase-material-costs", response_model=PurchaseMaterialCostResponse, status_code=201
)
def create_purchase_material_cost(
    *,
    db: Session = Depends(deps.get_db),
    cost_in: PurchaseMaterialCostCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建采购物料成本（采购部提交）
    """
    cost = PurchaseMaterialCost(**cost_in.model_dump(), submitted_by=current_user.id)
    db.add(cost)
    db.flush()
    _log_material_cost_operation(
        db,
        cost,
        SalesOperationType.CREATE,
        current_user,
        new_value=_material_cost_audit_value(cost),
        operation_desc="创建采购物料成本",
    )
    db.commit()
    db.refresh(cost)

    return _build_material_cost_response(cost)


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
    cost = get_or_404(db, PurchaseMaterialCost, cost_id, detail="采购物料成本不存在")

    update_data = cost_in.model_dump(exclude_unset=True)
    old_value = _material_cost_audit_value(cost)
    for field, value in update_data.items():
        if hasattr(cost, field):
            setattr(cost, field, value)

    _log_material_cost_operation(
        db,
        cost,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=_material_cost_audit_value(cost),
        operation_desc="更新采购物料成本",
    )
    db.commit()
    db.refresh(cost)

    return _build_material_cost_response(cost)


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
    cost = get_or_404(db, PurchaseMaterialCost, cost_id, detail="采购物料成本不存在")

    old_value = _material_cost_audit_value(cost)
    db.delete(cost)
    _log_material_cost_operation(
        db,
        cost,
        SalesOperationType.DELETE,
        current_user,
        old_value=old_value,
        new_value={},
        operation_desc="删除采购物料成本",
    )
    db.commit()

    return ResponseModel(code=200, message="删除成功")
