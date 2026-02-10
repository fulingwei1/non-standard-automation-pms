# -*- coding: utf-8 -*-
"""
收款计划管理 endpoints
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get("/payment-plans", response_model=PaginatedResponse)
def get_payment_plans(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取收款计划列表
    """
    from app.models.project import ProjectPaymentPlan

    query = db.query(ProjectPaymentPlan)

    if project_id:
        query = query.filter(ProjectPaymentPlan.project_id == project_id)

    if contract_id:
        query = query.filter(ProjectPaymentPlan.contract_id == contract_id)

    if status:
        query = query.filter(ProjectPaymentPlan.status == status)

    total = query.count()
    plans = query.order_by(ProjectPaymentPlan.planned_date).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for plan in plans:
        items.append({
            "id": plan.id,
            "payment_no": plan.payment_no,
            "project_id": plan.project_id,
            "project_code": plan.project.project_code if plan.project else None,
            "contract_id": plan.contract_id,
            "contract_code": plan.contract.contract_code if plan.contract else None,
            "payment_stage": plan.payment_stage,
            "payment_ratio": float(plan.payment_ratio or 0),
            "planned_amount": float(plan.planned_amount or 0),
            "actual_amount": float(plan.actual_amount or 0),
            "planned_date": plan.planned_date,
            "actual_date": plan.actual_date,
            "milestone_id": plan.milestone_id,
            "milestone_name": plan.milestone.milestone_name if plan.milestone else None,
            "trigger_milestone": plan.trigger_milestone,
            "status": plan.status,
            "invoice_id": plan.invoice_id,
            "invoice_no": plan.invoice_no,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/payment-plans/{plan_id}/adjust", response_model=ResponseModel)
def adjust_payment_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    new_date: date = Query(..., description="新的收款日期"),
    reason: str = Query(..., description="调整原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 7.3: 手动调整收款计划
    记录调整历史并发送通知
    """
    from app.services.payment_adjustment_service import PaymentAdjustmentService

    service = PaymentAdjustmentService(db)
    result = service.manual_adjust_payment_plan(
        plan_id=plan_id,
        new_date=new_date,
        reason=reason,
        adjusted_by=current_user.id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "调整失败"))

    return ResponseModel(
        code=200,
        message=result.get("message", "收款计划已调整"),
        data=result
    )


@router.get("/payment-plans/{plan_id}/adjustment-history", response_model=ResponseModel)
def get_payment_adjustment_history(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 7.3: 获取收款计划调整历史
    """
    from app.services.payment_adjustment_service import PaymentAdjustmentService

    service = PaymentAdjustmentService(db)
    history = service.get_adjustment_history(plan_id)

    return ResponseModel(
        code=200,
        message="success",
        data={"history": history}
    )
