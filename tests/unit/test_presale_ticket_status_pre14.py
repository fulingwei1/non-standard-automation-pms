# -*- coding: utf-8 -*-
"""PRE-14: presale support ticket status vocabulary must be coherent."""

import uuid

from app.api.v1.endpoints.presale.tickets.crud import create_ticket, read_tickets
from app.api.v1.endpoints.presale.tickets.operations import (
    accept_ticket,
    update_ticket_progress,
)
from app.api.v1.endpoints.presale.tickets.utils import build_ticket_response
from app.common.pagination import PaginationParams
from app.models.presale import PresaleSupportTicket, PresaleTicketProgress
from app.models.sales import Customer, Opportunity
from app.models.user import User
from app.schemas.presale import TicketAcceptRequest, TicketCreate, TicketProgressUpdate


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_user(db_session) -> User:
    user = User(
        username=_unique("pre14").lower(),
        password_hash="test",
        real_name="PRE14测试用户",
        is_active=True,
        is_superuser=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _seed_ticket(db_session, user: User, status: str) -> PresaleSupportTicket:
    ticket = PresaleSupportTicket(
        ticket_no=_unique("PST"),
        title=f"{status}工单",
        ticket_type="SOLUTION",
        applicant_id=user.id,
        applicant_name=user.real_name,
        status=status,
        created_by=user.id,
    )
    db_session.add(ticket)
    db_session.commit()
    return ticket


def test_processing_status_is_queryable_and_updatable_as_in_progress(db_session):
    user = _seed_user(db_session)
    legacy_ticket = _seed_ticket(db_session, user, "PROCESSING")

    page = read_tickets(
        db=db_session,
        pagination=PaginationParams(page=1, page_size=20, offset=0, limit=20),
        keyword=None,
        status="IN_PROGRESS",
        ticket_type=None,
        ticket_id=None,
        lead_id=None,
        opportunity_id=None,
        project_id=None,
        applicant_id=None,
        assignee_id=None,
        customer_id=None,
        current_user=user,
    )
    assert [item.id for item in page["items"]] == [legacy_ticket.id]
    assert page["items"][0].status == "IN_PROGRESS"

    updated = update_ticket_progress(
        db=db_session,
        ticket_id=legacy_ticket.id,
        progress_request=TicketProgressUpdate(progress_note="已开始方案设计", progress_percent=30),
        current_user=user,
    )

    db_session.refresh(legacy_ticket)
    assert updated.status == "IN_PROGRESS"
    assert legacy_ticket.status == "IN_PROGRESS"
    assert db_session.query(PresaleTicketProgress).filter_by(ticket_id=legacy_ticket.id).count() == 1


def test_review_status_is_accepted_as_pending_for_legacy_review_tickets(db_session):
    user = _seed_user(db_session)
    legacy_review_ticket = _seed_ticket(db_session, user, "REVIEW")

    assert build_ticket_response(legacy_review_ticket).status == "PENDING"

    accepted = accept_ticket(
        db=db_session,
        ticket_id=legacy_review_ticket.id,
        accept_request=TicketAcceptRequest(),
        current_user=user,
    )

    db_session.refresh(legacy_review_ticket)
    assert accepted.status == "ACCEPTED"
    assert legacy_review_ticket.status == "ACCEPTED"


def test_solution_review_ticket_is_created_as_pending_not_review(db_session):
    user = _seed_user(db_session)
    customer = Customer(customer_code=_unique("CUST"), customer_name="PRE14客户")
    db_session.add(customer)
    db_session.flush()
    opportunity = Opportunity(
        opp_code=_unique("OPP"),
        opp_name="PRE14商机",
        customer_id=customer.id,
        owner_id=user.id,
        gate_status="PASS",
    )
    db_session.add(opportunity)
    db_session.commit()

    created = create_ticket(
        db=db_session,
        ticket_in=TicketCreate(
            title="方案评审申请",
            ticket_type="SOLUTION_REVIEW",
            opportunity_id=opportunity.id,
        ),
        current_user=user,
    )

    assert created.status == "PENDING"
