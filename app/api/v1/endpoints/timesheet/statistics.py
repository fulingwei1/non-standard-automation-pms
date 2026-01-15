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
    prefix="/timesheet/statistics",
    tags=["statistics"]
)

# 共 3 个路由

# ==================== 工时统计分析 ====================

@router.get("/statistics", response_model=TimesheetStatisticsResponse, status_code=status.HTTP_200_OK)
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
    query = db.query(Timesheet).filter(Timesheet.status == "APPROVED")
    
    # 权限控制
    if not hasattr(current_user, 'is_superuser') or not current_user.is_superuser:
        if user_id and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权查看其他用户的统计")
        query = query.filter(Timesheet.user_id == current_user.id)
    elif user_id:
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
        by_work_type=by_work_type
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
        Timesheet.user_id == current_user.id,
        Timesheet.status == 'APPROVED'
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
                'project_id': ts.project_id,
                'project_name': project_name,
                'total_hours': Decimal(0),
                'days': 0
            }
        by_project[project_name]['total_hours'] += hours
        by_project[project_name]['days'] += 1
        
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
            "by_project": {k: {'project_id': v['project_id'], 'project_name': v['project_name'], 'total_hours': float(v['total_hours']), 'days': v['days']} for k, v in by_project.items()},
            "by_date": {k: float(v) for k, v in by_date.items()},
            "by_work_type": {k: float(v) for k, v in by_work_type.items()},
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    )


@router.get("/departments/{dept_id}/timesheet-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
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
            }
        )
    
    # 查询部门成员的工时记录
    query = db.query(Timesheet).filter(
        Timesheet.user_id.in_(user_ids),
        Timesheet.status == 'APPROVED'
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
                'user_id': ts.user_id,
                'user_name': user_name,
                'total_hours': Decimal(0),
                'days': 0
            }
        by_user[user_name]['total_hours'] += hours
        by_user[user_name]['days'] += 1
        
        # 按项目统计
        project_name = "未分配项目"
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()
            project_name = project.project_name if project else "未知项目"
        
        if project_name not in by_project:
            by_project[project_name] = {
                'project_id': ts.project_id,
                'project_name': project_name,
                'total_hours': Decimal(0),
                'participants': set()
            }
        by_project[project_name]['total_hours'] += hours
        by_project[project_name]['participants'].add(ts.user_id)
        
        # 按日期统计
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal(0)
        by_date[date_str] += hours
    
    # 转换participants为数量
    for proj_name, proj_data in by_project.items():
        proj_data['participant_count'] = len(proj_data['participants'])
        del proj_data['participants']
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "department_id": dept_id,
            "department_name": department.dept_name,
            "total_hours": float(total_hours),
            "total_participants": len(participants),
            "by_user": [{**v, 'total_hours': float(v['total_hours'])} for v in by_user.values()],
            "by_project": {k: {**v, 'total_hours': float(v['total_hours'])} for k, v in by_project.items()},
            "by_date": {k: float(v) for k, v in by_date.items()},
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    )



