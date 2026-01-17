"""
人工成本计算

提供项目人工成本自动计算功能，从工时记录中计算人工成本。
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/projects/{project_id}/calculate-labor-cost", response_model=ResponseModel)
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


@router.post("/calculate-all-labor-costs", response_model=ResponseModel)
def calculate_all_projects_labor_cost(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD，可选）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD，可选）"),
    project_ids: Optional[List[int]] = Query(None, description="项目ID列表（可选，不提供则计算所有项目）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    批量计算所有项目的人工成本
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
        result = LaborCostService.calculate_all_projects_labor_cost(
            db, start, end, project_ids
        )
        return ResponseModel(
            code=200,
            message=result.get("message", "批量计算完成"),
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量计算失败：{str(e)}")


@router.post("/calculate-monthly-labor-cost", response_model=ResponseModel)
def calculate_monthly_labor_cost(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    project_ids: Optional[List[int]] = Query(None, description="项目ID列表（可选）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    计算指定月份的项目人工成本
    """
    from app.services.labor_cost_service import LaborCostService

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="月份必须在1-12之间")

    try:
        result = LaborCostService.calculate_monthly_labor_cost(
            db, year, month, project_ids
        )
        return ResponseModel(
            code=200,
            message=result.get("message", "月度计算完成"),
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"月度计算失败：{str(e)}")
