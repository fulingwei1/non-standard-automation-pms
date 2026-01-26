# -*- coding: utf-8 -*-
"""
岗位管理端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Position
from app.models.user import User
from app.schemas.organization import (
    PositionCreate,
    PositionResponse,
    PositionUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[PositionResponse])
def list_positions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    org_unit_id: Optional[int] = Query(None, description="组织单元ID"),
    category: Optional[str] = Query(None, description="岗位类别"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取岗位列表"""
    query = db.query(Position)
    if org_unit_id:
        query = query.filter(Position.org_unit_id == org_unit_id)
    if category:
        query = query.filter(Position.position_category == category)
    if is_active is not None:
        query = query.filter(Position.is_active == is_active)

    positions = (
        query.order_by(Position.sort_order, Position.position_code)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # 补充组织名称
    for p in positions:
        if p.org_unit:
            p.org_unit_name = p.org_unit.unit_name

    return positions


@router.post("/", response_model=PositionResponse)
def create_position(
    *,
    db: Session = Depends(deps.get_db),
    pos_in: PositionCreate,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """创建岗位"""
    pos = (
        db.query(Position)
        .filter(Position.position_code == pos_in.position_code)
        .first()
    )
    if pos:
        raise HTTPException(status_code=400, detail="岗位编码已存在")

    pos = Position(**pos_in.model_dump())
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


@router.get("/{id}", response_model=PositionResponse)
def get_position(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取指定岗位信息"""
    pos = db.query(Position).filter(Position.id == id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")

    if pos.org_unit:
        pos.org_unit_name = pos.org_unit.unit_name

    return pos


@router.put("/{id}", response_model=PositionResponse)
def update_position(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    pos_in: PositionUpdate,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """更新岗位信息"""
    pos = db.query(Position).filter(Position.id == id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")

    update_data = pos_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pos, field, value)

    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos


@router.delete("/{id}")
def delete_position(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """删除岗位"""
    pos = db.query(Position).filter(Position.id == id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")

    db.delete(pos)
    db.commit()
    return {"message": "Success"}


@router.get("/{id}/roles", response_model=List[Any])
def get_position_roles(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取岗位的默认角色"""
    pos = db.query(Position).filter(Position.id == id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")

    roles = [pr.role for pr in pos.position_roles if pr.is_active]
    return roles
