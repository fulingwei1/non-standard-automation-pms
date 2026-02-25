# -*- coding: utf-8 -*-
"""
岗位能力模型管理端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.qualification import (
    PositionCompetencyModel,
    QualificationLevel,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.qualification import (
    PositionCompetencyModelCreate,
    PositionCompetencyModelListResponse,
    PositionCompetencyModelResponse,
    PositionCompetencyModelUpdate,
)
from app.services.qualification_service import QualificationService
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.post("/models", response_model=ResponseModel[PositionCompetencyModelResponse], status_code=status.HTTP_201_CREATED)
def create_competency_model(
    *,
    db: Session = Depends(deps.get_db),
    model_in: PositionCompetencyModelCreate,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """创建岗位能力模型"""
    # 检查等级是否存在
    level = get_or_404(db, QualificationLevel, model_in.level_id, "等级不存在")

    model = PositionCompetencyModel(**model_in.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)

    return ResponseModel(code=200, message="创建成功", data=model)


@router.get("/models", response_model=PositionCompetencyModelListResponse, status_code=status.HTTP_200_OK)
def get_competency_models(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    position_type: Optional[str] = Query(None, description="岗位类型"),
    position_subtype: Optional[str] = Query(None, description="岗位子类型"),
    level_id: Optional[int] = Query(None, description="等级ID"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取岗位能力模型列表"""
    query = db.query(PositionCompetencyModel)

    if position_type:
        query = query.filter(PositionCompetencyModel.position_type == position_type)
    if position_subtype:
        query = query.filter(PositionCompetencyModel.position_subtype == position_subtype)
    if level_id:
        query = query.filter(PositionCompetencyModel.level_id == level_id)
    if is_active is not None:
        query = query.filter(PositionCompetencyModel.is_active == is_active)

    total = query.count()
    models = query.order_by(desc(PositionCompetencyModel.created_at)).offset(
        pagination.offset
    ).limit(pagination.limit).all()

    return PositionCompetencyModelListResponse(
        items=models,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/models/{position_type}/{level_id}", response_model=ResponseModel[PositionCompetencyModelResponse], status_code=status.HTTP_200_OK)
def get_competency_model_by_position_level(
    *,
    db: Session = Depends(deps.get_db),
    position_type: str,
    level_id: int,
    position_subtype: Optional[str] = Query(None, description="岗位子类型"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取特定岗位等级的能力要求"""
    model = QualificationService.get_competency_model(
        db, position_type, level_id, position_subtype
    )
    if not model:
        raise HTTPException(status_code=404, detail="能力模型不存在")

    return ResponseModel(code=200, message="获取成功", data=model)


@router.put("/models/{model_id}", response_model=ResponseModel[PositionCompetencyModelResponse], status_code=status.HTTP_200_OK)
def update_competency_model(
    *,
    db: Session = Depends(deps.get_db),
    model_id: int,
    model_in: PositionCompetencyModelUpdate,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """更新岗位能力模型"""
    model = get_or_404(db, PositionCompetencyModel, model_id, "能力模型不存在")

    update_data = model_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)

    db.commit()
    db.refresh(model)

    return ResponseModel(code=200, message="更新成功", data=model)
