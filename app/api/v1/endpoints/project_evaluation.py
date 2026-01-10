# -*- coding: utf-8 -*-
"""
项目评价模块 API 端点
"""

from typing import Any, List, Optional
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.project_evaluation import (
    ProjectEvaluation, ProjectEvaluationDimension
)
from app.schemas.project_evaluation import (
    ProjectEvaluationCreate, ProjectEvaluationUpdate,
    ProjectEvaluationResponse, ProjectEvaluationListResponse,
    ProjectEvaluationQuery, AutoEvaluationRequest,
    ProjectEvaluationDimensionCreate, ProjectEvaluationDimensionUpdate,
    ProjectEvaluationDimensionResponse, ProjectEvaluationDimensionListResponse,
    ProjectEvaluationStatisticsResponse
)
from app.schemas.common import ResponseModel
from app.services.project_evaluation_service import ProjectEvaluationService

router = APIRouter()


# ==================== 项目评价 ====================

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


# ==================== 评价维度配置 ====================

@router.get("/dimensions", response_model=ProjectEvaluationDimensionListResponse, status_code=status.HTTP_200_OK)
def get_evaluation_dimensions(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=100),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    获取评价维度配置列表
    """
    query = db.query(ProjectEvaluationDimension)
    
    if is_active is not None:
        query = query.filter(ProjectEvaluationDimension.is_active == is_active)
    
    total = query.count()
    dimensions = query.order_by(ProjectEvaluationDimension.sort_order).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return ProjectEvaluationDimensionListResponse(
        items=dimensions,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/dimensions/{dim_id}", response_model=ResponseModel[ProjectEvaluationDimensionResponse], status_code=status.HTTP_200_OK)
def get_evaluation_dimension(
    *,
    db: Session = Depends(deps.get_db),
    dim_id: int,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    获取评价维度配置详情
    """
    dimension = db.query(ProjectEvaluationDimension).filter(ProjectEvaluationDimension.id == dim_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="评价维度配置不存在")
    
    return ResponseModel(code=200, data=dimension)


