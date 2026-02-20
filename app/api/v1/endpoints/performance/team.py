# -*- coding: utf-8 -*-
"""
团队/部门绩效 API endpoints
重构后的薄 controller，业务逻辑已迁移到服务层
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.performance import (
    DepartmentPerformanceResponse,
    PerformanceRankingResponse,
    TeamPerformanceResponse,
)
from app.services.team_performance import TeamPerformanceService

router = APIRouter(prefix="/performance/team", tags=["team"])


@router.get(
    "/team/{team_id}",
    response_model=TeamPerformanceResponse,
    status_code=status.HTTP_200_OK,
)
def get_team_performance(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    团队绩效汇总（平均分/排名）
    注：当前使用部门作为团队，team_id 对应 department.id
    """
    service = TeamPerformanceService(db)
    result = service.get_team_performance(team_id, period_id)
    return TeamPerformanceResponse(**result)


@router.get(
    "/department/{dept_id}",
    response_model=DepartmentPerformanceResponse,
    status_code=status.HTTP_200_OK,
)
def get_department_performance(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    部门绩效汇总（等级分布）
    """
    service = TeamPerformanceService(db)
    result = service.get_department_performance(dept_id, period_id)

    if result is None:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    return DepartmentPerformanceResponse(**result)


@router.get(
    "/ranking",
    response_model=PerformanceRankingResponse,
    status_code=status.HTTP_200_OK,
)
def get_performance_ranking(
    *,
    db: Session = Depends(deps.get_db),
    ranking_type: str = Query(
        "COMPANY", description="排行榜类型：TEAM/DEPARTMENT/COMPANY"
    ),
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    绩效排行榜（团队/部门/公司）
    """
    service = TeamPerformanceService(db)
    result = service.get_performance_ranking(ranking_type, period_id)

    if result is None:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    return PerformanceRankingResponse(**result)
