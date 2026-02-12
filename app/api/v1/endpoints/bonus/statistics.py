# -*- coding: utf-8 -*-
"""
奖金统计 - 自动生成
从 bonus.py 拆分
"""

# -*- coding: utf-8 -*-
"""
奖金激励模块 API 端点
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.bonus import (
    BonusCalculation,
    BonusDistribution,
    BonusRule,
)
from app.models.user import User
from app.schemas.bonus import (
    BonusStatisticsResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/bonus/statistics",
    tags=["statistics"]
)

# 共 1 个路由

# ==================== 奖金统计 ====================

@router.get("/statistics", response_model=ResponseModel[BonusStatisticsResponse], status_code=status.HTTP_200_OK)
def get_bonus_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取奖金统计
    """
    # 计算记录统计
    calc_query = db.query(BonusCalculation)
    if start_date:
        calc_query = calc_query.filter(BonusCalculation.calculated_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        calc_query = calc_query.filter(BonusCalculation.calculated_at <= datetime.combine(end_date, datetime.max.time()))

    total_calculated = calc_query.with_entities(func.sum(BonusCalculation.calculated_amount)).scalar() or Decimal('0')
    calculation_count = calc_query.count()

    # 发放记录统计
    dist_query = db.query(BonusDistribution)
    if start_date:
        dist_query = dist_query.filter(BonusDistribution.distribution_date >= start_date)
    if end_date:
        dist_query = dist_query.filter(BonusDistribution.distribution_date <= end_date)

    total_distributed = dist_query.filter(
        BonusDistribution.status == 'PAID'
    ).with_entities(func.sum(BonusDistribution.distributed_amount)).scalar() or Decimal('0')

    total_pending = dist_query.filter(
        BonusDistribution.status == 'PENDING'
    ).with_entities(func.sum(BonusDistribution.distributed_amount)).scalar() or Decimal('0')

    distribution_count = dist_query.count()

    # 按类型统计
    by_type = {}
    type_query = calc_query.join(BonusRule).with_entities(
        BonusRule.bonus_type,
        func.sum(BonusCalculation.calculated_amount)
    ).group_by(BonusRule.bonus_type).all()

    for bonus_type, amount in type_query:
        by_type[bonus_type] = amount or Decimal('0')

    # 按部门统计（关联用户表）
    from app.models.user import User
    by_department = {}
    dept_query = calc_query.join(User, BonusCalculation.user_id == User.id).with_entities(
        User.department,
        func.sum(BonusCalculation.calculated_amount)
    ).group_by(User.department).all()

    for dept_name, amount in dept_query:
        if dept_name:  # 只统计有部门信息的记录
            by_department[dept_name] = amount or Decimal('0')

    return ResponseModel(
        code=200,
        data=BonusStatisticsResponse(
            total_calculated=total_calculated,
            total_distributed=total_distributed,
            total_pending=total_pending,
            calculation_count=calculation_count,
            distribution_count=distribution_count,
            by_type=by_type,
            by_department=by_department
        )
    )



