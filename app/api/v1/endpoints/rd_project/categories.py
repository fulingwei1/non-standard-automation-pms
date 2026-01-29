# -*- coding: utf-8 -*-
"""
研发项目分类管理
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.rd_project import RdProjectCategory
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.rd_project import RdProjectCategoryResponse

router = APIRouter()

# ==================== 研发项目分类 ====================

@router.get("/rd-project-categories", response_model=ResponseModel)
def get_rd_project_categories(
    db: Session = Depends(deps.get_db),
    category_type: Optional[str] = Query(None, description="分类类型筛选：SELF/ENTRUST/COOPERATION"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    获取研发项目分类列表
    """
    query = db.query(RdProjectCategory)

    if category_type:
        query = query.filter(RdProjectCategory.category_type == category_type)
    if is_active is not None:
        query = query.filter(RdProjectCategory.is_active == is_active)

    categories = query.order_by(RdProjectCategory.sort_order, RdProjectCategory.category_code).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[RdProjectCategoryResponse.model_validate(cat) for cat in categories]
    )



