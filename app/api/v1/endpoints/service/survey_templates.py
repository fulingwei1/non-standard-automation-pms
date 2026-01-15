# -*- coding: utf-8 -*-
"""
满意度调查模板 API
自动生成，从 service.py 拆分
"""

from typing import Any, List, Optional

from datetime import datetime, date, timedelta

from decimal import Decimal

import os

import uuid

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, UploadFile, File, Form

from sqlalchemy.orm import Session

from sqlalchemy import desc, or_, func

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.project import Project, Customer

from app.models.service import (

from app.schemas.service import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/service/survey-templates",
    tags=["survey_templates"]
)

# ==================== 路由定义 ====================
# 共 2 个路由

# ==================== 满意度调查模板 ====================

@router.get("/satisfaction-templates", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
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


@router.get("/satisfaction-templates/{template_id}", response_model=dict, status_code=status.HTTP_200_OK)
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



