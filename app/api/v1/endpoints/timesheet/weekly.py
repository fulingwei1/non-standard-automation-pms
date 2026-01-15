# -*- coding: utf-8 -*-
"""
周工时表 - 自动生成
从 timesheet.py 拆分
"""

# -*- coding: utf-8 -*-
"""
工时管理详细 API endpoints
核心功能：周工时表、批量填报、审批流程
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal
from calendar import monthrange

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func, case, extract

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.organization import Department, Employee
from app.models.rd_project import RdProject
from app.models.timesheet import (
    Timesheet, TimesheetBatch, TimesheetSummary,
    OvertimeApplication, TimesheetApprovalLog, TimesheetRule
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.timesheet import (
    TimesheetCreate, TimesheetUpdate, TimesheetResponse, TimesheetListResponse,
    TimesheetBatchCreate, WeekTimesheetResponse, MonthSummaryResponse,
    TimesheetStatisticsResponse
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
    prefix="/timesheet/weekly",
    tags=["weekly"]
)

# 共 1 个路由

# ==================== 周工时表 ====================

@router.get("/week", response_model=WeekTimesheetResponse, status_code=status.HTTP_200_OK)
def get_week_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    week_start: Optional[date] = Query(None, description="周开始日期（默认本周一）"),
    user_id: Optional[int] = Query(None, description="用户ID（默认当前用户）"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取周工时表（按周展示）
    """
    target_user_id = user_id or current_user.id
    
    # 权限检查
    if target_user_id != current_user.id:
        if not hasattr(current_user, 'is_superuser') or not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="无权查看其他用户的工时")
    
    # 计算周开始日期
    if not week_start:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
    
    week_end = week_start + timedelta(days=6)
    
    # 查询该周的工时记录
    timesheets = db.query(Timesheet).filter(
        Timesheet.user_id == target_user_id,
        Timesheet.work_date >= week_start,
        Timesheet.work_date <= week_end
    ).order_by(Timesheet.work_date).all()
    
    # 按日期统计
    by_date = {}
    total_hours = Decimal("0")
    for ts in timesheets:
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal("0")
        by_date[date_str] += ts.hours or Decimal("0")
        total_hours += ts.hours or Decimal("0")
    
    # 按项目统计
    by_project = {}
    for ts in timesheets:
        project_name = "未分配项目"
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()
            project_name = project.project_name if project else "未知项目"
        
        if project_name not in by_project:
            by_project[project_name] = Decimal("0")
        by_project[project_name] += ts.hours or Decimal("0")
    
    # 构建响应
    items = []
    user = db.query(User).filter(User.id == target_user_id).first()
    for ts in timesheets:
        project = None
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()
        
        items.append(TimesheetResponse(
            id=ts.id,
            user_id=ts.user_id,
            user_name=user.real_name or user.username if user else None,
            project_id=ts.project_id,
            rd_project_id=ts.rd_project_id,
            project_name=project.project_name if project else None,
            task_id=ts.task_id,
            task_name=None,
            work_date=ts.work_date,
            work_hours=ts.hours or Decimal("0"),
            work_type=ts.overtime_type or "NORMAL",
            description=ts.work_content,
            status=ts.status or "DRAFT",
            approved_by=ts.approver_id,
            approved_at=ts.approve_time,
            created_at=ts.created_at,
            updated_at=ts.updated_at
        ))
    
    return WeekTimesheetResponse(
        week_start=week_start,
        week_end=week_end,
        total_hours=total_hours,
        by_date=by_date,
        by_project=by_project,
        timesheets=items
    )



