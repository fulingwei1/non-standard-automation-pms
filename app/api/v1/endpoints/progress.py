# -*- coding: utf-8 -*-
"""
进度跟踪 API endpoints
包含：WBS模板管理、项目任务管理
"""

from typing import Any, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.organization import Department
from app.models.project import Project, Machine, ProjectMilestone
from sqlalchemy import func, case
from app.models.progress import (
    WbsTemplate, WbsTemplateTask, Task, TaskDependency, ProgressLog,
    ScheduleBaseline, BaselineTask, ProgressReport
)
from app.schemas.progress import (
    WbsTemplateCreate, WbsTemplateUpdate, WbsTemplateResponse, WbsTemplateListResponse,
    WbsTemplateTaskCreate, WbsTemplateTaskUpdate, WbsTemplateTaskResponse,
    TaskCreate, TaskUpdate, TaskProgressUpdate, TaskResponse, TaskListResponse,
    InitWbsRequest, InitWbsResponse,
    ProgressReportCreate, ProgressReportUpdate, ProgressReportResponse, ProgressReportListResponse,
    ProgressSummaryResponse, MachineProgressSummaryResponse,
    GanttDataResponse, GanttTaskItem,
    ProgressBoardResponse, ProgressBoardColumn,
    TaskDependencyCreate, TaskDependencyResponse,
    TaskAssigneeUpdate,
    MilestoneRateResponse, DelayReasonsResponse, DelayReasonItem,
    BaselineCreate, BaselineResponse, BaselineListResponse,
    ProgressLogResponse, ProgressLogListResponse,
    BatchTaskProgressUpdate, BatchTaskAssigneeUpdate
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


# ==================== WBS 模板管理 ====================

@router.get("/wbs-templates", response_model=WbsTemplateListResponse, status_code=status.HTTP_200_OK)
def read_wbs_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（模板编码/名称）"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取WBS模板列表（支持分页和筛选）
    """
    query = db.query(WbsTemplate)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                WbsTemplate.template_code.like(f"%{keyword}%"),
                WbsTemplate.template_name.like(f"%{keyword}%"),
            )
        )
    
    # 项目类型筛选
    if project_type:
        query = query.filter(WbsTemplate.project_type == project_type)
    
    # 设备类型筛选
    if equipment_type:
        query = query.filter(WbsTemplate.equipment_type == equipment_type)
    
    # 启用状态筛选
    if is_active is not None:
        query = query.filter(WbsTemplate.is_active == is_active)
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    templates = query.order_by(WbsTemplate.created_at.desc()).offset(offset).limit(page_size).all()
    
    return WbsTemplateListResponse(
        items=templates,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/wbs-templates/{template_id}", response_model=WbsTemplateResponse, status_code=status.HTTP_200_OK)
def read_wbs_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取WBS模板详情
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")
    
    return template


@router.post("/wbs-templates", response_model=WbsTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_wbs_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: WbsTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建WBS模板
    """
    # 检查模板编码是否已存在
    existing = db.query(WbsTemplate).filter(WbsTemplate.template_code == template_in.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")
    
    template = WbsTemplate(**template_in.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.put("/wbs-templates/{template_id}", response_model=WbsTemplateResponse, status_code=status.HTTP_200_OK)
def update_wbs_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: WbsTemplateUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新WBS模板
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")
    
    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return template


@router.get("/wbs-templates/{template_id}/tasks", response_model=List[WbsTemplateTaskResponse], status_code=status.HTTP_200_OK)
def read_wbs_template_tasks(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取WBS模板任务列表
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")
    
    tasks = db.query(WbsTemplateTask).filter(WbsTemplateTask.template_id == template_id).order_by(WbsTemplateTask.id).all()
    
    return tasks


@router.post("/wbs-templates/{template_id}/tasks", response_model=WbsTemplateTaskResponse, status_code=status.HTTP_201_CREATED)
def create_wbs_template_task(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    task_in: WbsTemplateTaskCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加WBS模板任务
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")
    
    # 验证依赖任务是否存在
    if task_in.depends_on_template_task_id:
        depends_task = db.query(WbsTemplateTask).filter(
            WbsTemplateTask.id == task_in.depends_on_template_task_id,
            WbsTemplateTask.template_id == template_id
        ).first()
        if not depends_task:
            raise HTTPException(status_code=400, detail="依赖的模板任务不存在")
    
    task = WbsTemplateTask(template_id=template_id, **task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.put("/wbs-template-tasks/{task_id}", response_model=WbsTemplateTaskResponse, status_code=status.HTTP_200_OK)
def update_wbs_template_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    task_in: WbsTemplateTaskUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新WBS模板任务
    """
    task = db.query(WbsTemplateTask).filter(WbsTemplateTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="模板任务不存在")
    
    update_data = task_in.model_dump(exclude_unset=True)
    
    # 验证依赖任务
    if "depends_on_template_task_id" in update_data and update_data["depends_on_template_task_id"]:
        depends_task = db.query(WbsTemplateTask).filter(
            WbsTemplateTask.id == update_data["depends_on_template_task_id"],
            WbsTemplateTask.template_id == task.template_id
        ).first()
        if not depends_task:
            raise HTTPException(status_code=400, detail="依赖的模板任务不存在")
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/wbs-template-tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_wbs_template_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除WBS模板任务
    """
    task = db.query(WbsTemplateTask).filter(WbsTemplateTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="模板任务不存在")
    
    # 检查是否有其他任务依赖此任务
    dependent_tasks = db.query(WbsTemplateTask).filter(
        WbsTemplateTask.depends_on_template_task_id == task_id
    ).count()
    
    if dependent_tasks > 0:
        raise HTTPException(
            status_code=400,
            detail=f"无法删除任务，有 {dependent_tasks} 个任务依赖此任务"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "模板任务已删除", "id": task_id}


@router.delete("/wbs-templates/{template_id}", status_code=status.HTTP_200_OK)
def delete_wbs_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除WBS模板
    """
    template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")
    
    # 检查是否有项目使用此模板（通过检查是否有任务关联此模板）
    # 这里简化处理，实际应该检查项目是否从该模板初始化
    # 暂时允许删除，因为模板任务会通过cascade自动删除
    
    db.delete(template)
    db.commit()
    
    return {"message": "WBS模板已删除", "id": template_id}


@router.post("/wbs-templates/{template_id}/copy", response_model=WbsTemplateResponse, status_code=status.HTTP_201_CREATED)
def copy_wbs_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    new_template_code: str = Query(..., description="新模板编码"),
    new_template_name: Optional[str] = Query(None, description="新模板名称"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    复制WBS模板
    """
    # 获取原模板
    original_template = db.query(WbsTemplate).filter(WbsTemplate.id == template_id).first()
    if not original_template:
        raise HTTPException(status_code=404, detail="WBS模板不存在")
    
    # 检查新模板编码是否已存在
    existing = db.query(WbsTemplate).filter(WbsTemplate.template_code == new_template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")
    
    # 创建新模板
    new_template = WbsTemplate(
        template_code=new_template_code,
        template_name=new_template_name or f"{original_template.template_name} (副本)",
        project_type=original_template.project_type,
        equipment_type=original_template.equipment_type,
        version_no="V1",
        is_active=original_template.is_active
    )
    db.add(new_template)
    db.flush()  # 获取new_template.id
    
    # 复制模板任务
    original_tasks = db.query(WbsTemplateTask).filter(
        WbsTemplateTask.template_id == template_id
    ).all()
    
    task_map = {}  # 原任务ID -> 新任务ID
    for original_task in original_tasks:
        new_task = WbsTemplateTask(
            template_id=new_template.id,
            task_name=original_task.task_name,
            stage=original_task.stage,
            default_owner_role=original_task.default_owner_role,
            plan_days=original_task.plan_days,
            weight=original_task.weight,
            depends_on_template_task_id=None  # 稍后更新
        )
        db.add(new_task)
        db.flush()  # 获取new_task.id
        task_map[original_task.id] = new_task.id
    
    # 更新依赖关系
    for original_task in original_tasks:
        if original_task.depends_on_template_task_id:
            new_task_id = task_map.get(original_task.id)
            new_depends_id = task_map.get(original_task.depends_on_template_task_id)
            if new_task_id and new_depends_id:
                new_task = db.query(WbsTemplateTask).filter(WbsTemplateTask.id == new_task_id).first()
                if new_task:
                    new_task.depends_on_template_task_id = new_depends_id
    
    db.commit()
    db.refresh(new_template)
    
    return new_template


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
        
        # 如果启用自动分配负责人，根据角色分配（这里简化处理，实际需要根据角色查找用户）
        if init_request.assign_owners and template_task.default_owner_role:
            # TODO: 根据角色查找用户并分配
            pass
        
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
    status: Optional[str] = Query(None, description="状态筛选"),
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
    if status:
        query = query.filter(Task.status == status)
    
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
                
                # 如果所有任务完成，自动完成里程碑
                all_done = all(t.status == "DONE" for t in milestone_tasks)
                if all_done and milestone.status != "COMPLETED":
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


# ==================== 进度填报 ====================

@router.post("/progress-reports", response_model=ProgressReportResponse, status_code=status.HTTP_201_CREATED)
def create_progress_report(
    *,
    db: Session = Depends(deps.get_db),
    report_in: ProgressReportCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交进度报告（日报/周报）
    """
    # 验证至少指定一个关联对象
    if not report_in.project_id and not report_in.machine_id and not report_in.task_id:
        raise HTTPException(status_code=400, detail="必须指定项目ID、机台ID或任务ID中的至少一个")
    
    # 验证项目是否存在
    if report_in.project_id:
        project = db.query(Project).filter(Project.id == report_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    # 验证机台是否存在
    if report_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == report_in.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")
        # 如果同时指定了项目ID，验证机台属于该项目
        if report_in.project_id and machine.project_id != report_in.project_id:
            raise HTTPException(status_code=400, detail="机台不属于指定的项目")
    
    # 验证任务是否存在
    if report_in.task_id:
        task = db.query(Task).filter(Task.id == report_in.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        # 如果同时指定了项目ID，验证任务属于该项目
        if report_in.project_id and task.project_id != report_in.project_id:
            raise HTTPException(status_code=400, detail="任务不属于指定的项目")
        # 如果同时指定了机台ID，验证任务属于该机台
        if report_in.machine_id and task.machine_id != report_in.machine_id:
            raise HTTPException(status_code=400, detail="任务不属于指定的机台")
    
    # 创建进度报告
    progress_report = ProgressReport(
        report_type=report_in.report_type,
        report_date=report_in.report_date,
        project_id=report_in.project_id,
        machine_id=report_in.machine_id,
        task_id=report_in.task_id,
        content=report_in.content,
        completed_work=report_in.completed_work,
        planned_work=report_in.planned_work,
        issues=report_in.issues,
        next_plan=report_in.next_plan,
        created_by=current_user.id
    )
    
    db.add(progress_report)
    db.commit()
    db.refresh(progress_report)
    
    return progress_report


@router.get("/progress-reports", response_model=ProgressReportListResponse, status_code=status.HTTP_200_OK)
def read_progress_reports(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    task_id: Optional[int] = Query(None, description="任务ID筛选"),
    report_type: Optional[str] = Query(None, description="报告类型筛选（daily/weekly）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取进度报告列表
    """
    query = db.query(ProgressReport)
    
    # 项目筛选
    if project_id:
        query = query.filter(ProgressReport.project_id == project_id)
    
    # 机台筛选
    if machine_id:
        query = query.filter(ProgressReport.machine_id == machine_id)
    
    # 任务筛选
    if task_id:
        query = query.filter(ProgressReport.task_id == task_id)
    
    # 报告类型筛选
    if report_type:
        query = query.filter(ProgressReport.report_type == report_type)
    
    # 日期范围筛选
    if start_date:
        query = query.filter(ProgressReport.report_date >= start_date)
    if end_date:
        query = query.filter(ProgressReport.report_date <= end_date)
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    reports = query.order_by(ProgressReport.report_date.desc(), ProgressReport.created_at.desc()).offset(offset).limit(page_size).all()
    
    return ProgressReportListResponse(
        items=reports,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 进度汇总 ====================

@router.get("/projects/{project_id}/progress-summary", response_model=ProgressSummaryResponse, status_code=status.HTTP_200_OK)
def get_project_progress_summary(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目进度汇总
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有任务
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    if not tasks:
        return ProgressSummaryResponse(
            project_id=project_id,
            project_name=project.project_name,
            overall_progress=0.0,
            stage_progress={},
            task_count=0,
            completed_count=0,
            in_progress_count=0,
            blocked_count=0,
            overdue_count=0
        )
    
    # 计算整体进度（按权重加权平均）
    total_weight = sum(float(task.weight) for task in tasks)
    weighted_progress = sum(float(task.weight) * task.progress_percent for task in tasks)
    overall_progress = (weighted_progress / total_weight) if total_weight > 0 else 0.0
    
    # 按阶段统计进度
    stage_progress = {}
    for stage in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"]:
        stage_tasks = [t for t in tasks if t.stage == stage]
        if stage_tasks:
            stage_weight = sum(float(t.weight) for t in stage_tasks)
            stage_weighted = sum(float(t.weight) * t.progress_percent for t in stage_tasks)
            stage_progress[stage] = (stage_weighted / stage_weight) if stage_weight > 0 else 0.0
    
    # 统计任务状态
    task_count = len(tasks)
    completed_count = len([t for t in tasks if t.status == "DONE"])
    in_progress_count = len([t for t in tasks if t.status == "IN_PROGRESS"])
    blocked_count = len([t for t in tasks if t.status == "BLOCKED"])
    
    # 统计逾期任务
    today = date.today()
    overdue_count = len([t for t in tasks if t.plan_end and t.plan_end < today and t.status != "DONE"])
    
    # 计算延期天数（取最晚的逾期天数）
    delay_days = None
    if overdue_count > 0:
        max_delay = 0
        for task in tasks:
            if task.plan_end and task.plan_end < today and task.status != "DONE":
                delay = (today - task.plan_end).days
                max_delay = max(max_delay, delay)
        delay_days = max_delay if max_delay > 0 else None
    
    return ProgressSummaryResponse(
        project_id=project_id,
        project_name=project.project_name,
        overall_progress=round(overall_progress, 2),
        stage_progress=stage_progress,
        task_count=task_count,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        blocked_count=blocked_count,
        overdue_count=overdue_count,
        delay_days=delay_days
    )


@router.get("/machines/{machine_id}/progress-summary", response_model=MachineProgressSummaryResponse, status_code=status.HTTP_200_OK)
def get_machine_progress_summary(
    machine_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取机台进度汇总
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")
    
    # 获取机台的所有任务
    tasks = db.query(Task).filter(Task.machine_id == machine_id).all()
    
    if not tasks:
        return MachineProgressSummaryResponse(
            machine_id=machine_id,
            machine_name=machine.machine_name,
            machine_code=machine.machine_code,
            overall_progress=0.0,
            task_count=0,
            completed_count=0,
            in_progress_count=0,
            blocked_count=0
        )
    
    # 计算整体进度
    total_weight = sum(float(task.weight) for task in tasks)
    weighted_progress = sum(float(task.weight) * task.progress_percent for task in tasks)
    overall_progress = (weighted_progress / total_weight) if total_weight > 0 else 0.0
    
    # 统计任务状态
    task_count = len(tasks)
    completed_count = len([t for t in tasks if t.status == "DONE"])
    in_progress_count = len([t for t in tasks if t.status == "IN_PROGRESS"])
    blocked_count = len([t for t in tasks if t.status == "BLOCKED"])
    
    return MachineProgressSummaryResponse(
        machine_id=machine_id,
        machine_name=machine.machine_name,
        machine_code=machine.machine_code,
        overall_progress=round(overall_progress, 2),
        task_count=task_count,
        completed_count=completed_count,
        in_progress_count=in_progress_count,
        blocked_count=blocked_count
    )


# ==================== 甘特图数据 ====================

@router.get("/projects/{project_id}/gantt", response_model=GanttDataResponse, status_code=status.HTTP_200_OK)
def get_gantt_data(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目甘特图数据
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有任务
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    # 获取所有依赖关系
    task_ids = [t.id for t in tasks]
    dependencies = db.query(TaskDependency).filter(TaskDependency.task_id.in_(task_ids)).all()
    dep_map = {}  # task_id -> [depends_on_task_ids]
    for dep in dependencies:
        if dep.task_id not in dep_map:
            dep_map[dep.task_id] = []
        dep_map[dep.task_id].append(dep.depends_on_task_id)
    
    # 构建甘特图任务项
    gantt_tasks = []
    for task in tasks:
        # 获取负责人名称
        owner_name = None
        if task.owner_id:
            owner = db.query(User).filter(User.id == task.owner_id).first()
            owner_name = owner.real_name or owner.username if owner else None
        
        gantt_task = GanttTaskItem(
            id=task.id,
            name=task.task_name,
            start=task.plan_start or date.today(),
            end=task.plan_end or date.today(),
            progress=task.progress_percent,
            status=task.status,
            dependencies=dep_map.get(task.id, []),
            owner=owner_name
        )
        gantt_tasks.append(gantt_task)
    
    return GanttDataResponse(
        project_id=project_id,
        project_name=project.project_name,
        tasks=gantt_tasks
    )


# ==================== 进度看板 ====================

@router.get("/projects/{project_id}/progress-board", response_model=ProgressBoardResponse, status_code=status.HTTP_200_OK)
def get_progress_board(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目进度看板数据
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有任务
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    # 按状态分组
    status_groups = {
        "TODO": [],
        "IN_PROGRESS": [],
        "BLOCKED": [],
        "DONE": [],
        "CANCELLED": []
    }
    
    for task in tasks:
        status = task.status or "TODO"
        if status in status_groups:
            status_groups[status].append(task)
    
    # 构建看板列
    columns = []
    status_names = {
        "TODO": "待办",
        "IN_PROGRESS": "进行中",
        "BLOCKED": "阻塞",
        "DONE": "已完成",
        "CANCELLED": "已取消"
    }
    
    for status, status_name in status_names.items():
        columns.append(ProgressBoardColumn(
            status=status,
            status_name=status_name,
            tasks=status_groups[status]
        ))
    
    # 汇总统计
    summary = {
        "total": len(tasks),
        "todo": len(status_groups["TODO"]),
        "in_progress": len(status_groups["IN_PROGRESS"]),
        "blocked": len(status_groups["BLOCKED"]),
        "done": len(status_groups["DONE"]),
        "cancelled": len(status_groups["CANCELLED"])
    }
    
    return ProgressBoardResponse(
        project_id=project_id,
        project_name=project.project_name,
        columns=columns,
        summary=summary
    )


# ==================== 进度报告详情 ====================

@router.get("/progress-reports/{report_id}", response_model=ProgressReportResponse, status_code=status.HTTP_200_OK)
def read_progress_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取进度报告详情
    """
    progress_report = db.query(ProgressReport).filter(ProgressReport.id == report_id).first()
    if not progress_report:
        raise HTTPException(status_code=404, detail="进度报告不存在")
    
    return progress_report


@router.put("/progress-reports/{report_id}", response_model=ProgressReportResponse, status_code=status.HTTP_200_OK)
def update_progress_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    report_in: ProgressReportUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新进度报告
    """
    progress_report = db.query(ProgressReport).filter(ProgressReport.id == report_id).first()
    if not progress_report:
        raise HTTPException(status_code=404, detail="进度报告不存在")
    
    # 权限检查：只能更新自己创建的报告（或管理员）
    if progress_report.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权更新此进度报告")
    
    update_data = report_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(progress_report, field, value)
    
    db.add(progress_report)
    db.commit()
    db.refresh(progress_report)
    
    return progress_report


@router.delete("/progress-reports/{report_id}", status_code=status.HTTP_200_OK)
def delete_progress_report(
    *,
    db: Session = Depends(deps.get_db),
    report_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除进度报告
    """
    progress_report = db.query(ProgressReport).filter(ProgressReport.id == report_id).first()
    if not progress_report:
        raise HTTPException(status_code=404, detail="进度报告不存在")
    
    # 权限检查：只能删除自己创建的报告（或管理员）
    if progress_report.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="无权删除此进度报告")
    
    db.delete(progress_report)
    db.commit()
    
    return {"message": "进度报告已删除", "id": report_id}


# ==================== 进度报告统计 ====================

@router.get("/progress-reports/statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_progress_report_statistics(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取进度报告统计信息
    """
    query = db.query(ProgressReport)
    
    # 筛选条件
    if project_id:
        query = query.filter(ProgressReport.project_id == project_id)
    if machine_id:
        query = query.filter(ProgressReport.machine_id == machine_id)
    if start_date:
        query = query.filter(ProgressReport.report_date >= start_date)
    if end_date:
        query = query.filter(ProgressReport.report_date <= end_date)
    
    reports = query.all()
    
    # 统计
    total_reports = len(reports)
    daily_reports = len([r for r in reports if r.report_type == "daily"])
    weekly_reports = len([r for r in reports if r.report_type == "weekly"])
    
    # 按创建人统计
    creator_stats = {}
    for report in reports:
        creator_id = report.created_by
        if creator_id not in creator_stats:
            creator = db.query(User).filter(User.id == creator_id).first()
            creator_stats[creator_id] = {
                "user_id": creator_id,
                "user_name": creator.real_name or creator.username if creator else "未知",
                "count": 0
            }
        creator_stats[creator_id]["count"] += 1
    
    # 按日期统计（最近30天）
    from datetime import timedelta
    today = date.today()
    date_stats = {}
    for i in range(30):
        check_date = today - timedelta(days=i)
        date_stats[check_date.isoformat()] = len([
            r for r in reports 
            if r.report_date == check_date
        ])
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_reports": total_reports,
            "daily_reports": daily_reports,
            "weekly_reports": weekly_reports,
            "by_creator": list(creator_stats.values()),
            "by_date": date_stats,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
    )


# ==================== 批量操作 ====================

@router.post("/tasks/batch/progress", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    batch_in: BatchTaskProgressUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新任务进度
    """
    if not batch_in.task_ids:
        raise HTTPException(status_code=400, detail="任务ID列表不能为空")
    
    if len(batch_in.task_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多更新50个任务")
    
    # 验证所有任务是否存在
    tasks = db.query(Task).filter(Task.id.in_(batch_in.task_ids)).all()
    if len(tasks) != len(batch_in.task_ids):
        raise HTTPException(status_code=404, detail="部分任务不存在")
    
    updated_count = 0
    updated_tasks = []
    
    for task in tasks:
        old_progress = task.progress_percent
        task.progress_percent = batch_in.progress_percent
        
        # 如果进度达到100%，自动设置为完成状态
        if batch_in.progress_percent >= 100:
            task.status = "DONE"
            if not task.actual_end:
                task.actual_end = date.today()
        
        # 如果进度大于0且状态为TODO，自动设置为进行中
        elif batch_in.progress_percent > 0 and task.status == "TODO":
            task.status = "IN_PROGRESS"
            if not task.actual_start:
                task.actual_start = date.today()
        
        db.add(task)
        
        # 创建进度日志
        progress_log = ProgressLog(
            task_id=task.id,
            progress_percent=batch_in.progress_percent,
            update_note=batch_in.update_note or f"批量更新进度：{old_progress}% → {batch_in.progress_percent}%",
            updated_by=current_user.id
        )
        db.add(progress_log)
        
        updated_tasks.append({
            "task_id": task.id,
            "task_name": task.task_name,
            "old_progress": old_progress,
            "new_progress": batch_in.progress_percent
        })
        updated_count += 1
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"成功更新 {updated_count} 个任务进度",
        data={
            "updated_count": updated_count,
            "tasks": updated_tasks
        }
    )


@router.post("/tasks/batch/assignee", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_assign_task_owner(
    *,
    db: Session = Depends(deps.get_db),
    batch_in: BatchTaskAssigneeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量分配任务负责人
    """
    if not batch_in.task_ids:
        raise HTTPException(status_code=400, detail="任务ID列表不能为空")
    
    if len(batch_in.task_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多分配50个任务")
    
    # 验证负责人是否存在
    owner = db.query(User).filter(User.id == batch_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="负责人不存在")
    
    # 验证所有任务是否存在
    tasks = db.query(Task).filter(Task.id.in_(batch_in.task_ids)).all()
    if len(tasks) != len(batch_in.task_ids):
        raise HTTPException(status_code=404, detail="部分任务不存在")
    
    updated_count = 0
    updated_tasks = []
    
    for task in tasks:
        old_owner_id = task.owner_id
        task.owner_id = batch_in.owner_id
        
        db.add(task)
        
        # 创建进度日志
        progress_log = ProgressLog(
            task_id=task.id,
            progress_percent=task.progress_percent,
            update_note=f"批量分配负责人：{owner.real_name or owner.username}",
            updated_by=current_user.id
        )
        db.add(progress_log)
        
        updated_tasks.append({
            "task_id": task.id,
            "task_name": task.task_name,
            "old_owner_id": old_owner_id,
            "new_owner_id": batch_in.owner_id,
            "owner_name": owner.real_name or owner.username
        })
        updated_count += 1
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"成功分配 {updated_count} 个任务负责人",
        data={
            "updated_count": updated_count,
            "owner_id": batch_in.owner_id,
            "owner_name": owner.real_name or owner.username,
            "tasks": updated_tasks
        }
    )


# ==================== 任务完成率统计 ====================

@router.get("/reports/task-completion-rate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_task_completion_rate(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务完成率统计（按部门/人员）
    """
    query = db.query(Task)
    
    # 筛选条件
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    if owner_id:
        query = query.filter(Task.owner_id == owner_id)
    elif department_id:
        # 通过负责人关联部门
        query = query.join(User).filter(User.department_id == department_id)
    
    if start_date:
        query = query.filter(Task.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Task.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    tasks = query.all()
    
    if not tasks:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "total_tasks": 0,
                "completed_tasks": 0,
                "completion_rate": 0.0,
                "by_department": [],
                "by_owner": []
            }
        )
    
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "DONE"])
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
    
    # 按部门统计
    dept_stats = {}
    for task in tasks:
        if task.owner_id:
            owner = db.query(User).filter(User.id == task.owner_id).first()
            if owner and owner.department_id:
                dept = db.query(Department).filter(Department.id == owner.department_id).first()
                dept_name = dept.dept_name if dept else "未分配部门"
                dept_id = owner.department_id
                
                if dept_id not in dept_stats:
                    dept_stats[dept_id] = {
                        "department_id": dept_id,
                        "department_name": dept_name,
                        "total_tasks": 0,
                        "completed_tasks": 0
                    }
                
                dept_stats[dept_id]["total_tasks"] += 1
                if task.status == "DONE":
                    dept_stats[dept_id]["completed_tasks"] += 1
    
    # 计算部门完成率
    by_department = []
    for dept_stat in dept_stats.values():
        dept_completion_rate = (dept_stat["completed_tasks"] / dept_stat["total_tasks"] * 100) if dept_stat["total_tasks"] > 0 else 0.0
        by_department.append({
            **dept_stat,
            "completion_rate": round(dept_completion_rate, 2)
        })
    
    # 按负责人统计
    owner_stats = {}
    for task in tasks:
        if task.owner_id:
            owner = db.query(User).filter(User.id == task.owner_id).first()
            owner_name = owner.real_name or owner.username if owner else "未知"
            
            if task.owner_id not in owner_stats:
                owner_stats[task.owner_id] = {
                    "owner_id": task.owner_id,
                    "owner_name": owner_name,
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            
            owner_stats[task.owner_id]["total_tasks"] += 1
            if task.status == "DONE":
                owner_stats[task.owner_id]["completed_tasks"] += 1
    
    # 计算负责人完成率
    by_owner = []
    for owner_stat in owner_stats.values():
        owner_completion_rate = (owner_stat["completed_tasks"] / owner_stat["total_tasks"] * 100) if owner_stat["total_tasks"] > 0 else 0.0
        by_owner.append({
            **owner_stat,
            "completion_rate": round(owner_completion_rate, 2)
        })
    
    # 按完成率排序
    by_department.sort(key=lambda x: x["completion_rate"], reverse=True)
    by_owner.sort(key=lambda x: x["completion_rate"], reverse=True)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 2),
            "by_department": by_department,
            "by_owner": by_owner[:20]  # 只返回前20名
        }
    )


# ==================== 里程碑达成率统计 ====================

@router.get("/reports/milestone-rate", response_model=MilestoneRateResponse, status_code=status.HTTP_200_OK)
def get_milestone_rate(
    project_id: Optional[int] = Query(None, description="项目ID（可选，不填则统计所有项目）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取里程碑达成率统计
    """
    if project_id:
        # 单个项目统计
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).all()
        
        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.status == "COMPLETED"])
        completion_rate = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0.0
        
        today = date.today()
        overdue_milestones = len([m for m in milestones if m.planned_date < today and m.status != "COMPLETED"])
        pending_milestones = len([m for m in milestones if m.status == "PENDING"])
        
        # 构建里程碑详情列表
        milestone_list = []
        for m in milestones:
            milestone_list.append({
                "id": m.id,
                "milestone_code": m.milestone_code,
                "milestone_name": m.milestone_name,
                "planned_date": m.planned_date.isoformat() if m.planned_date else None,
                "actual_date": m.actual_date.isoformat() if m.actual_date else None,
                "status": m.status,
                "is_key": m.is_key
            })
        
        return MilestoneRateResponse(
            project_id=project_id,
            project_name=project.project_name,
            total_milestones=total_milestones,
            completed_milestones=completed_milestones,
            completion_rate=round(completion_rate, 2),
            overdue_milestones=overdue_milestones,
            pending_milestones=pending_milestones,
            milestones=milestone_list
        )
    else:
        # 全局统计（所有项目）
        all_milestones = db.query(ProjectMilestone).all()
        
        total_milestones = len(all_milestones)
        completed_milestones = len([m for m in all_milestones if m.status == "COMPLETED"])
        completion_rate = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0.0
        
        today = date.today()
        overdue_milestones = len([m for m in all_milestones if m.planned_date < today and m.status != "COMPLETED"])
        pending_milestones = len([m for m in all_milestones if m.status == "PENDING"])
        
        return MilestoneRateResponse(
            project_id=0,  # 0表示全局
            project_name="全局统计",
            total_milestones=total_milestones,
            completed_milestones=completed_milestones,
            completion_rate=round(completion_rate, 2),
            overdue_milestones=overdue_milestones,
            pending_milestones=pending_milestones,
            milestones=[]
        )


# ==================== 延期原因统计 ====================

@router.get("/reports/delay-reasons", response_model=DelayReasonsResponse, status_code=status.HTTP_200_OK)
def get_delay_reasons(
    project_id: Optional[int] = Query(None, description="项目ID（可选）"),
    top_n: int = Query(10, ge=1, le=50, description="返回Top N原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取延期原因统计（Top N）
    """
    today = date.today()
    
    # 查询逾期任务
    query = db.query(Task).filter(
        Task.plan_end < today,
        Task.status != "DONE"
    )
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
    
    delayed_tasks = query.all()
    total_delayed = len(delayed_tasks)
    
    # 统计延期原因（从block_reason字段）
    reason_count = {}
    for task in delayed_tasks:
        reason = task.block_reason or "未填写原因"
        reason_count[reason] = reason_count.get(reason, 0) + 1
    
    # 按数量排序，取Top N
    sorted_reasons = sorted(reason_count.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    # 构建响应
    reasons = []
    for reason, count in sorted_reasons:
        percentage = (count / total_delayed * 100) if total_delayed > 0 else 0.0
        reasons.append(DelayReasonItem(
            reason=reason,
            count=count,
            percentage=round(percentage, 2)
        ))
    
    return DelayReasonsResponse(
        project_id=project_id,
        total_delayed_tasks=total_delayed,
        reasons=reasons
    )


# ==================== 计划基线管理 ====================

@router.get("/projects/{project_id}/baselines", response_model=BaselineListResponse, status_code=status.HTTP_200_OK)
def read_project_baselines(
    project_id: int,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目计划基线列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    query = db.query(ScheduleBaseline).filter(ScheduleBaseline.project_id == project_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    baselines = query.order_by(ScheduleBaseline.created_at.desc()).offset(offset).limit(page_size).all()
    
    # 补充任务数量
    items = []
    for baseline in baselines:
        task_count = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline.id).count()
        baseline_dict = {
            "id": baseline.id,
            "project_id": baseline.project_id,
            "baseline_no": baseline.baseline_no,
            "created_by": baseline.created_by,
            "task_count": task_count,
            "created_at": baseline.created_at,
            "updated_at": baseline.updated_at
        }
        items.append(baseline_dict)
    
    return BaselineListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/projects/{project_id}/baselines", response_model=BaselineResponse, status_code=status.HTTP_201_CREATED)
def create_project_baseline(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    baseline_in: BaselineCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目计划基线
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 生成基线编号（如果未提供）
    baseline_no = baseline_in.baseline_no
    if not baseline_no:
        # 查找已有基线数量，生成下一个编号
        existing_count = db.query(ScheduleBaseline).filter(ScheduleBaseline.project_id == project_id).count()
        baseline_no = f"V{existing_count + 1}"
    
    # 创建基线
    baseline = ScheduleBaseline(
        project_id=project_id,
        baseline_no=baseline_no,
        created_by=current_user.id
    )
    db.add(baseline)
    db.flush()  # 获取baseline.id
    
    # 获取项目所有任务，创建基线快照
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    for task in tasks:
        baseline_task = BaselineTask(
            baseline_id=baseline.id,
            task_id=task.id,
            plan_start=task.plan_start,
            plan_end=task.plan_end,
            weight=task.weight
        )
        db.add(baseline_task)
    
    db.commit()
    db.refresh(baseline)
    
    # 补充任务数量
    task_count = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline.id).count()
    
    return {
        "id": baseline.id,
        "project_id": baseline.project_id,
        "baseline_no": baseline.baseline_no,
        "created_by": baseline.created_by,
        "task_count": task_count,
        "created_at": baseline.created_at,
        "updated_at": baseline.updated_at
    }


@router.get("/baselines/{baseline_id}", response_model=BaselineResponse, status_code=status.HTTP_200_OK)
def read_baseline(
    baseline_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取计划基线详情
    """
    baseline = db.query(ScheduleBaseline).filter(ScheduleBaseline.id == baseline_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="计划基线不存在")
    
    task_count = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline_id).count()
    
    return {
        "id": baseline.id,
        "project_id": baseline.project_id,
        "baseline_no": baseline.baseline_no,
        "created_by": baseline.created_by,
        "task_count": task_count,
        "created_at": baseline.created_at,
        "updated_at": baseline.updated_at
    }


@router.get("/baselines/{baseline_id}/compare", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def compare_baseline(
    baseline_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    进度基线对比分析
    对比基线计划与实际进度
    """
    baseline = db.query(ScheduleBaseline).filter(ScheduleBaseline.id == baseline_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="计划基线不存在")
    
    # 获取基线任务
    baseline_tasks = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline_id).all()
    
    # 获取当前实际任务
    current_tasks = db.query(Task).filter(Task.project_id == baseline.project_id).all()
    
    # 构建任务映射
    task_map = {t.task_id: t for t in baseline_tasks}
    
    # 对比分析
    comparison_items = []
    total_deviation_days = 0
    delayed_tasks = 0
    ahead_tasks = 0
    on_schedule_tasks = 0
    
    for current_task in current_tasks:
        baseline_task = task_map.get(current_task.id)
        if not baseline_task:
            continue
        
        # 计算偏差
        if current_task.plan_end and baseline_task.plan_end:
            deviation_days = (current_task.plan_end - baseline_task.plan_end).days
            total_deviation_days += deviation_days
            
            if deviation_days > 0:
                delayed_tasks += 1
            elif deviation_days < 0:
                ahead_tasks += 1
            else:
                on_schedule_tasks += 1
        
        comparison_items.append({
            "task_id": current_task.id,
            "task_name": current_task.task_name,
            "baseline_start": baseline_task.plan_start.isoformat() if baseline_task.plan_start else None,
            "baseline_end": baseline_task.plan_end.isoformat() if baseline_task.plan_end else None,
            "actual_start": current_task.actual_start.isoformat() if current_task.actual_start else None,
            "actual_end": current_task.actual_end.isoformat() if current_task.actual_end else None,
            "plan_start": current_task.plan_start.isoformat() if current_task.plan_start else None,
            "plan_end": current_task.plan_end.isoformat() if current_task.plan_end else None,
            "deviation_days": (current_task.plan_end - baseline_task.plan_end).days if (current_task.plan_end and baseline_task.plan_end) else None,
            "progress": float(current_task.progress) if current_task.progress else 0.0
        })
    
    avg_deviation = total_deviation_days / len(comparison_items) if comparison_items else 0.0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "baseline_id": baseline_id,
            "baseline_no": baseline.baseline_no,
            "project_id": baseline.project_id,
            "summary": {
                "total_tasks": len(comparison_items),
                "delayed_tasks": delayed_tasks,
                "ahead_tasks": ahead_tasks,
                "on_schedule_tasks": on_schedule_tasks,
                "avg_deviation_days": round(avg_deviation, 2),
                "total_deviation_days": total_deviation_days
            },
            "comparison": comparison_items
        }
    )


@router.get("/projects/{project_id}/deviation-analysis", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def analyze_progress_deviation(
    project_id: int,
    db: Session = Depends(deps.get_db),
    baseline_id: Optional[int] = Query(None, description="基线ID（不提供则使用最新基线）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    进度偏差分析
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取基线
    if baseline_id:
        baseline = db.query(ScheduleBaseline).filter(ScheduleBaseline.id == baseline_id).first()
    else:
        baseline = db.query(ScheduleBaseline).filter(
            ScheduleBaseline.project_id == project_id
        ).order_by(ScheduleBaseline.created_at.desc()).first()
    
    if not baseline:
        raise HTTPException(status_code=404, detail="未找到计划基线")
    
    # 获取任务数据
    baseline_tasks = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline.id).all()
    current_tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    task_map = {t.task_id: t for t in baseline_tasks}
    
    # 偏差统计
    deviations = []
    for task in current_tasks:
        baseline_task = task_map.get(task.id)
        if not baseline_task or not task.plan_end or not baseline_task.plan_end:
            continue
        
        deviation = (task.plan_end - baseline_task.plan_end).days
        deviations.append({
            "task_id": task.id,
            "task_name": task.task_name,
            "deviation_days": deviation,
            "baseline_end": baseline_task.plan_end.isoformat(),
            "actual_end": task.plan_end.isoformat()
        })
    
    # 按偏差天数分组统计
    deviation_ranges = {
        "严重延期 (>7天)": len([d for d in deviations if d["deviation_days"] > 7]),
        "延期 (1-7天)": len([d for d in deviations if 1 <= d["deviation_days"] <= 7]),
        "按时完成": len([d for d in deviations if d["deviation_days"] == 0]),
        "提前完成 (1-7天)": len([d for d in deviations if -7 <= d["deviation_days"] < 0]),
        "大幅提前 (>7天)": len([d for d in deviations if d["deviation_days"] < -7])
    }
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "baseline_id": baseline.id,
            "baseline_no": baseline.baseline_no,
            "deviation_ranges": deviation_ranges,
            "total_tasks": len(deviations),
            "avg_deviation": round(sum(d["deviation_days"] for d in deviations) / len(deviations), 2) if deviations else 0.0,
            "details": deviations
        }
    )


@router.get("/projects/{project_id}/critical-path", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def calculate_critical_path(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关键路径计算
    使用拓扑排序和最长路径算法计算关键路径
    """
    from collections import deque
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取所有任务及其依赖
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    dependencies = db.query(TaskDependency).join(Task).filter(Task.project_id == project_id).all()
    
    # 构建任务图
    task_dict = {task.id: task for task in tasks}
    in_degree = {task.id: 0 for task in tasks}
    graph = {task.id: [] for task in tasks}
    
    for dep in dependencies:
        if dep.depends_on_task_id in graph:
            graph[dep.depends_on_task_id].append(dep.task_id)
            in_degree[dep.task_id] = in_degree.get(dep.task_id, 0) + 1
    
    # 拓扑排序 + 最长路径计算
    queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
    earliest_start = {task_id: 0 for task_id in task_dict.keys()}
    
    # 计算最早开始时间
    while queue:
        task_id = queue.popleft()
        task = task_dict[task_id]
        duration = 0
        if task.plan_start and task.plan_end:
            duration = (task.plan_end - task.plan_start).days
        
        for next_task_id in graph[task_id]:
            in_degree[next_task_id] -= 1
            if in_degree[next_task_id] == 0:
                queue.append(next_task_id)
            
            # 更新最早开始时间
            earliest_start[next_task_id] = max(
                earliest_start.get(next_task_id, 0),
                earliest_start[task_id] + duration
            )
    
    # 计算最晚开始时间（反向）
    max_duration = max(earliest_start.values()) if earliest_start else 0
    latest_start = {task_id: max_duration for task_id in task_dict.keys()}
    
    # 找出关键路径（最早开始时间 = 最晚开始时间的任务）
    critical_path = []
    for task_id in task_dict.keys():
        task = task_dict[task_id]
        duration = 0
        if task.plan_start and task.plan_end:
            duration = (task.plan_end - task.plan_start).days
        
        es = earliest_start.get(task_id, 0)
        ls = latest_start.get(task_id, max_duration)
        
        if es == ls or (es + duration) == max_duration:
            critical_path.append({
                "task_id": task_id,
                "task_name": task.task_name,
                "earliest_start": es,
                "latest_start": ls,
                "duration": duration,
                "slack": ls - es
            })
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "total_duration": max_duration,
            "critical_path": sorted(critical_path, key=lambda x: x["earliest_start"]),
            "critical_path_length": len(critical_path)
        }
    )
