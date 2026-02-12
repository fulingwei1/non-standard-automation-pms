# -*- coding: utf-8 -*-
"""
奖金发放 - 自动生成
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
    BonusDistribution,
)
from app.models.user import User
from app.schemas.bonus import (
    BonusDistributionCreate,
    BonusDistributionListResponse,
    BonusDistributionPay,
    BonusDistributionQuery,
    BonusDistributionResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/bonus/payment",
    tags=["payment"]
)

# 共 4 个路由

# ==================== 奖金发放 ====================

def generate_distribution_code() -> str:
    """生成发放单号"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"BD{timestamp}"


@router.post("/distribute", response_model=ResponseModel[BonusDistributionResponse], status_code=status.HTTP_201_CREATED)
def create_bonus_distribution(
    *,
    db: Session = Depends(deps.get_db),
    dist_in: BonusDistributionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建奖金发放记录
    """
    # 检查计算记录是否存在且已审批
    calculation = db.query(BonusCalculation).filter(
        BonusCalculation.id == dist_in.calculation_id
    ).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="计算记录不存在")

    if calculation.status != 'APPROVED':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="计算记录未审批，无法发放"
        )

    # 检查是否已发放
    existing = db.query(BonusDistribution).filter(
        BonusDistribution.calculation_id == dist_in.calculation_id,
        BonusDistribution.status == 'PAID'
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该计算记录已发放"
        )

    distribution = BonusDistribution(
        distribution_code=generate_distribution_code(),
        **dist_in.model_dump()
    )
    db.add(distribution)

    # 更新计算记录状态
    calculation.status = 'DISTRIBUTED'

    db.commit()
    db.refresh(distribution)

    return ResponseModel(code=200, message="创建成功", data=distribution)


@router.get("/distributions", response_model=BonusDistributionListResponse, status_code=status.HTTP_200_OK)
def get_bonus_distributions(
    *,
    db: Session = Depends(deps.get_db),
    query_params: BonusDistributionQuery = Depends(),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取奖金发放记录列表
    """
    query = db.query(BonusDistribution)

    if query_params.user_id:
        query = query.filter(BonusDistribution.user_id == query_params.user_id)
    if query_params.status:
        query = query.filter(BonusDistribution.status == query_params.status)
    if query_params.start_date:
        query = query.filter(BonusDistribution.distribution_date >= query_params.start_date)
    if query_params.end_date:
        query = query.filter(BonusDistribution.distribution_date <= query_params.end_date)

    total = query.count()
    pg = get_pagination_params(page=query_params.page, page_size=query_params.page_size)
    distributions = query.order_by(desc(BonusDistribution.distribution_date)).offset(
        pg.offset
    ).limit(pg.limit).all()

    return BonusDistributionListResponse(
        items=distributions,
        total=total,
        page=pg.page,
        page_size=pg.page_size,
        pages=pg.pages_for_total(total)
    )


@router.get("/distributions/{dist_id}", response_model=ResponseModel[BonusDistributionResponse], status_code=status.HTTP_200_OK)
def get_bonus_distribution(
    *,
    db: Session = Depends(deps.get_db),
    dist_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取奖金发放记录详情
    """
    distribution = db.query(BonusDistribution).filter(BonusDistribution.id == dist_id).first()
    if not distribution:
        raise HTTPException(status_code=404, detail="发放记录不存在")

    return ResponseModel(code=200, data=distribution)


@router.post("/distributions/{dist_id}/pay", response_model=ResponseModel[BonusDistributionResponse], status_code=status.HTTP_200_OK)
def pay_bonus_distribution(
    *,
    db: Session = Depends(deps.get_db),
    dist_id: int,
    pay_in: BonusDistributionPay,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认发放奖金
    """
    distribution = db.query(BonusDistribution).filter(BonusDistribution.id == dist_id).first()
    if not distribution:
        raise HTTPException(status_code=404, detail="发放记录不存在")

    if distribution.status == 'PAID':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该记录已发放"
        )

    distribution.status = 'PAID'
    distribution.paid_by = current_user.id
    distribution.paid_at = datetime.now()

    if pay_in.voucher_no:
        distribution.voucher_no = pay_in.voucher_no
    if pay_in.payment_account:
        distribution.payment_account = pay_in.payment_account
    if pay_in.payment_remark:
        distribution.payment_remark = pay_in.payment_remark

    db.commit()
    db.refresh(distribution)

    return ResponseModel(code=200, message="发放成功", data=distribution)



