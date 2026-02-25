# -*- coding: utf-8 -*-
"""
用户工时分配端点
"""

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.rd_project import RdProject
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/{user_id}/time-allocation", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_user_time_allocation(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    year: Optional[int] = Query(None, description="年份（不提供则查询全部）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取用户工时分配比例（研发/非研发）"""
    user = get_or_404(db, User, user_id, "用户不存在")

    if user_id != current_user.id:
        if not security.check_permission(current_user, "USER_VIEW"):
            raise HTTPException(status_code=403, detail="无权查看其他用户的工时分配")

    query = db.query(Timesheet).filter(
        Timesheet.user_id == user_id,
        Timesheet.status == 'APPROVED'
    )

    if year:
        query = query.filter(func.extract('year', Timesheet.work_date) == year)

    timesheets = query.all()

    rd_projects = db.query(RdProject).filter(
        RdProject.status.in_(['APPROVED', 'IN_PROGRESS', 'COMPLETED']),
        RdProject.linked_project_id.isnot(None)
    ).all()

    rd_linked_project_ids = {p.linked_project_id for p in rd_projects if p.linked_project_id}

    rd_hours = Decimal(0)
    non_rd_hours = Decimal(0)
    total_hours = Decimal(0)

    rd_projects_detail = {}
    non_rd_projects_detail = {}

    for ts in timesheets:
        hours = Decimal(str(ts.hours or 0))
        total_hours += hours

        is_rd = ts.project_id in rd_linked_project_ids if ts.project_id else False

        if is_rd:
            rd_hours += hours
            rd_project = None
            for rp in rd_projects:
                if rp.linked_project_id == ts.project_id:
                    rd_project = rp
                    break

            project_key = f"RD-{rd_project.id}" if rd_project else f"P-{ts.project_id}"
            if project_key not in rd_projects_detail:
                project = db.query(Project).filter(Project.id == ts.project_id).first()
                rd_projects_detail[project_key] = {
                    "project_id": ts.project_id,
                    "project_name": project.project_name if project else "未知项目",
                    "rd_project_id": rd_project.id if rd_project else None,
                    "rd_project_name": rd_project.project_name if rd_project else None,
                    "total_hours": Decimal(0),
                    "days": 0
                }
            rd_projects_detail[project_key]["total_hours"] += hours
            rd_projects_detail[project_key]["days"] += 1
        else:
            non_rd_hours += hours
            project_key = f"P-{ts.project_id}" if ts.project_id else "未分配"
            if project_key not in non_rd_projects_detail:
                project = db.query(Project).filter(Project.id == ts.project_id).first() if ts.project_id else None
                non_rd_projects_detail[project_key] = {
                    "project_id": ts.project_id,
                    "project_name": project.project_name if project else "未分配项目",
                    "total_hours": Decimal(0),
                    "days": 0
                }
            non_rd_projects_detail[project_key]["total_hours"] += hours
            non_rd_projects_detail[project_key]["days"] += 1

    rd_ratio = float(rd_hours / total_hours * 100) if total_hours > 0 else 0.0
    non_rd_ratio = float(non_rd_hours / total_hours * 100) if total_hours > 0 else 0.0

    for data in rd_projects_detail.values():
        data["total_hours"] = float(data["total_hours"])
    for data in non_rd_projects_detail.values():
        data["total_hours"] = float(data["total_hours"])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "user_id": user_id,
            "user_name": user.real_name or user.username,
            "year": year,
            "total_hours": float(total_hours),
            "rd_hours": float(rd_hours),
            "non_rd_hours": float(non_rd_hours),
            "rd_ratio": rd_ratio,
            "non_rd_ratio": non_rd_ratio,
            "rd_ratio_percent": f"{rd_ratio:.2f}%",
            "non_rd_ratio_percent": f"{non_rd_ratio:.2f}%",
            "rd_projects": list(rd_projects_detail.values()),
            "non_rd_projects": list(non_rd_projects_detail.values()),
        }
    )
