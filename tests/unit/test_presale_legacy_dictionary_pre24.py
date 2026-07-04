# -*- coding: utf-8 -*-
"""PRE-24: legacy presale dictionaries must be normalized and query-safe."""

import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.ai_copilot import my_day
from app.api.v1.endpoints.sales.opportunity_workflow import (
    RequestPresaleSupportRequest,
    request_presale_support,
)
from app.models.presale_ai_quotation import PresaleAIQuotation
from app.models.sales import Customer, Opportunity
from app.models.user import User
from app.services.presale.presale_ai_quotation_service import AIQuotationGeneratorService


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_user_customer(db_session) -> tuple[User, Customer]:
    user = User(
        username=_unique("pre24").lower(),
        password_hash="test",
        real_name="PRE24测试用户",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="PRE24测试客户",
    )
    db_session.add(customer)
    db_session.flush()
    return user, customer


def _seed_opportunity(db_session, user: User, customer: Customer, status: str | None) -> Opportunity:
    opportunity = Opportunity(
        opp_code=_unique("OPP"),
        opp_name=f"PRE24商机-{status or 'NULL'}",
        customer_id=customer.id,
        owner_id=user.id,
        stage="DISCOVERY",
        assessment_status=status,
    )
    db_session.add(opportunity)
    db_session.flush()
    return opportunity


def test_quotation_history_normalizes_legacy_type_values():
    engine = create_engine("sqlite:///:memory:")
    PresaleAIQuotation.__table__.create(bind=engine)
    db = sessionmaker(bind=engine)()
    db.execute(
        text(
            """
            INSERT INTO presale_ai_quotation(
                presale_ticket_id, quotation_number, quotation_type, items,
                subtotal, tax, discount, total, validity_days, status,
                version, created_by, created_at
            )
            VALUES
            (1, 'QT-PRE24-1', 'AUTO', '[]', 0, 0, 0, 0, 30, 'DRAFT', 3, 1, CURRENT_TIMESTAMP),
            (1, 'QT-PRE24-2', 'MANUAL', '[]', 0, 0, 0, 0, 30, 'DRAFT', 2, 1, CURRENT_TIMESTAMP),
            (1, 'QT-PRE24-3', 'NORMAL', '[]', 0, 0, 0, 0, 30, 'DRAFT', 1, 1, CURRENT_TIMESTAMP)
            """
        )
    )
    db.commit()

    history = AIQuotationGeneratorService(db).get_quotation_history(ticket_id=1)

    assert [row["version"] for row in history] == [3, 2, 1]
    assert {row["quotation_type"] for row in history} == {"standard"}
    assert {row["status"] for row in history} == {"draft"}


def test_request_presale_support_writes_canonical_pending_status(db_session):
    user, customer = _seed_user_customer(db_session)
    opportunity = _seed_opportunity(db_session, user, customer, None)
    db_session.commit()

    response = request_presale_support(
        db=db_session,
        opp_id=opportunity.id,
        req=RequestPresaleSupportRequest(),
        current_user=user,
    )

    db_session.refresh(opportunity)
    assert response.data["assessment_status"] == "PENDING"
    assert opportunity.assessment_status == "PENDING"


def test_my_day_counts_all_open_assessment_status_aliases(db_session, monkeypatch):
    db_session.execute(text("ALTER TABLE opportunities ADD COLUMN last_progress_at DATETIME"))
    db_session.commit()
    user, customer = _seed_user_customer(db_session)
    for status in (
        None,
        "REQUESTED",
        "PENDING",
        "IN_PROGRESS",
        "ASSESSMENT_IN_PROGRESS",
        "ASSESSMENT_COMPLETED",
        "COMPLETED",
    ):
        _seed_opportunity(db_session, user, customer, status)
    db_session.commit()
    monkeypatch.setattr("app.api.v1.endpoints.ai_copilot._ai", lambda *_args, **_kwargs: "focus")

    response = my_day(db=db_session, current_user=user)

    assert response.data["my_opportunities"] == 7
    assert response.data["unassessed"] == 5
