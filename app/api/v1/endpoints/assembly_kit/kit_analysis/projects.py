# -*- coding: utf-8 -*-
"""
齐套分析 - 项目相关
"""
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models import BomHeader, Machine, MaterialReadiness, Project
from app.schemas.assembly_kit import MaterialReadinessResponse
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/projects/{project_id}/assembly-readiness", response_model=ResponseModel)
async def get_project_readiness_list(
    project_id: int,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """获取项目齐套分析列表"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(MaterialReadiness).filter(MaterialReadiness.project_id == project_id)
    total = query.count()

    readiness_list = query.order_by(MaterialReadiness.analysis_time.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for r in readiness_list:
        bom = db.query(BomHeader).filter(BomHeader.id == r.bom_id).first()
        machine = db.query(Machine).filter(Machine.id == r.machine_id).first() if r.machine_id else None

        result.append(MaterialReadinessResponse(
            id=r.id,
            readiness_no=r.readiness_no,
            project_id=r.project_id,
            machine_id=r.machine_id,
            bom_id=r.bom_id,
            check_date=r.planned_start_date or date.today(),
            overall_kit_rate=r.overall_kit_rate,
            blocking_kit_rate=r.blocking_kit_rate,
            can_start=r.can_start,
            first_blocked_stage=r.first_blocked_stage,
            estimated_ready_date=r.estimated_ready_date,
            stage_kit_rates=[],
            project_no=project.project_code if project else None,
            project_name=project.project_name if project else None,
            machine_no=machine.machine_code if machine else None,
            bom_no=bom.bom_no if bom else None,
            analysis_time=r.analysis_time,
            analyzed_by=r.analyzed_by,
            created_at=r.created_at
        ))

    return ResponseModel(
        code=200,
        message="success",
        data={"total": total, "items": result, "page": page, "page_size": page_size}
    )
