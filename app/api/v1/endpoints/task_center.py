# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func, case

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.notification import Notification
from app.services.sales_reminder_service import create_notification
from app.models.task_center import (
    TaskUnified, TaskComment, TaskOperationLog, TaskReminder, JobDutyTemplate
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.task_center import (
    TaskOverviewResponse, TaskUnifiedCreate, TaskUnifiedUpdate, TaskUnifiedResponse,
    TaskUnifiedListResponse, TaskProgressUpdate, TaskTransferRequest,
    TaskCommentCreate, TaskCommentResponse, BatchTaskOperation, BatchOperationResponse,
    BatchOperationStatistics
)

router = APIRouter()


def generate_task_code(db: Session) -> str:
    """生成任务编号：TASK-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    
    return generate_sequential_no(
        db=db,
        model_class=TaskUnified,
        no_field='task_code',
        prefix='TASK',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def log_task_operation(
    db: Session,
    task_id: int,
    operation_type: str,
    operation_desc: str,
    operator_id: int,
    operator_name: str,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None
):
    """记录任务操作日志"""
    log = TaskOperationLog(
        task_id=task_id,
        operation_type=operation_type,
        operation_desc=operation_desc,
        operator_id=operator_id,
        operator_name=operator_name,
        old_value=old_value,
        new_value=new_value
    )
    db.add(log)
    db.commit()


# ==================== 任务概览 ====================

@router.get("/overview", response_model=TaskOverviewResponse, status_code=status.HTTP_200_OK)
def get_task_overview(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    任务概览统计（待办/逾期/本周）
    """
    user_id = current_user.id
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    # 总任务数
    total_tasks = db.query(TaskUnified).filter(TaskUnified.assignee_id == user_id).count()
    
    # 待接收任务（转办任务）
    pending_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.status == "PENDING"
    ).count()
    
    # 进行中任务
    in_progress_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.status == "IN_PROGRESS"
    ).count()
    
    # 逾期任务
    today_str = today.strftime("%Y-%m-%d")
    overdue_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"]),
        TaskUnified.deadline.isnot(None),
        func.date(TaskUnified.deadline) < today_str
    ).count()
    
    # 本周任务
    this_week_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.plan_start_date >= week_start,
        TaskUnified.plan_start_date <= week_start + timedelta(days=6)
    ).count()
    
    # 紧急任务
    urgent_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"]),
        or_(TaskUnified.is_urgent == True, TaskUnified.priority == "URGENT")
    ).count()
    
    # 按状态统计
    status_stats = {}
    status_counts = (
        db.query(TaskUnified.status, func.count(TaskUnified.id))
        .filter(TaskUnified.assignee_id == user_id)
        .group_by(TaskUnified.status)
        .all()
    )
    for status, count in status_counts:
        status_stats[status] = count
    
    # 按优先级统计
    priority_stats = {}
    priority_counts = (
        db.query(TaskUnified.priority, func.count(TaskUnified.id))
        .filter(TaskUnified.assignee_id == user_id)
        .group_by(TaskUnified.priority)
        .all()
    )
    for priority, count in priority_counts:
        priority_stats[priority] = count
    
    # 按类型统计
    type_stats = {}
    type_counts = (
        db.query(TaskUnified.task_type, func.count(TaskUnified.id))
        .filter(TaskUnified.assignee_id == user_id)
        .group_by(TaskUnified.task_type)
        .all()
    )
    for task_type, count in type_counts:
        type_stats[task_type] = count
    
    return TaskOverviewResponse(
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        overdue_tasks=overdue_tasks,
        this_week_tasks=this_week_tasks,
        urgent_tasks=urgent_tasks,
        by_status=status_stats,
        by_priority=priority_stats,
        by_type=type_stats
    )


# ==================== 我的任务列表 ====================

