from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sales import Contract, Customer, Invoice
from app.models.user import User


pytestmark = [pytest.mark.api]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db_session: Session) -> User:
    return db_session.query(User).filter(User.username == "admin").one()


def _create_issued_invoice(
    db_session: Session,
    *,
    total: Decimal = Decimal("100.00"),
    paid: Decimal = Decimal("20.00"),
    suffix: str | None = None,
) -> Invoice:
    suffix = suffix or uuid4().hex[:8].upper()
    admin = _admin_user(db_session)

    customer = Customer(
        customer_code=f"CUST-PAY-{suffix}",
        customer_name=f"回款客户-{suffix}",
        status="ACTIVE",
        sales_owner_id=admin.id,
        created_by=admin.id,
    )
    db_session.add(customer)
    db_session.flush()

    contract = Contract(
        contract_code=f"CT-PAY-{suffix}",
        contract_name=f"回款合同-{suffix}",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=total,
        received_amount=paid,
        unreceived_amount=total - paid,
        status="executing",
        sales_owner_id=admin.id,
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"INV-PAY-{suffix}",
        contract_id=contract.id,
        amount=total,
        total_amount=total,
        paid_amount=paid,
        status="ISSUED",
        payment_status="PARTIAL" if paid else "PENDING",
        issue_date=date.today(),
        buyer_name=customer.customer_name,
    )
    db_session.add(invoice)
    db_session.commit()
    return invoice


class TestSalesPaymentRecordContracts:
    def test_create_payment_record_rejects_amount_over_invoice_unpaid(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        invoice = _create_issued_invoice(db_session)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/payments/records",
            headers=_auth_headers(admin_token),
            json={
                "contract_id": invoice.contract_id,
                "payment_date": date.today().isoformat(),
                "amount": "80.01",
            },
        )

        assert response.status_code >= 400, response.text

        db_session.expire_all()
        stored_invoice = db_session.get(Invoice, invoice.id)
        assert float(stored_invoice.paid_amount) == pytest.approx(20.0)

    def test_create_payment_record_allows_amount_equal_to_unpaid(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        invoice = _create_issued_invoice(db_session)

        response = client.post(
            f"{settings.API_V1_PREFIX}/sales/payments/records",
            headers=_auth_headers(admin_token),
            json={
                "contract_id": invoice.contract_id,
                "payment_date": date.today().isoformat(),
                "amount": "80.00",
            },
        )

        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["paid_amount"] == pytest.approx(100.0)
        assert data["unpaid_amount"] == pytest.approx(0.0)
        assert data["payment_status"] == "PAID"

    def test_update_payment_record_rejects_paid_amount_over_invoice_total(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        invoice = _create_issued_invoice(db_session)

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/payments/records/{invoice.id}",
            headers=_auth_headers(admin_token),
            json={"amount": "100.01"},
        )

        assert response.status_code >= 400, response.text

        db_session.expire_all()
        stored_invoice = db_session.get(Invoice, invoice.id)
        assert float(stored_invoice.paid_amount) == pytest.approx(20.0)

    def test_match_invoice_rejects_mismatched_payment_and_invoice_ids(
        self, client: TestClient, admin_token: str, db_session: Session
    ):
        suffix = uuid4().hex[:8].upper()
        payment_invoice = _create_issued_invoice(db_session, suffix=f"A-{suffix}")
        target_invoice = _create_issued_invoice(db_session, suffix=f"B-{suffix}")

        response = client.put(
            f"{settings.API_V1_PREFIX}/sales/payments/records/{payment_invoice.id}/match-invoice",
            headers=_auth_headers(admin_token),
            params={"invoice_id": target_invoice.id, "match_amount": "10.00"},
        )

        assert response.status_code >= 400, response.text
