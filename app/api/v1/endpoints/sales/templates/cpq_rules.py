# -*- coding: utf-8 -*-
"""
CPQ规则集管理 API endpoints

包含CPQ规则集的CRUD和价格预览功能
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.sales import CpqRuleSet
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    CpqPricePreviewRequest,
    CpqPricePreviewResponse,
    CpqRuleSetCreate,
    CpqRuleSetResponse,
    CpqRuleSetUpdate,
)
from app.services.cpq_pricing_service import CpqPricingService
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter

from .common import _serialize_rule_set

router = APIRouter()


@router.get("/cpq/rule-sets", response_model=PaginatedResponse[CpqRuleSetResponse])
def list_cpq_rule_sets(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: str = Query(None),
    status: str = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取CPQ规则集列表"""
    query = db.query(CpqRuleSet)
    query = apply_keyword_filter(query, CpqRuleSet, keyword, ["rule_name", "rule_code"])
    if status:
        query = query.filter(CpqRuleSet.status == status)

    total = query.count()
    rule_sets = (
        query.order_by(desc(CpqRuleSet.created_at))
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )
    return PaginatedResponse(
        items=[_serialize_rule_set(r) for r in rule_sets],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/cpq/rule-sets", response_model=CpqRuleSetResponse)
def create_cpq_rule_set(
    *,
    db: Session = Depends(deps.get_db),
    rule_set_in: CpqRuleSetCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建CPQ规则集"""
    existing = (
        db.query(CpqRuleSet)
        .filter(CpqRuleSet.rule_code == rule_set_in.rule_code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="规则集编码已存在")

    rule_set = CpqRuleSet(
        rule_code=rule_set_in.rule_code,
        rule_name=rule_set_in.rule_name,
        description=rule_set_in.description,
        status=rule_set_in.status or "ACTIVE",
        base_price=rule_set_in.base_price or Decimal("0"),
        currency=rule_set_in.currency or "CNY",
        config_schema=rule_set_in.config_schema,
        pricing_matrix=rule_set_in.pricing_matrix,
        approval_threshold=rule_set_in.approval_threshold,
        visibility_scope=rule_set_in.visibility_scope or "ALL",
        is_default=rule_set_in.is_default or False,
        owner_role=rule_set_in.owner_role or (current_user.department or "SALES"),
    )
    db.add(rule_set)
    db.commit()
    db.refresh(rule_set)
    return _serialize_rule_set(rule_set)


@router.put("/cpq/rule-sets/{rule_set_id}", response_model=CpqRuleSetResponse)
def update_cpq_rule_set(
    *,
    db: Session = Depends(deps.get_db),
    rule_set_id: int,
    rule_set_in: CpqRuleSetUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新CPQ规则集"""
    rule_set = db.query(CpqRuleSet).filter(CpqRuleSet.id == rule_set_id).first()
    if not rule_set:
        raise HTTPException(status_code=404, detail="规则集不存在")

    update_data = rule_set_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule_set, field, value)
    db.commit()
    db.refresh(rule_set)
    return _serialize_rule_set(rule_set)


@router.post("/cpq/price-preview", response_model=CpqPricePreviewResponse)
def preview_cpq_price(
    *,
    db: Session = Depends(deps.get_db),
    preview_request: CpqPricePreviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """预览CPQ价格"""
    service = CpqPricingService(db)
    preview_data = service.preview_price(
        rule_set_id=preview_request.rule_set_id,
        template_version_id=preview_request.template_version_id,
        selections=preview_request.selections,
        manual_discount_pct=preview_request.manual_discount_pct,
        manual_markup_pct=preview_request.manual_markup_pct,
    )
    return CpqPricePreviewResponse(**preview_data)
