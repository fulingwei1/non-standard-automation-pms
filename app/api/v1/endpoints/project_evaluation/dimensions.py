# -*- coding: utf-8 -*-
"""
评价维度配置端点
"""

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project_evaluation import ProjectEvaluationDimension
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project_evaluation import (
    ProjectEvaluationDimensionCreate,
    ProjectEvaluationDimensionListResponse,
    ProjectEvaluationDimensionResponse,
    ProjectEvaluationDimensionUpdate,
)
from app.services.project_evaluation_service import ProjectEvaluationService

router = APIRouter()


# 注意：静态路由 /dimensions/weights/summary 必须在参数化路由 /dimensions/{dim_id} 之前定义
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

    update_data = dim_in.model_dump(exclude_unset=True)

    # 更新字段
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
