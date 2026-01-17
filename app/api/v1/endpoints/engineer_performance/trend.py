# -*- coding: utf-8 -*-
"""
绩效趋势分析 API 端点
"""

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.performance_trend_service import PerformanceTrendService

router = APIRouter(prefix="/trend", tags=["趋势分析"])


@router.get("/engineer/{engineer_id}", summary="获取工程师历史趋势")
async def get_engineer_trend(
    engineer_id: int,
    periods: int = Query(6, ge=2, le=12, description="历史周期数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师历史6个周期的得分趋势"""
    service = PerformanceTrendService(db)

    trend_data = service.get_engineer_trend(engineer_id, periods)

    return ResponseModel(
        code=200,
        message="获取趋势数据成功",
        data=trend_data
    )


@router.get("/ability-changes/{engineer_id}", summary="识别能力变化")
async def identify_ability_changes(
    engineer_id: int,
    periods: int = Query(6, ge=2, le=12, description="历史周期数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """识别工程师能力变化（提升/下降/稳定）"""
    service = PerformanceTrendService(db)

    changes = service.identify_ability_changes(engineer_id, periods)

    return ResponseModel(
        code=200,
        message="识别能力变化成功",
        data=changes
    )


@router.get("/department/{department_id}", summary="获取部门整体趋势")
async def get_department_trend(
    department_id: int,
    periods: int = Query(6, ge=2, le=12, description="历史周期数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部门整体趋势"""
    service = PerformanceTrendService(db)

    trend_data = service.get_department_trend(department_id, periods)

    return ResponseModel(
        code=200,
        message="获取部门趋势数据成功",
        data=trend_data
    )


class CompareDepartmentsRequest(BaseModel):
    """部门对比请求"""
    department_ids: List[int] = Field(..., description="部门ID列表")
    period_id: int = Field(..., description="考核周期ID")


@router.post("/compare-departments", summary="对比多个部门趋势")
async def compare_departments(
    request: CompareDepartmentsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """对比多个部门的趋势"""
    service = PerformanceTrendService(db)

    try:
        comparison = service.compare_departments(
            department_ids=request.department_ids,
            period_id=request.period_id
        )
        return ResponseModel(
            code=200,
            message="部门对比分析成功",
            data=comparison
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
