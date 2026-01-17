# -*- coding: utf-8 -*-
"""
个人绩效端点
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.performance import PerformancePeriod, PerformanceResult
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.engineer_performance import (
    EngineerProfileCreate,
    EngineerProfileResponse,
    EngineerProfileUpdate,
)
from app.services.engineer_performance.engineer_performance_service import (
    EngineerPerformanceService,
)

router = APIRouter(prefix="/engineer", tags=["个人绩效"])


@router.get("/profile", summary="获取当前用户工程师档案")
async def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前登录用户的工程师档案"""
    service = EngineerPerformanceService(db)
    profile = service.get_engineer_profile(current_user.id)

    if not profile:
        raise HTTPException(status_code=404, detail="工程师档案不存在")

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": profile.id,
            "user_id": profile.user_id,
            "job_type": profile.job_type,
            "job_level": profile.job_level,
            "skills": profile.skills,
            "certifications": profile.certifications,
            "job_start_date": profile.job_start_date.isoformat() if profile.job_start_date else None,
            "level_start_date": profile.level_start_date.isoformat() if profile.level_start_date else None
        }
    )


@router.post("/profile", summary="创建工程师档案")
async def create_profile(
    data: EngineerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建工程师档案（管理员操作）"""
    service = EngineerPerformanceService(db)

    # 检查是否已存在
    existing = service.get_engineer_profile(data.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="该用户的工程师档案已存在")

    profile = service.create_engineer_profile(data)

    return ResponseModel(
        code=200,
        message="创建成功",
        data={"id": profile.id}
    )


@router.put("/profile/{user_id}", summary="更新工程师档案")
async def update_profile(
    user_id: int,
    data: EngineerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新工程师档案"""
    service = EngineerPerformanceService(db)
    profile = service.update_engineer_profile(user_id, data)

    if not profile:
        raise HTTPException(status_code=404, detail="工程师档案不存在")

    return ResponseModel(
        code=200,
        message="更新成功",
        data={"id": profile.id}
    )


@router.get("/{user_id}", summary="获取工程师绩效详情")
async def get_engineer_performance(
    user_id: int,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定工程师的绩效详情"""
    service = EngineerPerformanceService(db)

    # 获取工程师档案
    profile = service.get_engineer_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="工程师档案不存在")

    # 获取周期
    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if period:
            period_id = period.id

    # 获取绩效结果
    result = db.query(PerformanceResult).filter(
        PerformanceResult.user_id == user_id,
        PerformanceResult.period_id == period_id
    ).first()

    user = db.query(User).filter(User.id == user_id).first()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "user_id": user_id,
            "user_name": user.name if user else None,
            "job_type": profile.job_type,
            "job_level": profile.job_level,
            "period_id": period_id,
            "total_score": float(result.total_score) if result and result.total_score else None,
            "level": result.level if result else None,
            "dimension_scores": {
                "technical": float(result.workload_score) if result and result.workload_score else None,
                "execution": float(result.task_score) if result and result.task_score else None,
                "cost_quality": float(result.quality_score) if result and result.quality_score else None,
                "knowledge": float(result.growth_score) if result and result.growth_score else None,
                "collaboration": float(result.collaboration_score) if result and result.collaboration_score else None,
            },
            "dept_rank": result.dept_rank if result else None,
            "company_rank": result.company_rank if result else None
        }
    )


@router.get("/{user_id}/trend", summary="获取绩效趋势")
async def get_engineer_trend(
    user_id: int,
    periods: int = Query(6, ge=1, le=12, description="历史周期数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师历史绩效趋势"""
    service = EngineerPerformanceService(db)
    trends = service.get_engineer_trend(user_id, periods)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "user_id": user_id,
            "trends": trends
        }
    )


@router.get("/{user_id}/comparison", summary="获取同岗位对比")
async def get_engineer_comparison(
    user_id: int,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师与同岗位/同级别的对比"""
    service = EngineerPerformanceService(db)

    # 获取工程师档案
    profile = service.get_engineer_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="工程师档案不存在")

    # 获取周期
    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if period:
            period_id = period.id

    # 获取个人绩效
    result = db.query(PerformanceResult).filter(
        PerformanceResult.user_id == user_id,
        PerformanceResult.period_id == period_id
    ).first()

    # 获取同岗位平均
    job_type_results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period_id,
        PerformanceResult.job_type == profile.job_type
    ).all()

    job_type_avg = 0
    if job_type_results:
        job_type_avg = sum(float(r.total_score or 0) for r in job_type_results) / len(job_type_results)

    # 获取同级别平均
    level_results = db.query(PerformanceResult).filter(
        PerformanceResult.period_id == period_id,
        PerformanceResult.job_level == profile.job_level
    ).all()

    level_avg = 0
    if level_results:
        level_avg = sum(float(r.total_score or 0) for r in level_results) / len(level_results)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "user_id": user_id,
            "job_type": profile.job_type,
            "job_level": profile.job_level,
            "my_score": float(result.total_score) if result and result.total_score else None,
            "job_type_avg": round(job_type_avg, 2),
            "job_type_count": len(job_type_results),
            "level_avg": round(level_avg, 2),
            "level_count": len(level_results)
        }
    )


@router.get("", summary="获取工程师列表")
async def list_engineers(
    job_type: Optional[str] = Query(None, description="岗位类型"),
    job_level: Optional[str] = Query(None, description="职级"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师列表"""
    service = EngineerPerformanceService(db)

    profiles, total = service.list_engineers(
        job_type=job_type,
        job_level=job_level,
        department_id=department_id,
        limit=limit,
        offset=offset
    )

    items = []
    for p in profiles:
        user = db.query(User).filter(User.id == p.user_id).first()
        items.append({
            "id": p.id,
            "user_id": p.user_id,
            "user_name": user.name if user else None,
            "job_type": p.job_type,
            "job_level": p.job_level,
            "skills": p.skills
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": total,
            "items": items
        }
    )
