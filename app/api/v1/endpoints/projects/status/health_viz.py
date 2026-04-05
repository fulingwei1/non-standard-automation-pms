# -*- coding: utf-8 -*-
"""
项目健康度可视化端点

提供健康度趋势、风险因素拆解、改进建议的 API。
"""

from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get(
    "/{project_id}/health/trend",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_health_trend(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    days: int = Query(30, ge=7, le=90, description="趋势天数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目健康度趋势（近 N 天）"""
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    from app.services.health_trend_service import HealthTrendService

    svc = HealthTrendService(db)
    data = svc.get_health_trend(project_id, days=days)
    return ResponseModel(code=200, message="success", data=data)


@router.get(
    "/{project_id}/health/risk-breakdown",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_risk_breakdown(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取风险因素拆解"""
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    from app.services.health_trend_service import HealthTrendService

    svc = HealthTrendService(db)
    data = svc.get_risk_breakdown(project_id)
    return ResponseModel(code=200, message="success", data=data)


@router.get(
    "/{project_id}/health/improvements",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_improvement_suggestions(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取改进建议"""
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    from app.services.health_trend_service import HealthTrendService

    svc = HealthTrendService(db)
    data = svc.get_improvement_suggestions(project_id)
    return ResponseModel(code=200, message="success", data=data)
