# -*- coding: utf-8 -*-
"""
项目工时自定义端点

包含汇总、统计等功能
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/summary", response_model=ResponseModel)
def get_project_timesheet_summary(
    project_id: int = Path(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目工时汇总"""
    check_project_access_or_raise(db, current_user, project_id)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(Timesheet).filter(
        Timesheet.project_id == project_id, Timesheet.status == "APPROVED"
    )
    
    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)
    
    timesheets = query.all()
    
    # 统计汇总
    total_hours = Decimal("0")
    by_user: Dict[str, Dict[str, Any]] = {}
    by_date: Dict[str, Decimal] = {}
    by_work_type: Dict[str, Decimal] = {}
    participants = set()
    
    for ts in timesheets:
        hours = Decimal(str(ts.hours or 0))
        total_hours += hours
        participants.add(ts.user_id)
        
        # 按用户统计
        user = db.query(User).filter(User.id == ts.user_id).first()
        user_name = user.real_name or user.username if user else f"用户{ts.user_id}"
        if user_name not in by_user:
            by_user[user_name] = {
                "user_id": ts.user_id,
                "user_name": user_name,
                "total_hours": Decimal("0"),
                "days": 0,
            }
        by_user[user_name]["total_hours"] += hours
        by_user[user_name]["days"] += 1
        
        # 按日期统计
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal("0")
        by_date[date_str] += hours
        
        # 按工作类型统计
        work_type = ts.overtime_type or "NORMAL"
        if work_type not in by_work_type:
            by_work_type[work_type] = Decimal("0")
        by_work_type[work_type] += hours
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_name": project.project_name,
            "total_hours": float(total_hours),
            "total_participants": len(participants),
            "by_user": [
                {**v, "total_hours": float(v["total_hours"])} for v in by_user.values()
            ],
            "by_date": {k: float(v) for k, v in by_date.items()},
            "by_work_type": {k: float(v) for k, v in by_work_type.items()},
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )


@router.get("/statistics", response_model=ResponseModel)
def get_project_timesheet_statistics(
    project_id: int = Path(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目工时统计分析"""
    check_project_access_or_raise(db, current_user, project_id)
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(Timesheet).filter(
        Timesheet.project_id == project_id, Timesheet.status == "APPROVED"
    )
    
    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)
    
    timesheets = query.all()
    
    # 统计
    total_hours = Decimal("0")
    draft_hours = Decimal("0")
    pending_hours = Decimal("0")
    approved_hours = Decimal("0")
    rejected_hours = Decimal("0")
    
    # 统计各状态的工时
    all_query = db.query(Timesheet).filter(Timesheet.project_id == project_id)
    if start_date:
        all_query = all_query.filter(Timesheet.work_date >= start_date)
    if end_date:
        all_query = all_query.filter(Timesheet.work_date <= end_date)
    
    all_timesheets = all_query.all()
    
    for ts in all_timesheets:
        hours = Decimal(str(ts.hours or 0))
        total_hours += hours
        if ts.status == "DRAFT":
            draft_hours += hours
        elif ts.status == "PENDING":
            pending_hours += hours
        elif ts.status == "APPROVED":
            approved_hours += hours
        elif ts.status == "REJECTED":
            rejected_hours += hours
    
    # 计算平均每日工时
    unique_dates = set(ts.work_date for ts in all_timesheets if ts.work_date)
    avg_daily_hours = (
        float(total_hours) / len(unique_dates) if unique_dates else 0.0
    )
    
    # 计算参与人数
    participants = set(ts.user_id for ts in all_timesheets)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_name": project.project_name,
            "total_hours": float(total_hours),
            "approved_hours": float(approved_hours),
            "pending_hours": float(pending_hours),
            "draft_hours": float(draft_hours),
            "rejected_hours": float(rejected_hours),
            "total_records": len(all_timesheets),
            "total_participants": len(participants),
            "unique_work_days": len(unique_dates),
            "avg_daily_hours": round(avg_daily_hours, 2),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )
