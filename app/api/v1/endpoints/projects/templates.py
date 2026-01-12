# -*- coding: utf-8 -*-
"""
项目模板端点

包含模板的创建、更新、删除、版本管理、从模板创建项目等操作
"""

from typing import Any, List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import (
    Project, ProjectTemplate, ProjectTemplateVersion,
    Machine, ProjectMilestone
)
from app.schemas.project import (
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
    ProjectTemplateResponse,
    ProjectTemplateVersionCreate,
    ProjectTemplateVersionUpdate,
    ProjectTemplateVersionResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


@router.get("/templates", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_templates(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    is_active: Optional[bool] = Query(True, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目模板列表
    """
    query = db.query(ProjectTemplate)

    if keyword:
        keyword_pattern = f"%{keyword}%"
        query = query.filter(
            ProjectTemplate.template_name.like(keyword_pattern)
        )

    if project_type:
        query = query.filter(ProjectTemplate.project_type == project_type)

    if is_active is not None:
        query = query.filter(ProjectTemplate.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    templates = query.order_by(desc(ProjectTemplate.created_at)).offset(offset).limit(page_size).all()

    items = []
    for template in templates:
        items.append({
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "project_type": template.project_type,
            "description": template.description,
            "is_active": template.is_active,
            "usage_count": template.usage_count or 0,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/templates", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_project_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: ProjectTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目模板
    """
    # 检查模板编码是否已存在
    existing = db.query(ProjectTemplate).filter(
        ProjectTemplate.template_code == template_in.template_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = ProjectTemplate(
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        project_type=template_in.project_type,
        description=template_in.description,
        config=template_in.config,
        is_active=True,
        usage_count=0,
        created_by=current_user.id,
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return ResponseModel(
        code=200,
        message="模板创建成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
        }
    )


@router.get("/templates/{template_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目模板详情
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 获取版本列表
    versions = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.template_id == template_id
    ).order_by(desc(ProjectTemplateVersion.version_no)).all()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "project_type": template.project_type,
            "description": template.description,
            "config": template.config,
            "is_active": template.is_active,
            "usage_count": template.usage_count or 0,
            "versions": [
                {
                    "id": v.id,
                    "version_no": v.version_no,
                    "version_name": v.version_name,
                    "is_published": v.is_published,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in versions
            ],
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None,
        }
    )


@router.put("/templates/{template_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_project_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: ProjectTemplateUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新项目模板
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    update_data = template_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(template, field):
            setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)

    return ResponseModel(
        code=200,
        message="模板更新成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
        }
    )


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
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

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
            ProjectTemplateVersion.is_published == True
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

    db.add(project)
    db.commit()
    db.refresh(project)

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


@router.get("/templates/{template_id}/versions", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_template_versions(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取模板版本列表
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    query = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.template_id == template_id
    )

    total = query.count()
    offset = (page - 1) * page_size
    versions = query.order_by(desc(ProjectTemplateVersion.version_no)).offset(offset).limit(page_size).all()

    items = []
    for version in versions:
        items.append({
            "id": version.id,
            "template_id": version.template_id,
            "version_no": version.version_no,
            "version_name": version.version_name,
            "description": version.description,
            "is_published": version.is_published,
            "published_at": version.published_at.isoformat() if version.published_at else None,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/templates/{template_id}/versions", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_in: ProjectTemplateVersionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建模板版本
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 获取最新版本号
    latest_version = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.template_id == template_id
    ).order_by(desc(ProjectTemplateVersion.version_no)).first()

    new_version_no = 1
    if latest_version:
        new_version_no = latest_version.version_no + 1

    version = ProjectTemplateVersion(
        template_id=template_id,
        version_no=new_version_no,
        version_name=version_in.version_name or f"V{new_version_no}.0",
        description=version_in.description,
        config=version_in.config,
        is_published=False,
        created_by=current_user.id,
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return ResponseModel(
        code=200,
        message="模板版本创建成功",
        data={
            "id": version.id,
            "template_id": version.template_id,
            "version_no": version.version_no,
            "version_name": version.version_name,
        }
    )


@router.put("/templates/{template_id}/versions/{version_id}/publish", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def publish_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发布模板版本
    """
    version = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.id == version_id,
        ProjectTemplateVersion.template_id == template_id
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    if version.is_published:
        return ResponseModel(
            code=200,
            message="版本已发布",
            data={"version_id": version_id}
        )

    version.is_published = True
    version.published_at = datetime.now()
    db.add(version)
    db.commit()

    return ResponseModel(
        code=200,
        message="版本发布成功",
        data={
            "version_id": version_id,
            "version_no": version.version_no,
            "published_at": version.published_at.isoformat(),
        }
    )


@router.get("/templates/{template_id}/versions/compare", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def compare_template_versions(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version1_id: int = Query(..., description="版本1 ID"),
    version2_id: int = Query(..., description="版本2 ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    比较模板版本
    """
    version1 = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.id == version1_id,
        ProjectTemplateVersion.template_id == template_id
    ).first()

    version2 = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.id == version2_id,
        ProjectTemplateVersion.template_id == template_id
    ).first()

    if not version1 or not version2:
        raise HTTPException(status_code=404, detail="版本不存在")

    # 比较配置差异
    config1 = version1.config or {}
    config2 = version2.config or {}

    differences = {
        "version1": {
            "id": version1.id,
            "version_no": version1.version_no,
            "version_name": version1.version_name,
            "config": config1,
        },
        "version2": {
            "id": version2.id,
            "version_no": version2.version_no,
            "version_name": version2.version_name,
            "config": config2,
        },
        "changes": []
    }

    # 简单的差异检测
    all_keys = set(config1.keys()) | set(config2.keys())
    for key in all_keys:
        val1 = config1.get(key)
        val2 = config2.get(key)
        if val1 != val2:
            differences["changes"].append({
                "field": key,
                "version1_value": val1,
                "version2_value": val2,
            })

    return ResponseModel(
        code=200,
        message="版本比较完成",
        data=differences
    )


@router.post("/templates/{template_id}/versions/{version_id}/rollback", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def rollback_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    回滚到指定模板版本（创建新版本并复制配置）
    """
    version = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.id == version_id,
        ProjectTemplateVersion.template_id == template_id
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    # 获取最新版本号
    latest_version = db.query(ProjectTemplateVersion).filter(
        ProjectTemplateVersion.template_id == template_id
    ).order_by(desc(ProjectTemplateVersion.version_no)).first()

    new_version_no = 1
    if latest_version:
        new_version_no = latest_version.version_no + 1

    # 创建新版本，复制配置
    new_version = ProjectTemplateVersion(
        template_id=template_id,
        version_no=new_version_no,
        version_name=f"回滚自 {version.version_name}",
        description=f"回滚自版本 {version.version_no}",
        config=version.config,
        is_published=False,
        created_by=current_user.id,
    )

    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    return ResponseModel(
        code=200,
        message="版本回滚成功",
        data={
            "new_version_id": new_version.id,
            "new_version_no": new_version.version_no,
            "rollback_from_version_id": version_id,
            "rollback_from_version_no": version.version_no,
        }
    )


@router.get("/templates/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_recommended_templates(
    *,
    db: Session = Depends(deps.get_db),
    project_type: Optional[str] = Query(None, description="项目类型"),
    limit: int = Query(5, ge=1, le=20, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取推荐模板
    """
    query = db.query(ProjectTemplate).filter(ProjectTemplate.is_active == True)

    if project_type:
        query = query.filter(ProjectTemplate.project_type == project_type)

    # 按使用次数排序
    templates = query.order_by(desc(ProjectTemplate.usage_count)).limit(limit).all()

    items = []
    for template in templates:
        items.append({
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "project_type": template.project_type,
            "description": template.description,
            "usage_count": template.usage_count or 0,
        })

    return ResponseModel(
        code=200,
        message="获取推荐模板成功",
        data={"templates": items}
    )


@router.get("/templates/{template_id}/usage-statistics", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_template_usage_statistics(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取模板使用统计
    """
    template = db.query(ProjectTemplate).filter(ProjectTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 统计使用该模板创建的项目
    projects = db.query(Project).filter(Project.template_id == template_id).all()

    # 按阶段统计
    stage_stats = {}
    for project in projects:
        stage = project.stage or 'S1'
        if stage not in stage_stats:
            stage_stats[stage] = 0
        stage_stats[stage] += 1

    # 按健康度统计
    health_stats = {}
    for project in projects:
        health = project.health or 'H1'
        if health not in health_stats:
            health_stats[health] = 0
        health_stats[health] += 1

    return ResponseModel(
        code=200,
        message="获取模板使用统计成功",
        data={
            "template_id": template_id,
            "template_name": template.template_name,
            "usage_count": len(projects),
            "by_stage": stage_stats,
            "by_health": health_stats,
            "projects": [
                {
                    "id": p.id,
                    "project_code": p.project_code,
                    "project_name": p.project_name,
                    "stage": p.stage,
                    "health": p.health,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in projects[:10]  # 只返回前10个
            ]
        }
    )
