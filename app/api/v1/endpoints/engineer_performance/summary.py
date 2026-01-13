# -*- coding: utf-8 -*-
"""
绩效总览端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.performance import PerformancePeriod
from app.services.engineer_performance_service import EngineerPerformanceService
from app.schemas.engineer_performance import CompanySummaryResponse
from app.schemas.common import ResponseModel

router = APIRouter(prefix="/summary", tags=["绩效总览"])


@router.get("/company", summary="公司整体概况")
async def get_company_summary(
    period_id: Optional[int] = Query(None, description="考核周期ID，不传则使用当前周期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取公司工程师绩效整体概况"""
    service = EngineerPerformanceService(db)

    # 如果未指定周期，获取当前活跃周期
    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="未找到当前考核周期")
        period_id = period.id
    else:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.id == period_id
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="考核周期不存在")

    summary = service.get_company_summary(period_id)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period_id": period_id,
            "period_name": period.period_name,
            **summary
        }
    )


@router.get("/by-job-type/{job_type}", summary="按岗位类型概况")
async def get_job_type_summary(
    job_type: str,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定岗位类型的绩效概况"""
    if job_type not in ['mechanical', 'test', 'electrical']:
        raise HTTPException(status_code=400, detail="无效的岗位类型")

    service = EngineerPerformanceService(db)

    # 获取周期
    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if not period:
            raise HTTPException(status_code=404, detail="未找到当前考核周期")
        period_id = period.id

    # 获取排名数据
    results, total = service.get_ranking(
        period_id=period_id,
        job_type=job_type,
        limit=100
    )

    if not results:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "job_type": job_type,
                "total": 0,
                "avg_score": 0,
                "level_distribution": {}
            }
        )

    # 统计
    scores = [float(r.total_score or 0) for r in results]
    level_dist = {}
    for r in results:
        level = r.level or 'D'
        level_dist[level] = level_dist.get(level, 0) + 1

    return ResponseModel(
        code=200,
        message="success",
        data={
            "job_type": job_type,
            "period_id": period_id,
            "total": total,
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
            "min_score": min(scores),
            "level_distribution": level_dist
        }
    )
