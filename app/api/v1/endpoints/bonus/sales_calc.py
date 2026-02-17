# -*- coding: utf-8 -*-
"""
销售奖金计算 - 自动生成
从 bonus.py 拆分
"""

# -*- coding: utf-8 -*-
"""
奖金激励模块 API 端点
"""

from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import get_pagination_params
from app.core import security
from app.models.bonus import (
    BonusCalculation,
    BonusRule,
)
from app.models.presale import PresaleSupportTicket
from app.models.sales import Contract
from app.models.user import User
from app.schemas.bonus import (
    BonusCalculationApprove,
    BonusCalculationListResponse,
    BonusCalculationQuery,
    BonusCalculationResponse,
    CalculatePresaleBonusRequest,
    CalculateSalesBonusRequest,
    CalculateSalesDirectorBonusRequest,
)
from app.schemas.common import ResponseModel
from app.services.bonus import BonusCalculator

router = APIRouter()



from fastapi import APIRouter
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter(
    prefix="/bonus/sales-calc",
    tags=["sales_calc"]
)

# 共 6 个路由

# ==================== 销售奖金计算 ====================

@router.post("/calculate/sales", response_model=ResponseModel[BonusCalculationResponse], status_code=status.HTTP_200_OK)
def calculate_sales_bonus(
    *,
    db: Session = Depends(deps.get_db),
    request: CalculateSalesBonusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算销售奖金

    支持两种计算方式：
    1. CONTRACT: 基于合同签订金额
    2. PAYMENT: 基于回款金额
    """
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    calculator = BonusCalculator(db)

    # 获取规则
    if request.rule_id:
        rule = db.query(BonusRule).filter(BonusRule.id == request.rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
    else:
        rules = calculator.get_active_rules(bonus_type='SALES_BASED')
        if not rules:
            raise HTTPException(status_code=404, detail="未找到销售奖金规则")
        rule = rules[0]

    calculation = calculator.calculate_sales_bonus(contract, rule, request.based_on)
    if not calculation:
        raise HTTPException(status_code=400, detail="不满足计算条件")

    db.add(calculation)
    db.commit()
    db.refresh(calculation)

    return ResponseModel(code=200, message="计算完成", data=calculation)


@router.post("/calculate/sales-director", response_model=ResponseModel[BonusCalculationResponse], status_code=status.HTTP_200_OK)
def calculate_sales_director_bonus(
    *,
    db: Session = Depends(deps.get_db),
    request: CalculateSalesDirectorBonusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算销售总监奖金（基于团队业绩）
    """
    calculator = BonusCalculator(db)

    # 获取规则
    if request.rule_id:
        rule = db.query(BonusRule).filter(BonusRule.id == request.rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
    else:
        rules = calculator.get_active_rules(bonus_type='SALES_DIRECTOR_BASED')
        if not rules:
            raise HTTPException(status_code=404, detail="未找到销售总监奖金规则")
        rule = rules[0]

    calculation = calculator.calculate_sales_director_bonus(
        request.director_id,
        request.period_start,
        request.period_end,
        rule
    )

    if not calculation:
        raise HTTPException(status_code=400, detail="该周期内无团队业绩")

    db.add(calculation)
    db.commit()
    db.refresh(calculation)

    return ResponseModel(code=200, message="计算完成", data=calculation)


@router.post("/calculate/presale", response_model=ResponseModel[BonusCalculationResponse], status_code=status.HTTP_200_OK)
def calculate_presale_bonus(
    *,
    db: Session = Depends(deps.get_db),
    request: CalculatePresaleBonusRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计算售前技术支持奖金

    支持两种计算方式：
    1. COMPLETION: 基于工单完成
    2. WON: 基于中标
    """
    ticket = db.query(PresaleSupportTicket).filter(
        PresaleSupportTicket.id == request.ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="售前支持工单不存在")

    calculator = BonusCalculator(db)

    # 获取规则
    if request.rule_id:
        rule = db.query(BonusRule).filter(BonusRule.id == request.rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
    else:
        rules = calculator.get_active_rules(bonus_type='PRESALE_BASED')
        if not rules:
            raise HTTPException(status_code=404, detail="未找到售前技术支持奖金规则")
        rule = rules[0]

    calculation = calculator.calculate_presale_bonus(ticket, rule, request.based_on)
    if not calculation:
        raise HTTPException(status_code=400, detail="不满足计算条件")

    db.add(calculation)
    db.commit()
    db.refresh(calculation)

    return ResponseModel(code=200, message="计算完成", data=calculation)


@router.get("/calculations", response_model=BonusCalculationListResponse, status_code=status.HTTP_200_OK)
def get_bonus_calculations(
    *,
    db: Session = Depends(deps.get_db),
    query_params: BonusCalculationQuery = Depends(),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取奖金计算记录列表
    """
    query = db.query(BonusCalculation)

    if query_params.rule_id:
        query = query.filter(BonusCalculation.rule_id == query_params.rule_id)
    if query_params.user_id:
        query = query.filter(BonusCalculation.user_id == query_params.user_id)
    if query_params.project_id:
        query = query.filter(BonusCalculation.project_id == query_params.project_id)
    if query_params.period_id:
        query = query.filter(BonusCalculation.period_id == query_params.period_id)
    if query_params.status:
        query = query.filter(BonusCalculation.status == query_params.status)
    if query_params.bonus_type:
        query = query.join(BonusRule).filter(BonusRule.bonus_type == query_params.bonus_type)
    if query_params.start_date:
        query = query.filter(BonusCalculation.calculated_at >= datetime.combine(query_params.start_date, datetime.min.time()))
    if query_params.end_date:
        query = query.filter(BonusCalculation.calculated_at <= datetime.combine(query_params.end_date, datetime.max.time()))

    total = query.count()
    pg = get_pagination_params(page=query_params.page, page_size=query_params.page_size)
    calculations = query.order_by(desc(BonusCalculation.calculated_at)).offset(
        pg.offset
    ).limit(pg.limit).all()

    return BonusCalculationListResponse(
        items=calculations,
        total=total,
        page=pg.page,
        page_size=pg.page_size,
        pages=pg.pages_for_total(total)
    )


@router.get("/calculations/{calc_id}", response_model=ResponseModel[BonusCalculationResponse], status_code=status.HTTP_200_OK)
def get_bonus_calculation(
    *,
    db: Session = Depends(deps.get_db),
    calc_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取奖金计算详情
    """
    calculation = get_or_404(db, BonusCalculation, calc_id, "计算记录不存在")

    return ResponseModel(code=200, data=calculation)


@router.post("/calculations/{calc_id}/approve", response_model=ResponseModel[BonusCalculationResponse], status_code=status.HTTP_200_OK)
def approve_bonus_calculation(
    *,
    db: Session = Depends(deps.get_db),
    calc_id: int,
    approve_in: BonusCalculationApprove,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批奖金计算
    """
    calculation = get_or_404(db, BonusCalculation, calc_id, "计算记录不存在")

    if approve_in.approved:
        calculation.status = 'APPROVED'
        calculation.approved_by = current_user.id
        calculation.approved_at = datetime.now()
        calculation.approval_comment = approve_in.comment
    else:
        calculation.status = 'CANCELLED'
        calculation.approved_by = current_user.id
        calculation.approved_at = datetime.now()
        calculation.approval_comment = approve_in.comment

    db.commit()
    db.refresh(calculation)

    return ResponseModel(code=200, message="审批完成", data=calculation)



