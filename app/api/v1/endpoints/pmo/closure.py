# -*- coding: utf-8 -*-
"""
项目结项 - 自动生成
从 pmo.py 拆分
"""

# -*- coding: utf-8 -*-
"""
PMO 项目管理部 API endpoints
包含：立项管理、项目阶段门管理、风险管理、项目结项管理、PMO驾驶舱
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.pmo import (
    PmoProjectClosure,
    PmoResourceAllocation,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.pmo import (
    ClosureCreate,
    ClosureLessonsRequest,
    ClosureResponse,
    ClosureReviewRequest,
)

# Included without extra prefix; decorators already include `/pmo/...` paths.
router = APIRouter(tags=["pmo-closure"])

# 使用统一的编码生成工具
from app.utils.domain_codes import pmo as pmo_codes

generate_initiation_no = pmo_codes.generate_initiation_no
generate_risk_no = pmo_codes.generate_risk_no

# 共 5 个路由

# ==================== 项目结项 ====================

@router.post("/pmo/projects/{project_id}/closure", response_model=ClosureResponse, status_code=status.HTTP_201_CREATED)
def create_closure(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    closure_in: ClosureCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    结项申请
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查是否已有结项记录
    existing = db.query(PmoProjectClosure).filter(PmoProjectClosure.project_id == project_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该项目已有结项记录")

    # 计算成本偏差
    cost_variance = None
    if project.budget_amount and project.actual_cost:
        cost_variance = float(project.actual_cost - project.budget_amount)

    # 计算工时偏差（从资源分配表统计）
    planned_hours = db.query(func.sum(PmoResourceAllocation.planned_hours)).filter(
        PmoResourceAllocation.project_id == project_id
    ).scalar() or 0

    actual_hours = db.query(func.sum(PmoResourceAllocation.actual_hours)).filter(
        PmoResourceAllocation.project_id == project_id
    ).scalar() or 0

    hours_variance = actual_hours - planned_hours

    # 计算进度偏差
    schedule_variance = None
    if project.planned_end_date and project.actual_end_date:
        schedule_variance = (project.actual_end_date - project.planned_end_date).days

    plan_duration = None
    actual_duration = None
    if project.planned_start_date and project.planned_end_date:
        plan_duration = (project.planned_end_date - project.planned_start_date).days
    if project.actual_start_date and project.actual_end_date:
        actual_duration = (project.actual_end_date - project.actual_start_date).days

    closure = PmoProjectClosure(
        project_id=project_id,
        acceptance_date=closure_in.acceptance_date,
        acceptance_result=closure_in.acceptance_result,
        acceptance_notes=closure_in.acceptance_notes,
        project_summary=closure_in.project_summary,
        achievement=closure_in.achievement,
        lessons_learned=closure_in.lessons_learned,
        improvement_suggestions=closure_in.improvement_suggestions,
        final_budget=project.budget_amount,
        final_cost=project.actual_cost,
        cost_variance=Decimal(str(cost_variance)) if cost_variance else None,
        final_planned_hours=planned_hours,
        final_actual_hours=actual_hours,
        hours_variance=hours_variance,
        plan_duration=plan_duration,
        actual_duration=actual_duration,
        schedule_variance=schedule_variance,
        quality_score=closure_in.quality_score,
        customer_satisfaction=closure_in.customer_satisfaction,
        status='DRAFT'
    )

    db.add(closure)
    db.commit()
    db.refresh(closure)

    return ClosureResponse(
        id=closure.id,
        project_id=closure.project_id,
        acceptance_date=closure.acceptance_date,
        acceptance_result=closure.acceptance_result,
        acceptance_notes=closure.acceptance_notes,
        project_summary=closure.project_summary,
        achievement=closure.achievement,
        lessons_learned=closure.lessons_learned,
        improvement_suggestions=closure.improvement_suggestions,
        final_budget=float(closure.final_budget) if closure.final_budget else None,
        final_cost=float(closure.final_cost) if closure.final_cost else None,
        cost_variance=float(closure.cost_variance) if closure.cost_variance else None,
        final_planned_hours=closure.final_planned_hours,
        final_actual_hours=closure.final_actual_hours,
        hours_variance=closure.hours_variance,
        plan_duration=closure.plan_duration,
        actual_duration=closure.actual_duration,
        schedule_variance=closure.schedule_variance,
        quality_score=closure.quality_score,
        customer_satisfaction=closure.customer_satisfaction,
        status=closure.status,
        review_result=closure.review_result,
        review_notes=closure.review_notes,
        reviewed_at=closure.reviewed_at,
        reviewed_by=closure.reviewed_by,
        created_at=closure.created_at,
        updated_at=closure.updated_at,
    )


@router.get("/pmo/projects/{project_id}/closure", response_model=ClosureResponse)
def read_closure(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    结项详情
    """
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.project_id == project_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="结项记录不存在")

    return ClosureResponse(
        id=closure.id,
        project_id=closure.project_id,
        acceptance_date=closure.acceptance_date,
        acceptance_result=closure.acceptance_result,
        acceptance_notes=closure.acceptance_notes,
        project_summary=closure.project_summary,
        achievement=closure.achievement,
        lessons_learned=closure.lessons_learned,
        improvement_suggestions=closure.improvement_suggestions,
        final_budget=float(closure.final_budget) if closure.final_budget else None,
        final_cost=float(closure.final_cost) if closure.final_cost else None,
        cost_variance=float(closure.cost_variance) if closure.cost_variance else None,
        final_planned_hours=closure.final_planned_hours,
        final_actual_hours=closure.final_actual_hours,
        hours_variance=closure.hours_variance,
        plan_duration=closure.plan_duration,
        actual_duration=closure.actual_duration,
        schedule_variance=closure.schedule_variance,
        quality_score=closure.quality_score,
        customer_satisfaction=closure.customer_satisfaction,
        status=closure.status,
        review_result=closure.review_result,
        review_notes=closure.review_notes,
        reviewed_at=closure.reviewed_at,
        reviewed_by=closure.reviewed_by,
        created_at=closure.created_at,
        updated_at=closure.updated_at,
    )


