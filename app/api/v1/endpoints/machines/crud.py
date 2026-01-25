# -*- coding: utf-8 -*-
"""
机台全局 CRUD 端点

⚠️ 大部分端点已废弃，请使用项目中心端点：
    /api/v1/projects/{project_id}/machines/

本文件保留的非废弃端点：
- PUT /{machine_id}/progress - 更新机台进度
- GET /{machine_id}/bom - 获取机台BOM
- GET /projects/{project_id}/summary - 获取项目机台汇总
- POST /projects/{project_id}/recalculate - 重新计算聚合数据
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


# ============================================================
# 已废弃的端点 - 请使用项目中心端点
# ============================================================

@router.get("/", response_model=PaginatedResponse[MachineResponse], deprecated=True)
def read_machines(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    stage: Optional[str] = Query(None, description="设备阶段筛选"),
    status: Optional[str] = Query(None, description="设备状态筛选"),
    health: Optional[str] = Query(None, description="健康度筛选"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 GET /projects/{project_id}/machines/

    获取机台列表
    """
    from app.utils.permission_helpers import filter_by_project_access

    query = db.query(Machine)

    # 数据权限过滤
    if project_id:
        query = query.filter(Machine.project_id == project_id)
    else:
        query = filter_by_project_access(db, query, current_user, Machine.project_id)

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


@router.post("/", response_model=MachineResponse, deprecated=True)
def create_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_in: MachineCreate,
    current_user: User = Depends(security.require_permission("machine:create")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 POST /projects/{project_id}/machines/

    创建机台
    """
    from app.services.machine_service import MachineService, ProjectAggregationService
    from app.utils.permission_helpers import check_project_access_or_raise

    project_id = machine_in.project_id
    if not project_id:
        raise HTTPException(status_code=400, detail="project_id 是必需的")

    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中创建机台")

    machine_data = machine_in.model_dump()
    machine_service = MachineService(db)

    if not machine_data.get("machine_code"):
        machine_code, machine_no = machine_service.generate_machine_code(project_id)
        machine_data["machine_code"] = machine_code
        machine_data["machine_no"] = machine_no

    machine = Machine(**machine_data)
    db.add(machine)
    db.commit()
    db.refresh(machine)

    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(project_id)

    return machine


@router.get("/{machine_id}", response_model=MachineResponse, deprecated=True)
def read_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 GET /projects/{project_id}/machines/{machine_id}

    获取机台详情
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    return machine


@router.put("/{machine_id}", response_model=MachineResponse, deprecated=True)
def update_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    machine_in: MachineUpdate,
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 PUT /projects/{project_id}/machines/{machine_id}

    更新机台信息
    """
    from app.services.machine_service import (
        MachineService,
        ProjectAggregationService,
        VALID_HEALTH,
        VALID_STAGES,
    )

    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    update_data = machine_in.model_dump(exclude_unset=True)
    machine_service = MachineService(db)

    if "stage" in update_data:
        new_stage = update_data["stage"]
        if new_stage not in VALID_STAGES:
            raise HTTPException(status_code=400, detail=f"无效的阶段值: {new_stage}")
        is_valid, error_msg = machine_service.validate_stage_transition(machine.stage, new_stage)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

    if "health" in update_data:
        if update_data["health"] not in VALID_HEALTH:
            raise HTTPException(status_code=400, detail=f"无效的健康度: {update_data['health']}")

    for field, value in update_data.items():
        if hasattr(machine, field):
            setattr(machine, field, value)

    db.add(machine)
    db.commit()
    db.refresh(machine)

    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(machine.project_id)

    return machine


@router.delete("/{machine_id}", status_code=200, deprecated=True)
def delete_machine(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_permission("machine:delete")),
) -> Any:
    """
    ⚠️ Deprecated: 请使用 DELETE /projects/{project_id}/machines/{machine_id}

    删除机台
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    bom_count = db.query(BomHeader).filter(BomHeader.machine_id == machine_id).count()
    if bom_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"机台下存在 {bom_count} 个BOM，无法删除。"
        )

    db.delete(machine)
    db.commit()

    return ResponseModel(code=200, message="机台已删除")


# ============================================================
# 以下端点仍然有效（项目中心端点中没有的功能）
# ============================================================

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

    更新后自动重新计算项目的聚合进度
    """
    from app.services.machine_service import ProjectAggregationService

    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    machine.progress_pct = progress_pct
    db.add(machine)
    db.commit()
    db.refresh(machine)

    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(machine.project_id)

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

    注意：完整BOM API在 /api/v1/bom/machines/{machine_id}/bom
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    bom_headers = (
        db.query(BomHeader)
        .filter(BomHeader.machine_id == machine_id)
        .order_by(desc(BomHeader.created_at))
        .all()
    )

    return [
        {
            "id": bom.id,
            "bom_no": bom.bom_no,
            "bom_name": bom.bom_name,
            "version": bom.version,
            "is_latest": bom.is_latest,
            "status": bom.status,
            "total_items": bom.total_items,
            "total_amount": float(bom.total_amount) if bom.total_amount else 0,
        }
        for bom in bom_headers
    ]


@router.get("/projects/{project_id}/summary")
def get_project_machine_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取项目机台汇总信息

    返回阶段分布、健康度分布、平均进度等汇总数据
    """
    from app.services.machine_service import ProjectAggregationService
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    aggregation_service = ProjectAggregationService(db)
    summary = aggregation_service.get_project_machine_summary(project_id)

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "project_stage": project.stage,
            "project_health": project.health,
            "project_progress": float(project.progress_pct or 0),
            **summary,
        }
    )


@router.post("/projects/{project_id}/recalculate")
def recalculate_project_aggregation(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    重新计算项目聚合数据

    当项目的进度、阶段或健康度与机台不一致时，可调用此接口强制重新计算
    """
    from app.services.machine_service import ProjectAggregationService
    from app.utils.permission_helpers import check_project_access_or_raise

    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    aggregation_service = ProjectAggregationService(db)
    updated_project = aggregation_service.update_project_aggregation(project_id)

    return ResponseModel(
        code=200,
        message="重新计算完成",
        data={
            "project_id": updated_project.id,
            "project_code": updated_project.project_code,
            "stage": updated_project.stage,
            "health": updated_project.health,
            "progress_pct": float(updated_project.progress_pct or 0),
        }
    )
