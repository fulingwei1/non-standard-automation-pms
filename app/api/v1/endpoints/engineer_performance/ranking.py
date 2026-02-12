# -*- coding: utf-8 -*-
"""
绩效排名端点
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.performance import PerformancePeriod
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.engineer_performance.engineer_performance_service import (
    EngineerPerformanceService,
)

router = APIRouter(prefix="/ranking", tags=["绩效排名"])


@router.get("", summary="综合排名")
async def get_ranking(
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    job_type: Optional[str] = Query(None, description="岗位类型"),
    job_level: Optional[str] = Query(None, description="职级"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师绩效排名"""
    service = EngineerPerformanceService(db)

    # 获取周期
    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="未找到当前考核周期")
        period_id = period.id
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()

    results, total = service.get_ranking(
        period_id=period_id,
        job_type=job_type,
        job_level=job_level,
        department_id=department_id,
        limit=pagination.limit,
        offset=pagination.offset
    )

    items = []
    for i, r in enumerate(results, pagination.offset + 1):
        items.append({
            "rank": i,
            "user_id": r.user_id,
            "user_name": r.user_name,
            "department_name": r.department_name,
            "job_type": r.job_type,
            "job_level": r.job_level,
            "total_score": float(r.total_score or 0),
            "level": r.level,
            "score_change": float(r.score_change) if r.score_change else None,
            "rank_change": r.rank_change
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period_id": period_id,
            "period_name": period.period_name if period else "",
            "total": total,
            "items": items
        }
    )


@router.get("/by-department", summary="按部门排名")
async def get_ranking_by_department(
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    department_id: int = Query(..., description="部门ID"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取部门内排名"""
    service = EngineerPerformanceService(db)

    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active
        ).first()
        if period:
            period_id = period.id

    results, total = service.get_ranking(
        period_id=period_id,
        department_id=department_id,
        limit=pagination.limit,
        offset=pagination.offset
    )

    items = []
    for i, r in enumerate(results, pagination.offset + 1):
        items.append({
            "rank": i,
            "user_id": r.user_id,
            "user_name": r.user_name,
            "job_type": r.job_type,
            "job_level": r.job_level,
            "total_score": float(r.total_score or 0),
            "level": r.level
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "department_id": department_id,
            "total": total,
            "items": items
        }
    )


@router.get("/by-job-type", summary="按岗位类型排名")
async def get_ranking_by_job_type(
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    job_type: str = Query(..., description="岗位类型"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取岗位类型内排名"""
    if job_type not in ['mechanical', 'test', 'electrical']:
        raise HTTPException(status_code=400, detail="无效的岗位类型")

    service = EngineerPerformanceService(db)

    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active
        ).first()
        if period:
            period_id = period.id

    results, total = service.get_ranking(
        period_id=period_id,
        job_type=job_type,
        limit=pagination.limit,
        offset=pagination.offset
    )

    items = []
    for i, r in enumerate(results, pagination.offset + 1):
        items.append({
            "rank": i,
            "user_id": r.user_id,
            "user_name": r.user_name,
            "department_name": r.department_name,
            "job_level": r.job_level,
            "total_score": float(r.total_score or 0),
            "level": r.level
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "job_type": job_type,
            "total": total,
            "items": items
        }
    )


@router.get("/top", summary="Top N 工程师")
async def get_top_engineers(
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    n: int = Query(10, ge=1, le=50, description="返回数量"),
    job_type: Optional[str] = Query(None, description="岗位类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 Top N 工程师"""
    service = EngineerPerformanceService(db)

    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active
        ).first()
        if period:
            period_id = period.id

    results, _ = service.get_ranking(
        period_id=period_id,
        job_type=job_type,
        limit=n
    )

    items = []
    for i, r in enumerate(results, 1):
        items.append({
            "rank": i,
            "user_id": r.user_id,
            "user_name": r.user_name,
            "department_name": r.department_name,
            "job_type": r.job_type,
            "job_level": r.job_level,
            "total_score": float(r.total_score or 0),
            "level": r.level
        })

    return ResponseModel(
        code=200,
        message="success",
        data=items
    )
