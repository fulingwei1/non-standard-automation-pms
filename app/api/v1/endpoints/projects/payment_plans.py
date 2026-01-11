# -*- coding: utf-8 -*-
"""
项目付款计划端点

包含付款计划的创建、更新、删除、列表等操作
"""

from typing import Any, List, Optional
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project, ProjectPaymentPlan
from app.schemas.project import (
    ProjectPaymentPlanCreate,
    ProjectPaymentPlanUpdate,
    ProjectPaymentPlanResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import _sync_invoice_request_receipt_status

router = APIRouter()


@router.get("/{project_id}/payment-plans", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_payment_plans(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
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
    offset = (page - 1) * page_size
    plans = query.order_by(ProjectPaymentPlan.planned_date).offset(offset).limit(page_size).all()

    items = []
    for plan in plans:
        items.append({
            "id": plan.id,
            "project_id": plan.project_id,
            "plan_name": plan.plan_name,
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
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
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
    project = check_project_access_or_raise(db, current_user, project_id)

    plan = ProjectPaymentPlan(
        project_id=project_id,
        plan_name=plan_in.plan_name,
        plan_type=plan_in.plan_type,
        planned_amount=plan_in.planned_amount,
        planned_date=plan_in.planned_date,
        milestone_id=plan_in.milestone_id,
        remark=plan_in.remark,
        status="PENDING",
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return ResponseModel(
        code=200,
        message="付款计划创建成功",
        data={
            "id": plan.id,
            "project_id": plan.project_id,
            "plan_name": plan.plan_name,
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
    plan = db.query(ProjectPaymentPlan).filter(ProjectPaymentPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="付款计划不存在")

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

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return ResponseModel(
        code=200,
        message="付款计划更新成功",
        data={
            "id": plan.id,
            "project_id": plan.project_id,
            "plan_name": plan.plan_name,
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
    plan = db.query(ProjectPaymentPlan).filter(ProjectPaymentPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="付款计划不存在")

    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, plan.project_id)

    # 检查是否已有回款记录
    if plan.actual_amount and float(plan.actual_amount) > 0:
        raise HTTPException(
            status_code=400,
            detail="该付款计划已有回款记录，无法删除"
        )

    db.delete(plan)
    db.commit()

    return ResponseModel(
        code=200,
        message="付款计划删除成功",
        data={"id": plan_id}
    )
