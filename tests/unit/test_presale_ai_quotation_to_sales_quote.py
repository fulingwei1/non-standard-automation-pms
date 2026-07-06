# -*- coding: utf-8 -*-
"""Presale AI quotation drafts can be promoted into the formal quote chain."""

from decimal import Decimal
from uuid import uuid4

from app.models.presale import PresaleSupportTicket
from app.models.presale_ai_quotation import (
    PresaleAIQuotation,
    QuotationStatus,
    QuotationType,
)
from app.models.project import Customer
from app.models.sales.leads import Opportunity
from app.models.sales.quotes import Quote, QuoteItem, QuoteVersion
from app.models.user import User
from app.services.presale.presale_ai_quotation_service import AIQuotationGeneratorService


def _suffix() -> str:
    return uuid4().hex[:8]


def test_promote_ai_quotation_route_registered():
    from app.modules.presale.api.presale_ai_quotation import router

    assert any(
        route.path == "/presale/ai/quotation/{quotation_id}/promote-to-sales-quote"
        and "POST" in route.methods
        for route in router.routes
    )


def test_promote_ai_quotation_creates_formal_quote_version_and_items(db_session):
    suffix = _suffix()
    user = User(
        username=f"ai_quote_bridge_{suffix}",
        password_hash="x",
        real_name="AI报价确认人",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    customer = Customer(
        customer_code=f"CUST-{suffix}",
        customer_name="AI报价客户",
        created_by=user.id,
    )
    db_session.add(customer)
    db_session.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-{suffix}",
        customer_id=customer.id,
        opp_name="AI报价商机",
        owner_id=user.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    ticket = PresaleSupportTicket(
        ticket_no=f"TICKET-{suffix}",
        title="FCT测试系统售前支持",
        ticket_type="QUOTATION",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        opportunity_id=opportunity.id,
        applicant_id=user.id,
        created_by=user.id,
    )
    db_session.add(ticket)
    db_session.flush()

    quotation = PresaleAIQuotation(
        presale_ticket_id=ticket.id,
        customer_id=customer.id,
        quotation_number=f"AIQ-{suffix}",
        quotation_type=QuotationType.STANDARD,
        items=[
            {
                "name": "FCT功能测试主机",
                "description": "含PLC控制、测试仪表集成和安全防护",
                "quantity": 2,
                "unit": "套",
                "unit_price": 100000,
                "total_price": 200000,
                "category": "自动化集成",
            }
        ],
        subtotal=Decimal("200000"),
        tax=Decimal("26000"),
        discount=Decimal("10000"),
        total=Decimal("216000"),
        payment_terms="30/40/30",
        validity_days=45,
        status=QuotationStatus.DRAFT,
        version=1,
        created_by=user.id,
    )
    db_session.add(quotation)
    db_session.commit()

    quote = AIQuotationGeneratorService(db_session).promote_to_sales_quote(
        quotation_id=quotation.id,
        user_id=user.id,
    )

    version = db_session.query(QuoteVersion).filter(QuoteVersion.quote_id == quote.id).one()
    items = db_session.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
    db_session.refresh(quotation)

    assert isinstance(quote, Quote)
    assert quote.opportunity_id == opportunity.id
    assert quote.customer_id == customer.id
    assert quote.current_version_id == version.id
    assert version.presale_ticket_id == ticket.id
    assert version.total_price == Decimal("216000.00")
    assert version.amount_without_tax == Decimal("190000.00")
    assert version.tax_amount == Decimal("26000.00")
    assert version.tax_rate == Decimal("13.00")
    assert len(items) == 1
    assert items[0].item_name == "FCT功能测试主机"
    assert items[0].qty == Decimal("2.00")
    assert items[0].unit_price == Decimal("100000.00")
    assert items[0].cost_category == "自动化集成"
    assert quotation.status == QuotationStatus.ACCEPTED
    assert f"promoted_quote_id={quote.id}" in (quotation.notes or "")


def test_promote_ai_quotation_rejects_without_opportunity(db_session):
    suffix = _suffix()
    user = User(username=f"ai_quote_no_opp_{suffix}", password_hash="x", is_active=True)
    db_session.add(user)
    db_session.flush()

    customer = Customer(customer_code=f"CUST-NOOPP-{suffix}", customer_name="无商机客户")
    db_session.add(customer)
    db_session.flush()

    quotation = PresaleAIQuotation(
        presale_ticket_id=999999,
        customer_id=customer.id,
        quotation_number=f"AIQ-NOOPP-{suffix}",
        quotation_type=QuotationType.BASIC,
        items=[],
        subtotal=Decimal("0"),
        tax=Decimal("0"),
        discount=Decimal("0"),
        total=Decimal("0"),
        validity_days=30,
        status=QuotationStatus.DRAFT,
        version=1,
        created_by=user.id,
    )
    db_session.add(quotation)
    db_session.commit()

    try:
        AIQuotationGeneratorService(db_session).promote_to_sales_quote(quotation.id, user.id)
    except ValueError as exc:
        assert "商机" in str(exc)
    else:
        raise AssertionError("expected promotion to require an opportunity")