@router.post("/dimensions", response_model=ResponseModel[ProjectEvaluationDimensionResponse], status_code=status.HTTP_201_CREATED)
def create_evaluation_dimension(
    *,
    db: Session = Depends(deps.get_db),
    dim_in: ProjectEvaluationDimensionCreate,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    创建评价维度配置（管理员功能）
    """
    # 检查维度编码是否已存在
    existing = db.query(ProjectEvaluationDimension).filter(
        ProjectEvaluationDimension.dimension_code == dim_in.dimension_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="维度编码已存在")
    
    dimension = ProjectEvaluationDimension(**dim_in.model_dump())
    db.add(dimension)
    db.commit()
    db.refresh(dimension)
    
    return ResponseModel(code=200, message="创建成功", data=dimension)


@router.put("/dimensions/{dim_id}", response_model=ResponseModel[ProjectEvaluationDimensionResponse], status_code=status.HTTP_200_OK)
def update_evaluation_dimension(
    *,
    db: Session = Depends(deps.get_db),
    dim_id: int,
    dim_in: ProjectEvaluationDimensionUpdate,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    更新评价维度配置（管理员功能）
    """
    dimension = db.query(ProjectEvaluationDimension).filter(ProjectEvaluationDimension.id == dim_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="评价维度配置不存在")
    
    # 检查维度编码是否与其他记录冲突
    if dim_in.dimension_code and dim_in.dimension_code != dimension.dimension_code:
        existing = db.query(ProjectEvaluationDimension).filter(
            ProjectEvaluationDimension.dimension_code == dim_in.dimension_code,
            ProjectEvaluationDimension.id != dim_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="维度编码已被其他配置使用")
    
    # 更新字段（update_data已在上面定义）
    for field, value in update_data.items():
        setattr(dimension, field, value)
    
    db.commit()
    db.refresh(dimension)
    
    return ResponseModel(code=200, message="更新成功", data=dimension)


@router.delete("/dimensions/{dim_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_evaluation_dimension(
    *,
    db: Session = Depends(deps.get_db),
    dim_id: int,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    删除评价维度配置（管理员功能）
    """
    dimension = db.query(ProjectEvaluationDimension).filter(ProjectEvaluationDimension.id == dim_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="评价维度配置不存在")
    
    db.delete(dimension)
    db.commit()
    
    return ResponseModel(code=200, message="删除成功")


@router.post("/dimensions/{dim_id}/toggle", response_model=ResponseModel[ProjectEvaluationDimensionResponse], status_code=status.HTTP_200_OK)
def toggle_dimension_status(
    *,
    db: Session = Depends(deps.get_db),
    dim_id: int,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    启用/停用评价维度配置（管理员功能）
    """
    dimension = db.query(ProjectEvaluationDimension).filter(ProjectEvaluationDimension.id == dim_id).first()
    if not dimension:
        raise HTTPException(status_code=404, detail="评价维度配置不存在")
    
    dimension.is_active = not dimension.is_active
    db.commit()
    db.refresh(dimension)
    
    return ResponseModel(
        code=200,
        message=f"{'启用' if dimension.is_active else '停用'}成功",
        data=dimension
    )


@router.get("/dimensions/weights/summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_dimension_weights_summary(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    获取维度权重配置摘要（用于前端显示和验证）
    """
    eval_service = ProjectEvaluationService(db)
    weights = eval_service.get_dimension_weights()
    
    # 转换为百分比格式
    weights_percent = {k: float(v * Decimal('100')) for k, v in weights.items()}
    total = sum(weights_percent.values())
    
    # 获取维度详情
    dimensions = db.query(ProjectEvaluationDimension).filter(
        ProjectEvaluationDimension.is_active == True
    ).order_by(ProjectEvaluationDimension.sort_order).all()
    
    dimension_details = []
    for dim in dimensions:
        dim_type_lower = dim.dimension_type.lower()
        if dim_type_lower in weights:
            dimension_details.append({
                "id": dim.id,
                "code": dim.dimension_code,
                "name": dim.dimension_name,
                "type": dim.dimension_type,
                "weight": float(weights[dim_type_lower] * Decimal('100')),
                "is_active": dim.is_active
            })
    
    return ResponseModel(
        code=200,
        data={
            "weights": weights_percent,
            "total": total,
            "is_valid": abs(total - 100) < 0.01,  # 允许0.01的误差
            "dimensions": dimension_details
        }
    )


# ==================== 评价统计 ====================

@router.get("/evaluations/statistics", response_model=ResponseModel[ProjectEvaluationStatisticsResponse], status_code=status.HTTP_200_OK)
def get_evaluation_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """
    获取项目评价统计
    """
    query = db.query(ProjectEvaluation).filter(
        ProjectEvaluation.status == 'CONFIRMED'
    )
    
    if start_date:
        query = query.filter(ProjectEvaluation.evaluation_date >= start_date)
    if end_date:
        query = query.filter(ProjectEvaluation.evaluation_date <= end_date)
    
    total_evaluations = query.count()
    
    # 按等级统计
    by_level = {}
    level_counts = query.with_entities(
        ProjectEvaluation.evaluation_level,
        func.count(ProjectEvaluation.id)
    ).group_by(ProjectEvaluation.evaluation_level).all()
    
    for level, count in level_counts:
        by_level[level] = count
    
    # 平均得分
    avg_scores = query.with_entities(
        func.avg(ProjectEvaluation.total_score),
        func.avg(ProjectEvaluation.novelty_score),
        func.avg(ProjectEvaluation.new_tech_score),
        func.avg(ProjectEvaluation.difficulty_score),
        func.avg(ProjectEvaluation.workload_score),
        func.avg(ProjectEvaluation.amount_score)
    ).first()
    
    return ResponseModel(
        code=200,
        data=ProjectEvaluationStatisticsResponse(
            total_evaluations=total_evaluations,
            by_level=by_level,
            avg_total_score=avg_scores[0] or Decimal('0'),
            avg_novelty_score=avg_scores[1] or Decimal('0'),
            avg_new_tech_score=avg_scores[2] or Decimal('0'),
            avg_difficulty_score=avg_scores[3] or Decimal('0'),
            avg_workload_score=avg_scores[4] or Decimal('0'),
            avg_amount_score=avg_scores[5] or Decimal('0')
        )
    )
