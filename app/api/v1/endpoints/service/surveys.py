# -*- coding: utf-8 -*-
"""
满意度调查管理 API endpoints
"""

import logging
from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.service import CustomerSatisfaction
from app.models.service.enums import (
    SurveyStatusEnum,
    SurveyTypeEnum,
    normalize_survey_status,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.service import (
    CustomerSatisfactionCreate,
    CustomerSatisfactionResponse,
    CustomerSatisfactionSubmit,
    CustomerSatisfactionUpdate,
)
from app.services.notification.channels.base import (
    NotificationChannel,
    NotificationPriority,
    NotificationRequest,
)
from app.services.notification.unified_notification_service import get_notification_service
from app.utils.db_helpers import get_or_404, save_obj

from .access import filter_owned_service_query, get_owned_service_object_or_404
from .number_utils import generate_survey_no

router = APIRouter()
logger = logging.getLogger(__name__)


def _as_int(value) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _send_satisfaction_survey_notification(
    db: Session,
    survey: CustomerSatisfaction,
    *,
    actor: Optional[User] = None,
    ticket_no: Optional[str] = None,
    extra_user_ids: Optional[list[int]] = None,
) -> dict:
    recipient_ids = {user_id for user_id in (extra_user_ids or []) if isinstance(user_id, int)}
    if actor and actor.id:
        recipient_ids.add(actor.id)
    if not recipient_ids:
        return {"sent": 0, "sent_user_ids": []}

    content_lines = [
        f"调查编号: {survey.survey_no}",
        f"客户: {survey.customer_name}",
        f"项目: {survey.project_name or survey.project_code or '-'}",
        f"发送方式: {survey.send_method or '-'}",
    ]
    if ticket_no:
        content_lines.append(f"来源工单: {ticket_no}")

    service = get_notification_service(db)
    sent_user_ids: list[int] = []
    for user_id in sorted(recipient_ids):
        request = NotificationRequest(
            recipient_id=user_id,
            notification_type="SURVEY_SENT",
            category="service",
            title=f"满意度调查已发送: {survey.survey_no}",
            content="\n".join(content_lines),
            priority=NotificationPriority.NORMAL,
            channels=[NotificationChannel.SYSTEM],
            source_type="customer_satisfaction",
            source_id=survey.id,
            link_url=f"/service/surveys/{survey.id}",
            extra_data={"survey_id": survey.id, "ticket_no": ticket_no},
            force_send=True,
        )
        try:
            result = service.send_notification(request)
        except Exception as exc:
            logger.error(
                "满意度调查通知发送失败 survey_id=%s recipient_id=%s: %s",
                survey.id,
                user_id,
                exc,
                exc_info=True,
            )
            continue
        if result.get("success"):
            sent_user_ids.append(user_id)
    return {"sent": len(sent_user_ids), "sent_user_ids": sent_user_ids}


def mark_customer_satisfaction_sent(
    db: Session,
    survey: CustomerSatisfaction,
    *,
    actor: Optional[User] = None,
    ticket_no: Optional[str] = None,
    extra_user_ids: Optional[list[int]] = None,
) -> CustomerSatisfaction:
    if survey.status == SurveyStatusEnum.COMPLETED.value:
        raise HTTPException(status_code=400, detail="调查已完成，无法发送")

    survey.status = SurveyStatusEnum.SENT.value
    survey.send_date = survey.send_date or date.today()
    saved = save_obj(db, survey)
    _send_satisfaction_survey_notification(
        db,
        saved,
        actor=actor,
        ticket_no=ticket_no,
        extra_user_ids=extra_user_ids,
    )
    return saved


def create_service_ticket_satisfaction_survey(
    db: Session,
    ticket,
    *,
    current_user: User,
) -> CustomerSatisfaction:
    customer = getattr(ticket, "customer", None)
    project = getattr(ticket, "project", None)
    send_method = "SYSTEM"
    if getattr(customer, "contact_email", None):
        send_method = "EMAIL"
    elif getattr(customer, "contact_phone", None):
        send_method = "SMS"

    survey = CustomerSatisfaction(
        survey_no=generate_survey_no(db),
        survey_type=SurveyTypeEnum.SERVICE.value,
        customer_name=getattr(customer, "customer_name", None) or f"客户{ticket.customer_id}",
        customer_contact=getattr(customer, "contact_person", None),
        customer_email=getattr(customer, "contact_email", None),
        customer_phone=getattr(customer, "contact_phone", None),
        project_code=getattr(project, "project_code", None),
        project_name=getattr(project, "project_name", None),
        survey_date=date.today(),
        send_method=send_method,
        deadline=date.today() + timedelta(days=7),
        status=SurveyStatusEnum.DRAFT.value,
        created_by=current_user.id,
        created_by_name=current_user.real_name or current_user.username,
    )
    saved = save_obj(db, survey)

    extra_user_ids = [
        user_id
        for user_id in {
            getattr(ticket, "assigned_to_id", None),
            _as_int(getattr(ticket, "reported_by", None)),
            getattr(project, "pm_id", None),
        }
        if isinstance(user_id, int)
    ]
    return mark_customer_satisfaction_sent(
        db,
        saved,
        actor=current_user,
        ticket_no=getattr(ticket, "ticket_no", None),
        extra_user_ids=extra_user_ids,
    )


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_customer_satisfaction_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取满意度调查统计
    """
    query = filter_owned_service_query(
        db, db.query(CustomerSatisfaction), CustomerSatisfaction, current_user, owner_field="created_by"
    )

    sent_statuses = [
        SurveyStatusEnum.SENT.value,
        "APPROVED",
        SurveyStatusEnum.PENDING.value,
        "ACTIVE",
        SurveyStatusEnum.COMPLETED.value,
    ]
    pending_statuses = [
        SurveyStatusEnum.PENDING.value,
        "ACTIVE",
    ]
    completed_statuses = [
        SurveyStatusEnum.COMPLETED.value,
    ]

    total = query.count()
    sent = query.filter(CustomerSatisfaction.status.in_(sent_statuses)).count()
    pending = query.filter(CustomerSatisfaction.status.in_(pending_statuses)).count()
    completed = query.filter(CustomerSatisfaction.status.in_(completed_statuses)).count()

    # 计算平均分
    completed_surveys = (
        query
        .filter(
            CustomerSatisfaction.status.in_(completed_statuses),
            CustomerSatisfaction.overall_score.isnot(None),
        )
        .all()
    )
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


@router.get(
    "",
    response_model=PaginatedResponse[CustomerSatisfactionResponse],
    status_code=status.HTTP_200_OK,
)
def read_customer_satisfactions(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    survey_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    survey_type: Optional[str] = Query(None, description="调查类型筛选"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取满意度调查列表
    """
    query = db.query(CustomerSatisfaction)
    query = filter_owned_service_query(
        db, query, CustomerSatisfaction, current_user, owner_field="created_by"
    )

    if survey_status:
        survey_status = normalize_survey_status(survey_status)
        query = query.filter(CustomerSatisfaction.status == survey_status)
    if survey_type:
        query = query.filter(CustomerSatisfaction.survey_type == survey_type)
    if date_from:
        query = query.filter(CustomerSatisfaction.survey_date >= date_from)
    if date_to:
        query = query.filter(CustomerSatisfaction.survey_date <= date_to)

    # 应用关键词过滤（调查编号/客户名称/项目名称）
    query = apply_keyword_filter(
        query, CustomerSatisfaction, keyword, ["survey_no", "customer_name", "project_name"]
    )

    total = query.count()
    items = apply_pagination(
        query.order_by(desc(CustomerSatisfaction.survey_date)), pagination.offset, pagination.limit
    ).all()

    # 获取创建人姓名
    for item in items:
        if item.created_by:
            creator = db.query(User).filter(User.id == item.created_by).first()
            if creator:
                item.created_by_name = creator.real_name or creator.username

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
    current_user: User = Depends(security.require_permission("service:create")),
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
        status=SurveyStatusEnum.DRAFT.value,
        created_by=current_user.id,
        created_by_name=current_user.real_name or current_user.username,
    )
    return save_obj(db, survey)


