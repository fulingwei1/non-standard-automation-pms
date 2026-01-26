# -*- coding: utf-8 -*-
"""
工时统计分析 - 自动生成
从 timesheet.py 拆分
"""

# -*- coding: utf-8 -*-
"""
工时管理详细 API endpoints
核心功能：周工时表、批量填报、审批流程
"""

from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department
from app.models.project import Project
from app.models.timesheet import (
    Timesheet,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.timesheet import (
    TimesheetStatisticsResponse,
)

router = APIRouter()


from fastapi import APIRouter

router = APIRouter(prefix="/timesheet/statistics", tags=["statistics"])

# 共 3 个路由

# ==================== 工时统计分析 ====================


@router.get(
    "/statistics",
    response_model=TimesheetStatisticsResponse,
    status_code=status.HTTP_200_OK,
)
def get_timesheet_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    工时统计分析（多维统计）
    """
    from app.core.permissions.timesheet import apply_timesheet_access_filter

    query = db.query(Timesheet).filter(Timesheet.status == "APPROVED")
    query = apply_timesheet_access_filter(query, db, current_user)

    if user_id:
        query = query.filter(Timesheet.user_id == user_id)

    if project_id:
        query = query.filter(Timesheet.project_id == project_id)
    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)

    timesheets = query.all()

    total_hours = Decimal("0")
    billable_hours = Decimal("0")
    by_user = {}
    by_project = {}
    by_date = {}
    by_work_type = {}

    for ts in timesheets:
        hours = ts.hours or Decimal("0")
        total_hours += hours

        if True:  # 所有已审批的工时都是可计费的
            billable_hours += hours

        # 按用户统计
        user = db.query(User).filter(User.id == ts.user_id).first()
        user_name = user.real_name or user.username if user else f"用户{ts.user_id}"
        if user_name not in by_user:
            by_user[user_name] = Decimal("0")
        by_user[user_name] += hours

        # 按项目统计
        project_name = "未分配项目"
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()
            project_name = project.project_name if project else "未知项目"

        if project_name not in by_project:
            by_project[project_name] = Decimal("0")
        by_project[project_name] += hours

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

    return TimesheetStatisticsResponse(
        total_hours=total_hours,
        billable_hours=billable_hours,
        by_user=by_user,
        by_project=by_project,
        by_date=by_date,
        by_work_type=by_work_type,
    )


@router.get("/my-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_my_timesheet_summary(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    我的工时汇总（个人统计）
    """
    query = db.query(Timesheet).filter(
        Timesheet.user_id == current_user.id, Timesheet.status == "APPROVED"
    )

    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)

    timesheets = query.all()

    # 统计汇总
    total_hours = Decimal(0)
    billable_hours = Decimal(0)
    by_project = {}
    by_date = {}
    by_work_type = {}

    for ts in timesheets:
        hours = Decimal(str(ts.hours or 0))
        total_hours += hours

        if True:  # 所有已审批的工时都是可计费的
            billable_hours += hours

        # 按项目统计
        project_name = "未分配项目"
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()
            project_name = project.project_name if project else "未知项目"

        if project_name not in by_project:
            by_project[project_name] = {
                "project_id": ts.project_id,
                "project_name": project_name,
                "total_hours": Decimal(0),
                "days": 0,
            }
        by_project[project_name]["total_hours"] += hours
        by_project[project_name]["days"] += 1

        # 按日期统计
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal(0)
        by_date[date_str] += hours

        # 按工作类型统计
        work_type = ts.overtime_type or "NORMAL"
        if work_type not in by_work_type:
            by_work_type[work_type] = Decimal(0)
        by_work_type[work_type] += hours

    return ResponseModel(
        code=200,
        message="success",
        data={
            "user_id": current_user.id,
            "user_name": current_user.real_name or current_user.username,
            "total_hours": float(total_hours),
            "billable_hours": float(billable_hours),
            "non_billable_hours": float(total_hours - billable_hours),
            "by_project": {
                k: {
                    "project_id": v["project_id"],
                    "project_name": v["project_name"],
                    "total_hours": float(v["total_hours"]),
                    "days": v["days"],
                }
                for k, v in by_project.items()
            },
            "by_date": {k: float(v) for k, v in by_date.items()},
            "by_work_type": {k: float(v) for k, v in by_work_type.items()},
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )


@router.get(
    "/departments/{dept_id}/timesheet-summary",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_department_timesheet_summary(
    *,
    db: Session = Depends(deps.get_db),
    dept_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    部门工时汇总
    """
    # 验证部门是否存在
    department = db.query(Department).filter(Department.id == dept_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")

    # 获取部门成员
    dept_users = db.query(User).filter(User.department_id == dept_id).all()
    user_ids = [u.id for u in dept_users]

    if not user_ids:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "department_id": dept_id,
                "department_name": department.dept_name,
                "total_hours": 0,
                "total_participants": 0,
                "by_user": [],
                "by_project": {},
                "by_date": {},
            },
        )

    # 查询部门成员的工时记录
    query = db.query(Timesheet).filter(
        Timesheet.user_id.in_(user_ids), Timesheet.status == "APPROVED"
    )

    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)

    timesheets = query.all()

    # 统计汇总
    total_hours = Decimal(0)
    by_user = {}
    by_project = {}
    by_date = {}
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
                "total_hours": Decimal(0),
                "days": 0,
            }
        by_user[user_name]["total_hours"] += hours
        by_user[user_name]["days"] += 1

        # 按项目统计
        project_name = "未分配项目"
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()
            project_name = project.project_name if project else "未知项目"

        if project_name not in by_project:
            by_project[project_name] = {
                "project_id": ts.project_id,
                "project_name": project_name,
                "total_hours": Decimal(0),
                "participants": set(),
            }
        by_project[project_name]["total_hours"] += hours
        by_project[project_name]["participants"].add(ts.user_id)

        # 按日期统计
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal(0)
        by_date[date_str] += hours

    # 转换participants为数量
    for proj_name, proj_data in by_project.items():
        proj_data["participant_count"] = len(proj_data["participants"])
        del proj_data["participants"]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "department_id": dept_id,
            "department_name": department.dept_name,
            "total_hours": float(total_hours),
            "total_participants": len(participants),
            "by_user": [
                {**v, "total_hours": float(v["total_hours"])} for v in by_user.values()
            ],
            "by_project": {
                k: {**v, "total_hours": float(v["total_hours"])}
                for k, v in by_project.items()
            },
            "by_date": {k: float(v) for k, v in by_date.items()},
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        },
    )
