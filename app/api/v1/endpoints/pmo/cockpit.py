# -*- coding: utf-8 -*-
"""
PMO 驾驶舱 - 自动生成
从 pmo.py 拆分
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.pmo import (
    DashboardResponse,
    ResourceOverviewResponse,
    RiskWallResponse,
    WeeklyReportResponse,
)
from app.services.pmo_cockpit import PmoCockpitService

router = APIRouter(tags=["pmo-cockpit"])


# ==================== PMO 驾驶舱 ====================


@router.get("/pmo/dashboard", response_model=DashboardResponse)
def get_pmo_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    PMO 驾驶舱数据
    """
    service = PmoCockpitService(db)
    return service.get_dashboard()


@router.get("/pmo/risk-wall", response_model=RiskWallResponse)
def get_risk_wall(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    风险预警墙
    """
    service = PmoCockpitService(db)
    return service.get_risk_wall()


@router.get("/pmo/weekly-report", response_model=WeeklyReportResponse)
def get_weekly_report(
    db: Session = Depends(deps.get_db),
    week_start: Optional[date] = Query(None, description="周开始日期（默认：当前周）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目状态周报
    """
    service = PmoCockpitService(db)
    return service.get_weekly_report(week_start=week_start)


@router.get("/pmo/resource-overview", response_model=ResourceOverviewResponse)
def get_resource_overview(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    资源负荷总览
    """
    service = PmoCockpitService(db)
    return service.get_resource_overview()
