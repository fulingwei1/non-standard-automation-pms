# -*- coding: utf-8 -*-
"""Sales invoice basic route contracts."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.approval import (
    ApprovalFlowDefinition,
    ApprovalInstance,
    ApprovalNodeDefinition,
    ApprovalTask,
    ApprovalTemplate,
)
from app.models.project import Project
from app.models.sales import Contract, Invoice
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_invoice_template(db_session: Session, admin: User, suffix: str) -> None:
    template = ApprovalTemplate(
        template_code=f"INV_BASIC_TPL_{suffix}",
        template_name="发票基础接口审批模板",
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
        flow_name="发票基础接口审批流程",
        is_default=True,
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(flow)
    db_session.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"INV_BASIC_NODE_{suffix}",
        node_name="发票审批",
        node_order=1,
        node_type="APPROVAL",
        approval_mode="SINGLE",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [admin.id]},
        is_active=True,
    )
    db_session.add(node)
    db_session.commit()


def test_invoice_list_accepts_legacy_trailing_slash(
    client: TestClient,
    admin_token: str,
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/sales/invoices/",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    assert "items" in response.json()


def test_invoice_calculate_tax_is_static_route_not_invoice_id(
    client: TestClient,
    admin_token: str,
):
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/calculate-tax",
        headers=_auth_headers(admin_token),
        json={"amount": 100000, "tax_rate": 13},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["amount"] == 100000
    assert data["tax_rate"] == 13
    assert data["tax_amount"] == 13000
    assert data["total_amount"] == 113000


def test_create_submitted_invoice_keeps_buyer_name_and_starts_unified_approval(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    suffix = uuid4().hex[:8].upper()
    contract = Contract(
        contract_code=f"INV-BASIC-CON-{suffix}",
        contract_name="发票基础接口合同",
        contract_type="sales",
        customer_id=project.customer_id,
        project_id=project.id,
        total_amount=1000,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.commit()

    _create_invoice_template(db_session, admin, suffix)

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices",
        headers=_auth_headers(admin_token),
        json={
            "invoice_no": f"INV-BASIC-{suffix}",
            "contract_id": contract.id,
            "amount": 1000,
            "tax_rate": 13,
            "tax_amount": 130,
            "total_amount": 1130,
            "status": "SUBMITTED",
            "buyer_name": "发票基础接口客户",
        },
    )

    assert response.status_code == 201, response.text
    invoice_id = response.json()["id"]

    invoice = db_session.get(Invoice, invoice_id)
    assert invoice is not None
    assert invoice.buyer_name == "发票基础接口客户"
    assert invoice.status == "PENDING_APPROVAL"

    instance = (
        db_session.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "INVOICE",
            ApprovalInstance.entity_id == invoice.id,
        )
        .one()
    )
    task = (
        db_session.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance.id)
        .one()
    )
    assert instance.status == "PENDING"
    assert task.status == "PENDING"
    assert task.assignee_id == admin.id
