# -*- coding: utf-8 -*-
"""
项目预算执行分析模块

提供项目预算执行情况分析和趋势分析。
路由: /projects/{project_id}/costs/budget
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


@router.get("/execution", response_model=ResponseModel)
def get_budget_execution_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目预算执行情况分析
    """
    from app.services.budget_analysis_service import BudgetAnalysisService

    try:
        result = BudgetAnalysisService.get_budget_execution_analysis(db, project_id)
        return ResponseModel(
            code=200,
            message="success",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算执行分析失败：{str(e)}")


@router.get("/trend", response_model=ResponseModel)
def get_budget_trend_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目预算执行趋势分析（按时间维度）
    """
    from app.services.budget_analysis_service import BudgetAnalysisService

    try:
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None

        result = BudgetAnalysisService.get_budget_trend_analysis(
            db, project_id, start_date=start, end_date=end
        )
        return ResponseModel(
            code=200,
            message="success",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算趋势分析失败：{str(e)}")
