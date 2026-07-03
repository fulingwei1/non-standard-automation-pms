# -*- coding: utf-8 -*-
"""催款优先级 API 权限边界测试"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.sales import Contract, Customer, Invoice
from app.models.user import User


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _create_sales_user(db_session: Session, suffix: str, real_name: str) -> User:
    user = User(
        username=f"collection_self_{suffix}",
        password_hash=get_password_hash("collection123"),
        email=f"collection_self_{suffix}@example.com",
        real_name=real_name,
        department="销售部",
        position="销售",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_overdue_invoice(
    db_session: Session,
    owner: User,
    suffix: str,
    unpaid_amount: Decimal,
) -> Invoice:
    customer = Customer(
        customer_code=f"CUST-COLL-{suffix}",
        customer_name=f"催款客户-{suffix}",
        contact_person="客户联系人",
        contact_phone="13800000000",
        status="ACTIVE",
        credit_level="B",
        sales_owner_id=owner.id,
        created_by=owner.id,
    )
    db_session.add(customer)
    db_session.flush()

    contract = Contract(
        contract_code=f"CT-COLL-{suffix}",
        contract_name=f"催款合同-{suffix}",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=unpaid_amount,
        received_amount=Decimal("0"),
        unreceived_amount=unpaid_amount,
        status="executing",
        sales_owner_id=owner.id,
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"INV-COLL-{suffix}",
        contract_id=contract.id,
        amount=unpaid_amount,
        total_amount=unpaid_amount,
        paid_amount=Decimal("0"),
        status="ISSUED",
        payment_status="PENDING",
        issue_date=date.today() - timedelta(days=70),
        due_date=date.today() - timedelta(days=45),
        buyer_name=customer.customer_name,
    )
    db_session.add(invoice)
    db_session.flush()
    return invoice


def test_regular_sales_user_can_read_own_collection_summary_without_contract_read(
    client: TestClient,
    db_session: Session,
):
    """销售工作台本人催款汇总可读，但不放开合同/催款管理列表"""
    suffix = uuid4().hex[:8].upper()
    owner = _create_sales_user(db_session, f"OWNER-{suffix}", "催款销售")
    other = _create_sales_user(db_session, f"OTHER-{suffix}", "其他销售")
    own_invoice = _create_overdue_invoice(
        db_session, owner, f"OWN-{suffix}", Decimal("9000.00")
    )
    other_invoice = _create_overdue_invoice(
        db_session, other, f"OTHER-{suffix}", Decimal("12000.00")
    )
    db_session.commit()

    headers = _auth_headers_for_user(owner)

    list_response = client.get(
        f"{settings.API_V1_PREFIX}/sales/collection/priority",
        headers=headers,
    )
    assert list_response.status_code == 403

    critical_response = client.get(
        f"{settings.API_V1_PREFIX}/sales/collection/priority/critical",
        headers=headers,
    )
    assert critical_response.status_code == 403

    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/collection/priority/summary",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    summary = response.json()["data"]

    assert summary["total_count"] == 1
    assert summary["total_unpaid"] == 9000.0
    assert summary["by_urgency"]["high"]["count"] == 1
    assert summary["top_priority_items"][0]["invoice_code"] == own_invoice.invoice_code
    assert summary["top_priority_items"][0]["customer_name"] == own_invoice.buyer_name
    assert all(
        item["invoice_code"] != other_invoice.invoice_code
        for item in summary["top_priority_items"]
    )
