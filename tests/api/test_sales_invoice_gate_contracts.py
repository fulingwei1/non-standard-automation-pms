# -*- coding: utf-8 -*-
"""Sales invoice approval and status gate contracts."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.approval import ApprovalFlowDefinition, ApprovalInstance, ApprovalTemplate
from app.models.project import Project
from app.models.sales import Contract, Invoice, Opportunity
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_invoice(
    db_session: Session,
    *,
    admin: User,
    project: Project,
    prefix: str,
    contract_total: Decimal = Decimal("1000"),
    invoice_amount: Decimal = Decimal("1000"),
    invoice_status: str = "DRAFT",
    approval_status: str | None = None,
) -> tuple[Invoice, ApprovalInstance | None]:
    suffix = uuid4().hex[:8].upper()
    opportunity = Opportunity(
        opp_code=f"{prefix}-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name=f"{prefix} 发票门禁测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"{prefix}-CON-{suffix}",
        contract_name=f"{prefix} 发票门禁测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=contract_total,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"{prefix}-INV-{suffix}",
        contract_id=contract.id,
        amount=invoice_amount,
        total_amount=invoice_amount,
        status=invoice_status,
        buyer_name=f"{prefix} 发票门禁测试客户",
    )
    db_session.add(invoice)
    db_session.flush()

    instance = None
    if approval_status is not None:
        template = ApprovalTemplate(
            template_code=f"{prefix}_TPL_{suffix}",
            template_name=f"{prefix} 发票门禁审批模板",
            category="BUSINESS",
            entity_type="INVOICE",
            is_active=True,
            is_published=True,
            created_by=admin.id,
        )
        db_session.add(template)
        db_session.flush()

        flow = ApprovalFlowDefinition(
            template_id=template.id,
            flow_name=f"{prefix} 发票门禁审批流程",
            is_default=True,
            is_active=True,
            created_by=admin.id,
        )
        db_session.add(flow)
        db_session.flush()

        instance = ApprovalInstance(
            instance_no=f"AP{prefix}{suffix}",
            template_id=template.id,
            flow_id=flow.id,
            entity_type="INVOICE",
            entity_id=invoice.id,
            initiator_id=admin.id,
            initiator_name=admin.real_name or admin.username,
            status=approval_status,
            title=f"{prefix} 发票门禁审批",
            summary=f"{prefix} 发票门禁审批",
        )
        db_session.add(instance)
        db_session.flush()
        invoice.approval_instance_id = instance.id
        invoice.approval_status = instance.status

    db_session.commit()
    return invoice, instance


def test_invoice_model_maps_unified_approval_fields():
    assert "approval_instance_id" in Invoice.__table__.columns
    assert "approval_status" in Invoice.__table__.columns


def test_issue_rejects_pending_unified_approval_instance(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    invoice, _ = _seed_invoice(
        db_session,
        admin=admin,
        project=project,
        prefix="INV-GATE-PEND",
        invoice_status="PENDING_APPROVAL",
        approval_status="PENDING",
    )

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/issue",
        headers=_auth_headers(admin_token),
        json={"issue_date": date.today().isoformat()},
    )

    assert response.status_code == 400, response.text
    db_session.refresh(invoice)
    assert invoice.status == "PENDING_APPROVAL"


def test_issue_allows_approved_unified_approval_instance(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    issue_date = date.today()
    invoice, _ = _seed_invoice(
        db_session,
        admin=admin,
        project=project,
        prefix="INV-GATE-APPR",
        invoice_status="APPROVED",
        approval_status="APPROVED",
    )

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/issue",
        headers=_auth_headers(admin_token),
        json={"issue_date": issue_date.isoformat()},
    )

    assert response.status_code == 200, response.text
    db_session.refresh(invoice)
    assert invoice.status == "ISSUED"
    assert invoice.payment_status == "PENDING"
    assert invoice.due_date == issue_date + timedelta(days=30)


def test_void_paid_invoice_creates_red_credit_without_deleting_payment(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    invoice, _ = _seed_invoice(
        db_session,
        admin=admin,
        project=project,
        prefix="INV-GATE-VOID",
        invoice_status="ISSUED",
        approval_status=None,
    )
    invoice.paid_amount = Decimal("1000.00")
    invoice.payment_status = "PAID"
    invoice.paid_date = date.today()
    db_session.commit()

    response = client.put(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/void",
        headers=_auth_headers(admin_token),
        params={"reason": "客户信息开错"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]

    db_session.expire_all()
    original = db_session.get(Invoice, invoice.id)
    red_invoice = (
        db_session.query(Invoice)
        .filter(Invoice.contract_id == original.contract_id)
        .filter(Invoice.invoice_type == "RED_CREDIT")
        .one()
    )

    assert original.status == "CANCELLED"
    assert original.paid_amount == Decimal("1000.00")
    assert "红冲发票" in (original.remark or "")
    assert red_invoice.status == "ISSUED"
    assert red_invoice.amount == Decimal("-1000.00")
    assert red_invoice.total_amount == Decimal("-1000.00")
    assert red_invoice.paid_amount == Decimal("-1000.00")
    assert red_invoice.payment_status == "REVERSED"
    assert "客户信息开错" in (red_invoice.remark or "")
    assert data["red_invoice_id"] == red_invoice.id
    assert data["red_invoice_code"] == red_invoice.invoice_code


def test_invoice_amount_limit_ignores_red_credit_invoice_amounts(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    invoice, _ = _seed_invoice(
        db_session,
        admin=admin,
        project=project,
        prefix="INV-GATE-RED",
        contract_total=Decimal("1000.00"),
        invoice_amount=Decimal("800.00"),
        invoice_status="ISSUED",
        approval_status=None,
    )
    red_invoice = Invoice(
        invoice_code=f"INV-RED-{uuid4().hex[:8].upper()}",
        contract_id=invoice.contract_id,
        invoice_type="RED_CREDIT",
        amount=Decimal("-800.00"),
        total_amount=Decimal("-800.00"),
        paid_amount=Decimal("-800.00"),
        status="ISSUED",
        payment_status="REVERSED",
        issue_date=date.today(),
        buyer_name=invoice.buyer_name,
        remark=f"红冲发票，原发票: {invoice.invoice_code}",
    )
    db_session.add(red_invoice)
    db_session.commit()

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices",
        headers=_auth_headers(admin_token),
        json={
            "invoice_no": f"INV-RED-NEW-{uuid4().hex[:6].upper()}",
            "contract_id": invoice.contract_id,
            "amount": 300,
            "buyer_name": invoice.buyer_name,
        },
    )

    assert response.status_code == 400, response.text
    assert "累计开票金额" in response.text


def test_issue_rejects_cancelled_invoice_even_with_approved_instance(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    invoice, _ = _seed_invoice(
        db_session,
        admin=admin,
        project=project,
        prefix="INV-GATE-CAN",
        invoice_status="CANCELLED",
        approval_status="APPROVED",
    )

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/issue",
        headers=_auth_headers(admin_token),
        json={"issue_date": date.today().isoformat()},
    )

    assert response.status_code == 400, response.text
    db_session.refresh(invoice)
    assert invoice.status == "CANCELLED"


def test_update_invoice_rejects_direct_status_change(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    invoice, _ = _seed_invoice(
        db_session,
        admin=admin,
        project=project,
        prefix="INV-GATE-STAT",
        invoice_status="DRAFT",
        approval_status=None,
    )

    response = client.put(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}",
        headers=_auth_headers(admin_token),
        json={"status": "ISSUED"},
    )

    assert response.status_code == 400, response.text
    db_session.refresh(invoice)
    assert invoice.status == "DRAFT"


def test_update_invoice_rechecks_contract_invoice_limit(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    invoice, _ = _seed_invoice(
        db_session,
        admin=admin,
        project=project,
        prefix="INV-GATE-AMT",
        contract_total=Decimal("1000"),
        invoice_amount=Decimal("800"),
        invoice_status="DRAFT",
        approval_status=None,
    )

    response = client.put(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}",
        headers=_auth_headers(admin_token),
        json={"invoice_amount": 1200},
    )

    assert response.status_code == 400, response.text
    db_session.refresh(invoice)
    assert invoice.amount == Decimal("800")


def test_create_invoice_rejects_unsigned_contract(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    suffix = uuid4().hex[:8].upper()
    opportunity = Opportunity(
        opp_code=f"INV-GATE-DRAFT-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name="未签署合同发票门禁测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"INV-GATE-DRAFT-CON-{suffix}",
        contract_name="未签署合同发票门禁测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=Decimal("1000"),
        status="DRAFT",
    )
    db_session.add(contract)
    db_session.commit()

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices",
        headers=_auth_headers(admin_token),
        json={
            "invoice_no": f"INVD{suffix}",
            "contract_id": contract.id,
            "amount": 1000,
            "buyer_name": "未签署合同发票门禁测试客户",
        },
    )

    assert response.status_code == 400, response.text
