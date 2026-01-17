# -*- coding: utf-8 -*-
"""
机台基本 CRUD 端点
"""

from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import BomHeader
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import (
    MachineCreate,
    MachineResponse,
    MachineUpdate,
)

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MachineResponse])
def read_machines(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    stage: Optional[str] = Query(None, description="设备阶段筛选"),
    status: Optional[str] = Query(None, description="设备状态筛选"),
    health: Optional[str] = Query(None, description="健康度筛选"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取机台列表（支持分页、筛选）
    """
    query = db.query(Machine)

    if project_id:
        query = query.filter(Machine.project_id == project_id)
    if stage:
        query = query.filter(Machine.stage == stage)
    if status:
        query = query.filter(Machine.status == status)
    if health:
        query = query.filter(Machine.health == health)

    total = query.count()
    offset = (page - 1) * page_size
    machines = query.order_by(desc(Machine.created_at)).offset(offset).limit(page_size).all()

    return PaginatedResponse(
        items=machines,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/projects/{project_id}/machines", response_model=List[MachineResponse])
def get_project_machines(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取项目的机台列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    machines = db.query(Machine).filter(Machine.project_id == project_id).order_by(Machine.machine_no).all()
    return machines


@router.post("/", response_model=MachineResponse)
def create_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_in: MachineCreate,
    current_user: User = Depends(security.require_permission("machine:create")),
) -> Any:
    """
    Create new machine.
    """
    # Check if project exists
    project = db.query(Project).filter(Project.id == machine_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if machine code exists in project
    existing = (
        db.query(Machine)
        .filter(
            Machine.project_id == machine_in.project_id,
            Machine.machine_code == machine_in.machine_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Machine with this code already exists in this project.",
        )

    machine = Machine(**machine_in.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.post("/projects/{project_id}/machines", response_model=MachineResponse)
def create_project_machine(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    machine_in: MachineCreate,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    为项目创建机台
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 确保project_id一致
    machine_data = machine_in.model_dump()
    machine_data['project_id'] = project_id

    # 检查机台编码是否已存在
    existing = (
        db.query(Machine)
        .filter(
            Machine.project_id == project_id,
            Machine.machine_code == machine_in.machine_code,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="该机台编码已在此项目中存在",
        )

    machine = Machine(**machine_data)
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.get("/{machine_id}", response_model=MachineResponse)
def read_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    Get machine by ID.
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    machine_in: MachineUpdate,
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    Update a machine.
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    update_data = machine_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(machine, field):
            setattr(machine, field, value)

    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.put("/{machine_id}/progress", response_model=MachineResponse)
def update_machine_progress(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    progress_pct: Decimal = Query(..., ge=0, le=100, description="进度百分比（0-100）"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    更新机台进度
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    machine.progress_pct = progress_pct
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.get("/{machine_id}/bom", response_model=List)
def get_machine_bom(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取机台的BOM列表
    注意：实际的BOM列表API在 /api/v1/bom/machines/{machine_id}/bom
    这里提供快捷访问
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 通过BOM API获取，这里返回提示信息
    bom_headers = (
        db.query(BomHeader)
        .filter(BomHeader.machine_id == machine_id)
        .order_by(desc(BomHeader.created_at))
        .all()
    )

    result = []
    for bom in bom_headers:
        result.append({
            "id": bom.id,
            "bom_no": bom.bom_no,
            "bom_name": bom.bom_name,
            "version": bom.version,
            "is_latest": bom.is_latest,
            "status": bom.status,
            "total_items": bom.total_items,
            "total_amount": float(bom.total_amount) if bom.total_amount else 0,
        })

    return result


@router.delete("/{machine_id}", status_code=200)
def delete_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:delete")),
) -> Any:
    """
    删除机台
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 检查是否有关联的BOM
    bom_count = db.query(BomHeader).filter(BomHeader.machine_id == machine_id).count()
    if bom_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"机台下存在 {bom_count} 个BOM，无法删除。请先删除或转移BOM。"
        )

    db.delete(machine)
    db.commit()

    return ResponseModel(code=200, message="机台已删除")
