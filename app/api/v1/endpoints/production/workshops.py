# -*- coding: utf-8 -*-
"""
生产管理模块 - 车间管理端点

包含：车间CRUD、产能统计
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.production import Worker, WorkOrder, Workshop, Workstation
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.production import (
    WorkshopCreate,
    WorkshopResponse,
    WorkshopTaskBoardResponse,
    WorkshopUpdate,
)
from app.services.production.workshop_service import WorkshopService
from app.utils.db_helpers import get_or_404

router = APIRouter()


# ==================== 车间管理 ====================


@router.get("/workshops", response_model=PaginatedResponse)
def read_workshops(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    workshop_type: Optional[str] = Query(None, description="车间类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取车间列表（机加/装配/调试）
    """
    service = WorkshopService(db)
    return service.list_workshops(
        pagination=pagination,
        workshop_type=workshop_type,
        is_active=is_active,
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
    service = WorkshopService(db)
    return service.create_workshop(workshop_in)


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
    service = WorkshopService(db)
    return service.get_workshop(workshop_id)


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
    service = WorkshopService(db)
    return service.get_capacity(
        workshop_id=workshop_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/workshops/{workshop_id}/task-board", response_model=WorkshopTaskBoardResponse)
def get_workshop_task_board(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取车间任务看板。"""
    workshop = get_or_404(db, Workshop, workshop_id, detail="车间不存在")

    workstations = (
        db.query(Workstation).filter(Workstation.workshop_id == workshop_id).all()
    )
    workers = db.query(Worker).filter(Worker.workshop_id == workshop_id).all()
    work_orders = db.query(WorkOrder).filter(WorkOrder.workshop_id == workshop_id).all()

    return WorkshopTaskBoardResponse(
        workshop_id=workshop.id,
        workshop_name=workshop.workshop_name,
        workstations=[
            {
                "id": workstation.id,
                "workstation_code": workstation.workstation_code,
                "workstation_name": workstation.workstation_name,
                "status": workstation.status,
                "current_worker_id": workstation.current_worker_id,
                "current_work_order_id": workstation.current_work_order_id,
                "is_active": workstation.is_active,
            }
            for workstation in workstations
        ],
        work_orders=[
            {
                "id": order.id,
                "work_order_no": order.work_order_no,
                "task_name": order.task_name,
                "status": order.status,
                "priority": order.priority,
                "progress": order.progress,
                "assigned_to": order.assigned_to,
                "workstation_id": order.workstation_id,
            }
            for order in work_orders
        ],
        workers=[
            {
                "id": worker.id,
                "worker_no": worker.worker_no,
                "worker_name": worker.worker_name,
                "status": worker.status,
                "position": worker.position,
                "is_active": worker.is_active,
            }
            for worker in workers
        ],
    )


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
    service = WorkshopService(db)
    return service.update_workshop(workshop_id, workshop_in)
