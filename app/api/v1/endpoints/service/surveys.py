# -*- coding: utf-8 -*-
"""
满意度调查管理 API endpoints
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.service import CustomerSatisfaction
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.service import (
    CustomerSatisfactionCreate,
    CustomerSatisfactionResponse,
    CustomerSatisfactionUpdate,
)
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

from .number_utils import generate_survey_no

router = APIRouter()


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_customer_satisfaction_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查统计
    """
    total = db.query(CustomerSatisfaction).count()
    sent = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.status.in_(["SENT", "PENDING", "COMPLETED"])).count()
    pending = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.status == "PENDING").count()
    completed = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.status == "COMPLETED").count()

    # 计算平均分
    completed_surveys = db.query(CustomerSatisfaction).filter(
        CustomerSatisfaction.status == "COMPLETED",
        CustomerSatisfaction.overall_score.isnot(None)
    ).all()
    average_score = 0.0
    if completed_surveys:
        total_score = sum(float(s.overall_score) for s in completed_surveys)
        average_score = round(total_score / len(completed_surveys), 1)

    # 计算回复率
    response_rate = 0.0
    if total > 0:
        response_rate = round((completed / total) * 100, 1)

    return {
        "total": total,
        "sent": sent,
        "pending": pending,
        "completed": completed,
        "average_score": average_score,
        "response_rate": response_rate,
    }


@router.get("", response_model=PaginatedResponse[CustomerSatisfactionResponse], status_code=status.HTTP_200_OK)
def read_customer_satisfactions(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    survey_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    survey_type: Optional[str] = Query(None, description="调查类型筛选"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查列表
    """
    query = db.query(CustomerSatisfaction)

    if survey_status:
        query = query.filter(CustomerSatisfaction.status == survey_status)
    if survey_type:
        query = query.filter(CustomerSatisfaction.survey_type == survey_type)
    if date_from:
        query = query.filter(CustomerSatisfaction.survey_date >= date_from)
    if date_to:
        query = query.filter(CustomerSatisfaction.survey_date <= date_to)

    # 应用关键词过滤（调查编号/客户名称/项目名称）
    query = apply_keyword_filter(query, CustomerSatisfaction, keyword, ["survey_no", "customer_name", "project_name"])

    total = query.count()
    items = apply_pagination(query.order_by(desc(CustomerSatisfaction.survey_date)), pagination.offset, pagination.limit).all()

    # 获取创建人姓名
    for item in items:
        if item.created_by:
            creator = db.query(User).filter(User.id == item.created_by).first()
            if creator:
                item.created_by_name = creator.name or creator.username

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total),
    }


@router.post("", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_201_CREATED)
def create_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_in: CustomerSatisfactionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建满意度调查
    """
    survey = CustomerSatisfaction(
        survey_no=generate_survey_no(db),
        survey_type=survey_in.survey_type,
        customer_name=survey_in.customer_name,
        customer_contact=survey_in.customer_contact,
        customer_email=survey_in.customer_email,
        customer_phone=survey_in.customer_phone,
        project_code=survey_in.project_code,
        project_name=survey_in.project_name,
        survey_date=survey_in.survey_date,
        send_method=survey_in.send_method,
        deadline=survey_in.deadline,
        status="DRAFT",
        created_by=current_user.id,
        created_by_name=current_user.real_name or current_user.username,
    )
    return save_obj(db, survey)


@router.get("/{survey_id}", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK)
def read_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查详情
    """
    survey = get_or_404(db, CustomerSatisfaction, survey_id, "满意度调查不存在")

    return survey


@router.put("/{survey_id}", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK)
def update_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    survey_in: CustomerSatisfactionUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新满意度调查
    """
    survey = get_or_404(db, CustomerSatisfaction, survey_id, "满意度调查不存在")

    if survey_in.status is not None:
        survey.status = survey_in.status
        if survey_in.status == "SENT" and not survey.send_date:
            survey.send_date = date.today()
    if survey_in.response_date is not None:
        survey.response_date = survey_in.response_date
    if survey_in.overall_score is not None:
        survey.overall_score = survey_in.overall_score
    if survey_in.scores is not None:
        survey.scores = survey_in.scores
    if survey_in.feedback is not None:
        survey.feedback = survey_in.feedback
    if survey_in.suggestions is not None:
        survey.suggestions = survey_in.suggestions

    if survey_in.status == "COMPLETED" and survey.overall_score:
        survey.status = "COMPLETED"

    return save_obj(db, survey)


@router.post("/{survey_id}/send", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK)
def send_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发送满意度调查
    """
    survey = get_or_404(db, CustomerSatisfaction, survey_id, "满意度调查不存在")

    if survey.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="调查已完成，无法发送")

    survey.status = "SENT"
    survey.send_date = date.today()

    return save_obj(db, survey)
