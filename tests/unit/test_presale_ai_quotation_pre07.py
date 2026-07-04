# -*- coding: utf-8 -*-
"""PRE-07: updating quotation items must recompute tax/discount amounts."""

from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.presale_ai_quotation import (
    PresaleAIQuotation,
    QuotationStatus,
    QuotationType,
    QuotationVersion,
)
from app.schemas.presale_ai_quotation import QuotationItem, QuotationUpdateRequest
from app.services.presale.presale_ai_quotation_service import AIQuotationGeneratorService


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    PresaleAIQuotation.__table__.create(bind=engine)
    QuotationVersion.__table__.create(bind=engine)
    return sessionmaker(bind=engine)()


def _seed_quotation(db):
    quotation = PresaleAIQuotation(
        presale_ticket_id=1,
        customer_id=1,
        quotation_number="QT-PRE07-0001",
        quotation_type=QuotationType.STANDARD,
        items=[
            {
                "name": "旧项目",
                "quantity": 1,
                "unit": "项",
                "unit_price": 100,
                "total_price": 100,
            }
        ],
        subtotal=Decimal("100.00"),
        tax=Decimal("13.00"),
        discount=Decimal("5.00"),
        total=Decimal("108.00"),
        validity_days=30,
        status=QuotationStatus.DRAFT,
        version=1,
        created_by=7,
    )
    db.add(quotation)
    db.commit()
    db.refresh(quotation)
    return quotation


def test_update_items_recomputes_tax_and_discount_using_existing_rates():
    db = _make_session()
    quotation = _seed_quotation(db)
    service = AIQuotationGeneratorService(db)

    updated = service.update_quotation(
        quotation.id,
        QuotationUpdateRequest(
            items=[
                QuotationItem(
                    name="新项目",
                    quantity=Decimal("2"),
                    unit="项",
                    unit_price=Decimal("100"),
                    total_price=Decimal("200"),
                )
            ]
        ),
        user_id=7,
    )

    assert updated.subtotal == Decimal("200.00")
    assert updated.tax == Decimal("26.00")
    assert updated.discount == Decimal("10.00")
    assert updated.total == Decimal("216.00")
    assert updated.items[0]["total_price"] == 200.0


def test_update_items_can_override_tax_and_discount_rates_together():
    db = _make_session()
    quotation = _seed_quotation(db)
    service = AIQuotationGeneratorService(db)

    updated = service.update_quotation(
        quotation.id,
        QuotationUpdateRequest(
            items=[
                QuotationItem(
                    name="新项目",
                    quantity=Decimal("3"),
                    unit="项",
                    unit_price=Decimal("100"),
                    total_price=Decimal("300"),
                )
            ],
            tax_rate=Decimal("0.10"),
            discount_rate=Decimal("0.20"),
        ),
        user_id=7,
    )

    assert updated.subtotal == Decimal("300.00")
    assert updated.tax == Decimal("30.00")
    assert updated.discount == Decimal("60.00")
    assert updated.total == Decimal("270.00")
