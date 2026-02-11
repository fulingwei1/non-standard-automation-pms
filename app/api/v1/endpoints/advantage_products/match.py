# -*- coding: utf-8 -*-
"""
产品匹配检查端点
"""

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.advantage_product import AdvantageProduct, AdvantageProductCategory
from app.models.user import User
from app.schemas.advantage_product import (
    AdvantageProductSimple,
    ProductMatchCheckRequest,
    ProductMatchCheckResponse,
)

router = APIRouter()


@router.post("/check-match", response_model=ProductMatchCheckResponse)
def check_product_match(
    request: ProductMatchCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:read"))
):
    """检查产品名称是否匹配优势产品"""
    product_name = request.product_name.strip()

    if not product_name:
        return ProductMatchCheckResponse(
            match_type="UNKNOWN",
            matched_product=None,
            suggestions=[]
        )

    # 精确匹配
    exact_match = db.query(AdvantageProduct).filter(
        AdvantageProduct.is_active == True,
        AdvantageProduct.product_name == product_name
    ).first()

    if exact_match:
        cat = db.query(AdvantageProductCategory).filter(
            AdvantageProductCategory.id == exact_match.category_id
        ).first()
        return ProductMatchCheckResponse(
            match_type="ADVANTAGE",
            matched_product=AdvantageProductSimple(
                id=exact_match.id,
                product_code=exact_match.product_code,
                product_name=exact_match.product_name,
                category_id=exact_match.category_id,
                category_name=cat.name if cat else None
            ),
            suggestions=[]
        )

    # 模糊匹配 - 查找相似产品
    base_query = db.query(AdvantageProduct).filter(AdvantageProduct.is_active == True)
    base_query = apply_keyword_filter(base_query, AdvantageProduct, product_name, ["product_name", "product_code"], use_ilike=False)
    similar_products = base_query.limit(5).all()

    categories = {c.id: c.name for c in db.query(AdvantageProductCategory).all()}

    suggestions = [
        AdvantageProductSimple(
            id=p.id,
            product_code=p.product_code,
            product_name=p.product_name,
            category_id=p.category_id,
            category_name=categories.get(p.category_id)
        )
        for p in similar_products
    ]

    if suggestions:
        return ProductMatchCheckResponse(
            match_type="ADVANTAGE",  # 有相似产品，可能是优势产品
            matched_product=None,
            suggestions=suggestions
        )

    # 没有匹配，视为新产品
    return ProductMatchCheckResponse(
        match_type="NEW",
        matched_product=None,
        suggestions=[]
    )
