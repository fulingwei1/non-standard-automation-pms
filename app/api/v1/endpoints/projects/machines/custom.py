# -*- coding: utf-8 -*-
"""
项目机台自定义端点

包含汇总、重新计算、进度更新、BOM查询等功能
"""

from decimal import Decimal
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import MachineResponse
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


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


@router.get("/{machine_id}/bom")
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
