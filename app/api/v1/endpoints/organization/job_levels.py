# -*- coding: utf-8 -*-
"""
职级管理端点
"""

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import JobLevel
from app.models.user import User
from app.schemas.organization import (
    JobLevelCreate,
    JobLevelResponse,
    JobLevelUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[JobLevelResponse])
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
    return levels


@router.post("/", response_model=JobLevelResponse)
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
    return level


@router.get("/{id}", response_model=JobLevelResponse)
def get_job_level(
    id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取指定职级信息"""
    level = db.query(JobLevel).filter(JobLevel.id == id).first()
    if not level:
        raise HTTPException(status_code=404, detail="职级不存在")
    return level


@router.put("/{id}", response_model=JobLevelResponse)
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
    return level


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
    return {"message": "Success"}
