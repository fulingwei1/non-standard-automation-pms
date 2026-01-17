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
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, desc, extract, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.organization import Department, Employee
from app.models.project import Project
from app.models.rd_project import RdProject
from app.models.timesheet import (
    OvertimeApplication,
    Timesheet,
    TimesheetApprovalLog,
    TimesheetBatch,
    TimesheetRule,
    TimesheetSummary,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.timesheet import (
    MonthSummaryResponse,
    TimesheetBatchCreate,
    TimesheetCreate,
    TimesheetListResponse,
    TimesheetResponse,
    TimesheetStatisticsResponse,
    TimesheetUpdate,
    WeekTimesheetResponse,
)

router = APIRouter()


def check_timesheet_approval_permission(
    db: Session,
    timesheet: Timesheet,
    current_user: User
) -> bool:
    """
    检查用户是否有权审批指定的工时记录

    审批权限规则：
    1. 超级管理员可以审批所有工时
    2. 项目经理可以审批其项目的工时
    3. 研发项目负责人可以审批其研发项目的工时
    4. 部门经理可以审批其部门成员的工时

    Args:
        db: 数据库会话
        timesheet: 工时记录
        current_user: 当前用户

    Returns:
        bool: 是否有审批权限
    """
    # 1. 超级管理员可以审批所有工时
    if hasattr(current_user, 'is_superuser') and current_user.is_superuser:
        return True

    # 2. 检查是否是项目经理（非标项目）
    if timesheet.project_id:
        project = db.query(Project).filter(Project.id == timesheet.project_id).first()
        if project and project.pm_id == current_user.id:
            return True

    # 3. 检查是否是研发项目负责人
    if timesheet.rd_project_id:
        rd_project = db.query(RdProject).filter(RdProject.id == timesheet.rd_project_id).first()
        if rd_project and rd_project.project_manager_id == current_user.id:
            return True

    # 4. 检查是否是部门经理
    if timesheet.department_id:
        department = db.query(Department).filter(Department.id == timesheet.department_id).first()
        if department and department.manager_id:
            # 需要通过 employee_id 关联到 user
            # 查找当前用户对应的 employee
            if hasattr(current_user, 'employee_id') and current_user.employee_id:
                if department.manager_id == current_user.employee_id:
                    return True

    # 5. 如果工时记录有提交人的部门信息，检查当前用户是否是该部门经理
    if timesheet.user_id:
        # 获取工时提交人
        timesheet_user = db.query(User).filter(User.id == timesheet.user_id).first()
        if timesheet_user and hasattr(timesheet_user, 'employee_id') and timesheet_user.employee_id:
            # 获取提交人的员工信息
            employee = db.query(Employee).filter(Employee.id == timesheet_user.employee_id).first()
            if employee and employee.department:
                # 查找该部门
                dept = db.query(Department).filter(Department.dept_name == employee.department).first()
                if dept and dept.manager_id:
                    # 检查当前用户是否是该部门经理
                    if hasattr(current_user, 'employee_id') and current_user.employee_id == dept.manager_id:
                        return True

    return False



from fastapi import APIRouter

router = APIRouter(
    prefix="/timesheet/monthly",
    tags=["monthly"]
)

# 共 1 个路由

# ==================== 月度汇总 ====================

@router.get("/month-summary", response_model=MonthSummaryResponse, status_code=status.HTTP_200_OK)
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
    target_user_id = user_id or current_user.id

    if target_user_id != current_user.id:
        if not hasattr(current_user, 'is_superuser') or not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="无权查看其他用户的工时")

    # 计算月份的开始和结束日期
    _, last_day = monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)

    # 查询该月的工时记录
    timesheets = db.query(Timesheet).filter(
        Timesheet.user_id == target_user_id,
        Timesheet.work_date >= month_start,
        Timesheet.work_date <= month_end
    ).all()

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
        by_date=by_date
    )



