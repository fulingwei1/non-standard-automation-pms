# -*- coding: utf-8 -*-
"""
项目模板 - 版本管理

包含版本CRUD、发布、比较、回滚等操作
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import ProjectTemplate, ProjectTemplateVersion
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.schemas.project import (
    ProjectTemplateVersionCreate,
)

router = APIRouter()


@router.get("/templates/{template_id}/versions", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_template_versions(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
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
    versions = apply_pagination(query.order_by(desc(ProjectTemplateVersion.version_no)), pagination.offset, pagination.limit).all()

    items = []
    for version in versions:
        items.append({
            "id": version.id,
            "template_id": version.template_id,
            "version_no": version.version_no,
            "description": version.description,
            "is_published": version.status == "published",
            "published_at": version.published_at.isoformat() if version.published_at else None,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
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
        release_notes=getattr(version_in, 'description', '') or getattr(version_in, 'release_notes', ''),
        template_config=getattr(version_in, 'config', None) or getattr(version_in, 'template_config', None),
        status="draft",
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

    if version.status == "published":
        return ResponseModel(
            code=200,
            message="版本已发布",
            data={"version_id": version_id}
        )

    version.status = "published"
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
    config1 = version1.template_config or {}
    config2 = version2.template_config or {}

    differences = {
        "version1": {
            "id": version1.id,
            "version_no": version1.version_no,
            "version_no": version1.version_name,
            "config": config1,
        },
        "version2": {
            "id": version2.id,
            "version_no": version2.version_no,
            "version_no": version2.version_name,
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
        release_notes=f"回滚自版本 {version.version_no}",
        template_config=version.template_config,
        status="draft",
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
