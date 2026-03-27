# -*- coding: utf-8 -*-
"""
物料采购管理 P3 级增强端点
"""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas.response import SuccessResponse, success_response
from app.models.user import User
from app.schemas.material_procurement_optimization import (
    DuplicatePurchaseCheckRequest,
    ShortageWasteCalculationRequest,
)
from app.services.material_procurement_optimization_service import (
    MaterialProcurementOptimizationService,
)

router = APIRouter()


@router.post(
    "/shortage-waste-calculation",
    response_model=SuccessResponse[dict],
    summary="缺料等待浪费计算",
    description="计算缺料导致的人力、设备、延期罚款和机会成本浪费",
)
def shortage_waste_calculation(
    payload: ShortageWasteCalculationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> SuccessResponse[dict]:
    service = MaterialProcurementOptimizationService(db)
    data = service.calculate_shortage_waste(payload)
    return success_response(data=data, message="缺料等待浪费计算完成")


@router.get(
    "/safety-stock-alerts",
    response_model=SuccessResponse[dict],
    summary="安全库存动态预警",
    description="基于近90天消耗和采购周期输出安全库存预警与补货建议",
)
def safety_stock_alerts(
    days: int = Query(90, ge=30, le=365, description="消耗分析天数"),
    safety_factor: Decimal = Query(Decimal("1.5"), ge=0, description="安全系数"),
    purchase_cycle_days: Optional[int] = Query(None, ge=1, le=365, description="统一采购周期（可选，覆盖物料默认值）"),
    focus_shortage_threshold: int = Query(2, ge=1, le=30, description="高频缺料判定阈值"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> SuccessResponse[dict]:
    service = MaterialProcurementOptimizationService(db)
    data = service.get_safety_stock_alerts(
        days=days,
        safety_factor=safety_factor,
        purchase_cycle_days=purchase_cycle_days,
        focus_shortage_threshold=focus_shortage_threshold,
    )
    return success_response(data=data, message="安全库存预警计算完成")


@router.post(
    "/check-duplicate-purchase",
    response_model=SuccessResponse[dict],
    summary="重复采购检查",
    description="检查采购申请是否与已有采购申请、采购订单或BOM版本冲突",
)
def check_duplicate_purchase(
    payload: DuplicatePurchaseCheckRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> SuccessResponse[dict]:
    service = MaterialProcurementOptimizationService(db)
    data = service.check_duplicate_purchase(payload)
    return success_response(data=data, message="重复采购检查完成")


@router.get(
    "/slow-moving-analysis",
    response_model=SuccessResponse[dict],
    summary="呆滞物料分析",
    description="识别慢动物料、呆滞物料和报废物料，并输出处置建议与潜在回收金额",
)
def slow_moving_analysis(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> SuccessResponse[dict]:
    service = MaterialProcurementOptimizationService(db)
    data = service.get_slow_moving_analysis()
    return success_response(data=data, message="呆滞物料分析完成")
