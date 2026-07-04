# -*- coding: utf-8 -*-
"""AS-21: service ticket close should trigger customer satisfaction follow-up."""

from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

from app.api.v1.endpoints.service import surveys
from app.api.v1.endpoints.service.tickets.status import close_service_ticket
from app.models.notification import Notification
from app.models.project import Customer, Project
from app.models.service import CustomerSatisfaction, ServiceTicket
from app.models.service.enums import ServiceTicketStatusEnum, SurveyStatusEnum
from app.models.user import User
from app.schemas.service import ServiceTicketClose


def _seed_resolved_ticket(db_session):
    user = User(
        username="as21-admin",
        password_hash="x",
        real_name="AS21 Admin",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(
        customer_code="AS21-CUST",
        customer_name="AS21 客户",
        contact_person="张工",
        contact_phone="13800000000",
        contact_email="customer@example.com",
    )
    db_session.add_all([user, customer])
    db_session.flush()
    project = Project(
        project_code="AS21-PROJ",
        project_name="AS21 项目",
        customer_id=customer.id,
        pm_id=user.id,
    )
    db_session.add(project)
    db_session.flush()
    ticket = ServiceTicket(
        ticket_no="AS21-TICKET",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="AS21 关单回访",
        urgency="MEDIUM",
        reported_by=str(user.id),
        reported_time=datetime(2026, 7, 4, 10, 0),
        assigned_to_id=user.id,
        status=ServiceTicketStatusEnum.RESOLVED.value,
    )
    db_session.add(ticket)
    db_session.commit()
    return user, ticket


def test_close_ticket_creates_and_sends_service_satisfaction_survey(db_session):
    user, ticket = _seed_resolved_ticket(db_session)

    close_service_ticket(
        db=db_session,
        ticket_id=ticket.id,
        close_in=ServiceTicketClose(solution="已修复"),
        current_user=user,
    )

    survey = (
        db_session.query(CustomerSatisfaction)
        .filter(CustomerSatisfaction.survey_type == "SERVICE")
        .one()
    )
    notification = (
        db_session.query(Notification)
        .filter(
            Notification.source_type == "customer_satisfaction",
            Notification.source_id == survey.id,
            Notification.user_id == user.id,
        )
        .one()
    )

    assert survey.status == SurveyStatusEnum.SENT.value
    assert survey.customer_name == "AS21 客户"
    assert survey.customer_contact == "张工"
    assert survey.customer_email == "customer@example.com"
    assert survey.project_code == "AS21-PROJ"
    assert survey.project_name == "AS21 项目"
    assert survey.send_date is not None
    assert "AS21-TICKET" in notification.content


def test_customer_can_submit_survey_without_employee_update(db_session):
    user, _ticket = _seed_resolved_ticket(db_session)
    survey = CustomerSatisfaction(
        survey_no="AS21-SURVEY",
        survey_type="SERVICE",
        customer_name="AS21 客户",
        survey_date=datetime(2026, 7, 4).date(),
        send_method="EMAIL",
        status=SurveyStatusEnum.SENT.value,
        created_by=user.id,
        created_by_name=user.real_name,
    )
    db_session.add(survey)
    db_session.commit()

    result = surveys.submit_customer_satisfaction(
        db=db_session,
        survey_id=survey.id,
        survey_in=SimpleNamespace(
            overall_score=Decimal("4.5"),
            scores={"service": 5},
            feedback="响应及时",
            suggestions="保持",
        ),
    )

    assert result.status == SurveyStatusEnum.COMPLETED.value
    assert result.response_date is not None
    assert result.overall_score == Decimal("4.5")
    assert result.feedback == "响应及时"
