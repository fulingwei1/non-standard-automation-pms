# -*- coding: utf-8 -*-
"""
奖金计算 - 自动生成
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
    prefix="/bonus/calculation",
    tags=["calculation"]
)

# 共 4 个路由

# ==================== 奖金计算 ====================

@router.post("/calculate/performance", response_model=ResponseModel[List[BonusCalculationResponse]], status_code=status.HTTP_200_OK)
def calculate_performance_bonus(
    *,
    db: Session = Depends(deps.get_db),
    request: CalculatePerformanceBonusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算绩效奖金
    """
    calculator = BonusCalculator(db)

    # 获取绩效结果
    query = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == request.period_id
    )
    if request.user_id:
        query = query.filter(PerformanceResult.user_id == request.user_id)
    performance_results = query.all()

    if not performance_results:
        return ResponseModel(code=200, message="未找到绩效结果", data=[])

    # 获取规则
    if request.rule_id:
        rules = [db.query(BonusRule).filter(BonusRule.id == request.rule_id).first()]
        if not rules[0]:
            raise HTTPException(status_code=404, detail="规则不存在")
    else:
        rules = calculator.get_active_rules(bonus_type='PERFORMANCE_BASED')

    calculations = []
    for perf_result in performance_results:
        for rule in rules:
            calc = calculator.calculate_performance_bonus(perf_result, rule)
            if calc:
                db.add(calc)
                calculations.append(calc)

    db.commit()

    for calc in calculations:
        db.refresh(calc)

    return ResponseModel(code=200, message="计算完成", data=calculations)


@router.post("/calculate/project", response_model=ResponseModel[List[BonusCalculationResponse]], status_code=status.HTTP_200_OK)
def calculate_project_bonus(
    *,
    db: Session = Depends(deps.get_db),
    request: CalculateProjectBonusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算项目奖金
    """
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    calculator = BonusCalculator(db)

    # 获取项目贡献记录
    contributions = db.query(ProjectContribution).filter(
        ProjectContribution.project_id == request.project_id
    ).all()

    if not contributions:
        return ResponseModel(code=200, message="未找到项目贡献记录", data=[])

    # 获取规则
    if request.rule_id:
        rules = [db.query(BonusRule).filter(BonusRule.id == request.rule_id).first()]
        if not rules[0]:
            raise HTTPException(status_code=404, detail="规则不存在")
    else:
        rules = calculator.get_active_rules(bonus_type='PROJECT_BASED')

    calculations = []
    for contrib in contributions:
        for rule in rules:
            calc = calculator.calculate_project_bonus(contrib, project, rule)
            if calc:
                db.add(calc)
                calculations.append(calc)

    db.commit()

    for calc in calculations:
        db.refresh(calc)

    return ResponseModel(code=200, message="计算完成", data=calculations)


@router.post("/calculate/milestone", response_model=ResponseModel[List[BonusCalculationResponse]], status_code=status.HTTP_200_OK)
def calculate_milestone_bonus(
    *,
    db: Session = Depends(deps.get_db),
    request: CalculateMilestoneBonusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算里程碑奖金
    """
    milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == request.milestone_id).first()
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")

    project = db.query(Project).filter(Project.id == milestone.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    calculator = BonusCalculator(db)

    # 获取规则
    if request.rule_id:
        rules = [db.query(BonusRule).filter(BonusRule.id == request.rule_id).first()]
        if not rules[0]:
            raise HTTPException(status_code=404, detail="规则不存在")
    else:
        rules = calculator.get_active_rules(bonus_type='MILESTONE_BASED')

    calculations = []
    for rule in rules:
        calcs = calculator.calculate_milestone_bonus(milestone, project, rule)
        for calc in calcs:
            db.add(calc)
            calculations.append(calc)

    db.commit()

    for calc in calculations:
        db.refresh(calc)

    return ResponseModel(code=200, message="计算完成", data=calculations)


@router.post("/calculate/team", response_model=ResponseModel[TeamBonusAllocationResponse], status_code=status.HTTP_200_OK)
def calculate_team_bonus(
    *,
    db: Session = Depends(deps.get_db),
    request: CalculateTeamBonusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算团队奖金
    """
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    calculator = BonusCalculator(db)

    # 获取规则
    if request.rule_id:
        rule = db.query(BonusRule).filter(BonusRule.id == request.rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
    else:
        rules = calculator.get_active_rules(bonus_type='TEAM_BASED')
        if not rules:
            raise HTTPException(status_code=404, detail="未找到团队奖金规则")
        rule = rules[0]

    allocation = calculator.calculate_team_bonus(project, rule, request.period_id)
    db.add(allocation)
    db.commit()
    db.refresh(allocation)

    return ResponseModel(code=200, message="计算完成", data=allocation)



