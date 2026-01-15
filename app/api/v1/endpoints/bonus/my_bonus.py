# -*- coding: utf-8 -*-
"""
我的奖金 - 自动生成
从 bonus.py 拆分
"""

# -*- coding: utf-8 -*-
"""
奖金激励模块 API 端点
"""

from typing import Any, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
import os
import io
import uuid
from pathlib import Path

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.bonus import (
    BonusRule, BonusCalculation, BonusDistribution, TeamBonusAllocation, BonusAllocationSheet
)
from app.models.performance import PerformanceResult, ProjectContribution, PerformancePeriod
from app.models.project import Project, ProjectMilestone
from app.models.sales import Contract, Invoice
from app.models.presale import PresaleSupportTicket
from app.schemas.bonus import (
    BonusRuleCreate, BonusRuleUpdate, BonusRuleResponse, BonusRuleListResponse,
    BonusCalculationCreate, BonusCalculationResponse, BonusCalculationListResponse,
    BonusCalculationApprove, BonusCalculationQuery,
    BonusDistributionCreate, BonusDistributionResponse, BonusDistributionListResponse,
    BonusDistributionPay, BonusDistributionQuery,
    TeamBonusAllocationCreate, TeamBonusAllocationResponse, TeamBonusAllocationListResponse,
    TeamBonusAllocationApprove,
    CalculatePerformanceBonusRequest, CalculateProjectBonusRequest,
    CalculateMilestoneBonusRequest, CalculateTeamBonusRequest,
    CalculateSalesBonusRequest, CalculateSalesDirectorBonusRequest, CalculatePresaleBonusRequest,
    MyBonusResponse, BonusStatisticsResponse,
    BonusAllocationSheetResponse, BonusAllocationSheetConfirm, BonusAllocationRow
)
from app.schemas.common import ResponseModel, PageParams
from app.services.bonus_calculator import BonusCalculator

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



