import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.project import Customer
from app.models.sales import Opportunity, Quote, QuoteItem, QuoteVersion
from app.models.user import User


pytestmark = [pytest.mark.api]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db):
    return db.query(User).filter(User.username == "admin").first()


def _create_quote_version_with_item(
    db, *, quote_status: str = "DRAFT", version_status: str = "DRAFT"
) -> tuple[Quote, QuoteVersion, QuoteItem]:
    suffix = uuid.uuid4().hex[:8]
    admin = _admin_user(db)

    customer = Customer(
        customer_code=f"CUST-QI-{suffix}",
        customer_name=f"报价明细客户-{suffix}",
        status="ACTIVE",
        created_by=admin.id if admin else None,
        sales_owner_id=admin.id if admin else None,
    )
    db.add(customer)
    db.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-QI-{suffix}",
        customer_id=customer.id,
        opp_name=f"报价明细商机-{suffix}",
        owner_id=admin.id if admin else None,
    )
    db.add(opportunity)
    db.flush()

    quote = Quote(
        quote_code=f"QT-QI-{suffix}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        owner_id=admin.id if admin else None,
        status=quote_status,
    )
    db.add(quote)
    db.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        total_price=Decimal("100.00"),
        cost_total=Decimal("20.00"),
        gross_margin=Decimal("80.00"),
        status=version_status,
        created_by=admin.id if admin else None,
    )
    db.add(version)
    db.flush()
    quote.current_version_id = version.id

    item = QuoteItem(
        quote_version_id=version.id,
        item_type="MATERIAL",
        item_name="标准件",
        qty=Decimal("1"),
        unit_price=Decimal("100.00"),
        cost=Decimal("20.00"),
        unit="件",
    )
    db.add(item)
    db.commit()
    return quote, version, item


class TestQuoteItemContracts:
    def test_approved_quote_items_are_locked_for_all_write_methods(
        self, client: TestClient, admin_token: str, db
    ):
        _quote, version, item = _create_quote_version_with_item(db, quote_status="APPROVED")
        headers = _auth_headers(admin_token)

        create_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{version.id}/items",
            headers=headers,
            json={
                "item_type": "MATERIAL",
                "item_name": "追加件",
                "qty": 1,
                "unit_price": 10,
                "cost": 5,
            },
        )
        update_response = client.put(
            f"{settings.API_V1_PREFIX}/sales/quotes/items/{item.id}",
            headers=headers,
            json={"unit_price": 123456},
        )
        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/sales/quotes/items/{item.id}",
            headers=headers,
        )

        assert create_response.status_code >= 400, create_response.text
        assert update_response.status_code >= 400, update_response.text
        assert delete_response.status_code >= 400, delete_response.text

        db.expire_all()
        assert db.get(QuoteItem, item.id) is not None

    def test_approved_quote_version_items_are_locked_even_when_quote_is_draft(
        self, client: TestClient, admin_token: str, db
    ):
        _quote, _version, item = _create_quote_version_with_item(
            db, quote_status="DRAFT", version_status="APPROVED"
        )

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/quotes/items/{item.id}",
            headers=_auth_headers(admin_token),
            json={"unit_price": 123456},
        )

        assert response.status_code >= 400, response.text

    def test_editable_quote_item_update_recalculates_version_totals(
        self, client: TestClient, admin_token: str, db
    ):
        _quote, version, item = _create_quote_version_with_item(db, quote_status="DRAFT")

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/quotes/items/{item.id}",
            headers=_auth_headers(admin_token),
            json={"qty": 3, "unit_price": 50, "cost": 10},
        )

        assert response.status_code == 200, response.text

        db.expire_all()
        stored_version = db.get(QuoteVersion, version.id)
        assert float(stored_version.total_price) == pytest.approx(150.0)
        assert float(stored_version.cost_total) == pytest.approx(30.0)
        assert float(stored_version.gross_margin) == pytest.approx(80.0)
