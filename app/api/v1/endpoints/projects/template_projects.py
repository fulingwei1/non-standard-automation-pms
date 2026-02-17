# -*- coding: utf-8 -*-
"""
项目模板 - 从模板创建项目
"""

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, Project, ProjectMilestone, ProjectTemplate, ProjectTemplateVersion
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


@router.post("/templates/{template_id}/create-project", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_from_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    project_code: str = Body(..., description="项目编码"),
    project_name: str = Body(..., description="项目名称"),
    customer_id: Optional[int] = Body(None, description="客户ID"),
    pm_id: Optional[int] = Body(None, description="项目经理ID"),
    version_id: Optional[int] = Body(None, description="版本ID（不提供则使用最新发布版本）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从模板创建项目
    """
    template = get_or_404(db, ProjectTemplate, template_id, detail="模板不存在")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已停用")

    # 检查项目编码是否已存在
    existing = db.query(Project).filter(Project.project_code == project_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="项目编码已存在")

    # 获取模板版本
    if version_id:
        version = db.query(ProjectTemplateVersion).filter(
            ProjectTemplateVersion.id == version_id,
            ProjectTemplateVersion.template_id == template_id
        ).first()
    else:
        version = db.query(ProjectTemplateVersion).filter(
            ProjectTemplateVersion.template_id == template_id,
            ProjectTemplateVersion.is_published
        ).order_by(desc(ProjectTemplateVersion.version_no)).first()

    # 创建项目
    project = Project(
        project_code=project_code,
        project_name=project_name,
        project_type=template.project_type,
        customer_id=customer_id,
        pm_id=pm_id or current_user.id,
        stage='S1',
        status='ST01',
        health='H1',
        description=template.description,
        is_active=True,
        template_id=template_id,
    )

    # 填充客户和PM信息
    if customer_id:
        from app.models.project import Customer
        customer = db.query(Customer).get(customer_id)
        if customer:
            project.customer_name = customer.customer_name
            project.customer_contact = customer.contact_person
            project.customer_phone = customer.contact_phone

    pm = db.query(User).get(project.pm_id)
    if pm:
        project.pm_name = pm.real_name or pm.username

    save_obj(db, project)

    # 从模板版本复制配置（如果有）
    if version and version.config:
        config = version.config
        # 复制机台配置
        if config.get("machines"):
            for machine_config in config["machines"]:
                machine = Machine(
                    project_id=project.id,
                    machine_code=machine_config.get("machine_code", f"PN{project.id:03d}"),
                    machine_name=machine_config.get("machine_name", ""),
                    machine_type=machine_config.get("machine_type", ""),
                    status='PENDING',
                    progress_pct=0,
                )
                db.add(machine)

        # 复制里程碑配置
        if config.get("milestones"):
            for milestone_config in config["milestones"]:
                milestone = ProjectMilestone(
                    project_id=project.id,
                    milestone_name=milestone_config.get("milestone_name", ""),
                    milestone_type=milestone_config.get("milestone_type", ""),
                    stage=milestone_config.get("stage", "S1"),
                    is_key=milestone_config.get("is_key", False),
                )
                db.add(milestone)

    # 初始化标准阶段
    from app.utils.project_utils import init_project_stages
    init_project_stages(db, project.id)

    # 更新模板使用次数
    template.usage_count = (template.usage_count or 0) + 1
    db.add(template)

    db.commit()

    return ResponseModel(
        code=200,
        message="从模板创建项目成功",
        data={
            "id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "template_id": template_id,
            "template_name": template.template_name,
        }
    )
