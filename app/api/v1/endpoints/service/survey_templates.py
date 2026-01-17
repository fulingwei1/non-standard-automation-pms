# -*- coding: utf-8 -*-
"""
满意度调查模板管理 API endpoints
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.service import SatisfactionSurveyTemplate
from app.models.user import User
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse, status_code=200)
def list_satisfaction_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
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
    if keyword:
        query = query.filter(
            or_(
                SatisfactionSurveyTemplate.template_name.like(f"%{keyword}%"),
                SatisfactionSurveyTemplate.template_code.like(f"%{keyword}%"),
            )
        )

    total = query.count()
    items = query.order_by(desc(SatisfactionSurveyTemplate.usage_count), desc(SatisfactionSurveyTemplate.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
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
    template = db.query(SatisfactionSurveyTemplate).filter(SatisfactionSurveyTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="调查模板不存在")

    return {
        "id": template.id,
        "template_name": template.template_name,
        "template_code": template.template_code,
        "survey_type": template.survey_type,
        "questions": template.questions or [],
        "default_send_method": template.default_send_method,
        "default_deadline_days": template.default_deadline_days,
    }
