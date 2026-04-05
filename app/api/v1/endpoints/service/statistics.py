# -*- coding: utf-8 -*-
"""
客服统计 API endpoints
"""

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import CustomerSatisfaction, ServiceRecord, ServiceTicket
from app.models.service.enums import (
    ServiceRecordStatusEnum,
    ServiceTicketStatusEnum,
    SurveyStatusEnum,
)
from app.models.user import User
from app.schemas.service import ServiceDashboardStatistics

from .access import filter_owned_service_query, filter_service_project_query

router = APIRouter()


@router.get("/dashboard-statistics", response_model=ServiceDashboardStatistics, status_code=200)
def get_service_dashboard_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    客服部统计（给生产总监看）
    """
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())

    ticket_query = filter_service_project_query(
        db, db.query(ServiceTicket), current_user, ServiceTicket.project_id
    )
    record_query = filter_service_project_query(
        db, db.query(ServiceRecord), current_user, ServiceRecord.project_id
    )
    survey_query = filter_owned_service_query(
        db,
        db.query(CustomerSatisfaction),
        CustomerSatisfaction,
        current_user,
        owner_field="created_by",
    )

    # 服务案例统计
    active_cases = ticket_query.filter(
        ServiceTicket.status.in_(
            [
                ServiceTicketStatusEnum.PENDING.value,
                ServiceTicketStatusEnum.IN_PROGRESS.value,
            ]
        )
    ).count()

    resolved_today = (
        ticket_query
        .filter(
            ServiceTicket.status.in_(
                [
                    ServiceTicketStatusEnum.RESOLVED.value,
                    ServiceTicketStatusEnum.CLOSED.value,
                ]
            ),
            ServiceTicket.resolved_time >= today_start,
        )
        .count()
    )

    pending_cases = ticket_query.filter(
        ServiceTicket.status == ServiceTicketStatusEnum.PENDING.value
    ).count()

    # 平均响应时间（从服务工单中计算：响应时间 - 报告时间）
    tickets_with_response = ticket_query.filter(
        ServiceTicket.response_time.isnot(None), ServiceTicket.reported_time.isnot(None)
    ).all()

    avg_response_time = 0.0
    if tickets_with_response:
        total_hours = 0
        for ticket in tickets_with_response:
            if ticket.response_time and ticket.reported_time:
                delta = ticket.response_time - ticket.reported_time
                total_hours += delta.total_seconds() / 3600.0
        avg_response_time = (
            total_hours / len(tickets_with_response) if tickets_with_response else 0.0
        )

    # 客户满意度（转换为百分制）
    completed_surveys = survey_query.filter(
        CustomerSatisfaction.status == SurveyStatusEnum.COMPLETED.value,
        CustomerSatisfaction.overall_score.isnot(None),
    ).all()

    customer_satisfaction = 0.0
    if completed_surveys:
        total_score = sum(float(s.overall_score) for s in completed_surveys)
        customer_satisfaction = (total_score / len(completed_surveys)) * 20  # 5分制转百分制

    # 现场服务（从服务记录中统计，使用INSTALLATION类型作为现场服务）
    on_site_services = record_query.filter(
        ServiceRecord.service_type.in_(["INSTALLATION", "REPAIR", "MAINTENANCE"]),
        ServiceRecord.status.in_(
            [
                ServiceRecordStatusEnum.SCHEDULED.value,
                ServiceRecordStatusEnum.IN_PROGRESS.value,
            ]
        ),
    ).count()

    engineers = (
        record_query.filter(ServiceRecord.service_engineer_id.isnot(None))
        .with_entities(ServiceRecord.service_engineer_id)
        .distinct()
        .all()
    )
    total_engineers = len(engineers)
    active_engineers = total_engineers

    return ServiceDashboardStatistics(
        active_cases=active_cases,
        resolved_today=resolved_today,
        pending_cases=pending_cases,
        avg_response_time=avg_response_time,
        customer_satisfaction=customer_satisfaction,
        on_site_services=on_site_services,
        total_engineers=total_engineers,
        active_engineers=active_engineers,
    )
