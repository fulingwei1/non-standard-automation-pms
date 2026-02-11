# -*- coding: utf-8 -*-
"""
优势产品CRUD端点
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.advantage_product import AdvantageProduct, AdvantageProductCategory
from app.models.user import User
from app.schemas.advantage_product import (
    AdvantageProductCategoryResponse,
    AdvantageProductCreate,
    AdvantageProductGrouped,
    AdvantageProductResponse,
    AdvantageProductSimple,
    AdvantageProductUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[AdvantageProductResponse])
def get_products(
    category_id: Optional[int] = Query(None, description="按类别筛选"),
    search: Optional[str] = Query(None, description="搜索产品名称或编码"),
    include_inactive: bool = Query(False, description="是否包含已禁用的产品"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:read"))
):
    """获取优势产品列表"""
    query = db.query(AdvantageProduct)

    if not include_inactive:
        query = query.filter(AdvantageProduct.is_active == True)

    if category_id:
        query = query.filter(AdvantageProduct.category_id == category_id)

    query = apply_keyword_filter(query, AdvantageProduct, search, ["product_name", "product_code"], use_ilike=False)

    products = query.order_by(AdvantageProduct.product_code).all()

    # 获取类别名称映射
    categories = {c.id: c.name for c in db.query(AdvantageProductCategory).all()}

    result = []
    for p in products:
        result.append(AdvantageProductResponse(
            id=p.id,
            product_code=p.product_code,
            product_name=p.product_name,
            category_id=p.category_id,
            series_code=p.series_code,
            description=p.description,
            is_active=p.is_active,
            category_name=categories.get(p.category_id),
            created_at=p.created_at,
            updated_at=p.updated_at
        ))

    return result


@router.get("/grouped", response_model=List[AdvantageProductGrouped])
def get_products_grouped(
    include_inactive: bool = Query(False, description="是否包含已禁用的"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:read"))
):
    """获取按类别分组的产品列表"""
    # 获取所有类别
    cat_query = db.query(AdvantageProductCategory)
    if not include_inactive:
        cat_query = cat_query.filter(AdvantageProductCategory.is_active == True)
    categories = cat_query.order_by(AdvantageProductCategory.sort_order).all()

    result = []
    for cat in categories:
        # 获取该类别下的产品
        prod_query = db.query(AdvantageProduct).filter(
            AdvantageProduct.category_id == cat.id
        )
        if not include_inactive:
            prod_query = prod_query.filter(AdvantageProduct.is_active == True)
        products = prod_query.order_by(AdvantageProduct.product_code).all()

        product_count = len(products)

        cat_response = AdvantageProductCategoryResponse(
            id=cat.id,
            code=cat.code,
            name=cat.name,
            description=cat.description,
            sort_order=cat.sort_order,
            is_active=cat.is_active,
            created_at=cat.created_at,
            updated_at=cat.updated_at,
            product_count=product_count
        )

        prod_responses = [
            AdvantageProductResponse(
                id=p.id,
                product_code=p.product_code,
                product_name=p.product_name,
                category_id=p.category_id,
                series_code=p.series_code,
                description=p.description,
                is_active=p.is_active,
                category_name=cat.name,
                created_at=p.created_at,
                updated_at=p.updated_at
            )
            for p in products
        ]

        result.append(AdvantageProductGrouped(
            category=cat_response,
            products=prod_responses
        ))

    return result


@router.get("/simple", response_model=List[AdvantageProductSimple])
def get_products_simple(
    category_id: Optional[int] = Query(None, description="按类别筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:read"))
):
    """获取产品简略列表（用于下拉选择）"""
    query = db.query(AdvantageProduct).filter(AdvantageProduct.is_active == True)

    if category_id:
        query = query.filter(AdvantageProduct.category_id == category_id)

    products = query.order_by(AdvantageProduct.product_code).all()

    # 获取类别名称映射
    categories = {c.id: c.name for c in db.query(AdvantageProductCategory).all()}

    return [
        AdvantageProductSimple(
            id=p.id,
            product_code=p.product_code,
            product_name=p.product_name,
            category_id=p.category_id,
            category_name=categories.get(p.category_id)
        )
        for p in products
    ]


@router.post("/", response_model=AdvantageProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: AdvantageProductCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:create"))
):
    """创建优势产品"""
    # 检查产品编码是否已存在
    existing = db.query(AdvantageProduct).filter(
        AdvantageProduct.product_code == product_in.product_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"产品编码 '{product_in.product_code}' 已存在"
        )

    # 检查类别是否存在
    if product_in.category_id:
        category = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == product_in.category_id
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的类别不存在"
            )

    product = AdvantageProduct(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    category_name = None
    if product.category_id:
        cat = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == product.category_id
        ).first()
        category_name = cat.name if cat else None

    return AdvantageProductResponse(
        id=product.id,
        product_code=product.product_code,
        product_name=product.product_name,
        category_id=product.category_id,
        series_code=product.series_code,
        description=product.description,
        is_active=product.is_active,
        category_name=category_name,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.put("/{product_id}", response_model=AdvantageProductResponse)
def update_product(
    product_id: int,
    product_in: AdvantageProductUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:update"))
):
    """更新优势产品"""
    product = db.query(AdvantageProduct).filter(
        AdvantageProduct.id == product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )

    update_data = product_in.model_dump(exclude_unset=True)

    # 检查类别是否存在
    if "category_id" in update_data and update_data["category_id"]:
        category = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == update_data["category_id"]
        ).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的类别不存在"
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    category_name = None
    if product.category_id:
        cat = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == product.category_id
        ).first()
        category_name = cat.name if cat else None

    return AdvantageProductResponse(
        id=product.id,
        product_code=product.product_code,
        product_name=product.product_name,
        category_id=product.category_id,
        series_code=product.series_code,
        description=product.description,
        is_active=product.is_active,
        category_name=category_name,
        created_at=product.created_at,
        updated_at=product.updated_at
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:delete"))
):
    """删除优势产品（软删除）"""
    product = db.query(AdvantageProduct).filter(
        AdvantageProduct.id == product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在"
        )

    product.is_active = False
    db.commit()
