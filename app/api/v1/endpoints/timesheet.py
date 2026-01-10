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
from app.models.organization import Department
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
        for ts in timesheets:
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
    
    return ResponseModel(message=f"已审批通过 {len(timesheets)} 条工时记录")


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


# ==================== 工时汇总与报表 ====================

@router.post("/aggregate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def aggregate_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    user_id: Optional[int] = Query(None, description="用户ID（可选）"),
    department_id: Optional[int] = Query(None, description="部门ID（可选）"),
    project_id: Optional[int] = Query(None, description="项目ID（可选）"),
    current_user: User = Depends(security.require_permission("timesheet:manage")),
) -> Any:
    """
    手动触发工时汇总
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    
    try:
        service = TimesheetAggregationService(db)
        result = service.aggregate_monthly_timesheet(year, month, user_id, department_id, project_id)
        
        return ResponseModel(
            code=200,
            message="工时汇总完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"工时汇总失败: {str(e)}")


@router.get("/reports/hr", response_model=ResponseModel)
def get_hr_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    department_id: Optional[int] = Query(None, description="部门ID（可选）"),
    format: str = Query("json", description="格式：json/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取HR加班工资报表
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_report_service import TimesheetReportService
    from fastapi.responses import StreamingResponse
    
    try:
        if format == "excel":
            # 生成Excel报表
            report_service = TimesheetReportService(db)
            excel_file = report_service.generate_hr_report_excel(year, month, department_id)
            
            filename = f"HR加班工资表_{year}年{month}月.xlsx"
            return StreamingResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON数据
            service = TimesheetAggregationService(db)
            data = service.generate_hr_report(year, month, department_id)
            
            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成HR报表失败: {str(e)}")


@router.get("/reports/finance", response_model=ResponseModel)
def get_finance_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    project_id: Optional[int] = Query(None, description="项目ID（可选）"),
    format: str = Query("json", description="格式：json/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取财务报表（项目成本核算表）
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_report_service import TimesheetReportService
    from fastapi.responses import StreamingResponse
    
    try:
        if format == "excel":
            # 生成Excel报表
            report_service = TimesheetReportService(db)
            excel_file = report_service.generate_finance_report_excel(year, month, project_id)
            
            filename = f"项目成本核算表_{year}年{month}月.xlsx"
            return StreamingResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON数据
            service = TimesheetAggregationService(db)
            data = service.generate_finance_report(year, month, project_id)
            
            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成财务报表失败: {str(e)}")


@router.get("/reports/rd", response_model=ResponseModel)
def get_rd_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份"),
    rd_project_id: Optional[int] = Query(None, description="研发项目ID（可选）"),
    format: str = Query("json", description="格式：json/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取研发报表（研发费用核算表）
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_report_service import TimesheetReportService
    from fastapi.responses import StreamingResponse
    
    try:
        if format == "excel":
            # 生成Excel报表
            report_service = TimesheetReportService(db)
            excel_file = report_service.generate_rd_report_excel(year, month, rd_project_id)
            
            filename = f"研发费用核算表_{year}年{month}月.xlsx"
            return StreamingResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON数据
            service = TimesheetAggregationService(db)
            data = service.generate_rd_report(year, month, rd_project_id)
            
            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成研发报表失败: {str(e)}")


@router.get("/reports/project", response_model=ResponseModel)
def get_project_report(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Query(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期（可选）"),
    end_date: Optional[date] = Query(None, description="结束日期（可选）"),
    format: str = Query("json", description="格式：json/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取项目报表（项目工时统计）
    """
    from app.services.timesheet_aggregation_service import TimesheetAggregationService
    from app.services.timesheet_report_service import TimesheetReportService
    from fastapi.responses import StreamingResponse
    
    try:
        if format == "excel":
            # 生成Excel报表
            report_service = TimesheetReportService(db)
            excel_file = report_service.generate_project_report_excel(project_id, start_date, end_date)
            
            project = db.query(Project).filter(Project.id == project_id).first()
            project_name = project.project_name if project else f"项目{project_id}"
            filename = f"{project_name}_工时报表.xlsx"
            
            return StreamingResponse(
                excel_file,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            # 返回JSON数据
            service = TimesheetAggregationService(db)
            data = service.generate_project_report(project_id, start_date, end_date)
            
            return ResponseModel(
                code=200,
                message="success",
                data=data
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成项目报表失败: {str(e)}")


@router.post("/sync", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def sync_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: Optional[int] = Query(None, description="工时记录ID（可选）"),
    project_id: Optional[int] = Query(None, description="项目ID（可选，用于批量同步）"),
    rd_project_id: Optional[int] = Query(None, description="研发项目ID（可选，用于批量同步）"),
    year: Optional[int] = Query(None, description="年份（用于批量同步）"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月份（用于批量同步）"),
    sync_target: str = Query("all", description="同步目标：all/finance/rd/project/hr"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    手动触发数据同步
    """
    from app.services.timesheet_sync_service import TimesheetSyncService
    
    try:
        service = TimesheetSyncService(db)
        results = {}
        
        if timesheet_id:
            # 同步单个工时记录
            if sync_target in ["all", "finance"]:
                results['finance'] = service.sync_to_finance(timesheet_id=timesheet_id)
            if sync_target in ["all", "rd"]:
                results['rd'] = service.sync_to_rd(timesheet_id=timesheet_id)
            if sync_target in ["all", "project"]:
                results['project'] = service.sync_to_project(timesheet_id=timesheet_id)
        elif project_id and year and month:
            # 批量同步项目
            if sync_target in ["all", "finance"]:
                results['finance'] = service.sync_to_finance(project_id=project_id, year=year, month=month)
            if sync_target in ["all", "project"]:
                results['project'] = service.sync_to_project(project_id=project_id)
        elif rd_project_id and year and month:
            # 批量同步研发项目
            if sync_target in ["all", "rd"]:
                results['rd'] = service.sync_to_rd(rd_project_id=rd_project_id, year=year, month=month)
        elif year and month:
            # 同步所有数据
            if sync_target in ["all", "hr"]:
                results['hr'] = service.sync_to_hr(year=year, month=month)
        else:
            raise HTTPException(status_code=400, detail="参数不完整")
        
        return ResponseModel(
            code=200,
            message="数据同步完成",
            data=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据同步失败: {str(e)}")


@router.get("/sync-status/{timesheet_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_sync_status(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取工时记录的同步状态
    """
    from app.models.finance import FinancialProjectCost
    from app.models.rd_project import RdCost
    from app.models.project import ProjectCost
    
    timesheet = db.query(Timesheet).filter(Timesheet.id == timesheet_id).first()
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    
    # 检查同步状态
    sync_status = {
        'finance': {'status': 'not_synced', 'message': '未同步'},
        'rd': {'status': 'not_synced', 'message': '未同步'},
        'project': {'status': 'not_synced', 'message': '未同步'},
        'hr': {'status': 'not_synced', 'message': '未同步'},
    }
    
    # 检查财务同步状态
    if timesheet.project_id and timesheet.status == 'APPROVED':
        finance_cost = db.query(FinancialProjectCost).filter(
            FinancialProjectCost.source_type == 'TIMESHEET',
            FinancialProjectCost.source_id == timesheet_id
        ).first()
        if finance_cost:
            sync_status['finance'] = {
                'status': 'synced',
                'message': '已同步',
                'cost_id': finance_cost.id,
                'sync_time': finance_cost.created_at.isoformat() if finance_cost.created_at else None
            }
    
    # 检查研发同步状态
    if timesheet.rd_project_id and timesheet.status == 'APPROVED':
        rd_cost = db.query(RdCost).filter(
            RdCost.source_type == 'CALCULATED',
            RdCost.source_id == timesheet_id
        ).first()
        if rd_cost:
            sync_status['rd'] = {
                'status': 'synced',
                'message': '已同步',
                'cost_id': rd_cost.id,
                'sync_time': rd_cost.created_at.isoformat() if rd_cost.created_at else None
            }
    
    # 检查项目同步状态（通过ProjectCost）
    if timesheet.project_id and timesheet.status == 'APPROVED':
        # 项目成本通过LaborCostService更新，这里检查是否有对应的成本记录
        project_cost = db.query(ProjectCost).filter(
            ProjectCost.project_id == timesheet.project_id,
            ProjectCost.cost_type == 'LABOR'
        ).first()
        if project_cost:
            sync_status['project'] = {
                'status': 'synced',
                'message': '已同步',
                'cost_id': project_cost.id,
                'sync_time': project_cost.updated_at.isoformat() if project_cost.updated_at else None
            }
    
    # HR同步状态（审批通过即视为已同步到HR）
    if timesheet.status == 'APPROVED':
        sync_status['hr'] = {
            'status': 'synced',
            'message': '已同步',
            'sync_time': timesheet.approve_time.isoformat() if timesheet.approve_time else None
        }
    
    return ResponseModel(
        code=200,
        message="success",
        data=sync_status
    )
