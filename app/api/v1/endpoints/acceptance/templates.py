# -*- coding: utf-8 -*-
"""
验收模板管理端点

包含：验收模板CRUD、分类管理、检查项管理
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.acceptance import (
    AcceptanceOrder,
    AcceptanceTemplate,
    TemplateCategory,
    TemplateCheckItem,
)
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceTemplateCreate,
    AcceptanceTemplateResponse,
    TemplateCheckItemCreate,
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


@router.get("/acceptance-templates", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_acceptance_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（编码/名称）"),
    acceptance_type: Optional[str] = Query(None, description="验收类型筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收模板列表
    """
    query = db.query(AcceptanceTemplate)

    if keyword:
        query = query.filter(
            or_(
                AcceptanceTemplate.template_code.like(f"%{keyword}%"),
                AcceptanceTemplate.template_name.like(f"%{keyword}%"),
            )
        )

    if acceptance_type:
        query = query.filter(AcceptanceTemplate.acceptance_type == acceptance_type)

    if equipment_type:
        query = query.filter(AcceptanceTemplate.equipment_type == equipment_type)

    if is_active is not None:
        query = query.filter(AcceptanceTemplate.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    templates = query.order_by(AcceptanceTemplate.created_at).offset(offset).limit(page_size).all()

    items = []
    for template in templates:
        items.append(AcceptanceTemplateResponse(
            id=template.id,
            template_code=template.template_code,
            template_name=template.template_name,
            acceptance_type=template.acceptance_type,
            equipment_type=template.equipment_type,
            version=template.version,
            is_system=template.is_system,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/acceptance-templates/{template_id}", response_model=dict, status_code=status.HTTP_200_OK)
def read_acceptance_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收模板详情（含分类和检查项）
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")

    # 获取分类
    categories_data = []
    categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template_id).order_by(TemplateCategory.sort_order).all()
    for category in categories:
        # 获取检查项
        items_data = []
        items = db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).order_by(TemplateCheckItem.sort_order).all()
        for item in items:
            items_data.append({
                "id": item.id,
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

        categories_data.append({
            "id": category.id,
            "category_code": category.category_code,
            "category_name": category.category_name,
            "weight": float(category.weight) if category.weight else 0,
            "sort_order": category.sort_order,
            "is_required": category.is_required,
            "description": category.description,
            "check_items": items_data
        })

    return {
        "id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "acceptance_type": template.acceptance_type,
        "equipment_type": template.equipment_type,
        "version": template.version,
        "description": template.description,
        "is_system": template.is_system,
        "is_active": template.is_active,
        "categories": categories_data,
        "created_at": template.created_at,
        "updated_at": template.updated_at
    }


@router.post("/acceptance-templates", response_model=AcceptanceTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: AcceptanceTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建验收模板
    """
    # 检查编码是否已存在
    existing = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.template_code == template_in.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = AcceptanceTemplate(
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        acceptance_type=template_in.acceptance_type,
        equipment_type=template_in.equipment_type,
        version=template_in.version,
        description=template_in.description,
        is_system=False,
        is_active=True,
        created_by=current_user.id
    )

    db.add(template)
    db.flush()  # 获取template.id

    # 创建分类和检查项
    for cat_in in template_in.categories:
        category = TemplateCategory(
            template_id=template.id,
            category_code=cat_in.category_code,
            category_name=cat_in.category_name,
            weight=cat_in.weight,
            sort_order=cat_in.sort_order,
            is_required=cat_in.is_required,
            description=cat_in.description
        )
        db.add(category)
        db.flush()  # 获取category.id

        # 创建检查项
        for item_in in cat_in.check_items:
            item = TemplateCheckItem(
                category_id=category.id,
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
    db.refresh(template)

    return AcceptanceTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        acceptance_type=template.acceptance_type,
        equipment_type=template.equipment_type,
        version=template.version,
        is_system=template.is_system,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.get("/acceptance-templates/{template_id}/items", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_template_items(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取模板检查项列表
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")

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
    items: List[TemplateCheckItemCreate],
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加模板检查项
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")

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


@router.put("/acceptance-templates/{template_id}", response_model=AcceptanceTemplateResponse, status_code=status.HTTP_200_OK)
def update_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: AcceptanceTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新验收模板
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")

    # 系统预置模板不能修改
    if template.is_system:
        raise HTTPException(status_code=400, detail="系统预置模板不能修改")

    # 检查编码是否已被其他模板使用
    if template_in.template_code != template.template_code:
        existing = db.query(AcceptanceTemplate).filter(
            AcceptanceTemplate.template_code == template_in.template_code,
            AcceptanceTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="模板编码已被使用")

    # 更新模板基本信息
    template.template_name = template_in.template_name
    template.acceptance_type = template_in.acceptance_type
    template.equipment_type = template_in.equipment_type
    template.version = template_in.version
    template.description = template_in.description

    db.add(template)
    db.commit()
    db.refresh(template)

    return AcceptanceTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        acceptance_type=template.acceptance_type,
        equipment_type=template.equipment_type,
        version=template.version,
        is_system=template.is_system,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at
    )


@router.delete("/acceptance-templates/{template_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_acceptance_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除验收模板（软删除）
    """
    template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="验收模板不存在")

    # 系统预置模板不能删除
    if template.is_system:
        raise HTTPException(status_code=400, detail="系统预置模板不能删除")

    # 检查是否被使用
    used_count = db.query(AcceptanceOrder).filter(AcceptanceOrder.template_id == template_id).count()
    if used_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"模板已被 {used_count} 个验收单使用，无法删除。建议禁用模板而不是删除"
        )

    # 软删除：删除分类和检查项
    categories = db.query(TemplateCategory).filter(TemplateCategory.template_id == template_id).all()
    for category in categories:
        # 删除检查项
        db.query(TemplateCheckItem).filter(TemplateCheckItem.category_id == category.id).delete()
        # 删除分类
        db.delete(category)

    # 删除模板
    db.delete(template)
    db.commit()

    return ResponseModel(message="验收模板已删除")


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
    source_template = db.query(AcceptanceTemplate).filter(AcceptanceTemplate.id == template_id).first()
    if not source_template:
        raise HTTPException(status_code=404, detail="源模板不存在")

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
