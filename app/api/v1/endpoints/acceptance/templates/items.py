# -*- coding: utf-8 -*-
"""
验收模板管理 - 检查项管理
"""
from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import (
    AcceptanceTemplate,
    TemplateCategory,
    TemplateCheckItem,
)
from app.models.user import User
from app.schemas.acceptance import TemplateCheckItemCreate
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/acceptance-templates/{template_id}/items", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_template_items(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取模板检查项列表
    """
    template = get_or_404(db, AcceptanceTemplate, template_id, "验收模板不存在")

    categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template_id).order_by(TemplateCategory.sort_order).all()

    items_data = []
    for category in categories:
        items = db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).order_by(TemplateCheckItem.sort_order).all()
        for item in items:
            items_data.append({
                "id": item.id,
                "category_id": category.id,
                "category_code": category.category_code,
                "category_name": category.category_name,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "check_method": item.check_method,
                "acceptance_criteria": item.acceptance_criteria,
                "standard_value": item.standard_value,
                "tolerance_min": item.tolerance_min,
                "tolerance_max": item.tolerance_max,
                "unit": item.unit,
                "is_required": item.is_required,
                "is_key_item": item.is_key_item,
                "sort_order": item.sort_order
            })

    return items_data


@router.post("/acceptance-templates/{template_id}/items", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_template_items(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    category_id: int = Query(..., description="分类ID"),
    items: List[TemplateCheckItemCreate] = Body(...),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加模板检查项
    """
    template = get_or_404(db, AcceptanceTemplate, template_id, "验收模板不存在")

    category = db.query(TemplateCategory).filter(
        TemplateCategory.id == category_id,
        TemplateCategory.template_id == template_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在或不属于该模板")

    for item_in in items:
        item = TemplateCheckItem(
            category_id=category_id,
            item_code=item_in.item_code,
            item_name=item_in.item_name,
            check_method=item_in.check_method,
            acceptance_criteria=item_in.acceptance_criteria,
            standard_value=item_in.standard_value,
            tolerance_min=item_in.tolerance_min,
            tolerance_max=item_in.tolerance_max,
            unit=item_in.unit,
            is_required=item_in.is_required,
            is_key_item=item_in.is_key_item,
            sort_order=item_in.sort_order
        )
        db.add(item)

    db.commit()

    return ResponseModel(message="检查项添加成功")
