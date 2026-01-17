# -*- coding: utf-8 -*-
"""
我的奖金 - 自动生成
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
    prefix="/bonus/my",
    tags=["my_bonus"]
)

# 共 1 个路由

# ==================== 我的奖金 ====================

@router.get("/my", response_model=ResponseModel[MyBonusResponse], status_code=status.HTTP_200_OK)
def get_my_bonus(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取我的奖金
    """
    # 获取计算记录
    calculations = db.query(BonusCalculation).filter(
        BonusCalculation.user_id == current_user.id
    ).order_by(desc(BonusCalculation.calculated_at)).all()

    # 获取发放记录
    distributions = db.query(BonusDistribution).filter(
        BonusDistribution.user_id == current_user.id
    ).order_by(desc(BonusDistribution.distribution_date)).all()

    # 计算总金额
    total_amount = sum(float(c.calculated_amount) for c in calculations)
    paid_amount = sum(float(d.distributed_amount) for d in distributions if d.status == 'PAID')
    pending_amount = total_amount - paid_amount

    return ResponseModel(
        code=200,
        data=MyBonusResponse(
            total_amount=Decimal(str(total_amount)),
            pending_amount=Decimal(str(pending_amount)),
            paid_amount=Decimal(str(paid_amount)),
            calculations=calculations,
            distributions=distributions
        )
    )



