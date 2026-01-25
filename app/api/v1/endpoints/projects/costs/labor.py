# -*- coding: utf-8 -*-
"""
项目人工成本计算模块

提供项目人工成本自动计算功能，从工时记录中计算人工成本。
路由: /projects/{project_id}/costs/labor
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/calculate-labor-cost", response_model=ResponseModel)
def calculate_project_labor_cost(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD，可选）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD，可选）"),
    recalculate: bool = Query(False, description="是否重新计算（删除现有记录重新计算）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    计算项目人工成本
    从已审批的工时记录自动计算项目人工成本
    """
    from app.services.labor_cost_service import LaborCostService

    start = None
    end = None

    if start_date:
        try:
            start = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="开始日期格式错误，请使用YYYY-MM-DD格式")

    if end_date:
        try:
            end = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="结束日期格式错误，请使用YYYY-MM-DD格式")

    try:
        result = LaborCostService.calculate_project_labor_cost(
            db, project_id, start, end, recalculate
        )
        return ResponseModel(
            code=200,
            message=result.get("message", "计算完成"),
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败：{str(e)}")
