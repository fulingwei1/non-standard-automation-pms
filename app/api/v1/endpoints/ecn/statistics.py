# -*- coding: utf-8 -*-
"""
ECN追溯/统计 API endpoints

包含：日志列表、项目ECN列表、统计分析
"""

from datetime import date, datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.ecn import Ecn, EcnLog
from app.models.project import Project
from app.models.user import User
from app.schemas.ecn import EcnListResponse

from .utils import build_ecn_list_response, get_user_display_name

router = APIRouter()


@router.get("/ecns/{ecn_id}/logs", response_model=List[dict], status_code=status.HTTP_200_OK)
def read_ecn_logs(
    ecn_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取ECN日志列表
    """
    ecn = db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    logs = db.query(EcnLog).filter(EcnLog.ecn_id == ecn_id).order_by(desc(EcnLog.created_at)).all()

    items = []
    for log in logs:
        created_by_name = get_user_display_name(db, log.created_by)

        items.append({
            "id": log.id,
            "ecn_id": log.ecn_id,
            "log_type": log.log_type,
            "log_action": log.log_action,
            "old_status": log.old_status,
            "new_status": log.new_status,
            "log_content": log.log_content,
            "created_by": log.created_by,
            "created_by_name": created_by_name,
            "created_at": log.created_at
        })

    return items


@router.get("/projects/{project_id}/ecns", response_model=List[EcnListResponse], status_code=status.HTTP_200_OK)
def read_project_ecns(
    project_id: int,
    db: Session = Depends(deps.get_db),
    ecn_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目ECN列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(Ecn).filter(Ecn.project_id == project_id)

    if ecn_status:
        query = query.filter(Ecn.status == ecn_status)

    ecns = query.order_by(desc(Ecn.created_at)).all()

    items = []
    for ecn in ecns:
        applicant_name = get_user_display_name(db, ecn.applicant_id)

        items.append(EcnListResponse(
            id=ecn.id,
            ecn_no=ecn.ecn_no,
            ecn_title=ecn.ecn_title,
            ecn_type=ecn.ecn_type,
            project_id=ecn.project_id,
            project_name=project.project_name,
            status=ecn.status,
            priority=ecn.priority,
            applicant_name=applicant_name,
            applied_at=ecn.applied_at,
            created_at=ecn.created_at
        ))

    return items


@router.get("/ecns/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_ecn_statistics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    ECN统计分析
    统计ECN的数量、状态分布、类型分布、成本影响等
    """
    query = db.query(Ecn)

    if project_id:
        query = query.filter(Ecn.project_id == project_id)
    if start_date:
        query = query.filter(Ecn.applied_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Ecn.applied_at <= datetime.combine(end_date, datetime.max.time()))

    ecns = query.all()

    # 总数统计
    total_count = len(ecns)

    # 按状态统计
    by_status = {}
    for ecn in ecns:
        status_key = ecn.status or "UNKNOWN"
        if status_key not in by_status:
            by_status[status_key] = {"status": status_key, "count": 0, "total_cost_impact": 0.0}
        by_status[status_key]["count"] += 1
        if ecn.cost_impact:
            by_status[status_key]["total_cost_impact"] += float(ecn.cost_impact)

    # 按类型统计
    by_type = {}
    for ecn in ecns:
        type_key = ecn.ecn_type or "UNKNOWN"
        if type_key not in by_type:
            by_type[type_key] = {"type": type_key, "count": 0, "total_cost_impact": 0.0}
        by_type[type_key]["count"] += 1
        if ecn.cost_impact:
            by_type[type_key]["total_cost_impact"] += float(ecn.cost_impact)

    # 按优先级统计
    by_priority = {}
    for ecn in ecns:
        priority_key = ecn.priority or "UNKNOWN"
        if priority_key not in by_priority:
            by_priority[priority_key] = {"priority": priority_key, "count": 0}
        by_priority[priority_key]["count"] += 1

    # 成本影响统计
    total_cost_impact = sum(float(ecn.cost_impact or 0) for ecn in ecns)
    avg_cost_impact = total_cost_impact / total_count if total_count > 0 else 0.0

    # 进度影响统计
    total_schedule_impact = sum(ecn.schedule_impact_days or 0 for ecn in ecns)
    avg_schedule_impact = total_schedule_impact / total_count if total_count > 0 else 0.0

    # 按项目统计（如果未指定项目）
    by_project = {}
    if not project_id:
        for ecn in ecns:
            if ecn.project_id:
                project = db.query(Project).filter(Project.id == ecn.project_id).first()
                project_name = project.project_name if project else f"项目{ecn.project_id}"
                if ecn.project_id not in by_project:
                    by_project[ecn.project_id] = {
                        "project_id": ecn.project_id,
                        "project_name": project_name,
                        "count": 0,
                        "total_cost_impact": 0.0
                    }
                by_project[ecn.project_id]["count"] += 1
                if ecn.cost_impact:
                    by_project[ecn.project_id]["total_cost_impact"] += float(ecn.cost_impact)

    return {
        "total_count": total_count,
        "total_cost_impact": round(total_cost_impact, 2),
        "avg_cost_impact": round(avg_cost_impact, 2),
        "total_schedule_impact": total_schedule_impact,
        "avg_schedule_impact": round(avg_schedule_impact, 2),
        "by_status": list(by_status.values()),
        "by_type": list(by_type.values()),
        "by_priority": list(by_priority.values()),
        "by_project": list(by_project.values()) if by_project else None,
    }
