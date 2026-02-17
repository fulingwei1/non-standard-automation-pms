# -*- coding: utf-8 -*-
"""
生产管理模块 - 工位管理端点

包含：工位列表、创建、状态查询
"""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.production import Equipment, Worker, WorkOrder, Workshop, Workstation
from app.models.user import User
from app.schemas.production import (
    WorkstationCreate,
    WorkstationResponse,
    WorkstationStatusResponse,
)
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


# ==================== 工位管理 ====================

@router.get("/workshops/{workshop_id}/workstations", response_model=List[WorkstationResponse])
def read_workstations(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工位列表
    """
    workshop = get_or_404(db, Workshop, workshop_id, detail="车间不存在")

    workstations = db.query(Workstation).filter(Workstation.workshop_id == workshop_id).all()

    items = []
    for ws in workstations:
        equipment_name = None
        if ws.equipment_id:
            equipment = db.query(Equipment).filter(Equipment.id == ws.equipment_id).first()
            equipment_name = equipment.equipment_name if equipment else None

        items.append(WorkstationResponse(
            id=ws.id,
            workstation_code=ws.workstation_code,
            workstation_name=ws.workstation_name,
            workshop_id=ws.workshop_id,
            workshop_name=workshop.workshop_name,
            equipment_id=ws.equipment_id,
            equipment_name=equipment_name,
            status=ws.status,
            current_worker_id=ws.current_worker_id,
            current_work_order_id=ws.current_work_order_id,
            description=ws.description,
            is_active=ws.is_active,
            created_at=ws.created_at,
            updated_at=ws.updated_at,
        ))

    return items


@router.post("/workshops/{workshop_id}/workstations", response_model=WorkstationResponse)
def create_workstation(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    workstation_in: WorkstationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工位
    """
    workshop = get_or_404(db, Workshop, workshop_id, detail="车间不存在")

    # 检查工位编码是否已存在
    existing = db.query(Workstation).filter(Workstation.workstation_code == workstation_in.workstation_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="工位编码已存在")

    workstation = Workstation(
        workshop_id=workshop_id,
        status="IDLE",
        **workstation_in.model_dump()
    )
    save_obj(db, workstation)

    equipment_name = None
    if workstation.equipment_id:
        equipment = db.query(Equipment).filter(Equipment.id == workstation.equipment_id).first()
        equipment_name = equipment.equipment_name if equipment else None

    return WorkstationResponse(
        id=workstation.id,
        workstation_code=workstation.workstation_code,
        workstation_name=workstation.workstation_name,
        workshop_id=workstation.workshop_id,
        workshop_name=workshop.workshop_name,
        equipment_id=workstation.equipment_id,
        equipment_name=equipment_name,
        status=workstation.status,
        current_worker_id=workstation.current_worker_id,
        current_work_order_id=workstation.current_work_order_id,
        description=workstation.description,
        is_active=workstation.is_active,
        created_at=workstation.created_at,
        updated_at=workstation.updated_at,
    )


@router.get("/workstations/{workstation_id}/status", response_model=WorkstationStatusResponse)
def get_workstation_status(
    *,
    db: Session = Depends(deps.get_db),
    workstation_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工位状态（空闲/工作中）
    """
    workstation = get_or_404(db, Workstation, workstation_id, detail="工位不存在")

    current_worker_name = None
    if workstation.current_worker_id:
        worker = db.query(Worker).filter(Worker.id == workstation.current_worker_id).first()
        current_worker_name = worker.worker_name if worker else None

    current_work_order_no = None
    if workstation.current_work_order_id:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == workstation.current_work_order_id).first()
        current_work_order_no = work_order.work_order_no if work_order else None

    is_available = workstation.status == "IDLE" and workstation.current_work_order_id is None

    return WorkstationStatusResponse(
        workstation_id=workstation.id,
        workstation_code=workstation.workstation_code,
        workstation_name=workstation.workstation_name,
        status=workstation.status,
        current_worker_id=workstation.current_worker_id,
        current_worker_name=current_worker_name,
        current_work_order_id=workstation.current_work_order_id,
        current_work_order_no=current_work_order_no,
        is_available=is_available,
    )
