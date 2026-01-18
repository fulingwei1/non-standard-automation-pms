# -*- coding: utf-8 -*-
"""
项目模块 - 克隆功能

包含项目克隆操作
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, Project, ProjectMilestone
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import ProjectCloneRequest

router = APIRouter()


@router.post("/{project_id}/clone", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def clone_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Path(..., description="源项目ID"),
    clone_request: ProjectCloneRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    克隆项目
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    source_project = check_project_access_or_raise(db, current_user, project_id, "您没有权限克隆该项目")

    # 检查项目编码是否已存在
    existing = db.query(Project).filter(Project.project_code == clone_request.project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")

    # 创建新项目
    new_project = Project(
        project_code=clone_request.project_code,
        project_name=clone_request.project_name,
        project_type=source_project.project_type,
        customer_id=source_project.customer_id,
        customer_name=source_project.customer_name,
        customer_contact=source_project.customer_contact,
        customer_phone=source_project.customer_phone,
        pm_id=current_user.id,
        pm_name=current_user.real_name or current_user.username,
        stage='S1',
        status='ST01',
        health='H1',
        description=source_project.description,
        requirements=source_project.requirements,
        budget_amount=source_project.budget_amount,
        is_active=True,
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # 克隆机台（如果需要）
    if clone_request.clone_machines:
        source_machines = db.query(Machine).filter(Machine.project_id == project_id).all()
        for source_machine in source_machines:
            new_machine = Machine(
                project_id=new_project.id,
                machine_code=source_machine.machine_code,
                machine_name=source_machine.machine_name,
                machine_type=source_machine.machine_type,
                status='PENDING',
                progress_pct=0,
            )
            db.add(new_machine)

    # 克隆里程碑（如果需要）
    if clone_request.clone_milestones:
        source_milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project_id
        ).all()
        for source_milestone in source_milestones:
            new_milestone = ProjectMilestone(
                project_id=new_project.id,
                milestone_name=source_milestone.milestone_name,
                milestone_type=source_milestone.milestone_type,
                stage=source_milestone.stage,
                is_key=source_milestone.is_key,
            )
            db.add(new_milestone)

    # 初始化标准阶段
    from app.utils.project_utils import init_project_stages
    init_project_stages(db, new_project.id)

    db.commit()

    return ResponseModel(
        code=200,
        message="项目克隆成功",
        data={
            "id": new_project.id,
            "project_code": new_project.project_code,
            "project_name": new_project.project_name,
            "source_project_id": project_id,
        }
    )