@router.get("/my-tasks", response_model=TaskUnifiedListResponse, status_code=status.HTTP_200_OK)
def get_my_tasks(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    is_urgent: Optional[bool] = Query(None, description="是否紧急"),
    is_overdue: Optional[bool] = Query(None, description="是否逾期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题/描述）"),
    sort_by: str = Query("deadline", description="排序字段：deadline/priority/created_at"),
    sort_order: str = Query("asc", description="排序方向：asc/desc"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    我的任务列表（聚合所有来源）
    """
    user_id = current_user.id
    query = db.query(TaskUnified).filter(TaskUnified.assignee_id == user_id)
    
    # 状态筛选
    if status:
        query = query.filter(TaskUnified.status == status)
    
    # 任务类型筛选
    if task_type:
        query = query.filter(TaskUnified.task_type == task_type)
    
    # 优先级筛选
    if priority:
        query = query.filter(TaskUnified.priority == priority)
    
    # 紧急任务筛选
    if is_urgent is not None:
        query = query.filter(TaskUnified.is_urgent == is_urgent)
    
    # 逾期任务筛选
    if is_overdue is not None:
        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")
        if is_overdue:
            query = query.filter(
                TaskUnified.deadline.isnot(None),
                func.date(TaskUnified.deadline) < today_str,
                TaskUnified.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"])
            )
        else:
            query = query.filter(
                or_(
                    TaskUnified.deadline.is_(None),
                    func.date(TaskUnified.deadline) >= today_str,
                    ~TaskUnified.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"])
                )
            )
    
    # 项目筛选
    if project_id:
        query = query.filter(TaskUnified.project_id == project_id)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                TaskUnified.title.like(f"%{keyword}%"),
                TaskUnified.description.like(f"%{keyword}%")
            )
        )
    
    # 排序
    if sort_by == "deadline":
        order_by = TaskUnified.deadline
    elif sort_by == "priority":
        priority_order = case(
            (TaskUnified.priority == "URGENT", 1),
            (TaskUnified.priority == "HIGH", 2),
            (TaskUnified.priority == "MEDIUM", 3),
            (TaskUnified.priority == "LOW", 4),
            else_=5
        )
        order_by = priority_order
    else:
        order_by = TaskUnified.created_at
    
    if sort_order == "desc":
        query = query.order_by(desc(order_by))
    else:
        query = query.order_by(order_by)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    tasks = query.offset(offset).limit(page_size).all()
    
    # 构建响应
    items = []
    today = datetime.now().date()
    for task in tasks:
        is_overdue = False
        if task.deadline and task.status in ["PENDING", "ACCEPTED", "IN_PROGRESS"]:
            deadline_date = task.deadline.date() if isinstance(task.deadline, datetime) else task.deadline
            if deadline_date < today:
                is_overdue = True
        
        items.append(TaskUnifiedResponse(
            id=task.id,
            task_code=task.task_code,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            source_type=task.source_type,
            source_id=task.source_id,
            source_name=task.source_name,
            project_id=task.project_id,
            project_name=task.project_name,
            assignee_id=task.assignee_id,
            assignee_name=task.assignee_name,
            assigner_id=task.assigner_id,
            assigner_name=task.assigner_name,
            plan_start_date=task.plan_start_date,
            plan_end_date=task.plan_end_date,
            actual_start_date=task.actual_start_date,
            actual_end_date=task.actual_end_date,
            deadline=task.deadline,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours or Decimal("0"),
            status=task.status,
            progress=task.progress or 0,
            priority=task.priority,
            is_urgent=task.is_urgent or False,
            is_transferred=task.is_transferred or False,
            transfer_from_name=task.transfer_from_name,
            tags=task.tags if task.tags else [],
            category=task.category,
            is_overdue=is_overdue,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))
    
    return TaskUnifiedListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 任务详情 ====================

@router.get("/tasks/{task_id}", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def get_task_detail(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    任务详情
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 检查权限（只有执行人可以查看）
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    today = datetime.now().date()
    is_overdue = False
    if task.deadline and task.status in ["PENDING", "ACCEPTED", "IN_PROGRESS"]:
        deadline_date = task.deadline.date() if isinstance(task.deadline, datetime) else task.deadline
        if deadline_date < today:
            is_overdue = True
    
    return TaskUnifiedResponse(
        id=task.id,
        task_code=task.task_code,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        source_type=task.source_type,
        source_id=task.source_id,
        source_name=task.source_name,
        project_id=task.project_id,
        project_name=task.project_name,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee_name,
        assigner_id=task.assigner_id,
        assigner_name=task.assigner_name,
        plan_start_date=task.plan_start_date,
        plan_end_date=task.plan_end_date,
        actual_start_date=task.actual_start_date,
        actual_end_date=task.actual_end_date,
        deadline=task.deadline,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours or Decimal("0"),
        status=task.status,
        progress=task.progress or 0,
        priority=task.priority,
        is_urgent=task.is_urgent or False,
        is_transferred=task.is_transferred or False,
        transfer_from_name=task.transfer_from_name,
        tags=task.tags if task.tags else [],
        category=task.category,
        is_overdue=is_overdue,
        created_at=task.created_at,
        updated_at=task.updated_at
    )


# ==================== 创建个人任务 ====================

@router.post("/tasks", response_model=TaskUnifiedResponse, status_code=status.HTTP_201_CREATED)
def create_personal_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: TaskUnifiedCreate,
    current_user: User = Depends(security.require_permission("task_center:create")),
) -> Any:
    """
    创建个人任务（自建任务）
    """
    # 验证项目（如果提供）
    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    task_code = generate_task_code(db)
    
    task = TaskUnified(
        task_code=task_code,
        title=task_in.title,
        description=task_in.description,
        task_type=task_in.task_type or "PERSONAL",
        project_id=task_in.project_id,
        assignee_id=current_user.id,
        assignee_name=current_user.real_name or current_user.username,
        assigner_id=current_user.id,
        assigner_name=current_user.real_name or current_user.username,
        plan_start_date=task_in.plan_start_date,
        plan_end_date=task_in.plan_end_date,
        deadline=task_in.deadline,
        estimated_hours=task_in.estimated_hours,
        priority=task_in.priority,
        is_urgent=task_in.is_urgent,
        tags=task_in.tags if task_in.tags else [],
        category=task_in.category,
        reminder_enabled=task_in.reminder_enabled,
        reminder_before_hours=task_in.reminder_before_hours,
        status="ACCEPTED",
        created_by=current_user.id
    )
    
    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if project:
            task.project_code = project.project_code
            task.project_name = project.project_name
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    log_task_operation(
        db, task.id, "CREATE", f"创建个人任务：{task.title}",
        current_user.id, current_user.real_name or current_user.username
    )
    
    return get_task_detail(task.id, db, current_user)


# ==================== 更新任务进度 ====================

@router.put("/tasks/{task_id}/progress", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def update_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    progress_in: TaskProgressUpdate,
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """
    更新任务进度
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权更新此任务")
    
    old_progress = task.progress
    old_hours = task.actual_hours
    
    task.progress = progress_in.progress
    if progress_in.actual_hours is not None:
        task.actual_hours = progress_in.actual_hours
    task.updated_by = current_user.id
    
    # 如果进度为100%，自动完成
    if progress_in.progress >= 100 and task.status != "COMPLETED":
        task.status = "COMPLETED"
        task.actual_end_date = datetime.now().date()
    
    # 如果开始更新进度且未开始，自动开始
    if progress_in.progress > 0 and task.status == "ACCEPTED":
        task.status = "IN_PROGRESS"
        if not task.actual_start_date:
            task.actual_start_date = datetime.now().date()
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    log_task_operation(
        db, task.id, "UPDATE_PROGRESS",
        f"更新进度：{old_progress}% -> {progress_in.progress}%",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"progress": old_progress, "actual_hours": float(old_hours) if old_hours else 0},
        new_value={"progress": progress_in.progress, "actual_hours": float(progress_in.actual_hours) if progress_in.actual_hours else None}
    )
    
    return get_task_detail(task_id, db, current_user)


# ==================== 完成任务 ====================

@router.put("/tasks/{task_id}/complete", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def complete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    完成任务
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权完成此任务")
    
    if task.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="任务已完成")
    
    old_status = task.status
    task.status = "COMPLETED"
    task.progress = 100
    task.actual_end_date = datetime.now().date()
    task.updated_by = current_user.id
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    log_task_operation(
        db, task.id, "COMPLETE", f"完成任务：{task.title}",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"status": old_status},
        new_value={"status": "COMPLETED"}
    )
    
    return get_task_detail(task_id, db, current_user)


