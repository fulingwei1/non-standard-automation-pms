# -*- coding: utf-8 -*-
"""
生产管理模块 - 车间管理端点

包含：车间CRUD、产能统计
"""
from typing import Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.production import (
    Workshop, WorkOrder, ProductionDailyReport
)
from app.schemas.production import (
    WorkshopCreate,
    WorkshopUpdate,
    WorkshopResponse,
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


# ==================== 车间管理 ====================

@router.get("/workshops", response_model=PaginatedResponse)
def read_workshops(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    workshop_type: Optional[str] = Query(None, description="车间类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取车间列表（机加/装配/调试）
    """
    query = db.query(Workshop)

    if workshop_type:
        query = query.filter(Workshop.workshop_type == workshop_type)

    if is_active is not None:
        query = query.filter(Workshop.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    workshops = query.order_by(Workshop.created_at).offset(offset).limit(page_size).all()

    items = []
    for workshop in workshops:
        manager_name = None
        if workshop.manager_id:
            manager = db.query(User).filter(User.id == workshop.manager_id).first()
            manager_name = manager.real_name if manager else None

        items.append(WorkshopResponse(
            id=workshop.id,
            workshop_code=workshop.workshop_code,
            workshop_name=workshop.workshop_name,
            workshop_type=workshop.workshop_type,
            manager_id=workshop.manager_id,
            manager_name=manager_name,
            location=workshop.location,
            capacity_hours=float(workshop.capacity_hours) if workshop.capacity_hours else None,
            description=workshop.description,
            is_active=workshop.is_active,
            created_at=workshop.created_at,
            updated_at=workshop.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/workshops", response_model=WorkshopResponse)
def create_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_in: WorkshopCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建车间
    """
    # 检查车间编码是否已存在
    existing = db.query(Workshop).filter(Workshop.workshop_code == workshop_in.workshop_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="车间编码已存在")

    # 检查车间主管是否存在
    if workshop_in.manager_id:
        manager = db.query(User).filter(User.id == workshop_in.manager_id).first()
        if not manager:
            raise HTTPException(status_code=404, detail="车间主管不存在")

    workshop = Workshop(**workshop_in.model_dump())
    db.add(workshop)
    db.commit()
    db.refresh(workshop)

    manager_name = None
    if workshop.manager_id:
        manager = db.query(User).filter(User.id == workshop.manager_id).first()
        manager_name = manager.real_name if manager else None

    return WorkshopResponse(
        id=workshop.id,
        workshop_code=workshop.workshop_code,
        workshop_name=workshop.workshop_name,
        workshop_type=workshop.workshop_type,
        manager_id=workshop.manager_id,
        manager_name=manager_name,
        location=workshop.location,
        capacity_hours=float(workshop.capacity_hours) if workshop.capacity_hours else None,
        description=workshop.description,
        is_active=workshop.is_active,
        created_at=workshop.created_at,
        updated_at=workshop.updated_at,
    )


@router.get("/workshops/{workshop_id}", response_model=WorkshopResponse)
def read_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取车间详情（含产能/人员）
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")

    manager_name = None
    if workshop.manager_id:
        manager = db.query(User).filter(User.id == workshop.manager_id).first()
        manager_name = manager.real_name if manager else None

    return WorkshopResponse(
        id=workshop.id,
        workshop_code=workshop.workshop_code,
        workshop_name=workshop.workshop_name,
        workshop_type=workshop.workshop_type,
        manager_id=workshop.manager_id,
        manager_name=manager_name,
        location=workshop.location,
        capacity_hours=float(workshop.capacity_hours) if workshop.capacity_hours else None,
        description=workshop.description,
        is_active=workshop.is_active,
        created_at=workshop.created_at,
        updated_at=workshop.updated_at,
    )


@router.get("/workshops/{workshop_id}/capacity", response_model=dict)
def get_workshop_capacity(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    车间产能统计
    统计车间的产能、实际负荷、利用率等信息
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")

    # 基础产能信息
    capacity_hours = float(workshop.capacity_hours) if workshop.capacity_hours else 0.0
    worker_count = workshop.worker_count or 0

    # 如果没有指定日期范围，使用当前月
    from datetime import timedelta
    from calendar import monthrange
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, last_day = monthrange(today.year, today.month)
        end_date = date(today.year, today.month, last_day)

    # 计算工作天数
    work_days = (end_date - start_date).days + 1

    # 计算总产能（如果capacity_hours是日产能，则乘以工作天数；否则使用capacity_hours）
    total_capacity = capacity_hours * work_days if capacity_hours > 0 else work_days * 8 * worker_count

    # 统计该期间的工单
    work_orders = db.query(WorkOrder).filter(
        WorkOrder.workshop_id == workshop_id,
        WorkOrder.plan_start_date >= start_date,
        WorkOrder.plan_start_date <= end_date
    ).all()

    # 计算计划工时和实际工时
    plan_hours = sum(float(wo.standard_hours or 0) for wo in work_orders)
    actual_hours = sum(float(wo.actual_hours or 0) for wo in work_orders)

    # 从生产日报获取实际工时（更准确）
    daily_reports = db.query(ProductionDailyReport).filter(
        ProductionDailyReport.workshop_id == workshop_id,
        ProductionDailyReport.report_date >= start_date,
        ProductionDailyReport.report_date <= end_date
    ).all()

    if daily_reports:
        actual_hours = sum(float(dr.actual_hours or 0) for dr in daily_reports)

    # 计算负荷率和利用率
    load_rate = (plan_hours / total_capacity * 100) if total_capacity > 0 else 0
    utilization_rate = (actual_hours / total_capacity * 100) if total_capacity > 0 else 0

    # 统计工单状态
    pending_count = sum(1 for wo in work_orders if wo.status == "PENDING")
    in_progress_count = sum(1 for wo in work_orders if wo.status in ["ASSIGNED", "STARTED", "PAUSED"])
    completed_count = sum(1 for wo in work_orders if wo.status == "COMPLETED")

    return {
        "workshop_id": workshop.id,
        "workshop_name": workshop.workshop_name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "work_days": work_days,
        "worker_count": worker_count,
        "capacity_hours": capacity_hours,
        "total_capacity": total_capacity,
        "plan_hours": round(plan_hours, 2),
        "actual_hours": round(actual_hours, 2),
        "load_rate": round(load_rate, 2),
        "utilization_rate": round(utilization_rate, 2),
        "work_order_count": len(work_orders),
        "pending_count": pending_count,
        "in_progress_count": in_progress_count,
        "completed_count": completed_count,
    }


@router.put("/workshops/{workshop_id}", response_model=WorkshopResponse)
def update_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    workshop_in: WorkshopUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新车间
    """
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="车间不存在")

    # 检查车间主管是否存在
    if workshop_in.manager_id is not None:
        if workshop_in.manager_id:
            manager = db.query(User).filter(User.id == workshop_in.manager_id).first()
            if not manager:
                raise HTTPException(status_code=404, detail="车间主管不存在")

    update_data = workshop_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workshop, field, value)

    db.add(workshop)
    db.commit()
    db.refresh(workshop)

    manager_name = None
    if workshop.manager_id:
        manager = db.query(User).filter(User.id == workshop.manager_id).first()
        manager_name = manager.real_name if manager else None

    return WorkshopResponse(
        id=workshop.id,
        workshop_code=workshop.workshop_code,
        workshop_name=workshop.workshop_name,
        workshop_type=workshop.workshop_type,
        manager_id=workshop.manager_id,
        manager_name=manager_name,
        location=workshop.location,
        capacity_hours=float(workshop.capacity_hours) if workshop.capacity_hours else None,
        description=workshop.description,
        is_active=workshop.is_active,
        created_at=workshop.created_at,
        updated_at=workshop.updated_at,
    )
