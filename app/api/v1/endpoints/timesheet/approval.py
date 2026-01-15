# -*- coding: utf-8 -*-
"""
提交与审批 - 自动生成
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
    prefix="/timesheet/approval",
    tags=["approval"]
)

# 共 5 个路由

# ==================== 提交与审批 ====================

@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_ids: List[int] = Body(..., description="工时记录ID列表"),
    current_user: User = Depends(security.require_permission("timesheet:update")),
) -> Any:
    """
    提交工时（草稿→待审核）
    """
    timesheets = db.query(Timesheet).filter(
        Timesheet.id.in_(timesheet_ids),
        Timesheet.user_id == current_user.id,
        Timesheet.status == "DRAFT"
    ).all()
    
    if not timesheets:
        raise HTTPException(status_code=400, detail="没有可提交的记录")
    
    for ts in timesheets:
        ts.status = "PENDING"
    
    db.commit()
    
    return ResponseModel(message=f"已提交 {len(timesheets)} 条工时记录")


@router.put("/{timesheet_id}/approve", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def approve_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    comment: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("timesheet:approve")),
) -> Any:
    """
    审批单条工时记录
    """
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    if timesheet.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能审批待审核状态的记录")

    # 检查审批权限
    if not security.has_timesheet_approval_access(current_user, db, timesheet.user_id, timesheet.department_id):
        raise HTTPException(status_code=403, detail="您没有权限审批此工时记录")

    timesheet.status = "APPROVED"
    timesheet.approver_id = current_user.id
    timesheet.approver_name = current_user.real_name or current_user.username
    timesheet.approve_time = datetime.now()
    timesheet.approve_comment = comment
    
    # 记录审批日志
    log = TimesheetApprovalLog(
        timesheet_id=timesheet.id,
        approver_id=current_user.id,
        approver_name=current_user.real_name or current_user.username,
        action="APPROVE",
        comment=comment
    )
    db.add(log)
    db.commit()
    
    # 审批通过后自动同步到各系统
    try:
        from app.services.timesheet_sync_service import TimesheetSyncService
        sync_service = TimesheetSyncService(db)
        sync_service.sync_all_on_approval(timesheet.id)
    except Exception as e:
        # 同步失败不影响审批结果，只记录日志
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"工时记录{timesheet.id}审批通过后自动同步失败: {str(e)}")
    
    return ResponseModel(message="工时记录已审批通过")


@router.post("/approve", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def approve_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_ids: List[int] = Body(..., description="工时记录ID列表"),
    comment: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("timesheet:approve")),
) -> Any:
    """
    批量审批工时（PM/部门审批）
    """
    timesheets = db.query(Timesheet).filter(
        Timesheet.id.in_(timesheet_ids),
        Timesheet.status == "PENDING"
    ).all()
    
    if not timesheets:
        raise HTTPException(status_code=400, detail="没有待审核的记录")

    # 检查审批权限
    if not security.check_timesheet_approval_permission(current_user, db, timesheets):
        raise HTTPException(status_code=403, detail="您没有权限审批这些工时记录")

    for ts in timesheets:
        if check_timesheet_approval_permission(db, ts, current_user):
            approved_timesheets.append(ts)
        else:
            no_permission_ids.append(ts.id)

    if not approved_timesheets:
        raise HTTPException(status_code=403, detail="无权审批所选的工时记录")

    for ts in approved_timesheets:
        ts.status = "APPROVED"
        ts.approver_id = current_user.id
        ts.approver_name = current_user.real_name or current_user.username
        ts.approve_time = datetime.now()
        ts.approve_comment = comment
        
        # 记录审批日志
        log = TimesheetApprovalLog(
            timesheet_id=ts.id,
            approver_id=current_user.id,
            approver_name=current_user.real_name or current_user.username,
            action="APPROVE",
            comment=comment
        )
        db.add(log)
    
    db.commit()
    
    # 批量审批通过后自动同步
    try:
        from app.services.timesheet_sync_service import TimesheetSyncService
        sync_service = TimesheetSyncService(db)
        for ts in approved_timesheets:
            try:
                sync_service.sync_all_on_approval(ts.id)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"工时记录{ts.id}审批通过后自动同步失败: {str(e)}")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"批量同步失败: {str(e)}")

    # 返回审批结果，包含跳过的记录信息
    message = f"已审批通过 {len(approved_timesheets)} 条工时记录"
    if no_permission_ids:
        message += f"，{len(no_permission_ids)} 条记录因无权限被跳过"

    return ResponseModel(message=message)


@router.put("/batch-approve", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_approve_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_ids: List[int] = Body(..., description="工时记录ID列表"),
    comment: Optional[str] = Body(None, description="审批意见"),
    current_user: User = Depends(security.require_permission("timesheet:approve")),
) -> Any:
    """
    批量审批工时（PUT方式，与POST /approve功能相同）
    """
    return approve_timesheets(db=db, timesheet_ids=timesheet_ids, comment=comment, current_user=current_user)


@router.post("/reject", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def reject_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_ids: List[int] = Body(..., description="工时记录ID列表"),
    comment: str = Body(..., description="拒绝原因"),
    current_user: User = Depends(security.require_permission("timesheet:approve")),
) -> Any:
    """
    拒绝工时
    """
    timesheets = db.query(Timesheet).filter(
        Timesheet.id.in_(timesheet_ids),
        Timesheet.status == "PENDING"
    ).all()
    
    if not timesheets:
        raise HTTPException(status_code=400, detail="没有待审核的记录")
    
    for ts in timesheets:
        ts.status = "REJECTED"
        ts.approver_id = current_user.id
        ts.approver_name = current_user.real_name or current_user.username
        ts.approve_time = datetime.now()
        
        log = TimesheetApprovalLog(
            timesheet_id=ts.id,
            approver_id=current_user.id,
            approval_action="REJECT",
            approval_comment=comment
        )
        db.add(log)
    
    db.commit()
    
    return ResponseModel(message=f"已拒绝 {len(timesheets)} 条工时记录")



