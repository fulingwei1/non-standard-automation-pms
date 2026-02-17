# -*- coding: utf-8 -*-
"""
项目模板 - 基础CRUD操作
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import ProjectTemplate
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.schemas.project import (
    ProjectTemplateCreate,
    ProjectTemplateUpdate,
)
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


@router.get("/templates", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_templates(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    is_active: Optional[bool] = Query(True, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目模板列表
    """
    query = db.query(ProjectTemplate)

    query = apply_keyword_filter(query, ProjectTemplate, keyword, "template_name", use_ilike=False)

    if project_type:
        query = query.filter(ProjectTemplate.project_type == project_type)

    if is_active is not None:
        query = query.filter(ProjectTemplate.is_active == is_active)

    total = query.count()
    templates = apply_pagination(query.order_by(desc(ProjectTemplate.created_at)), pagination.offset, pagination.limit).all()

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
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
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
        is_active=template_in.is_active if template_in.is_active is not None else True,
    )

    save_obj(db, template)

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
    template = get_or_404(db, ProjectTemplate, template_id, detail="模板不存在")

    return ResponseModel(
        code=200,
        message="获取模板成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "project_type": template.project_type,
            "description": template.description,
            "is_active": template.is_active,
            "usage_count": template.usage_count or 0,
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
    template = get_or_404(db, ProjectTemplate, template_id, detail="模板不存在")

    update_data = template_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(template, field):
            setattr(template, field, value)

    save_obj(db, template)

    return ResponseModel(
        code=200,
        message="模板更新成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
        }
    )
