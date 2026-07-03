import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.project import Customer
from app.models.sales import Opportunity, Quote
from app.models.user import User


pytestmark = [pytest.mark.api]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db):
    return db.query(User).filter(User.username == "admin").first()


def _create_draft_quote(db) -> Quote:
    suffix = uuid.uuid4().hex[:8]
    admin = _admin_user(db)

    customer = Customer(
        customer_code=f"CUST-QS-{suffix}",
        customer_name=f"报价状态客户-{suffix}",
        status="ACTIVE",
        created_by=admin.id if admin else None,
        sales_owner_id=admin.id if admin else None,
    )
    db.add(customer)
    db.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-QS-{suffix}",
        customer_id=customer.id,
        opp_name=f"报价状态商机-{suffix}",
        owner_id=admin.id if admin else None,
    )
    db.add(opportunity)
    db.flush()

    quote = Quote(
        quote_code=f"QT-QS-{suffix}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        owner_id=admin.id if admin else None,
        status="DRAFT",
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


class TestQuoteStatusContracts:
    def test_status_endpoint_cannot_approve_pending_quote(self, client: TestClient, admin_token: str, db):
        quote = _create_draft_quote(db)
        headers = _auth_headers(admin_token)

        submit_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/status",
            headers=headers,
            json={"new_status": "PENDING_APPROVAL"},
        )

        assert submit_response.status_code == 200, submit_response.text

        status_response = client.get(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/status",
            headers=headers,
        )
        assert status_response.status_code == 200, status_response.text
        allowed_transitions = {
            item["code"] for item in status_response.json()["data"]["allowed_transitions"]
        }
        assert "APPROVED" not in allowed_transitions
        assert "REJECTED" not in allowed_transitions

        approve_response = client.post(
            f"{settings.API_V1_PREFIX}/sales/quotes/{quote.id}/status",
            headers=headers,
            json={"new_status": "APPROVED"},
        )

        assert approve_response.status_code >= 400, approve_response.text

        db.expire_all()
        stored_quote = db.get(Quote, quote.id)
        assert stored_quote.status == "PENDING_APPROVAL"
