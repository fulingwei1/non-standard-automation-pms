# -*- coding: utf-8 -*-
"""
AI匹配 API端点
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.staff_matching import HrAIMatchingLog
from app.models.user import User
from app.schemas import staff_matching as schemas
from app.services.staff_matching import StaffMatchingService

router = APIRouter()


@router.post("/execute/{staffing_need_id}")
def execute_matching(
    staffing_need_id: int,
    top_n: int = Query(10, ge=1, le=50, description="返回候选人数量"),
    include_overloaded: bool = Query(False, description="是否包含超负荷员工"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """执行AI匹配"""
    try:
        result = StaffMatchingService.match_candidates(
            db=db,
            staffing_need_id=staffing_need_id,
            top_n=top_n,
            include_overloaded=include_overloaded
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"匹配失败: {str(e)}")


@router.get("/results/{staffing_need_id}", response_model=List[schemas.MatchingLogResponse])
def get_matching_results(
    staffing_need_id: int,
    request_id: Optional[str] = Query(None, description="匹配请求ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取匹配结果"""
    query = db.query(HrAIMatchingLog).filter(
        HrAIMatchingLog.staffing_need_id == staffing_need_id
    )

    if request_id:
        query = query.filter(HrAIMatchingLog.request_id == request_id)
    else:
        # 获取最新一次匹配
        latest_request = db.query(HrAIMatchingLog.request_id).filter(
            HrAIMatchingLog.staffing_need_id == staffing_need_id
        ).order_by(HrAIMatchingLog.matching_time.desc()).first()

        if latest_request:
            query = query.filter(HrAIMatchingLog.request_id == latest_request[0])

    logs = query.order_by(HrAIMatchingLog.rank).all()

    result = []
    for log in logs:
        result.append({
            'id': log.id,
            'request_id': log.request_id,
            'project_id': log.project_id,
            'staffing_need_id': log.staffing_need_id,
            'candidate_employee_id': log.candidate_employee_id,
            'total_score': log.total_score,
            'dimension_scores': log.dimension_scores,
            'rank': log.rank,
            'recommendation_type': log.recommendation_type,
            'is_accepted': log.is_accepted,
            'accept_time': log.accept_time,
            'acceptor_id': log.acceptor_id,
            'reject_reason': log.reject_reason,
            'matching_time': log.matching_time,
            'project_name': log.project.name if log.project else None,
            'employee_name': log.candidate.name if log.candidate else None,
            'acceptor_name': log.acceptor.real_name if log.acceptor else None
        })

    return result


@router.post("/accept")
def accept_candidate(
    accept_data: schemas.MatchingAcceptRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """采纳候选人"""
    success = StaffMatchingService.accept_candidate(
        db=db,
        matching_log_id=accept_data.matching_log_id,
        acceptor_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    return {"message": "候选人已采纳"}


@router.post("/reject")
def reject_candidate(
    reject_data: schemas.MatchingRejectRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """拒绝候选人"""
    success = StaffMatchingService.reject_candidate(
        db=db,
        matching_log_id=reject_data.matching_log_id,
        reject_reason=reject_data.reject_reason
    )

    if not success:
        raise HTTPException(status_code=404, detail="匹配记录不存在")

    return {"message": "已拒绝候选人"}


@router.get("/history", response_model=List[schemas.MatchingLogResponse])
def get_matching_history(
    project_id: Optional[int] = Query(None, description="项目ID"),
    staffing_need_id: Optional[int] = Query(None, description="需求ID"),
    employee_id: Optional[int] = Query(None, description="员工ID"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取匹配历史"""
    logs = StaffMatchingService.get_matching_history(
        db=db,
        project_id=project_id,
        staffing_need_id=staffing_need_id,
        employee_id=employee_id,
        limit=limit
    )

    result = []
    for log in logs:
        result.append({
            'id': log.id,
            'request_id': log.request_id,
            'project_id': log.project_id,
            'staffing_need_id': log.staffing_need_id,
            'candidate_employee_id': log.candidate_employee_id,
            'total_score': log.total_score,
            'dimension_scores': log.dimension_scores,
            'rank': log.rank,
            'recommendation_type': log.recommendation_type,
            'is_accepted': log.is_accepted,
            'accept_time': log.accept_time,
            'acceptor_id': log.acceptor_id,
            'reject_reason': log.reject_reason,
            'matching_time': log.matching_time,
            'project_name': log.project.name if log.project else None,
            'employee_name': log.candidate.name if log.candidate else None,
            'acceptor_name': log.acceptor.real_name if log.acceptor else None
        })

    return result
