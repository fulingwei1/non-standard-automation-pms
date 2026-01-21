# -*- coding: utf-8 -*-
"""
跨部门协作评价端点
"""

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.performance import PerformancePeriod
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.engineer_performance import CollaborationRatingCreate
from app.services.collaboration_service import CollaborationService

router = APIRouter(prefix="/collaboration", tags=["跨部门协作"])


@router.get("/matrix", summary="获取协作评价矩阵")
async def get_collaboration_matrix(
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取跨部门协作评价矩阵"""
    service = CollaborationService(db)

    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if period:
            period_id = period.id

    if not period_id:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    matrix = service.get_collaboration_matrix(period_id)

    return ResponseModel(
        code=200,
        message="success",
        data=matrix
    )


@router.post("", summary="提交跨部门评价")
async def create_collaboration_rating(
    data: CollaborationRatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交跨部门协作评价"""
    service = CollaborationService(db)

    try:
        rating = service.create_rating(data, current_user.id)
        return ResponseModel(
            code=200,
            message="评价提交成功",
            data={"id": rating.id, "total_score": float(rating.total_score)}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/received/{user_id}", summary="获取收到的评价")
async def get_ratings_received(
    user_id: int,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定用户收到的评价"""
    service = CollaborationService(db)

    ratings, total = service.get_ratings_received(
        user_id=user_id,
        period_id=period_id,
        limit=limit,
        offset=offset
    )

    items = []
    for r in ratings:
        rater = db.query(User).filter(User.id == r.rater_id).first()
        items.append({
            "id": r.id,
            "rater_id": r.rater_id,
            "rater_name": rater.name if rater else None,
            "rater_job_type": r.rater_job_type,
            "communication_score": r.communication_score,
            "response_score": r.response_score,
            "delivery_score": r.delivery_score,
            "interface_score": r.interface_score,
            "total_score": float(r.total_score) if r.total_score else None,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": total,
            "items": items
        }
    )


@router.get("/given/{user_id}", summary="获取给出的评价")
async def get_ratings_given(
    user_id: int,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定用户给出的评价"""
    service = CollaborationService(db)

    ratings, total = service.get_ratings_given(
        user_id=user_id,
        period_id=period_id,
        limit=limit,
        offset=offset
    )

    items = []
    for r in ratings:
        ratee = db.query(User).filter(User.id == r.ratee_id).first()
        items.append({
            "id": r.id,
            "ratee_id": r.ratee_id,
            "ratee_name": ratee.name if ratee else None,
            "ratee_job_type": r.ratee_job_type,
            "total_score": float(r.total_score) if r.total_score else None,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": total,
            "items": items
        }
    )


@router.get("/pending", summary="获取待评价列表")
async def get_pending_ratings(
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户待评价的工程师列表"""
    service = CollaborationService(db)

    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if period:
            period_id = period.id

    if not period_id:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    pending = service.get_pending_ratings(current_user.id, period_id)

    return ResponseModel(
        code=200,
        message="success",
        data=pending
    )


@router.get("/stats/{user_id}", summary="获取协作统计")
async def get_collaboration_stats(
    user_id: int,
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户的协作统计"""
    service = CollaborationService(db)
    stats = service.get_collaboration_stats(user_id, period_id)

    return ResponseModel(
        code=200,
        message="success",
        data=stats
    )


@router.post("/auto-select/{engineer_id}", summary="自动抽取合作人员")
async def auto_select_collaborators(
    engineer_id: int,
    period_id: int,
    target_count: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自动匿名抽取5个合作人员进行评价"""
    from app.services.collaboration_rating import CollaborationRatingService

    service = CollaborationRatingService(db)

    try:
        collaborators = service.auto_select_collaborators(
            engineer_id, period_id, target_count
        )
        invitations = service.create_rating_invitations(
            engineer_id, period_id, collaborators
        )

        return ResponseModel(
            code=200,
            message="自动抽取成功",
            data={
                'collaborator_count': len(collaborators),
                'collaborator_ids': collaborators,
                'invitations': invitations
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/submit-rating", summary="提交评价（新接口）")
async def submit_rating(
    rating_id: int = Body(..., description="评价记录ID"),
    communication_score: int = Body(..., ge=1, le=5, description="沟通配合得分（1-5）"),
    response_score: int = Body(..., ge=1, le=5, description="响应速度得分（1-5）"),
    delivery_score: int = Body(..., ge=1, le=5, description="交付质量得分（1-5）"),
    interface_score: int = Body(..., ge=1, le=5, description="接口规范得分（1-5）"),
    comment: Optional[str] = Body(None, description="评价备注"),
    project_id: Optional[int] = Body(None, description="关联项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交跨部门协作评价"""
    from app.services.collaboration_rating import CollaborationRatingService

    service = CollaborationRatingService(db)

    try:
        rating = service.submit_rating(
            rating_id=rating_id,
            rater_id=current_user.id,
            communication_score=communication_score,
            response_score=response_score,
            delivery_score=delivery_score,
            interface_score=interface_score,
            comment=comment,
            project_id=project_id
        )

        return ResponseModel(
            code=200,
            message="评价提交成功",
            data={
                'rating_id': rating.id,
                'total_score': float(rating.total_score or 0)
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pending-ratings", summary="获取待评价列表（新接口）")
async def get_pending_ratings_new(
    period_id: Optional[int] = Query(None, description="考核周期ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户待评价的列表"""
    from app.services.collaboration_rating import CollaborationRatingService

    service = CollaborationRatingService(db)

    if not period_id:
        period = db.query(PerformancePeriod).filter(
            PerformancePeriod.is_active == True
        ).first()
        if period:
            period_id = period.id

    if not period_id:
        raise HTTPException(status_code=404, detail="未找到考核周期")

    pending = service.get_pending_ratings(current_user.id, period_id)

    return ResponseModel(
        code=200,
        message="获取待评价列表成功",
        data=[
            {
                'rating_id': r.id,
                'ratee_id': r.ratee_id,
                'ratee_name': r.ratee.name if r.ratee else None,
                'period_id': r.period_id
            }
            for r in pending
        ]
    )


@router.get("/statistics/{period_id}", summary="获取评价统计信息")
async def get_rating_statistics(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定周期的评价统计信息"""
    from app.services.collaboration_rating import CollaborationRatingService

    service = CollaborationRatingService(db)

    try:
        stats = service.get_rating_statistics(period_id)
        return ResponseModel(
            code=200,
            message="获取评价统计成功",
            data=stats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend/{engineer_id}", summary="获取协作趋势")
async def get_collaboration_trend(
    engineer_id: int,
    periods: int = Query(6, ge=1, le=12, description="历史周期数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取工程师的跨部门协作趋势"""
    from app.services.collaboration_rating import CollaborationRatingService

    service = CollaborationRatingService(db)

    try:
        trend = service.get_collaboration_trend(engineer_id, periods)
        return ResponseModel(
            code=200,
            message="获取协作趋势成功",
            data=trend
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality-analysis/{period_id}", summary="分析评价质量")
async def analyze_rating_quality(
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分析指定周期的评价质量"""
    from app.services.collaboration_rating import CollaborationRatingService

    service = CollaborationRatingService(db)

    try:
        analysis = service.analyze_rating_quality(period_id)
        return ResponseModel(
            code=200,
            message="评价质量分析成功",
            data=analysis
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-complete/{period_id}", summary="自动完成缺失评价")
async def auto_complete_missing_ratings(
    period_id: int,
    default_score: float = 75.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自动完成缺失的评价（使用默认值）"""
    from decimal import Decimal

    from app.services.collaboration_rating import CollaborationRatingService

    service = CollaborationRatingService(db)

    try:
        count = service.auto_complete_missing_ratings(
            period_id, Decimal(str(default_score))
        )
        return ResponseModel(
            code=200,
            message=f"自动完成{count}个缺失评价",
            data={'completed_count': count}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
