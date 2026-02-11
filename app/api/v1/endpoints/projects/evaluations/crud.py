# -*- coding: utf-8 -*-
"""
项目评价 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
复杂逻辑通过覆盖端点实现
"""

from decimal import Decimal
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, status
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.project_evaluation import ProjectEvaluation
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project_evaluation import (
    ProjectEvaluationCreate,
    ProjectEvaluationUpdate,
    ProjectEvaluationResponse,
)
from app.services.project_evaluation_service import ProjectEvaluationService
from app.utils.permission_helpers import check_project_access_or_raise
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter


def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(ProjectEvaluation.status == status)


# 使用项目中心CRUD路由基类创建路由
base_router = create_project_crud_router(
    model=ProjectEvaluation,
    create_schema=ProjectEvaluationCreate,
    update_schema=ProjectEvaluationUpdate,
    response_schema=ProjectEvaluationResponse,
    permission_prefix="project_evaluation",
    project_id_field="project_id",
    keyword_fields=["evaluation_note"],  # 评价说明可搜索
    default_order_by="evaluation_date",
    default_order_direction="desc",
    custom_filters={
        "status": filter_by_status,  # 支持 ?status=DRAFT 筛选
    },
)

# 创建新的router，先添加覆盖的端点，再添加基类的其他端点
router = APIRouter()


# 覆盖创建端点，使用服务层创建评价
@router.post("/", response_model=ResponseModel[ProjectEvaluationResponse], status_code=status.HTTP_201_CREATED)
def create_project_evaluation(
    project_id: int = Path(..., description="项目ID"),
    eval_in: ProjectEvaluationCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:create")),
) -> Any:
    """创建项目评价（覆盖基类端点，使用服务层）"""
    check_project_access_or_raise(
        db, current_user, project_id, "您没有权限为该项目创建评价"
    )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    eval_service = ProjectEvaluationService(db)
    
    # 转换weights中的Decimal为float（如果提供）
    weights_dict = None
    if eval_in.weights:
        weights_dict = {
            k: Decimal(str(v)) if not isinstance(v, Decimal) else v
            for k, v in eval_in.weights.items()
        }
    
    evaluation = eval_service.create_evaluation(
        project_id=project_id,
        novelty_score=eval_in.novelty_score,
        new_tech_score=eval_in.new_tech_score,
        difficulty_score=eval_in.difficulty_score,
        workload_score=eval_in.workload_score,
        amount_score=eval_in.amount_score,
        evaluator_id=current_user.id,
        evaluator_name=current_user.real_name or current_user.username,
        weights=weights_dict,
        evaluation_detail=eval_in.evaluation_detail,
        evaluation_note=eval_in.evaluation_note,
    )
    
    # 转换weights中的Decimal为float，以便JSON序列化
    if evaluation.weights:
        evaluation.weights = {
            k: float(v) if isinstance(v, Decimal) else v
            for k, v in evaluation.weights.items()
        }
    
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    
    return ResponseModel(code=200, message="创建成功", data=evaluation)


# 覆盖更新端点，使用服务层重新计算得分
@router.put("/{eval_id}", response_model=ResponseModel[ProjectEvaluationResponse])
def update_project_evaluation(
    project_id: int = Path(..., description="项目ID"),
    eval_id: int = Path(..., description="评价ID"),
    eval_in: ProjectEvaluationUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:update")),
) -> Any:
    """更新项目评价（覆盖基类端点，使用服务层重新计算得分）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    evaluation = db.query(ProjectEvaluation).filter(
        ProjectEvaluation.id == eval_id,
        ProjectEvaluation.project_id == project_id,
    ).first()
    
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
        difficulty_score = update_data.get("difficulty_score", evaluation.difficulty_score)
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


# 覆盖列表端点，使用正确的响应格式
@router.get("/")
def list_project_evaluations(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: str = None,
    order_by: str = None,
    order_direction: str = "desc",
    status: str = None,
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """获取项目的所有评价记录（覆盖基类端点，使用正确的响应格式）"""
    from app.schemas.project_evaluation import ProjectEvaluationListResponse
    from sqlalchemy import or_
    
    check_project_access_or_raise(db, current_user, project_id)
    
    # 构建查询
    query = db.query(ProjectEvaluation).filter(ProjectEvaluation.project_id == project_id)
    
    # 状态筛选
    if status:
        query = query.filter(ProjectEvaluation.status == status)
    
    # 关键词搜索
    query = apply_keyword_filter(query, ProjectEvaluation, keyword, "evaluation_note")
    
    # 排序
    order_field = getattr(ProjectEvaluation, order_by or "evaluation_date", None)
    if order_field:
        if order_direction == "asc":
            query = query.order_by(order_field.asc())
        else:
            query = query.order_by(order_field.desc())
    
    # 分页
    total = query.count()
    evaluations = query.offset(pagination.offset).limit(pagination.limit).all()
    
    # 使用正确的响应格式（ProjectEvaluationListResponse是PaginatedResponse的别名）
    return ProjectEvaluationListResponse(
        items=evaluations,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


# 覆盖详情端点，使用正确的响应格式
@router.get("/{eval_id}", response_model=ResponseModel[ProjectEvaluationResponse])
def get_project_evaluation(
    project_id: int = Path(..., description="项目ID"),
    eval_id: int = Path(..., description="评价ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("project_evaluation:read")),
) -> Any:
    """获取项目评价详情（覆盖基类端点，使用正确的响应格式）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    evaluation = db.query(ProjectEvaluation).filter(
        ProjectEvaluation.id == eval_id,
        ProjectEvaluation.project_id == project_id,
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=404, detail="评价记录不存在")
    
    return ResponseModel(code=200, data=evaluation)
