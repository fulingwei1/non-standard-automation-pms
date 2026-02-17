# -*- coding: utf-8 -*-
"""
项目付款计划端点

包含付款计划的创建、更新、删除、列表等操作
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import ProjectPaymentPlan
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import (
    ProjectPaymentPlanCreate,
    ProjectPaymentPlanUpdate,
)

from .utils import _sync_invoice_request_receipt_status
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import delete_obj, get_or_404, save_obj

router = APIRouter()


@router.get("/{project_id}/payment-plans", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_payment_plans(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目付款计划列表
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectPaymentPlan).filter(
        ProjectPaymentPlan.project_id == project_id
    )

    if status_filter:
        query = query.filter(ProjectPaymentPlan.status == status_filter)

    total = query.count()
    plans = apply_pagination(query.order_by(ProjectPaymentPlan.planned_date), pagination.offset, pagination.limit).all()

    items = []
    for plan in plans:
        items.append({
            "id": plan.id,
            "project_id": plan.project_id,
            "payment_name": plan.payment_name,
            "plan_type": plan.plan_type,
            "planned_amount": float(plan.planned_amount or 0),
            "actual_amount": float(plan.actual_amount or 0),
            "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
            "actual_date": plan.actual_date.isoformat() if plan.actual_date else None,
            "status": plan.status,
            "milestone_id": plan.milestone_id,
            "remark": plan.remark,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/{project_id}/payment-plans", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_payment_plan(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    plan_in: ProjectPaymentPlanCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目付款计划
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    plan = ProjectPaymentPlan(
        project_id=project_id,
        payment_name=getattr(plan_in, "payment_name", "未命名") if hasattr(plan_in, "payment_name") else plan_in.plan_name if hasattr(plan_in, "plan_name") else "未命名",
        plan_type=plan_in.plan_type,
        planned_amount=plan_in.planned_amount,
        planned_date=plan_in.planned_date,
        milestone_id=plan_in.milestone_id,
        remark=plan_in.remark,
        status="PENDING",
    )

    save_obj(db, plan)

    return ResponseModel(
        code=200,
        message="付款计划创建成功",
        data={
            "id": plan.id,
            "project_id": plan.project_id,
            "payment_name": plan.payment_name,
            "plan_type": plan.plan_type,
            "planned_amount": float(plan.planned_amount or 0),
            "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
            "status": plan.status,
        }
    )


@router.put("/payment-plans/{plan_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_payment_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    plan_in: ProjectPaymentPlanUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目付款计划
    """
    plan = get_or_404(db, ProjectPaymentPlan, plan_id, detail="付款计划不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, plan.project_id)

    update_data = plan_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(plan, field):
            setattr(plan, field, value)

    # 如果更新了实收金额，同步开票申请状态
    if "actual_amount" in update_data:
        _sync_invoice_request_receipt_status(db, plan)

    # 如果实收金额等于或大于计划金额，自动更新状态为已收
    if plan.actual_amount and plan.planned_amount:
        if plan.actual_amount >= plan.planned_amount:
            plan.status = "PAID"
            if not plan.actual_date:
                plan.actual_date = date.today()
        elif plan.actual_amount > 0:
            plan.status = "PARTIAL"

    save_obj(db, plan)

    return ResponseModel(
        code=200,
        message="付款计划更新成功",
        data={
            "id": plan.id,
            "project_id": plan.project_id,
            "payment_name": plan.payment_name,
            "plan_type": plan.plan_type,
            "planned_amount": float(plan.planned_amount or 0),
            "actual_amount": float(plan.actual_amount or 0),
            "planned_date": plan.planned_date.isoformat() if plan.planned_date else None,
            "actual_date": plan.actual_date.isoformat() if plan.actual_date else None,
            "status": plan.status,
        }
    )


@router.delete("/payment-plans/{plan_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_project_payment_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除项目付款计划
    """
    plan = get_or_404(db, ProjectPaymentPlan, plan_id, detail="付款计划不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, plan.project_id)

    # 检查是否已有回款记录
    if plan.actual_amount and float(plan.actual_amount) > 0:
        raise HTTPException(
            status_code=400,
            detail="该付款计划已有回款记录，无法删除"
        )

    delete_obj(db, plan)

    return ResponseModel(
        code=200,
        message="付款计划删除成功",
        data={"id": plan_id}
    )
