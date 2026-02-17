# -*- coding: utf-8 -*-
"""
验收模板管理 - 业务操作（复制）
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import (
    AcceptanceTemplate,
    TemplateCategory,
    TemplateCheckItem,
)
from app.models.user import User
from app.schemas.acceptance import AcceptanceTemplateResponse
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


@router.post("/acceptance-templates/{template_id}/copy", response_model=AcceptanceTemplateResponse, status_code=status.HTTP_201_CREATED)
def copy_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    new_code: str = Query(..., description="新模板编码"),
    new_name: str = Query(..., description="新模板名称"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复制验收模板
    """
    source_template = get_or_404(db, AcceptanceTemplate, template_id, "源模板不存在")

    # 检查新编码是否已存在
    existing = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.template_code == new_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    # 创建新模板
    new_template = AcceptanceTemplate(
        template_code=new_code,
        template_name=new_name,
        acceptance_type=source_template.acceptance_type,
        equipment_type=source_template.equipment_type,
        version="1.0",
        description=source_template.description,
        is_system=False,
        is_active=True,
        created_by=current_user.id
    )
    db.add(new_template)
    db.flush()

    # 复制分类和检查项
    source_categories = db.query(TemplateCategory).filter(
        TemplateCategory.template_id == template_id
    ).order_by(TemplateCategory.sort_order).all()

    for source_category in source_categories:
        # 创建新分类
        new_category = TemplateCategory(
            template_id=new_template.id,
            category_code=source_category.category_code,
            category_name=source_category.category_name,
            weight=source_category.weight,
            sort_order=source_category.sort_order,
            is_required=source_category.is_required,
            description=source_category.description
        )
        db.add(new_category)
        db.flush()

        # 复制检查项
        source_items = db.query(TemplateCheckItem).filter(
            TemplateCheckItem.category_id == source_category.id
        ).order_by(TemplateCheckItem.sort_order).all()

        for source_item in source_items:
            new_item = TemplateCheckItem(
                category_id=new_category.id,
                item_code=source_item.item_code,
                item_name=source_item.item_name,
                check_method=source_item.check_method,
                acceptance_criteria=source_item.acceptance_criteria,
                standard_value=source_item.standard_value,
                tolerance_min=source_item.tolerance_min,
                tolerance_max=source_item.tolerance_max,
                unit=source_item.unit,
                is_required=source_item.is_required,
                is_key_item=source_item.is_key_item,
                sort_order=source_item.sort_order
            )
            db.add(new_item)

    db.commit()
    db.refresh(new_template)

    return AcceptanceTemplateResponse(
        id=new_template.id,
        template_code=new_template.template_code,
        template_name=new_template.template_name,
        acceptance_type=new_template.acceptance_type,
        equipment_type=new_template.equipment_type,
        version=new_template.version,
        is_system=new_template.is_system,
        is_active=new_template.is_active,
        created_at=new_template.created_at,
        updated_at=new_template.updated_at
    )
