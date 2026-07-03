# -*- coding: utf-8 -*-
"""Contract tests for sales quote cost batch price updates."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Customer
from app.models.sales import Opportunity, Quote, QuoteItem, QuoteVersion
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_quote_with_cost_item(db_session: Session) -> tuple[Quote, QuoteVersion, QuoteItem]:
    suffix = uuid4().hex[:8].upper()
    admin = db_session.query(User).filter(User.username == "admin").first()
    assert admin is not None

    customer = Customer(
        customer_code=f"QCBC-{suffix}",
        customer_name=f"报价批量改价客户-{suffix}",
        contact_person="测试联系人",
        contact_phone="021-10000000",
        created_by=admin.id,
        sales_owner_id=admin.id,
    )
    db_session.add(customer)
    db_session.flush()

    opportunity = Opportunity(
        opp_code=f"QCO-{suffix}",
        customer_id=customer.id,
        opp_name=f"报价批量改价商机-{suffix}",
        stage="QUALIFICATION",
        probability=80,
        est_amount=Decimal("1000.00"),
        expected_close_date=date.today() + timedelta(days=30),
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    quote = Quote(
        quote_code=f"QCQ-{suffix}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        owner_id=admin.id,
        valid_until=date.today() + timedelta(days=45),
    )
    db_session.add(quote)
    db_session.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        total_price=Decimal("100.00"),
        cost_total=Decimal("100.00"),
        gross_margin=Decimal("0.00"),
        created_by=admin.id,
    )
    db_session.add(version)
    db_session.flush()
    quote.current_version_id = version.id

    item = QuoteItem(
        quote_version_id=version.id,
        item_type="SYSTEM",
        item_name=f"批量改价测试明细-{suffix}",
        qty=Decimal("1.00"),
        unit_price=Decimal("100.00"),
        cost=Decimal("100.00"),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(quote)
    db_session.refresh(version)
    db_session.refresh(item)
    return quote, version, item


def _cleanup_quote_with_cost_item(
    db_session: Session,
    quote_id: int,
    version_id: int,
    item_id: int,
    opportunity_id: int,
    customer_id: int,
) -> None:
    quote = db_session.get(Quote, quote_id)
    if quote:
        quote.current_version_id = None
        db_session.flush()
    db_session.query(QuoteItem).filter(QuoteItem.id == item_id).delete(synchronize_session=False)
    db_session.query(QuoteVersion).filter(QuoteVersion.id == version_id).delete(
        synchronize_session=False
    )
    db_session.query(Quote).filter(Quote.id == quote_id).delete(synchronize_session=False)
    db_session.query(Opportunity).filter(Opportunity.id == opportunity_id).delete(
        synchronize_session=False
    )
    db_session.query(Customer).filter(Customer.id == customer_id).delete(synchronize_session=False)
    db_session.commit()


def test_quote_cost_batch_update_rejects_unknown_mode_without_price_changes(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    quote, version, item = _create_quote_with_cost_item(db_session)
    try:
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/cost-calculations/batch-update",
            headers=_auth_headers(admin_token),
            json={"version_id": version.id, "mode": "discount", "rate": 20},
        )

        assert response.status_code == 422, response.text
        db_session.expire_all()
        refreshed_item = db_session.get(QuoteItem, item.id)
        assert refreshed_item.unit_price == Decimal("100.00")
    finally:
        _cleanup_quote_with_cost_item(
            db_session,
            quote_id=quote.id,
            version_id=version.id,
            item_id=item.id,
            opportunity_id=quote.opportunity_id,
            customer_id=quote.customer_id,
        )


@pytest.mark.parametrize(
    ("mode", "rate", "expected_price"),
    [
        ("markup", 20, Decimal("120.00")),
        ("margin", 20, Decimal("125.00")),
    ],
)
def test_quote_cost_batch_update_accepts_valid_modes(
    client: TestClient,
    admin_token: str,
    db_session: Session,
    mode: str,
    rate: int,
    expected_price: Decimal,
):
    quote, version, item = _create_quote_with_cost_item(db_session)
    try:
        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/cost-calculations/batch-update",
            headers=_auth_headers(admin_token),
            json={"version_id": version.id, "mode": mode, "rate": rate},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["mode"] == mode
        db_session.expire_all()
        refreshed_item = db_session.get(QuoteItem, item.id)
        assert refreshed_item.unit_price == expected_price
    finally:
        _cleanup_quote_with_cost_item(
            db_session,
            quote_id=quote.id,
            version_id=version.id,
            item_id=item.id,
            opportunity_id=quote.opportunity_id,
            customer_id=quote.customer_id,
        )
