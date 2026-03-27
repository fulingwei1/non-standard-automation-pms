# -*- coding: utf-8 -*-
"""
绩效分析 API

提供绩效排行、团队效率、项目经理绩效、改进追踪四个端点。
支持按时间范围 / 部门 / 项目类型筛选。
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.performance_analysis_service import PerformanceAnalysisService

router = APIRouter()


@router.get(
    "/ranking",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="项目绩效排行",
)
def get_performance_ranking(
    start_date: Optional[date] = Query(None, description="筛选起始日期"),
    end_date: Optional[date] = Query(None, description="筛选截止日期"),
    dept_id: Optional[int] = Query(None, description="部门ID"),
    project_type: Optional[str] = Query(None, description="项目类型"),
    limit: int = Query(50, ge=1, le=200, description="返回条数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目绩效排行榜

    综合得分 = 健康度(40%) + 预算执行率(25%) + 进度偏差(25%) + 风险(10%)
    """
    service = PerformanceAnalysisService(db)
    data = service.get_performance_ranking(
        start_date=start_date,
        end_date=end_date,
        dept_id=dept_id,
        project_type=project_type,
        limit=limit,
    )
    return ResponseModel(data=data)


@router.get(
    "/team-efficiency",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="团队效率分析",
)
def get_team_efficiency(
    start_date: Optional[date] = Query(None, description="筛选起始日期"),
    end_date: Optional[date] = Query(None, description="筛选截止日期"),
    project_type: Optional[str] = Query(None, description="项目类型"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    团队效率分析

    输出各部门项目平均健康度、预算偏差率、里程碑按时完成率
    """
    service = PerformanceAnalysisService(db)
    data = service.get_team_efficiency(
        start_date=start_date,
        end_date=end_date,
        project_type=project_type,
    )
    return ResponseModel(data=data)


@router.get(
    "/pm",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="项目经理绩效",
)
def get_pm_performance(
    pm_id: Optional[int] = Query(None, description="项目经理ID（不传则返回全部）"),
    start_date: Optional[date] = Query(None, description="筛选起始日期"),
    end_date: Optional[date] = Query(None, description="筛选截止日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目经理绩效分析

    包含负责项目整体表现、历史趋势、管理幅度
    """
    service = PerformanceAnalysisService(db)
    data = service.get_pm_performance(
        pm_id=pm_id,
        start_date=start_date,
        end_date=end_date,
    )
    return ResponseModel(data=data)


@router.get(
    "/improvement",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
    summary="改进效果追踪",
)
def get_improvement_tracking(
    project_id: Optional[int] = Query(None, description="项目ID"),
    dept_id: Optional[int] = Query(None, description="部门ID"),
    days: int = Query(90, ge=7, le=365, description="追踪天数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    改进效果追踪

    健康度变化趋势、预警关闭率、风险缓解效果
    """
    service = PerformanceAnalysisService(db)
    data = service.get_improvement_tracking(
        project_id=project_id,
        dept_id=dept_id,
        days=days,
    )
    return ResponseModel(data=data)
