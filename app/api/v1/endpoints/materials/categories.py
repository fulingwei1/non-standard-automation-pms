# -*- coding: utf-8 -*-
"""
物料分类端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.material import MaterialCategoryResponse
from app.services.material_category_service import MaterialCategoryService

router = APIRouter()


@router.get("/categories/", response_model=List[MaterialCategoryResponse])
def read_material_categories(
    db: Session = Depends(deps.get_db),
    parent_id: Optional[int] = Query(
        None, description="父分类ID，为空则返回顶级分类树"
    ),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """获取物料分类列表（树形结构）"""
    service = MaterialCategoryService(db)
    # 如果指定了 is_active，建议在 service 中增加过滤，或者简单在这里处理
    # 目前 get_tree 默认获取所有。
    return service.get_tree(parent_id)
