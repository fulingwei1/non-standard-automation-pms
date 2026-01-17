# -*- coding: utf-8 -*-
"""
项目评价 CRUD 端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project_evaluation import ProjectEvaluation
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project_evaluation import (
    AutoEvaluationRequest,
    ProjectEvaluationCreate,
    ProjectEvaluationListResponse,
    ProjectEvaluationQuery,
    ProjectEvaluationResponse,
    ProjectEvaluationUpdate,
)
from app.services.project_evaluation_service import ProjectEvaluationService

router = APIRouter()


@router.post("/evaluations", response_model=ResponseModel[ProjectEvaluationResponse], status_code=status.HTTP_201_CREATED)
def create_project_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    eval_in: ProjectEvaluationCreate,
    current_user: User = Depends(security.require_permission("project_evaluation:create")),
) -> Any:
    """
    创建项目评价
    """
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == eval_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 创建评价服务
    eval_service = ProjectEvaluationService(db)

    # 创建评价记录
    evaluation = eval_service.create_evaluation(
        project_id=eval_in.project_id,
        novelty_score=eval_in.novelty_score,
        new_tech_score=eval_in.new_tech_score,
        difficulty_score=eval_in.difficulty_score,
        workload_score=eval_in.workload_score,
        amount_score=eval_in.amount_score,
        evaluator_id=current_user.id,
        evaluator_name=current_user.real_name or current_user.username,
        weights=eval_in.weights,
        evaluation_detail=eval_in.evaluation_detail,
        evaluation_note=eval_in.evaluation_note
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return ResponseModel(code=200, message="创建成功", data=evaluation)


@router.post("/evaluations/auto", response_model=ResponseModel[ProjectEvaluationResponse], status_code=status.HTTP_201_CREATED)
def auto_create_project_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    request: AutoEvaluationRequest,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    自动创建项目评价（部分维度自动计算）
    """
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    eval_service = ProjectEvaluationService(db)

    # 自动计算得分
    novelty_score = None
    amount_score = None

    if request.auto_calculate_novelty:
        novelty_score = eval_service.auto_calculate_novelty_score(project)

    if request.auto_calculate_amount:
        amount_score = eval_service.auto_calculate_amount_score(project)

    # 使用手动评分覆盖自动计算
    if request.manual_scores:
        if 'novelty_score' in request.manual_scores:
            novelty_score = request.manual_scores['novelty_score']
        if 'amount_score' in request.manual_scores:
            amount_score = request.manual_scores['amount_score']

    # 检查必需字段
    if novelty_score is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目新旧得分未提供且无法自动计算"
        )
    if amount_score is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="项目金额得分未提供且无法自动计算"
        )

    # 从手动评分中获取其他得分，或使用默认值
    new_tech_score = request.manual_scores.get('new_tech_score') if request.manual_scores else None
    difficulty_score = request.manual_scores.get('difficulty_score') if request.manual_scores else None
    workload_score = request.manual_scores.get('workload_score') if request.manual_scores else None

    if not all([new_tech_score, difficulty_score, workload_score]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供新技术、难度、工作量得分"
        )

    # 创建评价
    evaluation = eval_service.create_evaluation(
        project_id=request.project_id,
        novelty_score=novelty_score,
        new_tech_score=new_tech_score,
        difficulty_score=difficulty_score,
        workload_score=workload_score,
        amount_score=amount_score,
        evaluator_id=current_user.id,
        evaluator_name=current_user.real_name or current_user.username
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return ResponseModel(code=200, message="创建成功", data=evaluation)


@router.get("/evaluations", response_model=ProjectEvaluationListResponse, status_code=status.HTTP_200_OK)
def get_project_evaluations(
    *,
    db: Session = Depends(deps.get_db),
    query_params: ProjectEvaluationQuery = Depends(),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    获取项目评价列表
    """
    query = db.query(ProjectEvaluation)

    if query_params.project_id:
        query = query.filter(ProjectEvaluation.project_id == query_params.project_id)
    if query_params.evaluation_level:
        query = query.filter(ProjectEvaluation.evaluation_level == query_params.evaluation_level)
    if query_params.evaluator_id:
        query = query.filter(ProjectEvaluation.evaluator_id == query_params.evaluator_id)
    if query_params.start_date:
        query = query.filter(ProjectEvaluation.evaluation_date >= query_params.start_date)
    if query_params.end_date:
        query = query.filter(ProjectEvaluation.evaluation_date <= query_params.end_date)
    if query_params.status:
        query = query.filter(ProjectEvaluation.status == query_params.status)

    total = query.count()
    evaluations = query.order_by(desc(ProjectEvaluation.evaluation_date)).offset(
        (query_params.page - 1) * query_params.page_size
    ).limit(query_params.page_size).all()

    return ProjectEvaluationListResponse(
        items=evaluations,
        total=total,
        page=query_params.page,
        page_size=query_params.page_size,
        pages=(total + query_params.page_size - 1) // query_params.page_size
    )


@router.get("/evaluations/{eval_id}", response_model=ResponseModel[ProjectEvaluationResponse], status_code=status.HTTP_200_OK)
def get_project_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    eval_id: int,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    获取项目评价详情
    """
    evaluation = db.query(ProjectEvaluation).filter(ProjectEvaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="评价记录不存在")

    return ResponseModel(code=200, data=evaluation)


@router.get("/projects/{project_id}/evaluation", response_model=ResponseModel[ProjectEvaluationResponse], status_code=status.HTTP_200_OK)
def get_project_latest_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    获取项目最新评价
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    eval_service = ProjectEvaluationService(db)
    evaluation = eval_service.get_latest_evaluation(project_id)

    if not evaluation:
        raise HTTPException(status_code=404, detail="项目暂无评价记录")

    return ResponseModel(code=200, data=evaluation)


@router.put("/evaluations/{eval_id}", response_model=ResponseModel[ProjectEvaluationResponse], status_code=status.HTTP_200_OK)
def update_project_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    eval_id: int,
    eval_in: ProjectEvaluationUpdate,
    current_user: User = Depends(security.require_permission("project_evaluation:update")),
) -> Any:
    """
    更新项目评价
    """
    evaluation = db.query(ProjectEvaluation).filter(ProjectEvaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="评价记录不存在")

    # 更新字段
    update_data = eval_in.model_dump(exclude_unset=True)

    # 如果有得分更新，需要重新计算综合得分
    if any(key in update_data for key in ['novelty_score', 'new_tech_score', 'difficulty_score', 'workload_score', 'amount_score', 'weights']):
        eval_service = ProjectEvaluationService(db)

        novelty_score = update_data.get('novelty_score', evaluation.novelty_score)
        new_tech_score = update_data.get('new_tech_score', evaluation.new_tech_score)
        difficulty_score = update_data.get('difficulty_score', evaluation.difficulty_score)
        workload_score = update_data.get('workload_score', evaluation.workload_score)
        amount_score = update_data.get('amount_score', evaluation.amount_score)
        weights = update_data.get('weights', evaluation.weights)

        # 重新计算
        total_score = eval_service.calculate_total_score(
            novelty_score, new_tech_score, difficulty_score,
            workload_score, amount_score, weights
        )
        evaluation_level = eval_service.determine_evaluation_level(total_score)

        update_data['total_score'] = total_score
        update_data['evaluation_level'] = evaluation_level

    for field, value in update_data.items():
        setattr(evaluation, field, value)

    db.commit()
    db.refresh(evaluation)

    return ResponseModel(code=200, message="更新成功", data=evaluation)


@router.post("/evaluations/{eval_id}/confirm", response_model=ResponseModel[ProjectEvaluationResponse], status_code=status.HTTP_200_OK)
def confirm_project_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    eval_id: int,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    确认项目评价（将状态改为CONFIRMED）
    """
    evaluation = db.query(ProjectEvaluation).filter(ProjectEvaluation.id == eval_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="评价记录不存在")

    evaluation.status = 'CONFIRMED'
    db.commit()
    db.refresh(evaluation)

    return ResponseModel(code=200, message="确认成功", data=evaluation)
