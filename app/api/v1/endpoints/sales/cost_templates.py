# -*- coding: utf-8 -*-
"""
成本管理 - 报价成本模板管理

包含成本模板的CRUD操作
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.sales import QuoteCostTemplate
from app.models.sales.operation_log import SalesEntityType, SalesOperationType
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.sales import (
    QuoteCostTemplateCreate,
    QuoteCostTemplateResponse,
    QuoteCostTemplateUpdate,
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
    if isinstance(value, dict):
        return {key: _audit_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_audit_value(item) for item in value]
    return value


def _cost_template_audit_value(template: QuoteCostTemplate) -> dict[str, Any]:
    return {
        "template_id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "template_type": template.template_type,
        "equipment_type": template.equipment_type,
        "industry": template.industry,
        "description": template.description,
        "cost_structure": _audit_value(template.cost_structure),
        "total_cost": _audit_value(template.total_cost),
        "cost_categories": template.cost_categories,
        "is_active": template.is_active,
        "usage_count": template.usage_count,
        "created_by": template.created_by,
    }


def _changed_fields(old_value: dict[str, Any], new_value: dict[str, Any]) -> list[str]:
    return [
        field
        for field, value in new_value.items()
        if field in old_value and old_value[field] != value
    ]


def _log_cost_template_operation(
    db: Session,
    template: QuoteCostTemplate,
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
        entity_type=SalesEntityType.QUOTE_COST_TEMPLATE,
        entity_id=template.id,
        entity_code=template.template_code,
        operation_type=operation_type,
        operator=operator,
        operation_desc=operation_desc,
        old_value=old_snapshot,
        new_value=new_snapshot,
        changed_fields=_changed_fields(old_snapshot, new_snapshot),
        remark=template.template_name,
    )


def _build_template_response(template: QuoteCostTemplate) -> QuoteCostTemplateResponse:
    return QuoteCostTemplateResponse(
        id=template.id,
        name=template.template_name,
        template_code=template.template_code,
        template_name=template.template_name,
        template_type=template.template_type,
        equipment_type=template.equipment_type,
        industry=template.industry,
        description=template.description,
        category=template.template_type,
        items=(
            (template.cost_structure or {}).get("items")
            if isinstance(template.cost_structure, dict)
            else None
        ),
        cost_structure=template.cost_structure,
        total_cost=template.total_cost,
        is_active=template.is_active,
        usage_count=template.usage_count,
        creator_name=template.creator.real_name if template.creator else None,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/cost-templates", response_model=PaginatedResponse[QuoteCostTemplateResponse])
def get_cost_templates(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    template_type: Optional[str] = Query(None, description="模板类型筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本模板列表
    """
    query = db.query(QuoteCostTemplate)

    if template_type:
        query = query.filter(QuoteCostTemplate.template_type == template_type)
    if equipment_type:
        query = query.filter(QuoteCostTemplate.equipment_type == equipment_type)
    if industry:
        query = query.filter(QuoteCostTemplate.industry == industry)
    if is_active is not None:
        query = query.filter(QuoteCostTemplate.is_active == is_active)

    total = query.count()
    templates = apply_pagination(
        query.order_by(desc(QuoteCostTemplate.created_at)),
        pagination.offset,
        pagination.limit,
    ).all()

    items = [_build_template_response(template) for template in templates]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.get("/cost-templates/{template_id}", response_model=QuoteCostTemplateResponse)
def get_cost_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本模板详情
    """
    template = get_or_404(db, QuoteCostTemplate, template_id, detail="成本模板不存在")
    return _build_template_response(template)


@router.post("/cost-templates", response_model=QuoteCostTemplateResponse, status_code=201)
def create_cost_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: QuoteCostTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建成本模板
    """
    payload = template_in.model_dump(exclude_unset=True)
    template_name = payload.get("template_name") or payload.get("name")
    if not template_name:
        raise HTTPException(status_code=422, detail="模板名称不能为空")

    template_code = payload.get("template_code")
    if not template_code:
        template_code = f"QCT{datetime.now().strftime('%Y%m%d%H%M%S')}"

    cost_structure = payload.get("cost_structure")
    if cost_structure is None and payload.get("items") is not None:
        cost_structure = {"items": payload.get("items")}

    template = QuoteCostTemplate(
        template_code=template_code,
        template_name=template_name,
        template_type=payload.get("template_type") or payload.get("category"),
        equipment_type=payload.get("equipment_type"),
        industry=payload.get("industry"),
        description=payload.get("description"),
        cost_structure=cost_structure,
        is_active=True if payload.get("is_active") is None else payload.get("is_active"),
        created_by=current_user.id,
    )
    db.add(template)
    db.flush()
    _log_cost_template_operation(
        db,
        template,
        SalesOperationType.CREATE,
        current_user,
        new_value=_cost_template_audit_value(template),
        operation_desc="创建报价成本模板",
    )
    db.commit()
    db.refresh(template)
    return _build_template_response(template)


@router.put("/cost-templates/{template_id}", response_model=QuoteCostTemplateResponse)
def update_cost_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: QuoteCostTemplateUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新成本模板
    """
    template = get_or_404(db, QuoteCostTemplate, template_id, detail="成本模板不存在")

    payload = template_in.model_dump(exclude_unset=True)
    old_value = _cost_template_audit_value(template)

    if "template_code" in payload:
        template.template_code = payload["template_code"]

    if "template_name" in payload or "name" in payload:
        mapped_name = payload.get("template_name") or payload.get("name")
        if mapped_name:
            template.template_name = mapped_name

    if "template_type" in payload or "category" in payload:
        template.template_type = payload.get("template_type") or payload.get("category")

    if "equipment_type" in payload:
        template.equipment_type = payload.get("equipment_type")

    if "industry" in payload:
        template.industry = payload.get("industry")

    if "description" in payload:
        template.description = payload.get("description")

    if "is_active" in payload:
        template.is_active = payload.get("is_active")

    if "cost_structure" in payload or "items" in payload:
        cost_structure = payload.get("cost_structure")
        if cost_structure is None and payload.get("items") is not None:
            cost_structure = {"items": payload.get("items")}
        template.cost_structure = cost_structure

    _log_cost_template_operation(
        db,
        template,
        SalesOperationType.UPDATE,
        current_user,
        old_value=old_value,
        new_value=_cost_template_audit_value(template),
        operation_desc="更新报价成本模板",
    )
    db.commit()
    db.refresh(template)
    return _build_template_response(template)


@router.delete("/cost-templates/{template_id}", status_code=200)
def delete_cost_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除成本模板
    """
    template = get_or_404(db, QuoteCostTemplate, template_id, detail="成本模板不存在")

    old_value = _cost_template_audit_value(template)
    db.delete(template)
    _log_cost_template_operation(
        db,
        template,
        SalesOperationType.DELETE,
        current_user,
        old_value=old_value,
        new_value={},
        operation_desc="删除报价成本模板",
    )
    db.commit()
    return ResponseModel(code=200, message="删除成功")
