# -*- coding: utf-8 -*-
"""
待审核列表 - 自动生成
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
    prefix="/timesheet/pending",
    tags=["pending"]
)

# 共 1 个路由

# ==================== 待审核列表 ====================

@router.get("/pending-approval", response_model=TimesheetListResponse, status_code=status.HTTP_200_OK)
def get_pending_approval_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    待审核列表（审核人视角）
    只返回当前用户有权审批的工时记录
    """
    # 过滤出用户有权限审批的工时记录
    # 项目经理只能看到本项目的工时，部门经理只能看到本部门的工时
    query = db.query(Timesheet).filter(Timesheet.status == "PENDING")

    # 如果不是超级用户，需要根据角色过滤
    if not current_user.is_superuser:
        # 检查用户是否是项目经理
        from app.models.project import Project
        user_projects = db.query(Project).filter(Project.pm_id == current_user.id).all()
        project_ids = [p.id for p in user_projects]

        # 检查用户是否是部门经理
        is_dept_manager = any(
            ur.role.role_code.lower() in ['dept_manager', 'department_manager', '部门经理']
            for ur in current_user.roles
        ) if current_user.roles else False

        # 根据角色过滤数据
        if project_ids and is_dept_manager:
            # 既是项目经理又是部门经理，可以看到项目和部门的工时
            query = query.filter(
                (Timesheet.project_id.in_(project_ids)) |
                (Timesheet.department_id == current_user.department_id)
            )
        elif project_ids:
            # 只是项目经理，只能看到项目工时
            query = query.filter(Timesheet.project_id.in_(project_ids))
        elif is_dept_manager and current_user.department_id:
            # 只是部门经理，只能看到部门工时
            query = query.filter(Timesheet.department_id == current_user.department_id)
        else:
            # 其他情况，返回空列表
            query = query.filter(Timesheet.id == -1)

    if user_id:
        query = query.filter(Timesheet.user_id == user_id)
    if project_id:
        query = query.filter(Timesheet.project_id == project_id)

    total = query.count()
    offset = (page - 1) * page_size
    timesheets = query.order_by(Timesheet.work_date.desc()).offset(offset).limit(page_size).all()
    
    items = []
    for ts in timesheets:
        user = db.query(User).filter(User.id == ts.user_id).first()
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
    
    return TimesheetListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )



