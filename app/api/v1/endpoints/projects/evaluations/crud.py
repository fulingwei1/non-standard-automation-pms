# -*- coding: utf-8 -*-
"""
项目评价 CRUD 操作

路由: /projects/{project_id}/evaluations/
提供项目视角的评价管理功能
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project_evaluation import ProjectEvaluation
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project_evaluation import (
    ProjectEvaluationCreate,
    ProjectEvaluationListResponse,
    ProjectEvaluationResponse,
    ProjectEvaluationUpdate,
)
from app.services.project_evaluation_service import ProjectEvaluationService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/", response_model=ProjectEvaluationListResponse)
def list_project_evaluations(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    evaluation_status: Optional[str] = Query(None, alias="status", description="评价状态"),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """获取项目的所有评价记录"""
    check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectEvaluation).filter(ProjectEvaluation.project_id == project_id)

    if evaluation_status:
        query = query.filter(ProjectEvaluation.status == evaluation_status)

    total = query.count()
    evaluations = (
        query.order_by(desc(ProjectEvaluation.evaluation_date))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ProjectEvaluationListResponse(
        items=evaluations,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/latest", response_model=ResponseModel[ProjectEvaluationResponse])
def get_project_latest_evaluation(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """获取项目最新评价"""
    check_project_access_or_raise(db, current_user, project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    eval_service = ProjectEvaluationService(db)
    evaluation = eval_service.get_latest_evaluation(project_id)

    if not evaluation:
        raise HTTPException(status_code=404, detail="项目暂无评价记录")

    return ResponseModel(code=200, data=evaluation)


@router.post("/", response_model=ResponseModel[ProjectEvaluationResponse], status_code=status.HTTP_201_CREATED)
def create_project_evaluation(
    eval_in: ProjectEvaluationCreate,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:create")),
) -> Any:
    """创建项目评价"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限为该项目创建评价"
    )

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    eval_service = ProjectEvaluationService(db)

    evaluation = eval_service.create_evaluation(
        project_id=project_id,
        novelty_score=eval_in.novelty_score,
        new_tech_score=eval_in.new_tech_score,
        difficulty_score=eval_in.difficulty_score,
        workload_score=eval_in.workload_score,
        amount_score=eval_in.amount_score,
        evaluator_id=current_user.id,
        evaluator_name=current_user.real_name or current_user.username,
        weights=eval_in.weights,
        evaluation_detail=eval_in.evaluation_detail,
        evaluation_note=eval_in.evaluation_note,
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return ResponseModel(code=200, message="创建成功", data=evaluation)


@router.get("/{eval_id}", response_model=ResponseModel[ProjectEvaluationResponse])
def get_project_evaluation(
    project_id: int = Path(..., description="项目ID"),
    eval_id: int = Path(..., description="评价ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """获取项目评价详情"""
    check_project_access_or_raise(db, current_user, project_id)

    evaluation = (
        db.query(ProjectEvaluation)
        .filter(
            ProjectEvaluation.id == eval_id, ProjectEvaluation.project_id == project_id
        )
        .first()
    )

    if not evaluation:
        raise HTTPException(status_code=404, detail="评价记录不存在")

    return ResponseModel(code=200, data=evaluation)


@router.put("/{eval_id}", response_model=ResponseModel[ProjectEvaluationResponse])
def update_project_evaluation(
    eval_in: ProjectEvaluationUpdate,
    project_id: int = Path(..., description="项目ID"),
    eval_id: int = Path(..., description="评价ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:update")),
) -> Any:
    """更新项目评价"""
    check_project_access_or_raise(db, current_user, project_id)

    evaluation = (
        db.query(ProjectEvaluation)
        .filter(
            ProjectEvaluation.id == eval_id, ProjectEvaluation.project_id == project_id
        )
        .first()
    )

    if not evaluation:
        raise HTTPException(status_code=404, detail="评价记录不存在")

    update_data = eval_in.model_dump(exclude_unset=True)

    # 如果有得分更新，需要重新计算综合得分
    if any(
        key in update_data
        for key in [
            "novelty_score",
            "new_tech_score",
            "difficulty_score",
            "workload_score",
            "amount_score",
            "weights",
        ]
    ):
        eval_service = ProjectEvaluationService(db)

        novelty_score = update_data.get("novelty_score", evaluation.novelty_score)
        new_tech_score = update_data.get("new_tech_score", evaluation.new_tech_score)
        difficulty_score = update_data.get(
            "difficulty_score", evaluation.difficulty_score
        )
        workload_score = update_data.get("workload_score", evaluation.workload_score)
        amount_score = update_data.get("amount_score", evaluation.amount_score)
        weights = update_data.get("weights", evaluation.weights)

        total_score = eval_service.calculate_total_score(
            novelty_score,
            new_tech_score,
            difficulty_score,
            workload_score,
            amount_score,
            weights,
        )
        evaluation_level = eval_service.determine_evaluation_level(total_score)

        update_data["total_score"] = total_score
        update_data["evaluation_level"] = evaluation_level

    for field, value in update_data.items():
        setattr(evaluation, field, value)

    db.commit()
    db.refresh(evaluation)

    return ResponseModel(code=200, message="更新成功", data=evaluation)


@router.post("/{eval_id}/confirm", response_model=ResponseModel[ProjectEvaluationResponse])
def confirm_project_evaluation(
    project_id: int = Path(..., description="项目ID"),
    eval_id: int = Path(..., description="评价ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:update")),
) -> Any:
    """确认项目评价（将状态改为CONFIRMED）"""
    check_project_access_or_raise(db, current_user, project_id)

    evaluation = (
        db.query(ProjectEvaluation)
        .filter(
            ProjectEvaluation.id == eval_id, ProjectEvaluation.project_id == project_id
        )
        .first()
    )

    if not evaluation:
        raise HTTPException(status_code=404, detail="评价记录不存在")

    evaluation.status = "CONFIRMED"
    db.commit()
    db.refresh(evaluation)

    return ResponseModel(code=200, message="确认成功", data=evaluation)