@router.get(
    "/{survey_id}", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK
)
def read_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取满意度调查详情
    """
    survey = get_owned_service_object_or_404(
        db,
        CustomerSatisfaction,
        survey_id,
        current_user,
        "满意度调查不存在",
        owner_field="created_by",
    )

    return survey


@router.put(
    "/{survey_id}", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK
)
def update_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    survey_in: CustomerSatisfactionUpdate,
    current_user: User = Depends(security.require_permission("service:update")),
) -> Any:
    """
    更新满意度调查
    """
    survey = get_owned_service_object_or_404(
        db,
        CustomerSatisfaction,
        survey_id,
        current_user,
        "满意度调查不存在",
        owner_field="created_by",
    )

    if survey_in.status is not None:
        survey.status = survey_in.status
        if survey_in.status == SurveyStatusEnum.SENT and not survey.send_date:
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

    if survey_in.status == SurveyStatusEnum.COMPLETED and survey.overall_score:
        survey.status = SurveyStatusEnum.COMPLETED.value

    return save_obj(db, survey)


@router.post(
    "/{survey_id}/send", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK
)
def send_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    current_user: User = Depends(security.require_permission("service:update")),
) -> Any:
    """
    发送满意度调查
    """
    survey = get_owned_service_object_or_404(
        db,
        CustomerSatisfaction,
        survey_id,
        current_user,
        "满意度调查不存在",
        owner_field="created_by",
    )

    return mark_customer_satisfaction_sent(db, survey, actor=current_user)


@router.post(
    "/{survey_id}/submit",
    response_model=CustomerSatisfactionResponse,
    status_code=status.HTTP_200_OK,
)
def submit_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    survey_in: CustomerSatisfactionSubmit,
) -> Any:
    """
    客户提交满意度调查。

    该入口不要求员工登录，避免继续由员工代填满意度。
    """
    survey = get_or_404(db, CustomerSatisfaction, survey_id, "满意度调查不存在")

    if survey.status == SurveyStatusEnum.COMPLETED.value:
        raise HTTPException(status_code=400, detail="调查已完成，不能重复提交")
    if survey.status not in {SurveyStatusEnum.SENT.value, SurveyStatusEnum.PENDING.value}:
        raise HTTPException(status_code=400, detail="调查尚未发送，不能提交")

    survey.status = SurveyStatusEnum.COMPLETED.value
    survey.response_date = date.today()
    survey.overall_score = survey_in.overall_score
    survey.scores = survey_in.scores
    survey.feedback = survey_in.feedback
    survey.suggestions = survey_in.suggestions

    return save_obj(db, survey)
