# -*- coding: utf-8 -*-
"""
收款计划管理 endpoints
"""
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import (
    check_sales_data_permission,
    filter_sales_finance_data_by_scope,
)
from app.models.project import ProjectPaymentPlan
from app.models.sales import Contract
from app.models.user import User
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


class LegacyPaymentStageCreate(BaseModel):
    """旧版前端/测试使用的阶段式收款计划。"""

    stage: str = Field(min_length=1, description="阶段名称")
    percentage: Optional[Decimal] = Field(default=None, description="百分比")
    amount: Decimal = Field(description="金额")


class LegacyPaymentPlanCreateRequest(BaseModel):
    """旧版支付计划创建请求。"""

    contract_id: int = Field(description="合同ID")
    total_amount: Optional[Decimal] = Field(default=None, description="总金额")
    payment_stages: list[LegacyPaymentStageCreate] = Field(default_factory=list)


def _infer_payment_type(stage_name: str) -> str:
    """根据阶段名推断当前模型需要的 payment_type。"""
    normalized = stage_name.strip().upper()
    if any(keyword in normalized for keyword in ("签约", "预付款", "首款", "ADVANCE")):
        return "ADVANCE"
    if any(keyword in normalized for keyword in ("交付", "发货", "DELIVERY")):
        return "DELIVERY"
    if any(keyword in normalized for keyword in ("验收", "ACCEPTANCE")):
        return "ACCEPTANCE"
    if any(keyword in normalized for keyword in ("质保", "尾款", "WARRANTY")):
        return "WARRANTY"
    return "CUSTOM"


@router.get("/payments/plans", response_model=PaginatedResponse)
def get_payment_plans(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("contract:read")),
) -> Any:
    """
    获取收款计划列表
    """
    from app.models.project import ProjectPaymentPlan

    query = filter_sales_finance_data_by_scope(
        db.query(ProjectPaymentPlan).outerjoin(
            Contract,
            ProjectPaymentPlan.contract_id == Contract.id,
        ),
        current_user,
        db,
        Contract,
        "sales_owner_id",
    )

    if project_id:
        query = query.filter(ProjectPaymentPlan.project_id == project_id)

    if contract_id:
        query = query.filter(ProjectPaymentPlan.contract_id == contract_id)

    if status:
        query = query.filter(ProjectPaymentPlan.status == status)

    total = query.count()
    plans = apply_pagination(query.order_by(ProjectPaymentPlan.planned_date), pagination.offset, pagination.limit).all()

    items = []
    for plan in plans:
        # 兼容历史模型字段：旧前端使用 payment_stage，当前模型为 payment_name/payment_type
        payment_stage = plan.payment_name or plan.payment_type
        if not payment_stage:
            payment_stage = f"第{plan.payment_no}期"
        items.append({
            "id": plan.id,
            "payment_no": plan.payment_no,
            "project_id": plan.project_id,
            "project_code": plan.project.project_code if plan.project else None,
            "contract_id": plan.contract_id,
            "contract_code": plan.contract.contract_code if plan.contract else None,
            "payment_stage": payment_stage,
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


@router.post("/payments/plans", response_model=ResponseModel, status_code=201)
def create_payment_plans(
    *,
    db: Session = Depends(deps.get_db),
    payload: LegacyPaymentPlanCreateRequest,
    current_user: User = Depends(security.require_permission("contract:update")),
) -> Any:
    """兼容旧版的分阶段收款计划创建接口。"""
    contract = db.query(Contract).filter(Contract.id == payload.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    if not check_sales_data_permission(contract, current_user, db, "sales_owner_id"):
        raise HTTPException(status_code=403, detail="无权为该合同创建收款计划")

    if not payload.payment_stages:
        raise HTTPException(status_code=422, detail="payment_stages 不能为空")

    project_id = contract.project_id
    if not project_id:
        raise HTTPException(
            status_code=409,
            detail="合同未关联项目，需完成PMO立项或项目创建后再创建收款计划",
        )

    created_plans = []
    for index, stage in enumerate(payload.payment_stages, start=1):
        plan = ProjectPaymentPlan(
            project_id=project_id,
            contract_id=contract.id,
            payment_no=index,
            payment_name=stage.stage,
            payment_type=_infer_payment_type(stage.stage),
            payment_ratio=stage.percentage,
            planned_amount=stage.amount,
            actual_amount=Decimal("0"),
            status="PENDING",
        )
        db.add(plan)
        db.flush()
        created_plans.append(
            {
                "id": plan.id,
                "payment_no": plan.payment_no,
                "payment_name": plan.payment_name,
                "payment_ratio": float(plan.payment_ratio or 0),
                "planned_amount": float(plan.planned_amount or 0),
                "status": plan.status,
            }
        )

    db.commit()

    return ResponseModel(
        code=201,
        message="收款计划创建成功",
        data={
            "contract_id": contract.id,
            "project_id": project_id,
            "total_amount": float(payload.total_amount or 0),
            "items": created_plans,
        },
    )


@router.post("/payments/plans/{plan_id}/adjust", response_model=ResponseModel)
def adjust_payment_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    new_date: date = Query(..., description="新的收款日期"),
    reason: str = Query(..., description="调整原因"),
    current_user: User = Depends(security.require_permission("contract:update")),
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


@router.get("/payments/plans/{plan_id}/adjustment-history", response_model=ResponseModel)
def get_payment_adjustment_history(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.require_permission("contract:read")),
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