# ==================== 任务转办 ====================

@router.post("/tasks/{task_id}/transfer", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def transfer_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    transfer_in: TaskTransferRequest,
    current_user: User = Depends(security.require_permission("task_center:assign")),
) -> Any:
    """
    任务转办
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权转办此任务")
    
    if task.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="已完成的任务不能转办")
    
    # 验证目标用户
    target_user = db.query(User).filter(User.id == transfer_in.target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能转办给自己")
    
    old_assignee_id = task.assignee_id
    old_assignee_name = task.assignee_name
    
    task.assignee_id = transfer_in.target_user_id
    task.assignee_name = target_user.real_name or target_user.username
    task.is_transferred = True
    task.transfer_from_id = current_user.id
    task.transfer_from_name = current_user.real_name or current_user.username
    task.transfer_reason = transfer_in.transfer_reason
    task.transfer_time = datetime.now()
    task.status = "PENDING"  # 转办后需要接收
    task.updated_by = current_user.id
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    log_task_operation(
        db, task.id, "TRANSFER",
        f"转办任务：{old_assignee_name} -> {task.assignee_name}，原因：{transfer_in.transfer_reason}",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"assignee_id": old_assignee_id, "assignee_name": old_assignee_name},
        new_value={"assignee_id": transfer_in.target_user_id, "assignee_name": task.assignee_name}
    )
    
    # 发送通知给目标用户
    try:
        target_user = db.query(User).filter(User.id == transfer_in.target_user_id).first()
        if target_user:
            notification = create_notification(
                db=db,
                user_id=transfer_in.target_user_id,
                notification_type="TASK_ASSIGNED",
                title=f"任务转办通知",
                content=f"{current_user.real_name or current_user.username} 将任务「{task.title}」转办给您，原因：{transfer_in.transfer_reason}",
                source_type="task",
                source_id=task.id,
                link_url=f"/tasks/{task.id}",
                priority="HIGH",
                extra_data={"task_id": task.id, "from_user": current_user.real_name or current_user.username}
            )
            db.commit()
    except Exception as e:
        # 通知发送失败不影响主流程
        pass
    
    return get_task_detail(task_id, db, current_user)


# ==================== 接收/拒绝转办任务 ====================

@router.put("/tasks/{task_id}/accept", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def accept_transferred_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    接收转办任务
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权接收此任务")
    
    if task.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能接收待接收状态的任务")
    
    old_status = task.status
    task.status = "ACCEPTED"
    task.updated_by = current_user.id
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    log_task_operation(
        db, task.id, "ACCEPT", f"接收转办任务：{task.title}",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"status": old_status},
        new_value={"status": "ACCEPTED"}
    )
    
    return get_task_detail(task_id, db, current_user)


@router.put("/tasks/{task_id}/reject", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def reject_transferred_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    reason: Optional[str] = Query(None, description="拒绝原因"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    拒绝转办任务
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权拒绝此任务")
    
    if task.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能拒绝待接收状态的任务")
    
    # 拒绝后转回给原转办人
    if task.transfer_from_id:
        old_assignee_id = task.assignee_id
        old_assignee_name = task.assignee_name
        
        from_user = db.query(User).filter(User.id == task.transfer_from_id).first()
        if from_user:
            task.assignee_id = task.transfer_from_id
            task.assignee_name = from_user.real_name or from_user.username
            task.is_transferred = False
            task.status = "ACCEPTED"
            task.updated_by = current_user.id
            
            db.add(task)
            db.commit()
            db.refresh(task)
            
            log_task_operation(
                db, task.id, "REJECT",
                f"拒绝转办任务，原因：{reason or '未提供原因'}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"assignee_id": old_assignee_id, "assignee_name": old_assignee_name},
                new_value={"assignee_id": task.transfer_from_id, "assignee_name": task.assignee_name}
            )
            
            # 通知原转办人
            if task.transfer_from_id:
                try:
                    notification = create_notification(
                        db=db,
                        user_id=task.transfer_from_id,
                        notification_type="TASK_TRANSFER_REJECTED",
                        title=f"任务转办被拒绝",
                        content=f"{current_user.real_name or current_user.username} 拒绝了任务「{task.title}」的转办，原因：{reason or '未提供原因'}",
                        source_type="task",
                        source_id=task.id,
                        link_url=f"/tasks/{task.id}",
                        priority="NORMAL",
                        extra_data={"task_id": task.id, "reject_reason": reason}
                    )
                    db.commit()
                except Exception as e:
                    # 通知发送失败不影响主流程
                    pass
    
    return get_task_detail(task_id, db, current_user)


# ==================== 任务评论 ====================

@router.post("/tasks/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
def create_task_comment(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    comment_in: TaskCommentCreate,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    任务评论（协作沟通）
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 验证父评论
    parent_comment = None
    if comment_in.parent_id:
        parent_comment = db.query(TaskComment).filter(TaskComment.id == comment_in.parent_id).first()
        if not parent_comment or parent_comment.task_id != task_id:
            raise HTTPException(status_code=400, detail="父评论不存在或不属于此任务")
    
    comment = TaskComment(
        task_id=task_id,
        content=comment_in.content,
        comment_type=comment_in.comment_type,
        parent_id=comment_in.parent_id,
        commenter_id=current_user.id,
        commenter_name=current_user.real_name or current_user.username,
        mentioned_users=comment_in.mentioned_users if comment_in.mentioned_users else []
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # 通知被@的用户
    if comment_in.mentioned_users:
        try:
            for user_id in comment_in.mentioned_users:
                if user_id != current_user.id:  # 不通知自己
                    mentioned_user = db.query(User).filter(User.id == user_id).first()
                    if mentioned_user:
                        notification = create_notification(
                            db=db,
                            user_id=user_id,
                            notification_type="TASK_MENTIONED",
                            title=f"任务评论中@了您",
                            content=f"{current_user.real_name or current_user.username} 在任务「{task.title}」的评论中@了您：{comment_in.content[:100]}",
                            source_type="task",
                            source_id=task.id,
                            link_url=f"/tasks/{task.id}",
                            priority="NORMAL",
                            extra_data={"task_id": task.id, "comment_id": comment.id, "commenter": current_user.real_name or current_user.username}
                        )
            db.commit()
        except Exception as e:
            # 通知发送失败不影响主流程
            pass
    
    return TaskCommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        content=comment.content,
        comment_type=comment.comment_type,
        parent_id=comment.parent_id,
        commenter_id=comment.commenter_id,
        commenter_name=comment.commenter_name,
        mentioned_users=comment.mentioned_users if comment.mentioned_users else [],
        created_at=comment.created_at,
        replies=None
    )


@router.get("/tasks/{task_id}/comments", response_model=List[TaskCommentResponse], status_code=status.HTTP_200_OK)
def get_task_comments(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    获取任务评论列表
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    comments = db.query(TaskComment).filter(
        TaskComment.task_id == task_id,
        TaskComment.parent_id.is_(None)  # 只获取顶级评论
    ).order_by(TaskComment.created_at).all()
    
    items = []
    for comment in comments:
        # 获取回复
        replies = db.query(TaskComment).filter(
            TaskComment.parent_id == comment.id
        ).order_by(TaskComment.created_at).all()
        
        reply_items = []
        for reply in replies:
            reply_items.append(TaskCommentResponse(
                id=reply.id,
                task_id=reply.task_id,
                content=reply.content,
                comment_type=reply.comment_type,
                parent_id=reply.parent_id,
                commenter_id=reply.commenter_id,
                commenter_name=reply.commenter_name,
                mentioned_users=reply.mentioned_users if reply.mentioned_users else [],
                created_at=reply.created_at,
                replies=None
            ))
        
        items.append(TaskCommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            content=comment.content,
            comment_type=comment.comment_type,
            parent_id=comment.parent_id,
            commenter_id=comment.commenter_id,
            commenter_name=comment.commenter_name,
            mentioned_users=comment.mentioned_users if comment.mentioned_users else [],
            created_at=comment.created_at,
            replies=reply_items if reply_items else None
        ))
    
    return items


# ==================== 批量操作 ====================

@router.post("/batch/complete", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_complete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量完成任务
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "任务已完成"})
                continue
            
            task.status = "COMPLETED"
            task.progress = 100
            task.actual_end_date = datetime.now().date()
            task.updated_by = current_user.id
            
            log_task_operation(
                db, task.id, "BATCH_COMPLETE", f"批量完成任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username
            )
            
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/transfer", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_transfer_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    target_user_id: int = Body(..., description="目标用户ID"),
    transfer_reason: str = Body(..., description="转办原因"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量转办任务
    """
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "已完成的任务不能转办"})
                continue
            
            task.assignee_id = target_user_id
            task.assignee_name = target_user.real_name or target_user.username
            task.is_transferred = True
            task.transfer_from_id = current_user.id
            task.transfer_from_name = current_user.real_name or current_user.username
            task.transfer_reason = transfer_reason
            task.transfer_time = datetime.now()
            task.status = "PENDING"
            task.updated_by = current_user.id
            
            log_task_operation(
                db, task.id, "BATCH_TRANSFER",
                f"批量转办任务：{task.title} -> {target_user.real_name or target_user.username}",
                current_user.id, current_user.real_name or current_user.username
            )
            
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/priority", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_set_priority(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    priority: str = Body(..., description="优先级：URGENT/HIGH/MEDIUM/LOW"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量设置优先级
    """
    if priority not in ["URGENT", "HIGH", "MEDIUM", "LOW"]:
        raise HTTPException(status_code=400, detail="无效的优先级")
    
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            old_priority = task.priority
            task.priority = priority
            task.updated_by = current_user.id
            
            log_task_operation(
                db, task.id, "BATCH_SET_PRIORITY",
                f"批量设置优先级：{old_priority} -> {priority}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"priority": old_priority},
                new_value={"priority": priority}
            )
            
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/progress", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_update_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    progress: int = Body(..., ge=0, le=100, description="进度百分比"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量更新进度
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            old_progress = task.progress
            task.progress = progress
            task.updated_by = current_user.id
            
            if progress >= 100 and task.status != "COMPLETED":
                task.status = "COMPLETED"
                task.actual_end_date = datetime.now().date()
            
            if progress > 0 and task.status == "ACCEPTED":
                task.status = "IN_PROGRESS"
                if not task.actual_start_date:
                    task.actual_start_date = datetime.now().date()
            
            log_task_operation(
                db, task.id, "BATCH_UPDATE_PROGRESS",
                f"批量更新进度：{old_progress}% -> {progress}%",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"progress": old_progress},
                new_value={"progress": progress}
            )
            
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/delete", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_delete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量删除任务（仅个人任务）
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id,
        TaskUnified.task_type == "PERSONAL"  # 只能删除个人任务
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            if task.task_type != "PERSONAL":
                failed_tasks.append({"task_id": task.id, "reason": "只能删除个人任务"})
                continue
            
            log_task_operation(
                db, task.id, "BATCH_DELETE", f"批量删除任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username
            )
            
            db.delete(task)
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/start", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_start_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量开始任务
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            if task.status in ["IN_PROGRESS", "COMPLETED"]:
                failed_tasks.append({"task_id": task.id, "reason": "任务已开始或已完成"})
                continue
            
            old_status = task.status
            task.status = "IN_PROGRESS"
            if not task.actual_start_date:
                task.actual_start_date = datetime.now().date()
            task.updated_by = current_user.id
            
            log_task_operation(
                db, task.id, "BATCH_START", f"批量开始任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"status": old_status},
                new_value={"status": "IN_PROGRESS"}
            )
            
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/pause", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_pause_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量暂停任务
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            if task.status != "IN_PROGRESS":
                failed_tasks.append({"task_id": task.id, "reason": "只能暂停进行中的任务"})
                continue
            
            old_status = task.status
            task.status = "PAUSED"
            task.updated_by = current_user.id
            
            log_task_operation(
                db, task.id, "BATCH_PAUSE", f"批量暂停任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"status": old_status},
                new_value={"status": "PAUSED"}
            )
            
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/tag", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_tag_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    tags: List[str] = Body(..., description="标签列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量打标签
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            old_tags = task.tags if task.tags else []
            # 合并标签（去重）
            new_tags = list(set((old_tags or []) + tags))
            task.tags = new_tags
            task.updated_by = current_user.id
            
            log_task_operation(
                db, task.id, "BATCH_TAG", f"批量打标签：{tags}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"tags": old_tags},
                new_value={"tags": new_tags}
            )
            
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/urge", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_urge_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    urge_message: Optional[str] = Body(None, description="催办消息"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量催办任务（发送催办通知）
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids)
    ).all()
    
    success_count = 0
    failed_tasks = []
    
    for task in tasks:
        try:
            if not task.assignee_id:
                failed_tasks.append({"task_id": task.id, "reason": "任务未分配负责人"})
                continue
            
            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "已完成的任务无需催办"})
                continue
            
            # 创建催办通知
            notification = Notification(
                user_id=task.assignee_id,
                notification_type="TASK_URGE",
                title=f"任务催办：{task.title}",
                content=urge_message or f"任务【{task.title}】需要尽快处理，请及时关注。",
                source_type="TASK",
                source_id=task.id,
                link_url=f"/task-center/tasks/{task.id}",
                priority="HIGH",
                extra_data={
                    "task_id": task.id,
                    "task_title": task.title,
                    "urge_by": current_user.real_name or current_user.username,
                    "urge_by_id": current_user.id
                }
            )
            db.add(notification)
            
            log_task_operation(
                db, task.id, "BATCH_URGE",
                f"批量催办任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username
            )
            
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})
    
    db.commit()
    
    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.get("/batch/statistics", response_model=BatchOperationStatistics, status_code=status.HTTP_200_OK)
def get_batch_operation_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量操作统计（操作历史）
    """
    query = db.query(TaskOperationLog).filter(
        TaskOperationLog.operator_id == current_user.id,
        TaskOperationLog.operation_type.like("BATCH_%")
    )
    
    if start_date:
        start_date_str = start_date.strftime("%Y-%m-%d")
        query = query.filter(func.date(TaskOperationLog.operation_time) >= start_date_str)
    if end_date:
        end_date_str = end_date.strftime("%Y-%m-%d")
        query = query.filter(func.date(TaskOperationLog.operation_time) <= end_date_str)
    
    logs = query.order_by(desc(TaskOperationLog.operation_time)).all()
    
    # 按操作类型统计
    by_operation_type = {}
    for log in logs:
        op_type = log.operation_type.replace("BATCH_", "")
        by_operation_type[op_type] = by_operation_type.get(op_type, 0) + 1
    
    # 按日期统计
    by_date = {}
    for log in logs:
        date_str = log.operation_time.date().isoformat()
        by_date[date_str] = by_date.get(date_str, 0) + 1
    
    # 最近操作
    recent_operations = []
    for log in logs[:20]:  # 最近20条
        recent_operations.append({
            "operation_type": log.operation_type,
            "operation_desc": log.operation_desc,
            "operation_time": log.operation_time.isoformat(),
            "task_id": log.task_id
        })
    
    return BatchOperationStatistics(
        total_operations=len(logs),
        by_operation_type=by_operation_type,
        by_date=by_date,
        recent_operations=recent_operations
    )

