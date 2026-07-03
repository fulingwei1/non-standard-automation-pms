# -*- coding: utf-8 -*-
"""Purchase approval workflow contract regressions."""

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.approval import ApprovalFlowDefinition, ApprovalInstance, ApprovalNodeDefinition, ApprovalTask, ApprovalTemplate
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.user import User
from app.models.vendor import Vendor


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _admin_user(db: Session) -> User:
    return db.query(User).filter(User.username == "admin").first()


def _seed_purchase_workflow(db: Session, approver_id: int, suffix: str) -> None:
    existing = (
        db.query(ApprovalTemplate)
        .filter(ApprovalTemplate.template_code == "TPL_PURCHASE")
        .first()
    )
    if existing:
        return

    template = ApprovalTemplate(
        template_code="TPL_PURCHASE",
        template_name=f"QA 采购审批 {suffix}",
        category="BUSINESS",
        entity_type="PURCHASE_ORDER",
        version=1,
        is_published=True,
        is_active=True,
        created_by=approver_id,
    )
    db.add(template)
    db.flush()
    flow = ApprovalFlowDefinition(
        template_id=template.id,
        flow_name=f"QA 采购审批默认流 {suffix}",
        is_default=True,
        version=1,
        is_active=True,
        created_by=approver_id,
    )
    db.add(flow)
    db.flush()
    db.add(
        ApprovalNodeDefinition(
            flow_id=flow.id,
            node_code=f"QA-PO-{suffix}",
            node_name="管理员审批",
            node_order=1,
            node_type="APPROVAL",
            approval_mode="SINGLE",
            is_active=True,
            approver_type="FIXED_USER",
            approver_config={"user_ids": [approver_id]},
            notify_config={},
        )
    )
    db.commit()


def _seed_vendor(db: Session, suffix: str, user_id: int) -> Vendor:
    vendor = Vendor(
        supplier_code=f"QA-PO-V-{suffix}",
        supplier_name=f"QA 采购供应商 {suffix}",
        vendor_type="MATERIAL",
        supplier_level="A",
        status="ACTIVE",
        created_by=user_id,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def _create_purchase_order(
    client: TestClient, headers: dict, vendor_id: int, suffix: str
) -> int:
    response = client.post(
        f"{settings.API_V1_PREFIX}/purchase-orders/",
        headers=headers,
        json={
            "supplier_id": vendor_id,
            "order_title": f"QA 采购审批 {suffix}",
            "items": [
                {
                    "material_code": f"QA-PO-MAT-{suffix}",
                    "material_name": "QA 采购审批物料",
                    "unit": "件",
                    "quantity": 2,
                    "unit_price": 11,
                    "tax_rate": 13,
                }
            ],
        },
        follow_redirects=False,
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["id"]


def test_purchase_workflow_submit_pending_approve_and_duplicate_guard(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    _seed_purchase_workflow(db_session, admin.id, suffix)
    vendor = _seed_vendor(db_session, suffix, admin.id)
    headers = _auth_headers(admin_token)
    order_id = _create_purchase_order(client, headers, vendor.id, suffix)

    db_session.expire_all()
    order = db_session.get(PurchaseOrder, order_id)
    assert order.total_amount == Decimal("22.00")
    assert order.tax_amount == Decimal("2.86")
    assert order.amount_with_tax == Decimal("24.86")
    item = db_session.query(PurchaseOrderItem).filter_by(order_id=order_id).one()
    assert item.amount_with_tax == Decimal("24.86")

    submit_response = client.post(
        f"{settings.API_V1_PREFIX}/purchase-orders/workflow/submit",
        headers=headers,
        json={"order_ids": [order_id], "urgency": "NORMAL", "comment": "提交审批"},
        follow_redirects=False,
    )
    assert submit_response.status_code == 200, submit_response.text
    submit_data = submit_response.json()["data"]
    assert len(submit_data["success"]) == 1
    assert submit_data["errors"] == []

    db_session.expire_all()
    order = db_session.get(PurchaseOrder, order_id)
    assert order.status == "PENDING_APPROVAL"
    assert order.submitted_at is not None

    pending_response = client.get(
        f"{settings.API_V1_PREFIX}/purchase-orders/workflow/pending?page=1&page_size=20",
        headers=headers,
        follow_redirects=False,
    )
    assert pending_response.status_code == 200, pending_response.text
    pending_items = pending_response.json()["data"]["items"]
    pending_item = next(item for item in pending_items if item["order_id"] == order_id)
    assert pending_item["supplier_name"] == vendor.supplier_name
    task_id = pending_item["task_id"]

    approve_response = client.post(
        f"{settings.API_V1_PREFIX}/purchase-orders/workflow/action",
        headers=headers,
        json={"task_id": task_id, "action": "approve", "comment": "同意"},
        follow_redirects=False,
    )
    assert approve_response.status_code == 200, approve_response.text
    assert approve_response.json()["data"]["instance_status"] == "APPROVED"

    db_session.expire_all()
    instance = (
        db_session.query(ApprovalInstance)
        .filter_by(entity_type="PURCHASE_ORDER", entity_id=order_id)
        .one()
    )
    task = db_session.get(ApprovalTask, task_id)
    order = db_session.get(PurchaseOrder, order_id)
    assert instance.status == "APPROVED"
    assert task.status == "COMPLETED"
    assert order.status == "APPROVED"
    assert order.approved_by == admin.id
    assert order.approved_at is not None

    duplicate_response = client.post(
        f"{settings.API_V1_PREFIX}/purchase-orders/workflow/submit",
        headers=headers,
        json={"order_ids": [order_id], "urgency": "NORMAL", "comment": "重复提交"},
        follow_redirects=False,
    )
    assert duplicate_response.status_code == 200, duplicate_response.text
    duplicate_data = duplicate_response.json()["data"]
    assert duplicate_data["success"] == []
    assert duplicate_data["errors"]


def test_purchase_workflow_withdraw_restores_draft_order(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    _seed_purchase_workflow(db_session, admin.id, suffix)
    vendor = _seed_vendor(db_session, suffix, admin.id)
    headers = _auth_headers(admin_token)
    order_id = _create_purchase_order(client, headers, vendor.id, f"{suffix}-W")

    submit_response = client.post(
        f"{settings.API_V1_PREFIX}/purchase-orders/workflow/submit",
        headers=headers,
        json={"order_ids": [order_id], "urgency": "NORMAL", "comment": "提交后撤回"},
        follow_redirects=False,
    )
    assert submit_response.status_code == 200, submit_response.text
    assert submit_response.json()["data"]["success"]

    db_session.expire_all()
    order = db_session.get(PurchaseOrder, order_id)
    assert order.status == "PENDING_APPROVAL"
    assert order.submitted_at is not None

    withdraw_response = client.post(
        f"{settings.API_V1_PREFIX}/purchase-orders/workflow/withdraw",
        headers=headers,
        json={"order_id": order_id, "reason": "撤回修改"},
        follow_redirects=False,
    )
    assert withdraw_response.status_code == 200, withdraw_response.text

    db_session.expire_all()
    order = db_session.get(PurchaseOrder, order_id)
    instance = (
        db_session.query(ApprovalInstance)
        .filter_by(entity_type="PURCHASE_ORDER", entity_id=order_id)
        .one()
    )
    pending_tasks = (
        db_session.query(ApprovalTask)
        .filter_by(instance_id=instance.id, status="PENDING")
        .count()
    )
    assert order.status == "DRAFT"
    assert order.submitted_at is None
    assert instance.status == "CANCELLED"
    assert pending_tasks == 0
