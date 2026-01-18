# -*- coding: utf-8 -*-
"""
进度跟踪模块 - WBS初始化
从WBS模板初始化项目任务计划
"""

from datetime import date, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.progress import Task, TaskDependency, WbsTemplate, WbsTemplateTask
from app.models.project import Project
from app.models.user import User
from app.schemas.progress import InitWbsRequest, InitWbsResponse

router = APIRouter()


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
