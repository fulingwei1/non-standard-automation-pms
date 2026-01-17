# -*- coding: utf-8 -*-
"""
工时记录管理 - 自动生成
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
    prefix="/timesheet/records",
    tags=["records"]
)

# 共 6 个路由

# ==================== 工时记录管理 ====================

@router.get("", response_model=TimesheetListResponse, status_code=status.HTTP_200_OK)
def list_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    工时记录列表（分页+筛选）
    """
    query = db.query(Timesheet)

    # 权限控制：普通用户只能看自己的，管理员可以看所有
    if not hasattr(current_user, 'is_superuser') or not current_user.is_superuser:
        query = query.filter(Timesheet.user_id == current_user.id)
    elif user_id:
        query = query.filter(Timesheet.user_id == user_id)

    if project_id:
        query = query.filter(Timesheet.project_id == project_id)
    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)
    if status:
        query = query.filter(Timesheet.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    timesheets = query.order_by(desc(Timesheet.work_date), desc(Timesheet.created_at)).offset(offset).limit(page_size).all()

    items = []
    for ts in timesheets:
        user = db.query(User).filter(User.id == ts.user_id).first()
        project = None
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()

        task_name = None
        if ts.task_id:
            from app.models.progress import Task
            task = db.query(Task).filter(Task.id == ts.task_id).first()
            task_name = task.task_name if task else None

        items.append(TimesheetResponse(
            id=ts.id,
            user_id=ts.user_id,
            user_name=user.real_name or user.username if user else None,
            project_id=ts.project_id,
            rd_project_id=ts.rd_project_id,
            project_name=project.project_name if project else None,
            task_id=ts.task_id,
            task_name=task_name,
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


@router.post("", response_model=TimesheetResponse, status_code=status.HTTP_201_CREATED)
def create_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_in: TimesheetCreate,
    current_user: User = Depends(security.require_permission("timesheet:create")),
) -> Any:
    """
    创建单条工时
    """
    # 验证项目（至少需要有一个项目ID）
    if not timesheet_in.project_id and not timesheet_in.rd_project_id:
        raise HTTPException(status_code=400, detail="必须指定项目ID或研发项目ID")

    if timesheet_in.project_id:
        project = db.query(Project).filter(Project.id == timesheet_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

    if timesheet_in.rd_project_id:
        from app.models.rd_project import RdProject
        rd_project = db.query(RdProject).filter(RdProject.id == timesheet_in.rd_project_id).first()
        if not rd_project:
            raise HTTPException(status_code=404, detail="研发项目不存在")

    # 检查同一天是否已有记录
    query_filter = [
        Timesheet.user_id == current_user.id,
        Timesheet.work_date == timesheet_in.work_date,
        Timesheet.status != "REJECTED"
    ]
    if timesheet_in.project_id:
        query_filter.append(Timesheet.project_id == timesheet_in.project_id)
    if timesheet_in.rd_project_id:
        query_filter.append(Timesheet.rd_project_id == timesheet_in.rd_project_id)

    existing = db.query(Timesheet).filter(*query_filter).first()

    if existing:
        raise HTTPException(status_code=400, detail="该日期已有工时记录，请更新或删除后重试")

    # 获取用户和部门信息
    user = db.query(User).filter(User.id == current_user.id).first()
    department_id = None
    department_name = None
    if user and hasattr(user, 'department_id') and user.department_id:
        department = db.query(Department).filter(Department.id == user.department_id).first()
        if department:
            department_id = department.id
            department_name = department.name

    # 获取项目信息
    project_code = None
    project_name = None
    if timesheet_in.project_id:
        project = db.query(Project).filter(Project.id == timesheet_in.project_id).first()
        if project:
            project_code = project.project_code
            project_name = project.project_name

    timesheet = Timesheet(
        user_id=current_user.id,
        user_name=user.real_name or user.username if user else None,
        department_id=department_id,
        department_name=department_name,
        project_id=timesheet_in.project_id,
        project_code=project_code,
        project_name=project_name,
        rd_project_id=timesheet_in.rd_project_id,
        task_id=timesheet_in.task_id,
        work_date=timesheet_in.work_date,
        hours=timesheet_in.work_hours,
        overtime_type=timesheet_in.work_type,
        work_content=timesheet_in.description,
        status="DRAFT",
        created_by=current_user.id
    )

    db.add(timesheet)
    db.commit()
    db.refresh(timesheet)

    return get_timesheet_detail(timesheet.id, db, current_user)


@router.post("/batch", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def batch_create_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    batch_in: TimesheetBatchCreate,
    current_user: User = Depends(security.require_permission("timesheet:create")),
) -> Any:
    """
    批量创建工时
    """
    success_count = 0
    failed_count = 0
    errors = []

    for ts_in in batch_in.timesheets:
        try:
            # 验证项目
            if ts_in.project_id:
                project = db.query(Project).filter(Project.id == ts_in.project_id).first()
                if not project:
                    errors.append({"date": ts_in.work_date.isoformat(), "error": "项目不存在"})
                    failed_count += 1
                    continue

            # 检查是否已存在
            existing = db.query(Timesheet).filter(
                Timesheet.user_id == current_user.id,
                Timesheet.work_date == ts_in.work_date,
                Timesheet.project_id == ts_in.project_id,
                Timesheet.status != "REJECTED"
            ).first()

            if existing:
                errors.append({"date": ts_in.work_date.isoformat(), "error": "该日期已有记录"})
                failed_count += 1
                continue

            # 获取用户和项目信息
            user = db.query(User).filter(User.id == current_user.id).first()
            project_code = None
            project_name = None
            if ts_in.project_id:
                project = db.query(Project).filter(Project.id == ts_in.project_id).first()
                if project:
                    project_code = project.project_code
                    project_name = project.project_name

            timesheet = Timesheet(
                user_id=current_user.id,
                user_name=user.real_name or user.username if user else None,
                project_id=ts_in.project_id,
                project_code=project_code,
                project_name=project_name,
                task_id=ts_in.task_id,
                work_date=ts_in.work_date,
                hours=ts_in.work_hours,
                overtime_type=ts_in.work_type,
                work_content=ts_in.description,
                status="DRAFT",
                created_by=current_user.id
            )

            db.add(timesheet)
            success_count += 1
        except Exception as e:
            errors.append({"date": ts_in.work_date.isoformat() if ts_in.work_date else None, "error": str(e)})
            failed_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量创建完成：成功 {success_count} 条，失败 {failed_count} 条",
        data={"success_count": success_count, "failed_count": failed_count, "errors": errors}
    )


@router.get("/{timesheet_id}", response_model=TimesheetResponse, status_code=status.HTTP_200_OK)
def get_timesheet_detail(
    timesheet_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取工时记录详情
    """
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    # 权限检查
    if timesheet.user_id != current_user.id:
        if not hasattr(current_user, 'is_superuser') or not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="无权访问此记录")

    user = db.query(User).filter(User.id == timesheet.user_id).first()
    project = None
    if timesheet.project_id:
        project = db.query(Project).filter(Project.id == timesheet.project_id).first()

    rd_project = None
    if timesheet.rd_project_id:
        from app.models.rd_project import RdProject
        rd_project = db.query(RdProject).filter(RdProject.id == timesheet.rd_project_id).first()

    return TimesheetResponse(
        id=timesheet.id,
        user_id=timesheet.user_id,
        user_name=user.real_name or user.username if user else None,
        project_id=timesheet.project_id,
        rd_project_id=timesheet.rd_project_id,
        project_name=project.project_name if project else (rd_project.project_name if rd_project else None),
        task_id=timesheet.task_id,
        task_name=None,
        work_date=timesheet.work_date,
        work_hours=timesheet.hours or Decimal("0"),
        work_type=timesheet.overtime_type or "NORMAL",
        description=timesheet.work_content,
        is_billable=True,
        status=timesheet.status or "DRAFT",
        approved_by=timesheet.approver_id,
        approved_at=timesheet.approve_time,
        created_at=timesheet.created_at,
        updated_at=timesheet.updated_at
    )


@router.put("/{timesheet_id}", response_model=TimesheetResponse, status_code=status.HTTP_200_OK)
def update_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    timesheet_in: TimesheetUpdate,
    current_user: User = Depends(security.require_permission("timesheet:update")),
) -> Any:
    """
    更新工时记录
    """
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    # 权限检查：只能修改自己的草稿状态记录
    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此记录")

    if timesheet.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能修改草稿状态的记录")

    if timesheet_in.work_date is not None:
        timesheet.work_date = timesheet_in.work_date
    if timesheet_in.work_hours is not None:
        timesheet.hours = timesheet_in.work_hours
    if timesheet_in.work_type is not None:
        timesheet.overtime_type = timesheet_in.work_type
    if timesheet_in.description is not None:
        timesheet.work_content = timesheet_in.description

    db.add(timesheet)
    db.commit()
    db.refresh(timesheet)

    return get_timesheet_detail(timesheet_id, db, current_user)


@router.delete("/{timesheet_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    current_user: User = Depends(security.require_permission("timesheet:delete")),
) -> Any:
    """
    删除工时记录（仅草稿）
    """
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    if timesheet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此记录")

    if timesheet.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能删除草稿状态的记录")

    db.delete(timesheet)
    db.commit()

    return ResponseModel(message="工时记录已删除")



