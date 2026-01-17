# -*- coding: utf-8 -*-
"""
仪表板 API端点
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.staff_matching import HrAIMatchingLog, MesProjectStaffingNeed
from app.models.user import User

router = APIRouter()


@router.get("/")
def get_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("staff_matching:read"))
):
    """获取人员匹配仪表板"""
    # 需求统计
    open_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
        MesProjectStaffingNeed.status == 'OPEN'
    ).scalar() or 0

    matching_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
        MesProjectStaffingNeed.status == 'MATCHING'
    ).scalar() or 0

    filled_needs = db.query(func.count(MesProjectStaffingNeed.id)).filter(
        MesProjectStaffingNeed.status == 'FILLED'
    ).scalar() or 0

    # 按优先级统计
    priority_counts = db.query(
        MesProjectStaffingNeed.priority,
        func.count(MesProjectStaffingNeed.id)
    ).filter(
        MesProjectStaffingNeed.status.in_(['OPEN', 'MATCHING'])
    ).group_by(MesProjectStaffingNeed.priority).all()

    needs_by_priority = {p: c for p, c in priority_counts}

    # 匹配统计
    total_requests = db.query(func.count(func.distinct(HrAIMatchingLog.request_id))).scalar() or 0
    total_matched = db.query(func.count(HrAIMatchingLog.id)).scalar() or 0
    accepted = db.query(func.count(HrAIMatchingLog.id)).filter(
        HrAIMatchingLog.is_accepted == True
    ).scalar() or 0
    rejected = db.query(func.count(HrAIMatchingLog.id)).filter(
        HrAIMatchingLog.is_accepted == False
    ).scalar() or 0
    pending = total_matched - accepted - rejected

    avg_score = db.query(func.avg(HrAIMatchingLog.total_score)).filter(
        HrAIMatchingLog.is_accepted == True
    ).scalar()

    success_rate = (accepted / total_matched * 100) if total_matched > 0 else 0

    # 最近匹配
    recent_logs = db.query(HrAIMatchingLog).order_by(
        HrAIMatchingLog.matching_time.desc()
    ).limit(10).all()

    recent_matches = []
    for log in recent_logs:
        recent_matches.append({
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
            'matching_time': log.matching_time,
            'project_name': log.project.name if log.project else None,
            'employee_name': log.candidate.name if log.candidate else None
        })

    # 统计总人数需求
    total_headcount_needed = db.query(func.sum(MesProjectStaffingNeed.headcount)).filter(
        MesProjectStaffingNeed.status.in_(['OPEN', 'MATCHING', 'FILLED'])
    ).scalar() or 0

    # 统计已填充人数
    total_headcount_filled = db.query(func.sum(MesProjectStaffingNeed.filled_headcount)).filter(
        MesProjectStaffingNeed.status.in_(['OPEN', 'MATCHING', 'FILLED'])
    ).scalar() or 0

    return {
        'open_needs': open_needs,
        'matching_needs': matching_needs,
        'filled_needs': filled_needs,
        'total_headcount_needed': int(total_headcount_needed),
        'total_headcount_filled': int(total_headcount_filled),
        'needs_by_priority': needs_by_priority,
        'matching_stats': {
            'total_requests': total_requests,
            'total_candidates_matched': total_matched,
            'accepted_count': accepted,
            'rejected_count': rejected,
            'pending_count': pending,
            'avg_score': round(float(avg_score), 2) if avg_score else None,
            'success_rate': round(success_rate, 2)
        },
        'recent_matches': recent_matches
    }
