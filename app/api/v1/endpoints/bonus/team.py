# -*- coding: utf-8 -*-
"""
团队奖金分配 - 自动生成
从 bonus.py 拆分
"""

# -*- coding: utf-8 -*-
"""
奖金激励模块 API 端点
"""

import io
import os
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, List, Optional, Tuple

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.bonus import (
    BonusAllocationSheet,
    BonusCalculation,
    BonusDistribution,
    BonusRule,
    TeamBonusAllocation,
)
from app.models.performance import (
    PerformancePeriod,
    PerformanceResult,
    ProjectContribution,
)
from app.models.presale import PresaleSupportTicket
from app.models.project import Project, ProjectMilestone
from app.models.sales import Contract, Invoice
from app.models.user import User
from app.schemas.bonus import (
    BonusAllocationRow,
    BonusAllocationSheetConfirm,
    BonusAllocationSheetResponse,
    BonusCalculationApprove,
    BonusCalculationCreate,
    BonusCalculationListResponse,
    BonusCalculationQuery,
    BonusCalculationResponse,
    BonusDistributionCreate,
    BonusDistributionListResponse,
    BonusDistributionPay,
    BonusDistributionQuery,
    BonusDistributionResponse,
    BonusRuleCreate,
    BonusRuleListResponse,
    BonusRuleResponse,
    BonusRuleUpdate,
    BonusStatisticsResponse,
    CalculateMilestoneBonusRequest,
    CalculatePerformanceBonusRequest,
    CalculatePresaleBonusRequest,
    CalculateProjectBonusRequest,
    CalculateSalesBonusRequest,
    CalculateSalesDirectorBonusRequest,
    CalculateTeamBonusRequest,
    MyBonusResponse,
    TeamBonusAllocationApprove,
    TeamBonusAllocationCreate,
    TeamBonusAllocationListResponse,
    TeamBonusAllocationResponse,
)
from app.schemas.common import PageParams, ResponseModel
from app.services.bonus import BonusCalculator

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/bonus/team",
    tags=["team"]
)

# 共 3 个路由

# ==================== 团队奖金分配 ====================

@router.get("/team-allocations", response_model=TeamBonusAllocationListResponse, status_code=status.HTTP_200_OK)
def get_team_bonus_allocations(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    project_id: Optional[int] = Query(None, description="项目ID"),
    period_id: Optional[int] = Query(None, description="周期ID"),
    status: Optional[str] = Query(None, description="状态"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取团队奖金分配列表
    """
    query = db.query(TeamBonusAllocation)

    if project_id:
        query = query.filter(TeamBonusAllocation.project_id == project_id)
    if period_id:
        query = query.filter(TeamBonusAllocation.period_id == period_id)
    if status:
        query = query.filter(TeamBonusAllocation.status == status)

    total = query.count()
    allocations = query.order_by(desc(TeamBonusAllocation.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return TeamBonusAllocationListResponse(
        items=allocations,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/team-allocations/{allocation_id}", response_model=ResponseModel[TeamBonusAllocationResponse], status_code=status.HTTP_200_OK)
def get_team_bonus_allocation(
    *,
    db: Session = Depends(deps.get_db),
    allocation_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取团队奖金分配详情
    """
    allocation = db.query(TeamBonusAllocation).filter(TeamBonusAllocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="团队奖金分配记录不存在")

    return ResponseModel(code=200, data=allocation)


@router.post("/team-allocations/{allocation_id}/approve", response_model=ResponseModel[TeamBonusAllocationResponse], status_code=status.HTTP_200_OK)
def approve_team_bonus_allocation(
    *,
    db: Session = Depends(deps.get_db),
    allocation_id: int,
    approve_in: TeamBonusAllocationApprove,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批团队奖金分配
    """
    allocation = db.query(TeamBonusAllocation).filter(TeamBonusAllocation.id == allocation_id).first()
    if not allocation:
        raise HTTPException(status_code=404, detail="团队奖金分配记录不存在")

    if approve_in.approved:
        allocation.status = 'APPROVED'
        allocation.approved_by = current_user.id
        allocation.approved_at = datetime.now()
    else:
        allocation.status = 'REJECTED'
        allocation.approved_by = current_user.id
        allocation.approved_at = datetime.now()

    db.commit()
    db.refresh(allocation)

    return ResponseModel(code=200, message="审批完成", data=allocation)



