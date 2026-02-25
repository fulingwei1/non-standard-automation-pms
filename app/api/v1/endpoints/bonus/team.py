# -*- coding: utf-8 -*-
"""
团队奖金分配 - 自动生成
从 bonus.py 拆分
"""

# -*- coding: utf-8 -*-
"""
奖金激励模块 API 端点
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.bonus import (
    TeamBonusAllocation,
)
from app.models.user import User
from app.schemas.bonus import (
    TeamBonusAllocationApprove,
    TeamBonusAllocationListResponse,
    TeamBonusAllocationResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter
from app.utils.db_helpers import get_or_404

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
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID"),
    period_id: Optional[int] = Query(None, description="周期ID"),
    allocation_status: Optional[str] = Query(None, alias="status", description="状态"),
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
    if allocation_status:
        query = query.filter(TeamBonusAllocation.status == allocation_status)

    total = query.count()
    allocations = query.order_by(desc(TeamBonusAllocation.created_at)).offset(
        pagination.offset
    ).limit(pagination.limit).all()

    return TeamBonusAllocationListResponse(
        items=allocations,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
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
    allocation = get_or_404(db, TeamBonusAllocation, allocation_id, "团队奖金分配记录不存在")

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
    allocation = get_or_404(db, TeamBonusAllocation, allocation_id, "团队奖金分配记录不存在")

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



