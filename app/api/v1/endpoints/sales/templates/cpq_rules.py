# -*- coding: utf-8 -*-
"""
CPQ规则集管理 API endpoints

包含CPQ规则集的CRUD和价格预览功能
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.sales import CpqRuleSet
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    CpqPricePreviewRequest,
    CpqPricePreviewResponse,
    CpqRuleSetCreate,
    CpqRuleSetResponse,
    CpqRuleSetUpdate,
)
from app.services.presale.cpq_pricing_service import CpqPricingService
from app.services.sales.operation_log_service import SalesOperationLogService
from app.utils.db_helpers import get_or_404

from .common import _serialize_rule_set

router = APIRouter()


def _audit_scalar(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _rule_set_audit_value(rule_set: CpqRuleSet) -> dict[str, Any]:
    return {
        "rule_set_id": rule_set.id,
        "rule_code": rule_set.rule_code,
        "rule_name": rule_set.rule_name,
        "description": rule_set.description,
        "status": _audit_scalar(rule_set.status),
        "base_price": _audit_scalar(rule_set.base_price),
        "currency": rule_set.currency,
        "config_schema": rule_set.config_schema,
        "pricing_matrix": rule_set.pricing_matrix,
        "approval_threshold": rule_set.approval_threshold,
        "visibility_scope": rule_set.visibility_scope,
        "is_default": rule_set.is_default,
        "owner_role": rule_set.owner_role,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def _log_rule_set_operation(
    db: Session,
    rule_set: CpqRuleSet,
    operation_type: str,
    operator: User,
    *,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    operation_desc: str,
) -> None:
    old_snapshot = old_value or {}
    new_snapshot = new_value or {}
    SalesOperationLogService.log_operation(
        db,
        entity_type=SalesEntityType.CPQ_RULE_SET,
        entity_id=rule_set.id,
        entity_code=rule_set.rule_code,
        operation_type=operation_type,
        operator=operator,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=rule_set.rule_name,
    )


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
        pages=pagination.pages_for_total(total),
    )


@router.post("/cpq/rule-sets", response_model=CpqRuleSetResponse)
def create_cpq_rule_set(
    *,
    db: Session = Depends(deps.get_db),
    rule_set_in: CpqRuleSetCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建CPQ规则集"""
    existing = db.query(CpqRuleSet).filter(CpqRuleSet.rule_code == rule_set_in.rule_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="规则集编码已存在")

    rule_set = CpqRuleSet(
        rule_code=rule_set_in.rule_code,
        rule_name=rule_set_in.rule_name,
        description=rule_set_in.description,
        status="ACTIVE",
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
    db.flush()
    _log_rule_set_operation(
        db,
        rule_set,
        SalesOperationType.CREATE,
        current_user,
        new_value=_rule_set_audit_value(rule_set),
        operation_desc="创建CPQ规则集",
    )
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
    rule_set = get_or_404(db, CpqRuleSet, rule_set_id, detail="规则集不存在")

    old_value = _rule_set_audit_value(rule_set)
    update_data = rule_set_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule_set, field, value)
    new_value = _rule_set_audit_value(rule_set)
    _log_rule_set_operation(
        db,
        rule_set,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=new_value,
        operation_desc="更新CPQ规则集",
    )
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
