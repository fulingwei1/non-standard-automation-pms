# -*- coding: utf-8 -*-
"""
研发费用类型管理
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.rd_project import RdCostType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.rd_project import RdCostTypeResponse

router = APIRouter()

# ==================== 研发费用类型 ====================

@router.get("/rd-cost-types", response_model=ResponseModel)
def get_rd_cost_types(
    db: Session = Depends(deps.get_db),
    category: Optional[str] = Query(None, description="费用大类筛选：LABOR/MATERIAL/DEPRECIATION/OTHER"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    获取研发费用类型列表
    """
    query = db.query(RdCostType)

    if category:
        query = query.filter(RdCostType.category == category)
    if is_active is not None:
        query = query.filter(RdCostType.is_active == is_active)

    cost_types = query.order_by(RdCostType.sort_order, RdCostType.type_code).all()

    return ResponseModel(
        code=200,
        message="success",
        data=[RdCostTypeResponse.model_validate(ct) for ct in cost_types]
    )



