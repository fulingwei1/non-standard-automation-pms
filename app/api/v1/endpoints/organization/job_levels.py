# -*- coding: utf-8 -*-
"""
职级管理端点（重构版）
使用统一响应格式
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas import list_response, success_response
from app.models.organization import JobLevel
from app.models.user import User
from app.schemas.organization import (
    JobLevelCreate,
    JobLevelResponse,
    JobLevelUpdate,
)

router = APIRouter()


@router.get("/")
def list_job_levels(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="职级序列"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取职级列表"""
    query = db.query(JobLevel)
    if category:
        query = query.filter(JobLevel.level_category == category)
    if is_active is not None:
        query = query.filter(JobLevel.is_active == is_active)

    levels = (
        query.order_by(JobLevel.level_rank, JobLevel.sort_order, JobLevel.level_code)
        .offset(skip)
        .limit(limit)
        .all()
    )

    # 转换为Pydantic模型
    level_responses = [JobLevelResponse.model_validate(level) for level in levels]

    # 使用统一响应格式
    return list_response(
        items=level_responses,
        message="获取职级列表成功"
    )


@router.post("/")
def create_job_level(
    *,
    db: Session = Depends(deps.get_db),
    level_in: JobLevelCreate,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """创建职级"""
    level = (
        db.query(JobLevel).filter(JobLevel.level_code == level_in.level_code).first()
    )
    if level:
        raise HTTPException(status_code=400, detail="职级编码已存在")

    level = JobLevel(**level_in.model_dump())
    db.add(level)
    db.commit()
    db.refresh(level)

    # 转换为Pydantic模型
    level_response = JobLevelResponse.model_validate(level)

    # 使用统一响应格式
    return success_response(
        data=level_response,
        message="职级创建成功"
    )


@router.get("/{id}")
def get_job_level(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取指定职级信息"""
    level = db.query(JobLevel).filter(JobLevel.id == id).first()
    if not level:
        raise HTTPException(status_code=404, detail="职级不存在")

    # 转换为Pydantic模型
    level_response = JobLevelResponse.model_validate(level)

    # 使用统一响应格式
    return success_response(
        data=level_response,
        message="获取职级信息成功"
    )


@router.put("/{id}")
def update_job_level(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    level_in: JobLevelUpdate,
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """更新职级信息"""
    level = db.query(JobLevel).filter(JobLevel.id == id).first()
    if not level:
        raise HTTPException(status_code=404, detail="职级不存在")

    update_data = level_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(level, field, value)

    db.add(level)
    db.commit()
    db.refresh(level)

    # 转换为Pydantic模型
    level_response = JobLevelResponse.model_validate(level)

    # 使用统一响应格式
    return success_response(
        data=level_response,
        message="职级更新成功"
    )


@router.delete("/{id}")
def delete_job_level(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_superuser),
) -> Any:
    """删除职级"""
    level = db.query(JobLevel).filter(JobLevel.id == id).first()
    if not level:
        raise HTTPException(status_code=404, detail="职级不存在")

    db.delete(level)
    db.commit()

    # 使用统一响应格式
    return success_response(
        data={"id": id},
        message="职级删除成功"
    )
