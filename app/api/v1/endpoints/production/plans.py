# -*- coding: utf-8 -*-
"""
生产管理模块 - 生产计划端点

包含：计划CRUD、提交、审批、发布
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.production import ProductionPlan, Workshop
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.production import (
    ProductionPlanCreate,
    ProductionPlanResponse,
    ProductionPlanUpdate,
)

from .utils import generate_plan_no

router = APIRouter()


# ==================== 生产计划管理 ====================

@router.get("/production-plans", response_model=PaginatedResponse)
def read_production_plans(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    plan_type: Optional[str] = Query(None, description="计划类型筛选：MASTER/WORKSHOP"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产计划列表（主计划/车间计划）
    """
    query = db.query(ProductionPlan)

    if plan_type:
        query = query.filter(ProductionPlan.plan_type == plan_type)

    if project_id:
        query = query.filter(ProductionPlan.project_id == project_id)

    if workshop_id:
        query = query.filter(ProductionPlan.workshop_id == workshop_id)

    if status:
        query = query.filter(ProductionPlan.status == status)

    total = query.count()
    plans = query.order_by(desc(ProductionPlan.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for plan in plans:
        project_name = None
        if plan.project_id:
            project = db.query(Project).filter(Project.id == plan.project_id).first()
            project_name = project.project_name if project else None

        workshop_name = None
        if plan.workshop_id:
            workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
            workshop_name = workshop.workshop_name if workshop else None

        items.append(ProductionPlanResponse(
            id=plan.id,
            plan_no=plan.plan_no,
            plan_name=plan.plan_name,
            plan_type=plan.plan_type,
            project_id=plan.project_id,
            project_name=project_name,
            workshop_id=plan.workshop_id,
            workshop_name=workshop_name,
            plan_start_date=plan.plan_start_date,
            plan_end_date=plan.plan_end_date,
            status=plan.status,
            progress=plan.progress or 0,
            description=plan.description,
            created_by=plan.created_by,
            approved_by=plan.approved_by,
            approved_at=plan.approved_at,
            remark=plan.remark,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
        ))

    return pagination.to_response(items, total)


@router.post("/production-plans", response_model=ProductionPlanResponse)
def create_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: ProductionPlanCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建生产计划
    """
    # 检查项目是否存在
    if plan_in.project_id:
        project = db.query(Project).filter(Project.id == plan_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

    # 检查车间是否存在
    if plan_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")

    # 生成计划编号
    plan_no = generate_plan_no(db)

    plan = ProductionPlan(
        plan_no=plan_no,
        status="DRAFT",
        progress=0,
        created_by=current_user.id,
        **plan_in.model_dump()
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    project_name = None
    if plan.project_id:
        project = db.query(Project).filter(Project.id == plan.project_id).first()
        project_name = project.project_name if project else None

    workshop_name = None
    if plan.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None

    return ProductionPlanResponse(
        id=plan.id,
        plan_no=plan.plan_no,
        plan_name=plan.plan_name,
        plan_type=plan.plan_type,
        project_id=plan.project_id,
        project_name=project_name,
        workshop_id=plan.workshop_id,
        workshop_name=workshop_name,
        plan_start_date=plan.plan_start_date,
        plan_end_date=plan.plan_end_date,
        status=plan.status,
        progress=plan.progress or 0,
        description=plan.description,
        created_by=plan.created_by,
        approved_by=plan.approved_by,
        approved_at=plan.approved_at,
        remark=plan.remark,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.get("/production-plans/{plan_id}", response_model=ProductionPlanResponse)
def read_production_plan(
    plan_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取生产计划详情
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")

    project_name = None
    if plan.project_id:
        project = db.query(Project).filter(Project.id == plan.project_id).first()
        project_name = project.project_name if project else None

    workshop_name = None
    if plan.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None

    return ProductionPlanResponse(
        id=plan.id,
        plan_no=plan.plan_no,
        plan_name=plan.plan_name,
        plan_type=plan.plan_type,
        project_id=plan.project_id,
        project_name=project_name,
        workshop_id=plan.workshop_id,
        workshop_name=workshop_name,
        plan_start_date=plan.plan_start_date,
        plan_end_date=plan.plan_end_date,
        status=plan.status,
        progress=plan.progress or 0,
        description=plan.description,
        created_by=plan.created_by,
        approved_by=plan.approved_by,
        approved_at=plan.approved_at,
        remark=plan.remark,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.put("/production-plans/{plan_id}", response_model=ProductionPlanResponse)
def update_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    plan_in: ProductionPlanUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新生产计划
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")

    # 只有草稿状态才能更新
    if plan.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的计划才能更新")

    update_data = plan_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)

    db.add(plan)
    db.commit()
    db.refresh(plan)

    project_name = None
    if plan.project_id:
        project = db.query(Project).filter(Project.id == plan.project_id).first()
        project_name = project.project_name if project else None

    workshop_name = None
    if plan.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == plan.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None

    return ProductionPlanResponse(
        id=plan.id,
        plan_no=plan.plan_no,
        plan_name=plan.plan_name,
        plan_type=plan.plan_type,
        project_id=plan.project_id,
        project_name=project_name,
        workshop_id=plan.workshop_id,
        workshop_name=workshop_name,
        plan_start_date=plan.plan_start_date,
        plan_end_date=plan.plan_end_date,
        status=plan.status,
        progress=plan.progress or 0,
        description=plan.description,
        created_by=plan.created_by,
        approved_by=plan.approved_by,
        approved_at=plan.approved_at,
        remark=plan.remark,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.put("/production-plans/{plan_id}/submit", response_model=ResponseModel)
def submit_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交计划审批
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")

    if plan.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的计划才能提交")

    plan.status = "SUBMITTED"
    db.add(plan)
    db.commit()

    return ResponseModel(
        code=200,
        message="计划已提交审批"
    )


@router.put("/production-plans/{plan_id}/approve", response_model=ResponseModel)
def approve_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    approved: bool = Query(True, description="是否审批通过"),
    approval_note: Optional[str] = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批通过生产计划
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")

    if plan.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只有已提交的计划才能审批")

    if approved:
        plan.status = "APPROVED"
        plan.approved_by = current_user.id
        plan.approved_at = datetime.now()
    else:
        plan.status = "DRAFT"  # 驳回后回到草稿状态

    if approval_note:
        plan.remark = (plan.remark or "") + f"\n审批意见：{approval_note}"

    db.add(plan)
    db.commit()

    return ResponseModel(
        code=200,
        message="审批成功" if approved else "已驳回"
    )


@router.put("/production-plans/{plan_id}/publish", response_model=ResponseModel)
def publish_production_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    计划发布
    """
    plan = db.query(ProductionPlan).filter(ProductionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="生产计划不存在")

    if plan.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只有已审批的计划才能发布")

    plan.status = "PUBLISHED"
    db.add(plan)
    db.commit()

    return ResponseModel(
        code=200,
        message="计划已发布"
    )
