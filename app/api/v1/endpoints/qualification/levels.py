# -*- coding: utf-8 -*-
"""
任职资格等级管理端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.qualification import (
    EmployeeQualification,
    PositionCompetencyModel,
    QualificationLevel,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.qualification import (
    QualificationLevelCreate,
    QualificationLevelListResponse,
    QualificationLevelResponse,
    QualificationLevelUpdate,
)
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


@router.post("/levels", response_model=ResponseModel[QualificationLevelResponse], status_code=status.HTTP_201_CREATED)
def create_qualification_level(
    *,
    db: Session = Depends(deps.get_db),
    level_in: QualificationLevelCreate,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """创建任职资格等级（仅人力资源经理可配置）"""
    # 检查等级编码是否已存在
    existing = db.query(QualificationLevel).filter(
        QualificationLevel.level_code == level_in.level_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"等级编码 {level_in.level_code} 已存在"
        )

    level = QualificationLevel(**level_in.model_dump())
    db.add(level)
    db.commit()
    db.refresh(level)

    return ResponseModel(code=200, message="创建成功", data=level)


@router.get("/levels", response_model=QualificationLevelListResponse, status_code=status.HTTP_200_OK)
def get_qualification_levels(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    role_type: Optional[str] = Query(None, description="角色类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取任职资格等级列表"""
    query = db.query(QualificationLevel)

    if role_type:
        query = query.filter(QualificationLevel.role_type == role_type)
    if is_active is not None:
        query = query.filter(QualificationLevel.is_active == is_active)

    total = query.count()
    levels = query.order_by(QualificationLevel.level_order).offset(
        pagination.offset
    ).limit(pagination.limit).all()

    return QualificationLevelListResponse(
        items=levels,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/levels/{level_id}", response_model=ResponseModel[QualificationLevelResponse], status_code=status.HTTP_200_OK)
def get_qualification_level(
    *,
    db: Session = Depends(deps.get_db),
    level_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取任职资格等级详情"""
    level = get_or_404(db, QualificationLevel, level_id, "等级不存在")

    return ResponseModel(code=200, message="获取成功", data=level)


@router.put("/levels/{level_id}", response_model=ResponseModel[QualificationLevelResponse], status_code=status.HTTP_200_OK)
def update_qualification_level(
    *,
    db: Session = Depends(deps.get_db),
    level_id: int,
    level_in: QualificationLevelUpdate,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """更新任职资格等级"""
    level = get_or_404(db, QualificationLevel, level_id, "等级不存在")

    update_data = level_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(level, field, value)

    db.commit()
    db.refresh(level)

    return ResponseModel(code=200, message="更新成功", data=level)


@router.delete("/levels/{level_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_qualification_level(
    *,
    db: Session = Depends(deps.get_db),
    level_id: int,
    current_user: User = Depends(security.require_permission("hr:read")),
) -> Any:
    """删除任职资格等级"""
    level = get_or_404(db, QualificationLevel, level_id, "等级不存在")

    # 检查是否有关联数据
    competency_count = db.query(PositionCompetencyModel).filter(
        PositionCompetencyModel.level_id == level_id
    ).count()
    qualification_count = db.query(EmployeeQualification).filter(
        EmployeeQualification.current_level_id == level_id
    ).count()

    if competency_count > 0 or qualification_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该等级下存在关联数据，无法删除"
        )

    db.delete(level)
    db.commit()

    return ResponseModel(code=200, message="删除成功", data=None)
