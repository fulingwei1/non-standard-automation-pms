# -*- coding: utf-8 -*-
"""
物料分类端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import MaterialCategory
from app.models.user import User
from app.schemas.material import MaterialCategoryResponse

router = APIRouter()


@router.get("/categories/", response_model=List[MaterialCategoryResponse])
def read_material_categories(
    db: Session = Depends(deps.get_db),
    parent_id: Optional[int] = Query(None, description="父分类ID，为空则返回顶级分类"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """获取物料分类列表"""
    query = db.query(MaterialCategory)

    # 父分类筛选
    if parent_id is None:
        query = query.filter(MaterialCategory.parent_id.is_(None))
    else:
        query = query.filter(MaterialCategory.parent_id == parent_id)

    # 启用状态筛选
    if is_active is not None:
        query = query.filter(MaterialCategory.is_active == is_active)

    categories = query.order_by(MaterialCategory.sort_order, MaterialCategory.category_code).all()

    # 构建树形结构
    def build_tree(category_list, parent_id=None):
        result = []
        for cat in category_list:
            if (parent_id is None and cat.parent_id is None) or (parent_id and cat.parent_id == parent_id):
                children = build_tree(category_list, cat.id)
                item = MaterialCategoryResponse(
                    id=cat.id,
                    category_code=cat.category_code,
                    category_name=cat.category_name,
                    parent_id=cat.parent_id,
                    level=cat.level,
                    full_path=cat.full_path,
                    is_active=cat.is_active,
                    children=children,
                    created_at=cat.created_at,
                    updated_at=cat.updated_at,
                )
                result.append(item)
        return result

    return build_tree(categories)
