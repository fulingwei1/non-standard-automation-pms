# -*- coding: utf-8 -*-
"""APPR-18: quote items should become contract deliverables."""

from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.v1.endpoints.sales.contracts.basic import (
    ContractFromQuoteRequest,
    create_contract_from_quote,
)
from app.models.project import Customer
from app.models.sales import ContractDeliverable, Opportunity, Quote, QuoteItem, QuoteVersion
from app.models.user import User


def _create_user(db: Session) -> User:
    suffix = uuid4().hex[:8]
    user = User(
        username=f"appr18-{suffix}",
        password_hash="test",
        real_name="APPR18 Tester",
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.flush()
    return user


def _create_quote_with_items(db: Session, user: User) -> Quote:
    suffix = uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-APPR18-{suffix}",
        customer_name=f"APPR18 客户 {suffix}",
        status="ACTIVE",
        created_by=user.id,
        sales_owner_id=user.id,
    )
    db.add(customer)
    db.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-APPR18-{suffix[:6]}",
        customer_id=customer.id,
        opp_name=f"APPR18 商机 {suffix}",
        stage="QUOTATION",
        probability=80,
        owner_id=user.id,
    )
    db.add(opportunity)
    db.flush()

    quote = Quote(
        quote_code=f"QT-APPR18-{suffix[:6]}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        status="APPROVED",
        owner_id=user.id,
    )
    db.add(quote)
    db.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        amount_without_tax=Decimal("1000.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("130.00"),
        amount_with_tax=Decimal("1130.00"),
        total_price=Decimal("1130.00"),
        cost_total=Decimal("700.00"),
        gross_margin=Decimal("38.05"),
        created_by=user.id,
    )
    db.add(version)
    db.flush()
    quote.current_version_id = version.id

    db.add_all(
        [
            QuoteItem(
                quote_version_id=version.id,
                item_type="EQUIPMENT",
                item_name="PACK EOL 测试线",
                qty=Decimal("1.00"),
                unit_price=Decimal("900.00"),
                cost=Decimal("600.00"),
                unit="套",
            ),
            QuoteItem(
                quote_version_id=version.id,
                item_type="SERVICE",
                item_name="现场安装调试",
                qty=Decimal("1.00"),
                unit_price=Decimal("230.00"),
                cost=Decimal("100.00"),
                unit="项",
            ),
        ]
    )
    db.commit()
    return quote


def test_contract_from_quote_copies_quote_items_to_deliverables(db_session: Session):
    user = _create_user(db_session)
    quote = _create_quote_with_items(db_session, user)

    contract = create_contract_from_quote(
        db=db_session,
        request=ContractFromQuoteRequest(
            quote_id=quote.id,
            payment_terms="30%预付，70%终验后支付",
        ),
        skip_g3_validation=True,
        current_user=user,
    )

    deliverables = (
        db_session.query(ContractDeliverable)
        .filter(ContractDeliverable.contract_id == contract.id)
        .order_by(ContractDeliverable.id.asc())
        .all()
    )

    assert [d.deliverable_name for d in deliverables] == [
        "PACK EOL 测试线",
        "现场安装调试",
    ]
    assert [d.deliverable_type for d in deliverables] == ["EQUIPMENT", "SERVICE"]
    assert all(d.required_for_payment for d in deliverables)
    assert all((d.template_ref or "").startswith("quote_item:") for d in deliverables)
    assert [d.deliverable_name for d in contract.deliverables] == [
        "PACK EOL 测试线",
        "现场安装调试",
    ]
