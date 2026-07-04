# -*- coding: utf-8 -*-
"""AS-07: project after-sales must use actionable service tickets, not a read-only shadow table."""

from datetime import datetime

from app.api.v1.endpoints import after_sales
from app.models.project import Customer, Project
from app.models.service import ServiceTicket
from app.models.service.enums import ServiceTicketStatusEnum
from app.models.user import User


def _seed_project(db_session):
    user = User(
        username="as07-admin",
        password_hash="x",
        real_name="AS07 Admin",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(customer_code="AS07-CUST", customer_name="AS07 客户")
    db_session.add_all([user, customer])
    db_session.flush()
    project = Project(
        project_code="AS07-PROJ",
        project_name="AS07 项目",
        customer_id=customer.id,
        pm_id=user.id,
    )
    db_session.add(project)
    db_session.commit()
    return user, customer, project


def test_after_sales_support_ticket_list_reads_central_service_tickets(db_session):
    user, customer, project = _seed_project(db_session)
    ticket = ServiceTicket(
        ticket_no="AS07-ST-001",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="TECHNICAL",
        problem_desc="售后中心应展示统一服务工单",
        urgency="HIGH",
        reported_by=str(user.id),
        reported_time=datetime(2026, 7, 4, 9, 0),
        status=ServiceTicketStatusEnum.PENDING.value,
    )
    db_session.add(ticket)
    db_session.commit()

    result = after_sales.get_project_support_tickets(
        project.id,
        db=db_session,
        current_user=user,
    )

    assert result[0]["source"] == "service_ticket"
    assert result[0]["id"] == ticket.id
    assert result[0]["ticket_no"] == "AS07-ST-001"
    assert result[0]["subject"] == "售后中心应展示统一服务工单"
    assert result[0]["status"] == ServiceTicketStatusEnum.PENDING.value


def test_after_sales_support_ticket_create_writes_central_service_ticket(
    db_session,
    monkeypatch,
):
    user, _customer, project = _seed_project(db_session)
    monkeypatch.setattr(after_sales, "_send_after_sales_notification", lambda *args, **kwargs: None)

    result = after_sales.create_support_ticket(
        project_id=project.id,
        subject="统一工单入口",
        description="不能再写 after_sales_support_tickets 影子表",
        category="TECHNICAL",
        priority="HIGH",
        db=db_session,
        current_user=user,
    )

    ticket = db_session.query(ServiceTicket).filter(ServiceTicket.id == result["id"]).one()
    assert result["source"] == "service_ticket"
    assert ticket.project_id == project.id
    assert ticket.customer_id == project.customer_id
    assert ticket.problem_type == "TECHNICAL"
    assert ticket.problem_desc == "不能再写 after_sales_support_tickets 影子表"
    assert ticket.urgency == "HIGH"
