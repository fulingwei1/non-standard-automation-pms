# -*- coding: utf-8 -*-
"""
项目模板 - 分析和统计

包含推荐模板、使用统计等
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectTemplate
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


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
