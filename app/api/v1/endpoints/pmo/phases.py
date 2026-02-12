# -*- coding: utf-8 -*-
"""
项目阶段 - 自动生成
从 pmo.py 拆分
"""

# -*- coding: utf-8 -*-
"""
PMO 项目管理部 API endpoints
包含：立项管理、项目阶段门管理、风险管理、项目结项管理、PMO驾驶舱
"""
from datetime import date, datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.pmo import (
    PmoProjectPhase,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.pmo import (
    PhaseAdvanceRequest,
    PhaseEntryCheckRequest,
    PhaseExitCheckRequest,
    PhaseResponse,
    PhaseReviewRequest,
)

# Included without extra prefix; decorators already include `/pmo/...` paths.
router = APIRouter(tags=["pmo-phases"])

# 使用统一的编码生成工具
from app.utils.domain_codes import pmo as pmo_codes

generate_initiation_no = pmo_codes.generate_initiation_no
generate_risk_no = pmo_codes.generate_risk_no

# 共 5 个路由

# ==================== 项目阶段 ====================

@router.get("/pmo/projects/{project_id}/phases", response_model=List[PhaseResponse])
def read_project_phases(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目阶段列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    phases = db.query(PmoProjectPhase).filter(
        PmoProjectPhase.project_id == project_id
    ).order_by(PmoProjectPhase.phase_order).all()

    result = []
    for phase in phases:
        result.append(PhaseResponse(
            id=phase.id,
            project_id=phase.project_id,
            phase_code=phase.phase_code,
            phase_name=phase.phase_name,
            phase_order=phase.phase_order,
            plan_start_date=phase.plan_start_date,
            plan_end_date=phase.plan_end_date,
            actual_start_date=phase.actual_start_date,
            actual_end_date=phase.actual_end_date,
            status=phase.status,
            progress=phase.progress,
            entry_criteria=phase.entry_criteria,
            exit_criteria=phase.exit_criteria,
            entry_check_result=phase.entry_check_result,
            exit_check_result=phase.exit_check_result,
            review_required=phase.review_required,
            review_date=phase.review_date,
            review_result=phase.review_result,
            review_notes=phase.review_notes,
            created_at=phase.created_at,
            updated_at=phase.updated_at,
        ))

    return result


@router.post("/pmo/phases/{phase_id}/entry-check", response_model=PhaseResponse)
def phase_entry_check(
    *,
    db: Session = Depends(deps.get_db),
    phase_id: int,
    check_request: PhaseEntryCheckRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阶段入口检查
    """
    phase = db.query(PmoProjectPhase).filter(PmoProjectPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")

    phase.entry_check_result = check_request.check_result
    if check_request.notes:
        # 可以追加到现有结果中
        if phase.entry_check_result:
            phase.entry_check_result += f"\n{check_request.notes}"
        else:
            phase.entry_check_result = check_request.notes

    db.add(phase)
    db.commit()
    db.refresh(phase)

    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase_code=phase.phase_code,
        phase_name=phase.phase_name,
        phase_order=phase.phase_order,
        plan_start_date=phase.plan_start_date,
        plan_end_date=phase.plan_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        status=phase.status,
        progress=phase.progress,
        entry_criteria=phase.entry_criteria,
        exit_criteria=phase.exit_criteria,
        entry_check_result=phase.entry_check_result,
        exit_check_result=phase.exit_check_result,
        review_required=phase.review_required,
        review_date=phase.review_date,
        review_result=phase.review_result,
        review_notes=phase.review_notes,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
    )


@router.post("/pmo/phases/{phase_id}/exit-check", response_model=PhaseResponse)
def phase_exit_check(
    *,
    db: Session = Depends(deps.get_db),
    phase_id: int,
    check_request: PhaseExitCheckRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阶段出口检查
    """
    phase = db.query(PmoProjectPhase).filter(PmoProjectPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")

    phase.exit_check_result = check_request.check_result
    if check_request.notes:
        if phase.exit_check_result:
            phase.exit_check_result += f"\n{check_request.notes}"
        else:
            phase.exit_check_result = check_request.notes

    db.add(phase)
    db.commit()
    db.refresh(phase)

    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase_code=phase.phase_code,
        phase_name=phase.phase_name,
        phase_order=phase.phase_order,
        plan_start_date=phase.plan_start_date,
        plan_end_date=phase.plan_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        status=phase.status,
        progress=phase.progress,
        entry_criteria=phase.entry_criteria,
        exit_criteria=phase.exit_criteria,
        entry_check_result=phase.entry_check_result,
        exit_check_result=phase.exit_check_result,
        review_required=phase.review_required,
        review_date=phase.review_date,
        review_result=phase.review_result,
        review_notes=phase.review_notes,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
    )


@router.post("/pmo/phases/{phase_id}/review", response_model=PhaseResponse)
def phase_review(
    *,
    db: Session = Depends(deps.get_db),
    phase_id: int,
    review_request: PhaseReviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阶段评审
    """
    phase = db.query(PmoProjectPhase).filter(PmoProjectPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")

    phase.review_result = review_request.review_result
    phase.review_notes = review_request.review_notes
    phase.review_date = date.today()

    db.add(phase)
    db.commit()
    db.refresh(phase)

    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase_code=phase.phase_code,
        phase_name=phase.phase_name,
        phase_order=phase.phase_order,
        plan_start_date=phase.plan_start_date,
        plan_end_date=phase.plan_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        status=phase.status,
        progress=phase.progress,
        entry_criteria=phase.entry_criteria,
        exit_criteria=phase.exit_criteria,
        entry_check_result=phase.entry_check_result,
        exit_check_result=phase.exit_check_result,
        review_required=phase.review_required,
        review_date=phase.review_date,
        review_result=phase.review_result,
        review_notes=phase.review_notes,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
    )


@router.put("/pmo/phases/{phase_id}/advance", response_model=PhaseResponse)
def phase_advance(
    *,
    db: Session = Depends(deps.get_db),
    phase_id: int,
    advance_request: PhaseAdvanceRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阶段推进
    """
    phase = db.query(PmoProjectPhase).filter(PmoProjectPhase.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")

    if advance_request.actual_start_date:
        phase.actual_start_date = advance_request.actual_start_date
        phase.status = 'IN_PROGRESS'

    # 推进到下一阶段的逻辑：如果当前阶段已完成，自动创建下一阶段
    if phase.status == 'COMPLETED':
        # 查找当前项目的所有阶段
        all_phases = db.query(PmoProjectPhase).filter(
            PmoProjectPhase.project_id == phase.project_id
        ).order_by(PmoProjectPhase.phase_order).all()

        # 找到当前阶段的顺序
        current_order = None
        for p in all_phases:
            if p.id == phase.id:
                current_order = p.phase_order
                break

        # 查找下一个阶段
        next_phase = None
        for p in all_phases:
            if p.phase_order == current_order + 1:
                next_phase = p
                break

        # 如果存在下一阶段且状态为PENDING，则更新为IN_PROGRESS
        if next_phase and next_phase.status == 'PENDING':
            next_phase.status = 'IN_PROGRESS'
            next_phase.actual_start_date = datetime.now().date()
            db.add(next_phase)

    db.add(phase)
    db.commit()
    db.refresh(phase)

    return PhaseResponse(
        id=phase.id,
        project_id=phase.project_id,
        phase_code=phase.phase_code,
        phase_name=phase.phase_name,
        phase_order=phase.phase_order,
        plan_start_date=phase.plan_start_date,
        plan_end_date=phase.plan_end_date,
        actual_start_date=phase.actual_start_date,
        actual_end_date=phase.actual_end_date,
        status=phase.status,
        progress=phase.progress,
        entry_criteria=phase.entry_criteria,
        exit_criteria=phase.exit_criteria,
        entry_check_result=phase.entry_check_result,
        exit_check_result=phase.exit_check_result,
        review_required=phase.review_required,
        review_date=phase.review_date,
        review_result=phase.review_result,
        review_notes=phase.review_notes,
        created_at=phase.created_at,
        updated_at=phase.updated_at,
    )


