# -*- coding: utf-8 -*-
"""
ECN类型配置管理 API endpoints

包含：ECN类型列表、详情、创建、更新、删除
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.ecn import Ecn, EcnType
from app.schemas.ecn import EcnTypeCreate, EcnTypeUpdate, EcnTypeResponse
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/ecn-types", response_model=List[EcnTypeResponse], status_code=status.HTTP_200_OK)
def list_ecn_types(
    db: Session = Depends(deps.get_db),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN类型配置列表
    """
    query = db.query(EcnType)
    if is_active is not None:
        query = query.filter(EcnType.is_active == is_active)

    ecn_types = query.order_by(EcnType.type_code).all()

    items = []
    for et in ecn_types:
        items.append(EcnTypeResponse(
            id=et.id,
            type_code=et.type_code,
            type_name=et.type_name,
            description=et.description,
            required_depts=et.required_depts,
            optional_depts=et.optional_depts,
            approval_matrix=et.approval_matrix,
            is_active=et.is_active,
            created_at=et.created_at,
            updated_at=et.updated_at
        ))

    return items


@router.get("/ecn-types/{type_id}", response_model=EcnTypeResponse, status_code=status.HTTP_200_OK)
def get_ecn_type(
    type_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN类型配置详情
    """
    ecn_type = db.query(EcnType).filter(EcnType.id == type_id).first()
    if not ecn_type:
        raise HTTPException(status_code=404, detail="ECN类型配置不存在")

    return EcnTypeResponse(
        id=ecn_type.id,
        type_code=ecn_type.type_code,
        type_name=ecn_type.type_name,
        description=ecn_type.description,
        required_depts=ecn_type.required_depts,
        optional_depts=ecn_type.optional_depts,
        approval_matrix=ecn_type.approval_matrix,
        is_active=ecn_type.is_active,
        created_at=ecn_type.created_at,
        updated_at=ecn_type.updated_at
    )


@router.post("/ecn-types", response_model=EcnTypeResponse, status_code=status.HTTP_201_CREATED)
def create_ecn_type(
    *,
    db: Session = Depends(deps.get_db),
    type_in: EcnTypeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建ECN类型配置
    """
    # 检查类型编码是否已存在
    existing = db.query(EcnType).filter(EcnType.type_code == type_in.type_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="类型编码已存在")

    ecn_type = EcnType(
        type_code=type_in.type_code,
        type_name=type_in.type_name,
        description=type_in.description,
        required_depts=type_in.required_depts,
        optional_depts=type_in.optional_depts,
        approval_matrix=type_in.approval_matrix,
        is_active=type_in.is_active
    )

    db.add(ecn_type)
    db.commit()
    db.refresh(ecn_type)

    return get_ecn_type(ecn_type.id, db, current_user)


@router.put("/ecn-types/{type_id}", response_model=EcnTypeResponse, status_code=status.HTTP_200_OK)
def update_ecn_type(
    *,
    db: Session = Depends(deps.get_db),
    type_id: int,
    type_in: EcnTypeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新ECN类型配置
    """
    ecn_type = db.query(EcnType).filter(EcnType.id == type_id).first()
    if not ecn_type:
        raise HTTPException(status_code=404, detail="ECN类型配置不存在")

    update_data = type_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ecn_type, field, value)

    db.add(ecn_type)
    db.commit()
    db.refresh(ecn_type)

    return get_ecn_type(type_id, db, current_user)


@router.delete("/ecn-types/{type_id}", status_code=status.HTTP_200_OK)
def delete_ecn_type(
    *,
    db: Session = Depends(deps.get_db),
    type_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除ECN类型配置
    """
    ecn_type = db.query(EcnType).filter(EcnType.id == type_id).first()
    if not ecn_type:
        raise HTTPException(status_code=404, detail="ECN类型配置不存在")

    # 检查是否有ECN使用此类型
    ecn_count = db.query(Ecn).filter(Ecn.ecn_type == ecn_type.type_code).count()
    if ecn_count > 0:
        raise HTTPException(status_code=400, detail=f"有{ecn_count}个ECN使用此类型，无法删除")

    db.delete(ecn_type)
    db.commit()

    return ResponseModel(code=200, message="ECN类型配置已删除")
