# -*- coding: utf-8 -*-
"""
满意度调查模板管理 API endpoints
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.service import SatisfactionSurveyTemplate
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("", response_model=PaginatedResponse, status_code=200)
def list_satisfaction_templates(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    survey_type: Optional[str] = Query(None, description="调查类型筛选"),
    is_active: Optional[bool] = Query(True, description="是否启用"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查模板列表
    """
    query = db.query(SatisfactionSurveyTemplate)

    if survey_type:
        query = query.filter(SatisfactionSurveyTemplate.survey_type == survey_type)
    if is_active is not None:
        query = query.filter(SatisfactionSurveyTemplate.is_active == is_active)

    # 应用关键词过滤（模板名称/模板编码）
    query = apply_keyword_filter(query, SatisfactionSurveyTemplate, keyword, ["template_name", "template_code"])

    total = query.count()
    items = apply_pagination(query.order_by(desc(SatisfactionSurveyTemplate.usage_count), desc(SatisfactionSurveyTemplate.created_at)), pagination.offset, pagination.limit).all()

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total),
    }


@router.get("/{template_id}", response_model=dict, status_code=200)
def get_satisfaction_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查模板详情
    """
    template = get_or_404(db, SatisfactionSurveyTemplate, template_id, "调查模板不存在")

    return {
        "id": template.id,
        "template_name": template.template_name,
        "template_code": template.template_code,
        "survey_type": template.survey_type,
        "questions": template.questions or [],
        "default_send_method": template.default_send_method,
        "default_deadline_days": template.default_deadline_days,
    }
