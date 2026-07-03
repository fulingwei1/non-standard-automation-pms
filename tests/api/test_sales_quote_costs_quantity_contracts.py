import uuid
from datetime import datetime, timedelta
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


def _create_quote_with_quantity_cost(db) -> Quote:
    suffix = uuid.uuid4().hex[:8]
    admin = _admin_user(db)

    customer = Customer(
        customer_code=f"CUST-QC-{suffix}",
        customer_name=f"报价成本客户-{suffix}",
        status="ACTIVE",
        created_by=admin.id if admin else None,
        sales_owner_id=admin.id if admin else None,
    )
    db.add(customer)
    db.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-QC-{suffix}",
        customer_id=customer.id,
        opp_name=f"报价成本商机-{suffix}",
        owner_id=admin.id if admin else None,
    )
    db.add(opportunity)
    db.flush()

    quote = Quote(
        quote_code=f"QT-QC-{suffix}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        owner_id=admin.id if admin else None,
    )
    db.add(quote)
    db.flush()

    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        total_price=Decimal("600.00"),
        cost_total=Decimal("100.00"),
        gross_margin=Decimal("83.33"),
        created_by=admin.id if admin else None,
    )
    db.add(version)
    db.flush()

    quote.current_version_id = version.id
    db.add(
        QuoteItem(
            quote_version_id=version.id,
            item_type="MATERIAL",
            item_name="批量件",
            cost_category="材料",
            qty=Decimal("3"),
            unit_price=Decimal("200.00"),
            cost=Decimal("100.00"),
            unit="件",
        )
    )
    db.commit()
    db.refresh(quote)
    return quote


class TestQuoteCostQuantityContracts:
    def test_cost_breakdown_total_cost_multiplies_item_cost_by_quantity(
        self, client: TestClient, admin_token: str, db
    ):
        quote = _create_quote_with_quantity_cost(db)

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/cost-breakdown",
            headers=_auth_headers(admin_token),
        )

        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["total_price"] == pytest.approx(600.0)
        assert data["total_cost"] == pytest.approx(300.0)
        assert data["gross_margin"] == pytest.approx(50.0)
        assert data["breakdown"][0]["subtotal_cost"] == pytest.approx(300.0)

    def test_cost_recalculate_persists_quantity_adjusted_total_cost(
        self, client: TestClient, admin_token: str, db
    ):
        quote = _create_quote_with_quantity_cost(db)
        version_id = quote.current_version_id

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/cost-breakdown/recalculate",
            params={"version_id": version_id},
            headers=_auth_headers(admin_token),
        )

        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["total_price"] == pytest.approx(600.0)
        assert data["total_cost"] == pytest.approx(300.0)
        assert data["gross_margin"] == pytest.approx(50.0)

        version = db.get(QuoteVersion, version_id)
        assert float(version.cost_total) == pytest.approx(300.0)
        assert float(version.gross_margin) == pytest.approx(50.0)

    def test_cost_analysis_uses_quote_current_version_not_latest_created_version(
        self, client: TestClient, admin_token: str, db
    ):
        quote = _create_quote_with_quantity_cost(db)
        current_version = db.get(QuoteVersion, quote.current_version_id)
        current_version.version_no = "V1-CURRENT"
        current_version.created_at = datetime.now() - timedelta(days=1)

        draft_version = QuoteVersion(
            quote_id=quote.id,
            version_no="V2-DRAFT",
            total_price=Decimal("900.00"),
            cost_total=Decimal("450.00"),
            gross_margin=Decimal("50.00"),
            created_at=datetime.now(),
            created_by=current_version.created_by,
        )
        db.add(draft_version)
        db.flush()
        db.add(
            QuoteItem(
                quote_version_id=draft_version.id,
                item_type="MATERIAL",
                item_name="未设为当前版本的明细",
                cost_category="材料",
                qty=Decimal("1"),
                unit_price=Decimal("900.00"),
                cost=Decimal("450.00"),
                unit="件",
            )
        )
        quote.current_version_id = current_version.id
        db.commit()

        response = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/cost-analysis",
            headers=_auth_headers(admin_token),
        )

        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["version_count"] == 2
        assert data["current_version"]["version_no"] == "V1-CURRENT"
        assert data["current_version"]["total_price"] == pytest.approx(600.0)
        assert data["current_version"]["cost_total"] == pytest.approx(100.0)
