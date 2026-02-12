# -*- coding: utf-8 -*-
"""
成本管理 - 报价成本模板管理

包含成本模板的CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.sales import QuoteCostTemplate
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.common.pagination import PaginationParams, get_pagination_query
from app.schemas.sales import (
from app.common.query_filters import apply_pagination
    QuoteCostTemplateCreate,
    QuoteCostTemplateResponse,
    QuoteCostTemplateUpdate,
)

router = APIRouter()


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
    templates = apply_pagination(query.order_by(desc(QuoteCostTemplate.created_at)), pagination.offset, pagination.limit).all()

    items = []
    for template in templates:
        template_dict = {
            **{c.name: getattr(template, c.name) for c in template.__table__.columns},
            "creator_name": template.creator.real_name if template.creator else None
        }
        items.append(QuoteCostTemplateResponse(**template_dict))

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
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
    template = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="成本模板不存在")

    template_dict = {
        **{c.name: getattr(template, c.name) for c in template.__table__.columns},
        "creator_name": template.creator.real_name if template.creator else None
    }
    return QuoteCostTemplateResponse(**template_dict)


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
    template = QuoteCostTemplate(
        **template_in.model_dump(),
        created_by=current_user.id
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    template_dict = {
        **{c.name: getattr(template, c.name) for c in template.__table__.columns},
        "creator_name": template.creator.real_name if template.creator else None
    }
    return QuoteCostTemplateResponse(**template_dict)


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
    template = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="成本模板不存在")

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(template, field):
            setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)

    template_dict = {
        **{c.name: getattr(template, c.name) for c in template.__table__.columns},
        "creator_name": template.creator.real_name if template.creator else None
    }
    return QuoteCostTemplateResponse(**template_dict)


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
    template = db.query(QuoteCostTemplate).filter(QuoteCostTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="成本模板不存在")

    db.delete(template)
    db.commit()

    from app.schemas.common import ResponseModel
    return ResponseModel(code=200, message="删除成功")