@router.put("/pmo/closures/{closure_id}/review", response_model=ClosureResponse)
def review_closure(
    *,
    db: Session = Depends(deps.get_db),
    closure_id: int,
    review_request: ClosureReviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    结项评审
    """
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.id == closure_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="结项记录不存在")

    closure.status = 'REVIEWED'
    closure.review_result = review_request.review_result
    closure.review_notes = review_request.review_notes
    closure.reviewed_at = datetime.now()
    closure.reviewed_by = current_user.id

    db.add(closure)
    db.commit()
    db.refresh(closure)

    return ClosureResponse(
        id=closure.id,
        project_id=closure.project_id,
        acceptance_date=closure.acceptance_date,
        acceptance_result=closure.acceptance_result,
        acceptance_notes=closure.acceptance_notes,
        project_summary=closure.project_summary,
        achievement=closure.achievement,
        lessons_learned=closure.lessons_learned,
        improvement_suggestions=closure.improvement_suggestions,
        final_budget=float(closure.final_budget) if closure.final_budget else None,
        final_cost=float(closure.final_cost) if closure.final_cost else None,
        cost_variance=float(closure.cost_variance) if closure.cost_variance else None,
        final_planned_hours=closure.final_planned_hours,
        final_actual_hours=closure.final_actual_hours,
        hours_variance=closure.hours_variance,
        plan_duration=closure.plan_duration,
        actual_duration=closure.actual_duration,
        schedule_variance=closure.schedule_variance,
        quality_score=closure.quality_score,
        customer_satisfaction=closure.customer_satisfaction,
        status=closure.status,
        review_result=closure.review_result,
        review_notes=closure.review_notes,
        reviewed_at=closure.reviewed_at,
        reviewed_by=closure.reviewed_by,
        created_at=closure.created_at,
        updated_at=closure.updated_at,
    )


@router.put("/pmo/closures/{closure_id}/lessons", response_model=ClosureResponse)
def update_closure_lessons(
    *,
    db: Session = Depends(deps.get_db),
    closure_id: int,
    lessons_request: ClosureLessonsRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经验教训
    """
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.id == closure_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="结项记录不存在")

    closure.lessons_learned = lessons_request.lessons_learned
    closure.improvement_suggestions = lessons_request.improvement_suggestions

    db.add(closure)
    db.commit()
    db.refresh(closure)

    return ClosureResponse(
        id=closure.id,
        project_id=closure.project_id,
        acceptance_date=closure.acceptance_date,
        acceptance_result=closure.acceptance_result,
        acceptance_notes=closure.acceptance_notes,
        project_summary=closure.project_summary,
        achievement=closure.achievement,
        lessons_learned=closure.lessons_learned,
        improvement_suggestions=closure.improvement_suggestions,
        final_budget=float(closure.final_budget) if closure.final_budget else None,
        final_cost=float(closure.final_cost) if closure.final_cost else None,
        cost_variance=float(closure.cost_variance) if closure.cost_variance else None,
        final_planned_hours=closure.final_planned_hours,
        final_actual_hours=closure.final_actual_hours,
        hours_variance=closure.hours_variance,
        plan_duration=closure.plan_duration,
        actual_duration=closure.actual_duration,
        schedule_variance=closure.schedule_variance,
        quality_score=closure.quality_score,
        customer_satisfaction=closure.customer_satisfaction,
        status=closure.status,
        review_result=closure.review_result,
        review_notes=closure.review_notes,
        reviewed_at=closure.reviewed_at,
        reviewed_by=closure.reviewed_by,
        created_at=closure.created_at,
        updated_at=closure.updated_at,
    )


@router.post("/pmo/closures/{closure_id}/archive", response_model=ResponseModel)
def archive_closure(
    *,
    db: Session = Depends(deps.get_db),
    closure_id: int,
    archive_paths: Optional[List[str]] = Query(None, description="归档文件路径列表"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    文档归档
    """
    closure = db.query(PmoProjectClosure).filter(PmoProjectClosure.id == closure_id).first()
    if not closure:
        raise HTTPException(status_code=404, detail="结项记录不存在")

    # 更新归档状态
    closure.status = 'ARCHIVED'
    # 如果有归档路径，可以存储到数据库（需要扩展模型字段）或记录到日志

    db.add(closure)
    db.commit()

    return ResponseModel(
        code=200,
        message="文档归档成功",
        data={
            "closure_id": closure_id,
            "project_id": closure.project_id,
            "archive_paths": archive_paths or [],
            "archived_at": datetime.now().isoformat()
        }
    )


