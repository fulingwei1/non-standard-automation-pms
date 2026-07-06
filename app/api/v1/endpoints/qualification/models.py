# -*- coding: utf-8 -*-
"""
岗位能力模型管理端点
"""

from __future__ import annotations

from datetime import datetime
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
    QualificationLevelResponse,
)
from app.services.qualification_service import QualificationService
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _level_response(level: QualificationLevel | None) -> QualificationLevelResponse | None:
    if level is None:
        return None
    return QualificationLevelResponse(
        id=level.id,
        level_code=level.level_code or "",
        level_name=level.level_name or "",
        level_order=level.level_order or 0,
        role_type=level.role_type,
        description=level.description,
        is_active=True if level.is_active is None else bool(level.is_active),
        created_at=level.created_at,
        updated_at=level.updated_at,
    )


def _model_response(model: PositionCompetencyModel) -> PositionCompetencyModelResponse:
    return PositionCompetencyModelResponse(
        id=model.id,
        position_type=model.position_type or "",
        position_subtype=model.position_subtype,
        level_id=model.level_id,
        competency_dimensions=model.competency_dimensions or {},
        is_active=True if model.is_active is None else bool(model.is_active),
        created_at=model.created_at,
        updated_at=model.updated_at,
        level=_level_response(model.level),
    )


def _empty_model_response(
    position_type: str,
    level_id: int,
    position_subtype: str | None = None,
) -> PositionCompetencyModelResponse:
    now = datetime.utcnow()
    return PositionCompetencyModelResponse(
        id=0,
        position_type=position_type or "",
        position_subtype=position_subtype,
        level_id=level_id,
        competency_dimensions={},
        is_active=False,
        created_at=now,
        updated_at=now,
        level=None,
    )


@router.post(
    "/models",
    response_model=ResponseModel[PositionCompetencyModelResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_competency_model(
    *,
    db: Session = Depends(deps.get_db),
    model_in: PositionCompetencyModelCreate,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """创建岗位能力模型"""
    # 检查等级是否存在
    get_or_404(db, QualificationLevel, model_in.level_id, "等级不存在")

    model = PositionCompetencyModel(**model_in.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)

    return ResponseModel(code=200, message="创建成功", data=_model_response(model))


@router.get(
    "/models", response_model=PositionCompetencyModelListResponse, status_code=status.HTTP_200_OK
)
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
    models = (
        query.order_by(desc(PositionCompetencyModel.created_at))
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    return PositionCompetencyModelListResponse(
        items=[_model_response(model) for model in models],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.get(
    "/models/{position_type}/{level_id}",
    response_model=ResponseModel[PositionCompetencyModelResponse],
    status_code=status.HTTP_200_OK,
)
def get_competency_model_by_position_level(
    *,
    db: Session = Depends(deps.get_db),
    position_type: str,
    level_id: int,
    position_subtype: Optional[str] = Query(None, description="岗位子类型"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取特定岗位等级的能力要求"""
    model = QualificationService.get_competency_model(db, position_type, level_id, position_subtype)
    if not model:
        return ResponseModel(
            code=200,
            message="能力模型不存在，返回空模型",
            data=_empty_model_response(position_type, level_id, position_subtype),
        )

    return ResponseModel(code=200, message="获取成功", data=_model_response(model))


@router.get(
    "/models/{model_id}",
    response_model=ResponseModel[PositionCompetencyModelResponse],
    status_code=status.HTTP_200_OK,
)
def get_competency_model_by_id(
    *,
    db: Session = Depends(deps.get_db),
    model_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """按ID获取岗位能力模型，供编辑页读取详情。"""
    model = get_or_404(db, PositionCompetencyModel, model_id, "能力模型不存在")
    return ResponseModel(code=200, message="获取成功", data=_model_response(model))


@router.put(
    "/models/{model_id}",
    response_model=ResponseModel[PositionCompetencyModelResponse],
    status_code=status.HTTP_200_OK,
)
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

    return ResponseModel(code=200, message="更新成功", data=_model_response(model))
