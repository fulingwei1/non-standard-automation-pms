# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 项目任务管理
包含：任务CRUD、任务状态变更、任务依赖管理、负责人分配、进度日志
"""

from typing import Any, List, Optional
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User, Role, UserRole
from app.models.project import Project, Machine, ProjectMilestone
from app.models.progress import (
    WbsTemplate, WbsTemplateTask, Task, TaskDependency, ProgressLog
)
from app.schemas.progress import (
    TaskCreate, TaskUpdate, TaskProgressUpdate, TaskResponse, TaskListResponse,
    InitWbsRequest, InitWbsResponse,
    TaskDependencyCreate, TaskDependencyResponse,
    TaskAssigneeUpdate,
    ProgressLogResponse, ProgressLogListResponse,
)

router = APIRouter()


# ==================== 项目任务管理 ====================

@router.post("/projects/{project_id}/init-wbs", response_model=InitWbsResponse, status_code=status.HTTP_200_OK)
def init_wbs_from_template(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    init_request: InitWbsRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从WBS模板初始化项目任务计划
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证模板是否存在
    template = db.query(WbsTemplate).filter(WbsTemplate.id == init_request.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")

    # 检查项目是否已有任务
    existing_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    if existing_tasks > 0:
        raise HTTPException(status_code=400, detail="项目已存在任务，无法从模板初始化")

    # 获取模板任务
    template_tasks = db.query(WbsTemplateTask).filter(
        WbsTemplateTask.template_id == init_request.template_id
    ).order_by(WbsTemplateTask.id).all()

    if not template_tasks:
        raise HTTPException(status_code=400, detail="模板中没有任务")

    # 确定开始日期
    start_date = init_request.start_date or project.start_date or date.today()
    current_date = start_date

    # 创建任务映射（用于处理依赖关系）
    task_map = {}  # template_task_id -> project_task_id

    # 创建项目任务
    created_tasks = []
    for template_task in template_tasks:
        # 计算计划日期
        plan_start = current_date
        plan_end = current_date + timedelta(days=template_task.plan_days or 1) if template_task.plan_days else current_date

        # 创建任务
        task = Task(
            project_id=project_id,
            task_name=template_task.task_name,
            stage=template_task.stage,
            plan_start=plan_start,
            plan_end=plan_end,
            weight=template_task.weight,
            status="TODO"
        )

        # 如果启用自动分配负责人，根据角色查找用户并分配
        if init_request.assign_owners and template_task.default_owner_role:
            # 根据角色编码查找角色
            role = db.query(Role).filter(
                Role.role_code == template_task.default_owner_role,
                Role.is_active == True
            ).first()

            if role:
                # 查找拥有该角色的活跃用户（取第一个）
                user_role = db.query(UserRole).filter(
                    UserRole.role_id == role.id
                ).join(User).filter(
                    User.is_active == True
                ).first()

                if user_role:
                    task.owner_id = user_role.user_id

        db.add(task)
        db.flush()  # 获取task.id

        task_map[template_task.id] = task.id
        created_tasks.append(task)

        # 更新当前日期（简单处理，实际应该考虑依赖关系）
        if template_task.plan_days:
            current_date = plan_end + timedelta(days=1)

    # 创建任务依赖关系
    for template_task in template_tasks:
        if template_task.depends_on_template_task_id:
            task_id = task_map.get(template_task.id)
            depends_on_task_id = task_map.get(template_task.depends_on_template_task_id)

            if task_id and depends_on_task_id:
                dependency = TaskDependency(
                    task_id=task_id,
                    depends_on_task_id=depends_on_task_id,
                    dependency_type="FS"
                )
                db.add(dependency)

    db.commit()

    return InitWbsResponse(
        message=f"成功从模板创建 {len(created_tasks)} 个任务",
        data={"task_count": len(created_tasks)}
    )


@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse, status_code=status.HTTP_200_OK)
def read_project_tasks(
    project_id: int,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    milestone_id: Optional[int] = Query(None, description="里程碑ID筛选"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目任务列表
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(Task).filter(Task.project_id == project_id)

    # 机台筛选
    if machine_id:
        query = query.filter(Task.machine_id == machine_id)

    # 里程碑筛选
    if milestone_id:
        query = query.filter(Task.milestone_id == milestone_id)

    # 阶段筛选
    if stage:
        query = query.filter(Task.stage == stage)

    # 状态筛选
    if status_filter:
        query = query.filter(Task.status == status_filter)

    # 负责人筛选
    if owner_id:
        query = query.filter(Task.owner_id == owner_id)

    # 计算总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    tasks = query.order_by(Task.plan_start.asc(), Task.id.asc()).offset(offset).limit(page_size).all()

    return TaskListResponse(
        items=tasks,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_project_task(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    task_in: TaskCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目任务
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证机台（如果提供）
    if task_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == task_in.machine_id).first()
        if not machine or machine.project_id != project_id:
            raise HTTPException(status_code=400, detail="机台不存在或不属于该项目")

    # 验证里程碑（如果提供）
    if task_in.milestone_id:
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == task_in.milestone_id).first()
        if not milestone or milestone.project_id != project_id:
            raise HTTPException(status_code=400, detail="里程碑不存在或不属于该项目")

    task = Task(project_id=project_id, status="TODO", **task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def read_task(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务详情
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    task_in: TaskUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = task_in.model_dump(exclude_unset=True)

    # 如果更新状态为IN_PROGRESS且actual_start为空，自动设置
    if update_data.get("status") == "IN_PROGRESS" and not task.actual_start:
        update_data["actual_start"] = date.today()

    # 如果更新状态为DONE且actual_end为空，自动设置
    if update_data.get("status") == "DONE" and not task.actual_end:
        update_data["actual_end"] = date.today()
        if "progress_percent" not in update_data:
            update_data["progress_percent"] = 100

    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.put("/tasks/{task_id}/progress", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    progress_in: TaskProgressUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新任务进度（级联更新里程碑和项目进度）
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    old_progress = task.progress_percent

    # 禁止进度回退（除非是管理员或项目经理）
    if progress_in.progress_percent < old_progress and not current_user.is_superuser:
        # 检查是否是项目经理
        is_pm = False
        if task.project_id:
            project = db.query(Project).filter(Project.id == task.project_id).first()
            if project and project.pm_id == current_user.id:
                is_pm = True

        if not is_pm:
            raise HTTPException(
                status_code=400,
                detail=f"不允许进度回退（{old_progress}% → {progress_in.progress_percent}%），请联系项目经理审批"
            )

    # 更新任务进度
    task.progress_percent = progress_in.progress_percent

    # 如果进度达到100%，自动设置为完成状态
    if progress_in.progress_percent >= 100:
        task.status = "DONE"
        if not task.actual_end:
            task.actual_end = date.today()

    # 如果进度大于0且状态为TODO，自动设置为进行中
    elif progress_in.progress_percent > 0 and task.status == "TODO":
        task.status = "IN_PROGRESS"
        if not task.actual_start:
            task.actual_start = date.today()

    db.add(task)

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=progress_in.progress_percent,
        update_note=progress_in.update_note or f"进度更新：{old_progress}% → {progress_in.progress_percent}%",
        updated_by=current_user.id
    )
    db.add(progress_log)

    # 级联更新里程碑进度
    if task.milestone_id:
        milestone = db.query(ProjectMilestone).filter(ProjectMilestone.id == task.milestone_id).first()
        if milestone:
            # 获取里程碑下的所有任务
            milestone_tasks = db.query(Task).filter(
                Task.milestone_id == task.milestone_id,
                Task.status != "CANCELLED"
            ).all()

            if milestone_tasks:
                # 按权重加权计算里程碑进度
                total_weight = sum(float(t.weight) for t in milestone_tasks)
                weighted_progress = sum(float(t.progress_percent) * float(t.weight) for t in milestone_tasks)
                milestone_progress = int(weighted_progress / total_weight) if total_weight > 0 else 0

                # 更新里程碑进度（如果里程碑有progress字段）
                if hasattr(milestone, 'progress'):
                    milestone.progress = milestone_progress
                    db.add(milestone)

                # 如果所有任务完成，检查里程碑完成条件（验收联动）
                all_done = all(t.status == "DONE" for t in milestone_tasks)
                if all_done and milestone.status != "COMPLETED":
                    # 检查验收和交付物要求
                    try:
                        from app.services.progress_integration_service import ProgressIntegrationService
                        integration_service = ProgressIntegrationService(db)
                        can_complete, missing_items = integration_service.check_milestone_completion_requirements(milestone)

                        if can_complete:
                            milestone.status = "COMPLETED"
                            if not milestone.actual_date:
                                milestone.actual_date = date.today()
                            db.add(milestone)
                        else:
                            # 不满足完成条件，保持当前状态并记录原因
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"里程碑 {milestone.milestone_name} 不满足完成条件: {', '.join(missing_items)}")
                    except Exception as e:
                        # 检查失败时，默认允许完成（向后兼容）
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"检查里程碑完成条件失败: {str(e)}", exc_info=True)
                        milestone.status = "COMPLETED"
                        if not milestone.actual_date:
                            milestone.actual_date = date.today()
                        db.add(milestone)

    # 级联更新项目进度（通过进度汇总服务自动更新，这里不重复计算）
    # 项目进度会在定时任务中自动计算

    db.commit()
    db.refresh(task)

    return task


@router.put("/tasks/{task_id}/complete", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def complete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = "DONE"
    task.progress_percent = 100
    if not task.actual_end:
        task.actual_end = date.today()
    if not task.actual_start:
        task.actual_start = task.plan_start or date.today()

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=100,
        update_note="任务完成",
        updated_by=current_user.id
    )
    db.add(progress_log)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.put("/tasks/{task_id}/block", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def block_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    block_reason: str = Query(..., description="阻塞原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阻塞任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = "BLOCKED"
    task.block_reason = block_reason

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=task.progress_percent,
        update_note=f"任务阻塞：{block_reason}",
        updated_by=current_user.id
    )
    db.add(progress_log)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.put("/tasks/{task_id}/unblock", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def unblock_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    解除任务阻塞
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "BLOCKED":
        raise HTTPException(status_code=400, detail="任务当前不是阻塞状态")

    # 根据进度恢复状态
    if task.progress_percent >= 100:
        task.status = "DONE"
    elif task.progress_percent > 0:
        task.status = "IN_PROGRESS"
    else:
        task.status = "TODO"

    task.block_reason = None

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=task.progress_percent,
        update_note="任务解除阻塞",
        updated_by=current_user.id
    )
    db.add(progress_log)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.put("/tasks/{task_id}/cancel", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def cancel_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    cancel_reason: Optional[str] = Query(None, description="取消原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "DONE":
        raise HTTPException(status_code=400, detail="已完成的任务不能取消")

    task.status = "CANCELLED"
    if cancel_reason:
        task.block_reason = cancel_reason

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=task.progress_percent,
        update_note=f"任务取消：{cancel_reason or '无原因'}",
        updated_by=current_user.id
    )
    db.add(progress_log)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除任务（软删除，仅管理员）
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 权限检查：仅管理员可以删除
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除任务，仅管理员可操作")

    # 检查是否有依赖此任务的其他任务
    dependent_tasks = db.query(TaskDependency).filter(
        TaskDependency.depends_on_task_id == task_id
    ).count()

    if dependent_tasks > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除任务，有 {dependent_tasks} 个任务依赖此任务"
        )

    # 删除任务及其关联数据（依赖关系、进度日志等会通过cascade自动删除）
    db.delete(task)
    db.commit()

    return {"message": "任务已删除", "id": task_id}


@router.get("/tasks/{task_id}/logs", response_model=ProgressLogListResponse, status_code=status.HTTP_200_OK)
def get_task_progress_logs(
    task_id: int,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务进度日志
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    query = db.query(ProgressLog).filter(ProgressLog.task_id == task_id)

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(ProgressLog.updated_at.desc()).offset(offset).limit(page_size).all()

    # 补充更新人姓名
    items = []
    for log in logs:
        updater_name = None
        if log.updated_by:
            updater = db.query(User).filter(User.id == log.updated_by).first()
            updater_name = updater.real_name or updater.username if updater else None

        items.append(ProgressLogResponse(
            id=log.id,
            task_id=log.task_id,
            progress_percent=log.progress_percent,
            update_note=log.update_note,
            updated_by=log.updated_by,
            updated_by_name=updater_name,
            updated_at=log.updated_at
        ))

    return ProgressLogListResponse(
        items=items,
        total=total
    )


# ==================== 任务依赖管理 ====================

@router.get("/tasks/{task_id}/dependencies", response_model=List[TaskDependencyResponse], status_code=status.HTTP_200_OK)
def read_task_dependencies(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务依赖关系（前置任务）
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    dependencies = db.query(TaskDependency).filter(TaskDependency.task_id == task_id).all()

    # 补充依赖任务名称
    result = []
    for dep in dependencies:
        depends_task = db.query(Task).filter(Task.id == dep.depends_on_task_id).first()
        dep_dict = {
            "id": dep.id,
            "task_id": dep.task_id,
            "depends_on_task_id": dep.depends_on_task_id,
            "dependency_type": dep.dependency_type,
            "lag_days": dep.lag_days,
            "depends_on_task_name": depends_task.task_name if depends_task else None
        }
        result.append(dep_dict)

    return result


@router.post("/tasks/{task_id}/dependencies", response_model=TaskDependencyResponse, status_code=status.HTTP_201_CREATED)
def create_task_dependency(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    dependency_in: TaskDependencyCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    设置任务依赖关系
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证依赖的任务是否存在且属于同一项目
    depends_task = db.query(Task).filter(Task.id == dependency_in.depends_on_task_id).first()
    if not depends_task:
        raise HTTPException(status_code=404, detail="依赖的任务不存在")

    if depends_task.project_id != task.project_id:
        raise HTTPException(status_code=400, detail="依赖的任务必须属于同一项目")

    # 检查是否已存在该依赖
    existing = db.query(TaskDependency).filter(
        TaskDependency.task_id == task_id,
        TaskDependency.depends_on_task_id == dependency_in.depends_on_task_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该依赖关系已存在")

    # 检查循环依赖
    if dependency_in.depends_on_task_id == task_id:
        raise HTTPException(status_code=400, detail="任务不能依赖自身")

    dependency = TaskDependency(
        task_id=task_id,
        depends_on_task_id=dependency_in.depends_on_task_id,
        dependency_type=dependency_in.dependency_type,
        lag_days=dependency_in.lag_days
    )
    db.add(dependency)
    db.commit()
    db.refresh(dependency)

    # 补充依赖任务名称
    dependency_dict = {
        "id": dependency.id,
        "task_id": dependency.task_id,
        "depends_on_task_id": dependency.depends_on_task_id,
        "dependency_type": dependency.dependency_type,
        "lag_days": dependency.lag_days,
        "depends_on_task_name": depends_task.task_name
    }

    return dependency_dict


@router.delete("/task-dependencies/{dependency_id}", status_code=status.HTTP_200_OK)
def delete_task_dependency(
    *,
    db: Session = Depends(deps.get_db),
    dependency_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除任务依赖关系
    """
    dependency = db.query(TaskDependency).filter(TaskDependency.id == dependency_id).first()
    if not dependency:
        raise HTTPException(status_code=404, detail="依赖关系不存在")

    db.delete(dependency)
    db.commit()

    return {"message": "依赖关系已删除", "id": dependency_id}


@router.put("/tasks/{task_id}/assignee", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def assign_task_owner(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    assignee_in: TaskAssigneeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分配任务负责人
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证用户是否存在
    owner = db.query(User).filter(User.id == assignee_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="用户不存在")

    task.owner_id = assignee_in.owner_id
    db.add(task)
    db.commit()
    db.refresh(task)

    return task
