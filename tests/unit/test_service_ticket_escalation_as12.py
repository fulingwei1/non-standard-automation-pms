# -*- coding: utf-8 -*-
"""AS-12: service tickets can escalate into quality issues and ECNs."""

import uuid
from datetime import datetime

from app.api.v1.endpoints.service.tickets.issues import (
    TicketEcnEscalation,
    TicketIssueEscalation,
    escalate_ticket_to_ecn,
    escalate_ticket_to_issue,
)
from app.api.v1.endpoints.itr import read_itr_dashboard, read_ticket_timeline
from app.models.ecn import Ecn
from app.models.issue import Issue
from app.models.project import Customer, Machine, Project
from app.models.service import ServiceTicket
from app.models.user import User


def _seed_service_ticket(db_session):
    suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"as12-admin-{suffix}",
        password_hash="x",
        real_name="AS12 Admin",
        department="售后部",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(
        customer_code=f"AS12-CUST-{suffix}",
        customer_name="AS12 客户",
    )
    db_session.add_all([user, customer])
    db_session.flush()

    project = Project(
        project_code=f"AS12-PROJ-{suffix}",
        project_name="AS12 项目",
        customer_id=customer.id,
        pm_id=user.id,
    )
    db_session.add(project)
    db_session.flush()

    machine = Machine(
        project_id=project.id,
        customer_id=customer.id,
        machine_code=f"AS12-M-{suffix}",
        machine_name="AS12 设备",
        machine_type="TEST",
        serial_no=f"SN-AS12-{suffix}",
        status="DELIVERED",
    )
    db_session.add(machine)
    db_session.flush()

    ticket = ServiceTicket(
        ticket_no=f"AS12-TICKET-{suffix}",
        project_id=project.id,
        customer_id=customer.id,
        machine_id=machine.id,
        problem_type="MECHANICAL",
        problem_desc="客户现场反复出现定位偏差，需要质量闭环",
        urgency="HIGH",
        reported_by=str(user.id),
        reported_time=datetime(2026, 7, 4, 11, 0),
        status="IN_PROGRESS",
    )
    db_session.add(ticket)
    db_session.commit()
    db_session.refresh(ticket)
    return user, ticket


def test_service_ticket_can_escalate_to_quality_issue(db_session):
    user, ticket = _seed_service_ticket(db_session)

    response = escalate_ticket_to_issue(
        db=db_session,
        ticket_id=ticket.id,
        escalation_in=TicketIssueEscalation(
            title="定位偏差质量问题",
            severity="CRITICAL",
            is_blocking=True,
        ),
        current_user=user,
    )

    issue = db_session.query(Issue).filter(Issue.id == response.id).one()
    assert issue.category == "QUALITY"
    assert issue.service_ticket_id == ticket.id
    assert issue.project_id == ticket.project_id
    assert issue.machine_id == ticket.machine_id
    assert issue.title == "定位偏差质量问题"

    db_session.refresh(ticket)
    assert any(entry["type"] == "ISSUE_ESCALATED" for entry in ticket.timeline)

    timeline = read_ticket_timeline(db=db_session, ticket_id=ticket.id, current_user=user)
    assert any(
        event["event_type"] == "ISSUE_CREATED" and event["issue_id"] == issue.id
        for event in timeline["timeline"]
    )

    dashboard = read_itr_dashboard(
        db=db_session,
        project_id=ticket.project_id,
        start_date=None,
        end_date=None,
        current_user=user,
    )
    assert dashboard["issues"]["total"] >= 1


def test_service_ticket_can_escalate_to_ecn_draft(db_session):
    user, ticket = _seed_service_ticket(db_session)

    response = escalate_ticket_to_ecn(
        db=db_session,
        ticket_id=ticket.id,
        escalation_in=TicketEcnEscalation(
            ecn_title="定位机构设计变更",
            change_reason="售后重复质量问题",
        ),
        current_user=user,
    )

    ecn = db_session.query(Ecn).filter(Ecn.id == response.id).one()
    assert ecn.status == "DRAFT"
    assert ecn.source_type == "SERVICE_TICKET"
    assert ecn.source_id == ticket.id
    assert ecn.source_no == ticket.ticket_no
    assert ecn.project_id == ticket.project_id
    assert ecn.machine_id == ticket.machine_id
    assert ecn.change_reason == "售后重复质量问题"

    db_session.refresh(ticket)
    assert any(entry["type"] == "ECN_ESCALATED" for entry in ticket.timeline)
