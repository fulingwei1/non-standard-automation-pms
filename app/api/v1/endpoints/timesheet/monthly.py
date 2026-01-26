# -*- coding: utf-8 -*-
"""
月度汇总 - 自动生成
从 timesheet.py 拆分
"""

# -*- coding: utf-8 -*-
"""
工时管理详细 API endpoints
核心功能：周工时表、批量填报、审批流程
"""

from calendar import monthrange
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.timesheet import (
    Timesheet,
)
from app.models.user import User
from app.schemas.timesheet import (
    MonthSummaryResponse,
)

router = APIRouter()


from fastapi import APIRouter

router = APIRouter(prefix="/timesheet/monthly", tags=["monthly"])

# 共 1 个路由

# ==================== 月度汇总 ====================


@router.get(
    "/month-summary",
    response_model=MonthSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def get_month_summary(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    user_id: Optional[int] = Query(None, description="用户ID（默认当前用户）"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取月度汇总
    """
    from app.core.permissions.timesheet import get_user_manageable_dimensions

    # 获取目标用户ID
    target_user_id = user_id or current_user.id

    # 权限检查
    if target_user_id != current_user.id:
        dims = get_user_manageable_dimensions(db, current_user)
        if not dims["is_admin"] and target_user_id not in dims["subordinate_user_ids"]:
            # 检查是否属于我管理的部门
            target_user = db.query(User).filter(User.id == target_user_id).first()
            if (
                not target_user
                or target_user.department_id not in dims["department_ids"]
            ):
                raise HTTPException(
                    status_code=403, detail="无权查看其他用户的工时汇总数据"
                )

    # 计算月份的开始和结束日期
    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    # 查询该月的工时记录
    timesheets = (
        db.query(Timesheet)
        .filter(
            Timesheet.user_id == target_user_id,
            Timesheet.work_date >= month_start,
            Timesheet.work_date <= month_end,
        )
        .all()
    )

    total_hours = Decimal("0")
    billable_hours = Decimal("0")
    non_billable_hours = Decimal("0")
    by_project = {}
    by_work_type = {}
    by_date = {}

    for ts in timesheets:
        hours = ts.hours or Decimal("0")
        total_hours += hours

        if True:  # 所有已审批的工时都是可计费的
            billable_hours += hours
        else:
            non_billable_hours += hours

        # 按项目统计
        project_name = "未分配项目"
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()
            project_name = project.project_name if project else "未知项目"

        if project_name not in by_project:
            by_project[project_name] = Decimal("0")
        by_project[project_name] += hours

        # 按工作类型统计
        work_type = ts.overtime_type or "NORMAL"
        if work_type not in by_work_type:
            by_work_type[work_type] = Decimal("0")
        by_work_type[work_type] += hours

        # 按日期统计
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal("0")
        by_date[date_str] += hours

    return MonthSummaryResponse(
        year=year,
        month=month,
        total_hours=total_hours,
        billable_hours=billable_hours,
        non_billable_hours=non_billable_hours,
        by_project=by_project,
        by_work_type=by_work_type,
        by_date=by_date,
    )
