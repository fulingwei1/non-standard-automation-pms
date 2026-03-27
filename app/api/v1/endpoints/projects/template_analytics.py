# -*- coding: utf-8 -*-
"""
项目模板 - 智能推荐和统计

包含基于客户类型、产品类型、合同金额、历史成功模式的模板推荐
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectTemplate
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.template_recommendation_service import TemplateRecommendationService
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/templates/recommend", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_recommended_templates(
    *,
    db: Session = Depends(deps.get_db),
    project_type: Optional[str] = Query(None, description="项目类型"),
    product_category: Optional[str] = Query(None, description="产品类别（ICT/FCT/EOL等）"),
    industry: Optional[str] = Query(None, description="行业"),
    customer_id: Optional[int] = Query(None, description="客户ID（用于客户类型匹配和历史复用）"),
    contract_amount: Optional[float] = Query(None, description="合同金额（用于大/中/小项目匹配）"),
    limit: int = Query(5, ge=1, le=20, description="返回数量限制"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    智能推荐模板

    推荐维度：
    1. 客户类型 — 老客户/新客户/行业类型
    2. 产品类型 — 标准品/定制品/研发项目(ICT/FCT/EOL)
    3. 合同金额 — 大/中/小项目复杂度
    4. 历史成功模式 — 类似客户/产品的成功交付模板
    """
    service = TemplateRecommendationService(db)
    recommendations = service.recommend_templates(
        project_type=project_type,
        product_category=product_category,
        industry=industry,
        customer_id=customer_id,
        contract_amount=contract_amount,
        limit=limit,
    )

    return ResponseModel(
        code=200,
        message="获取推荐模板成功",
        data={
            "recommendations": recommendations,
            "templates": recommendations,  # 兼容旧字段
        },
    )


@router.get(
    "/templates/{template_id}/usage-statistics",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_template_usage_statistics(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取模板使用统计
    """
    template = get_or_404(db, ProjectTemplate, template_id, detail="模板不存在")

    # 统计使用该模板创建的项目
    projects = db.query(Project).filter(Project.template_id == template_id).all()

    # 按阶段统计
    stage_stats = {}
    for project in projects:
        stage = project.stage or "S1"
        if stage not in stage_stats:
            stage_stats[stage] = 0
        stage_stats[stage] += 1

    # 按健康度统计
    health_stats = {}
    for project in projects:
        health = project.health or "H1"
        if health not in health_stats:
            health_stats[health] = 0
        health_stats[health] += 1

    # 成功交付率
    total = len(projects)
    success_count = sum(1 for p in projects if p.stage == "S9")
    success_rate = round(success_count / total * 100, 1) if total > 0 else 0

    return ResponseModel(
        code=200,
        message="获取模板使用统计成功",
        data={
            "template_id": template_id,
            "template_name": template.template_name,
            "usage_count": total,
            "success_count": success_count,
            "success_rate": success_rate,
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
            ],
        },
    )
