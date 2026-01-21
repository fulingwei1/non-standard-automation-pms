# -*- coding: utf-8 -*-
"""
项目设备 CRUD 操作

适配自 app/api/v1/endpoints/machines/crud.py
变更: 路由从 /machines/ 改为 /projects/{project_id}/machines/
"""
from decimal import Decimal
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.material import BomHeader
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import MachineCreate, MachineResponse, MachineUpdate
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MachineResponse])
def read_project_machines(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"
    ),
    stage: str = Query(None, description="设备阶段筛选"),
    status: str = Query(None, description="设备状态筛选"),
    health: str = Query(None, description="健康度筛选"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """获取项目的机台列表（支持分页、筛选）"""
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(Machine).filter(Machine.project_id == project_id)

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
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=MachineResponse)
def create_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_in: MachineCreate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:create")),
) -> Any:
    """
    为项目创建机台

    机台编码自动生成格式：{项目编码}-PN{序号}
    例如：PJ250712001-PN001
    """
    from app.services.machine_service import MachineService, ProjectAggregationService

    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中创建机台")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 准备机台数据，强制使用路径中的 project_id
    machine_data = machine_in.model_dump()
    machine_data["project_id"] = project_id
    machine_service = MachineService(db)

    # 自动生成机台编码（如果未提供）
    if not machine_data.get("machine_code"):
        machine_code, machine_no = machine_service.generate_machine_code(project_id)
        machine_data["machine_code"] = machine_code
        machine_data["machine_no"] = machine_no
    else:
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

    # 更新项目聚合数据
    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(project_id)

    return machine


@router.get("/summary")
def get_project_machine_summary(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取项目机台汇总信息

    返回：
    - total_machines: 机台总数
    - stage_distribution: 阶段分布
    - health_distribution: 健康度分布
    - avg_progress: 平均进度
    - completed_count: 已完成数量（S9）
    - at_risk_count: 有风险数量（H2）
    - blocked_count: 阻塞数量（H3）
    """
    from app.services.machine_service import ProjectAggregationService

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
        },
    )


@router.post("/recalculate")
def recalculate_project_aggregation(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    重新计算项目聚合数据

    当项目的进度、阶段或健康度与机台不一致时，
    可以调用此接口强制重新计算。
    """
    from app.services.machine_service import ProjectAggregationService

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
        },
    )


@router.get("/{machine_id}", response_model=MachineResponse)
def read_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """获取项目机台详情"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    return machine


@router.put("/{machine_id}", response_model=MachineResponse)
def update_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    machine_in: MachineUpdate = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    更新项目机台信息

    - 阶段变更会验证是否合法（只能向前推进）
    - 状态变更会验证是否在有效范围内
    - 更新后自动重新计算项目的聚合数据
    """
    from app.services.machine_service import (
        MachineService,
        ProjectAggregationService,
        VALID_HEALTH,
        VALID_STAGES,
    )

    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    update_data = machine_in.model_dump(exclude_unset=True)
    machine_service = MachineService(db)

    # 验证阶段变更是否合法
    if "stage" in update_data:
        new_stage = update_data["stage"]
        if new_stage not in VALID_STAGES:
            raise HTTPException(
                status_code=400, detail=f"无效的阶段值: {new_stage}，有效值为 S1-S9"
            )

        is_valid, error_msg = machine_service.validate_stage_transition(machine.stage, new_stage)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

    # 验证健康度是否有效
    if "health" in update_data:
        new_health = update_data["health"]
        if new_health not in VALID_HEALTH:
            raise HTTPException(
                status_code=400, detail=f"无效的健康度: {new_health}，有效值为 H1-H4"
            )

    # 应用更新
    for field, value in update_data.items():
        if hasattr(machine, field):
            setattr(machine, field, value)

    db.add(machine)
    db.commit()
    db.refresh(machine)

    # 更新项目聚合数据
    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(project_id)

    return machine


@router.put("/{machine_id}/progress", response_model=MachineResponse)
def update_project_machine_progress(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    progress_pct: Decimal = Query(..., ge=0, le=100, description="进度百分比（0-100）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:update")),
) -> Any:
    """
    更新机台进度

    更新后自动重新计算项目的聚合进度
    """
    from app.services.machine_service import ProjectAggregationService

    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    machine.progress_pct = progress_pct
    db.add(machine)
    db.commit()
    db.refresh(machine)

    # 更新项目聚合数据
    aggregation_service = ProjectAggregationService(db)
    aggregation_service.update_project_aggregation(project_id)

    return machine


@router.get("/{machine_id}/bom", response_model=List)
def get_project_machine_bom(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    获取机台的BOM列表
    """
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

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
def delete_project_machine(
    project_id: int = Path(..., description="项目ID"),
    machine_id: int = Path(..., description="机台ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("machine:delete")),
) -> Any:
    """删除项目机台"""
    check_project_access_or_raise(db, current_user, project_id)

    machine = db.query(Machine).filter(
        Machine.id == machine_id,
        Machine.project_id == project_id,
    ).first()

    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 检查是否有关联的BOM
    bom_count = db.query(BomHeader).filter(BomHeader.machine_id == machine_id).count()
    if bom_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"机台下存在 {bom_count} 个BOM，无法删除。请先删除或转移BOM。",
        )

    db.delete(machine)
    db.commit()

    return ResponseModel(code=200, message="机台已删除")
