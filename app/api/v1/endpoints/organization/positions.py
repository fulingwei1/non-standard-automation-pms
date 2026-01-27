# -*- coding: utf-8 -*-
"""
岗位管理端点（重构版）
使用统一响应格式
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas import list_response, success_response
from app.models.organization import Position
from app.models.user import User
from app.schemas.organization import (
    PositionCreate,
    PositionResponse,
    PositionUpdate,
)

router = APIRouter()


@router.get("/")
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

    # 转换为Pydantic模型
    pos_responses = [PositionResponse.model_validate(pos) for pos in positions]

    # 使用统一响应格式
    return list_response(
        items=pos_responses,
        message="获取岗位列表成功"
    )


@router.post("/")
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

    # 转换为Pydantic模型
    pos_response = PositionResponse.model_validate(pos)

    # 使用统一响应格式
    return success_response(
        data=pos_response,
        message="岗位创建成功"
    )


@router.get("/{id}")
def get_position(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取指定岗位信息"""
    pos = db.query(Position).filter(Position.id == id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 转换为Pydantic模型
    pos_response = PositionResponse.model_validate(pos)

    # 使用统一响应格式
    return success_response(
        data=pos_response,
        message="获取岗位信息成功"
    )


@router.put("/{id}")
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

    # 转换为Pydantic模型
    pos_response = PositionResponse.model_validate(pos)

    # 使用统一响应格式
    return success_response(
        data=pos_response,
        message="岗位更新成功"
    )


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

    # 使用统一响应格式
    return success_response(
        data={"id": id},
        message="岗位删除成功"
    )


@router.get("/{id}/roles")
def get_position_roles(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取岗位的默认角色"""
    pos = db.query(Position).filter(Position.id == id).first()
    if not pos:
        raise HTTPException(status_code=404, detail="岗位不存在")

    # 获取角色列表
    roles = [pr.role for pr in pos.position_roles if pr.is_active]

    # 构建角色响应数据
    role_data = []
    for role in roles:
        role_data.append({
            "id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "is_active": role.is_active,
        })

    # 使用统一响应格式
    return list_response(
        items=role_data,
        message="获取岗位角色成功"
    )
