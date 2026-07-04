# -*- coding: utf-8 -*-
"""AS-05: service tickets must follow a real status transition matrix."""

import uuid
from datetime import datetime

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.service.tickets.status import (
    close_service_ticket,
    update_service_ticket_status,
)
from app.models.project import Customer, Project
from app.models.service import ServiceTicket
from app.models.service.enums import ServiceTicketStatusEnum
from app.models.user import User
from app.schemas.service import ServiceTicketClose


def _seed_ticket(db_session, *, status: str = ServiceTicketStatusEnum.PENDING.value):
    suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"as05-admin-{suffix}",
        password_hash="x",
        real_name="AS05 Admin",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(
        customer_code=f"AS05-CUST-{suffix}",
        customer_name="AS05 客户",
    )
    db_session.add_all([user, customer])
    db_session.flush()
    project = Project(
        project_code=f"AS05-PROJ-{suffix}",
        project_name="AS05 项目",
        customer_id=customer.id,
        pm_id=user.id,
    )
    db_session.add(project)
    db_session.flush()
    ticket = ServiceTicket(
        ticket_no=f"AS05-TICKET-{suffix}",
        project_id=project.id,
        customer_id=customer.id,
        problem_type="SOFTWARE",
        problem_desc="状态机测试",
        urgency="HIGH",
        reported_by=str(user.id),
        reported_time=datetime(2026, 7, 4, 10, 0),
        status=status,
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return user, ticket


def test_pending_ticket_cannot_jump_to_resolved_or_closed(db_session):
    user, ticket = _seed_ticket(db_session)

    with pytest.raises(HTTPException) as exc_info:
        update_service_ticket_status(
            db=db_session,
            ticket_id=ticket.id,
            status=ServiceTicketStatusEnum.RESOLVED.value,
            current_user=user,
        )

    assert exc_info.value.status_code == 400
    assert "不允许的状态转换" in exc_info.value.detail
    db_session.refresh(ticket)
    assert ticket.status == ServiceTicketStatusEnum.PENDING.value

    with pytest.raises(HTTPException) as exc_info:
        close_service_ticket(
            db=db_session,
            ticket_id=ticket.id,
            close_in=ServiceTicketClose(solution="直接关闭"),
            current_user=user,
        )

    assert exc_info.value.status_code == 400
    assert "RESOLVED" in exc_info.value.detail
    db_session.refresh(ticket)
    assert ticket.status == ServiceTicketStatusEnum.PENDING.value


def test_service_ticket_happy_path_requires_resolved_before_close(db_session):
    user, ticket = _seed_ticket(db_session)

    update_service_ticket_status(
        db=db_session,
        ticket_id=ticket.id,
        status=ServiceTicketStatusEnum.IN_PROGRESS.value,
        current_user=user,
    )
    db_session.refresh(ticket)
    assert ticket.status == ServiceTicketStatusEnum.IN_PROGRESS.value
    assert ticket.response_time is not None

    update_service_ticket_status(
        db=db_session,
        ticket_id=ticket.id,
        status=ServiceTicketStatusEnum.RESOLVED.value,
        current_user=user,
    )
    db_session.refresh(ticket)
    assert ticket.status == ServiceTicketStatusEnum.RESOLVED.value

    close_service_ticket(
        db=db_session,
        ticket_id=ticket.id,
        close_in=ServiceTicketClose(solution="按流程关闭"),
        current_user=user,
    )
    db_session.refresh(ticket)
    assert ticket.status == ServiceTicketStatusEnum.CLOSED.value
    assert ticket.resolved_time is not None
