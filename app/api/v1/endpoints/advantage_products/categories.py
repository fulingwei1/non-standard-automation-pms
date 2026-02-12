# -*- coding: utf-8 -*-
"""
产品类别管理端点
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.advantage_product import AdvantageProduct, AdvantageProductCategory
from app.models.user import User
from app.schemas.advantage_product import (
    AdvantageProductCategoryCreate,
    AdvantageProductCategoryResponse,
    AdvantageProductCategoryUpdate,
)

router = APIRouter()


@router.get("/categories", response_model=List[AdvantageProductCategoryResponse])
def get_categories(
    include_inactive: bool = Query(False, description="是否包含已禁用的类别"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:read"))
):
    """获取所有产品类别"""
    query = db.query(AdvantageProductCategory)
    if not include_inactive:
        query = query.filter(AdvantageProductCategory.is_active)

    categories = query.order_by(AdvantageProductCategory.sort_order).all()

    # 统计每个类别的产品数量
    result = []
    for cat in categories:
        product_count = db.query(func.count(AdvantageProduct.id)).filter(
            AdvantageProduct.category_id == cat.id,
            AdvantageProduct.is_active
        ).scalar()

        cat_dict = {
            "id": cat.id,
            "code": cat.code,
            "name": cat.name,
            "description": cat.description,
            "sort_order": cat.sort_order,
            "is_active": cat.is_active,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at,
            "product_count": product_count
        }
        result.append(AdvantageProductCategoryResponse(**cat_dict))

    return result


@router.post("/categories", response_model=AdvantageProductCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: AdvantageProductCategoryCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:create"))
):
    """创建产品类别"""
    # 检查编码是否已存在
    existing = db.query(AdvantageProductCategory).filter(
        AdvantageProductCategory.code == category_in.code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"类别编码 '{category_in.code}' 已存在"
        )

    category = AdvantageProductCategory(**category_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)

    return AdvantageProductCategoryResponse(
        **{**category.__dict__, "product_count": 0}
    )


@router.put("/categories/{category_id}", response_model=AdvantageProductCategoryResponse)
def update_category(
    category_id: int,
    category_in: AdvantageProductCategoryUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:update"))
):
    """更新产品类别"""
    category = db.query(AdvantageProductCategory).filter(
        AdvantageProductCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="类别不存在"
        )

    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    product_count = db.query(func.count(AdvantageProduct.id)).filter(
        AdvantageProduct.category_id == category.id,
        AdvantageProduct.is_active
    ).scalar()

    return AdvantageProductCategoryResponse(
        **{**category.__dict__, "product_count": product_count}
    )
