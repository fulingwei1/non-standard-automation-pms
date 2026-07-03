# -*- coding: utf-8 -*-
"""Sales invoice approval workflow route contracts."""

from decimal import Decimal
from uuid import uuid4

import pytest
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
from app.models.sales import Contract, Invoice, Opportunity
from app.models.user import User
from app.schemas.sales import ApprovalActionRequest


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _seed_pending_invoice_approval(
    db_session: Session,
    *,
    admin: User,
    project: Project,
    suffix: str,
    prefix: str,
    assignee: User | None = None,
    invoice_status: str = "PENDING_APPROVAL",
) -> dict:
    assignee = assignee or admin
    opportunity = Opportunity(
        opp_code=f"{prefix}-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name=f"{prefix} 发票审批测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"{prefix}-CON-{suffix}",
        contract_name=f"{prefix} 发票审批测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=1000,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"{prefix}-INV-{suffix}",
        contract_id=contract.id,
        amount=1000,
        total_amount=1000,
        status=invoice_status,
        buyer_name=f"{prefix} 发票审批测试客户",
    )
    db_session.add(invoice)
    db_session.flush()

    template = ApprovalTemplate(
        template_code=f"{prefix}_TPL_{suffix}",
        template_name=f"{prefix} 发票审批测试模板",
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
        flow_name=f"{prefix} 发票审批测试流程",
        is_default=True,
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(flow)
    db_session.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"{prefix}_NODE_{suffix}",
        node_name="发票审批",
        node_order=1,
        node_type="APPROVAL",
        approval_mode="SINGLE",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [assignee.id]},
        can_transfer=True,
        is_active=True,
    )
    db_session.add(node)
    db_session.flush()

    instance = ApprovalInstance(
        instance_no=f"AP{prefix}{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="INVOICE",
        entity_id=invoice.id,
        initiator_id=admin.id,
        initiator_name=admin.real_name or admin.username,
        status="PENDING",
        current_node_id=node.id,
        title=f"{prefix} 发票审批测试",
        summary=f"{prefix} 发票审批测试",
    )
    db_session.add(instance)
    db_session.flush()

    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        task_type="APPROVAL",
        task_order=1,
        assignee_id=assignee.id,
        assignee_name=assignee.real_name or assignee.username,
        status="PENDING",
    )
    db_session.add(task)
    db_session.commit()

    return {
        "opportunity": opportunity,
        "contract": contract,
        "invoice": invoice,
        "template": template,
        "flow": flow,
        "node": node,
        "instance": instance,
        "task": task,
    }


def test_invoice_approval_rejects_unknown_action_before_engine_lookup(
    client: TestClient,
    admin_token: str,
):
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/999999/approval/action",
        headers=_auth_headers(admin_token),
        json={"action": "ESCALATE", "comment": "invalid action"},
    )

    assert response.status_code == 422, response.text
    body = response.text
    assert "APPROVE" in body
    assert "REJECT" in body
    assert "DELEGATE" in body
    assert "WITHDRAW" in body


@pytest.mark.parametrize(
    "payload",
    [
        {"action": "APPROVE", "comment": "valid action"},
        {"action": "REJECT", "comment": "valid action"},
        {"action": "DELEGATE", "delegate_to_id": 1, "comment": "valid action"},
        {"action": "WITHDRAW", "comment": "valid action"},
    ],
)
def test_invoice_approval_valid_actions_do_not_crash_on_missing_invoice(
    client: TestClient,
    admin_token: str,
    payload: dict,
):
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/999999/approval/action",
        headers=_auth_headers(admin_token),
        json=payload,
    )

    assert response.status_code == 404, response.text
    assert "Internal Server Error" not in response.text


def test_invoice_approval_action_request_keeps_delegate_target():
    request = ApprovalActionRequest(
        action="DELEGATE",
        delegate_to_id=7,
        comment="delegate approval",
    )

    assert request.delegate_to_id == 7


def test_invoice_approval_action_request_normalizes_frontend_lowercase_action():
    request = ApprovalActionRequest(action="approve", comment="frontend action")

    assert request.action == "APPROVE"


def test_invoice_approval_start_accepts_empty_body_and_uses_unified_engine(
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
        opp_code=f"INV-START-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name="发票审批启动测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"INV-START-CON-{suffix}",
        contract_name="发票审批启动测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=1000,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"INV-START-{suffix}",
        contract_id=contract.id,
        amount=1000,
        total_amount=1000,
        status="DRAFT",
        buyer_name="发票审批启动测试客户",
    )
    db_session.add(invoice)
    db_session.flush()

    template = ApprovalTemplate(
        template_code=f"INV_START_TPL_{suffix}",
        template_name="发票审批启动测试模板",
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
        flow_name="发票审批启动测试流程",
        is_default=True,
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(flow)
    db_session.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"INV_START_NODE_{suffix}",
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

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/approval/start",
        headers=_auth_headers(admin_token),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["approval_instance_id"]
    assert data["status"] == "PENDING"

    instance = db_session.get(ApprovalInstance, data["approval_instance_id"])
    assert instance is not None
    assert instance.entity_type == "INVOICE"
    assert instance.entity_id == invoice.id
    task = (
        db_session.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance.id)
        .one()
    )
    assert task.status == "PENDING"
    assert task.assignee_id == admin.id
    db_session.refresh(invoice)
    assert invoice.status == "PENDING_APPROVAL"


def test_invoice_create_submitted_auto_starts_approval_with_buyer_fields(
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
        opp_code=f"INV-CREATE-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name="发票创建自动审批测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"INV-CREATE-CON-{suffix}",
        contract_name="发票创建自动审批测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=1000,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    template = ApprovalTemplate(
        template_code=f"INV_CREATE_TPL_{suffix}",
        template_name="发票创建自动审批测试模板",
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
        flow_name="发票创建自动审批测试流程",
        is_default=True,
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(flow)
    db_session.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"INV_CREATE_NODE_{suffix}",
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

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices",
        headers=_auth_headers(admin_token),
        json={
            "invoice_no": f"INV-CREATE-{suffix}",
            "contract_id": contract.id,
            "amount": 1000,
            "tax_rate": 13,
            "tax_amount": 130,
            "total_amount": 1130,
            "buyer_name": "发票创建自动审批测试客户",
            "buyer_tax_no": f"TAX{suffix}",
            "status": "SUBMITTED",
        },
    )

    assert response.status_code == 201, response.text
    invoice_id = response.json()["id"]
    invoice = db_session.get(Invoice, invoice_id)
    assert invoice is not None
    assert invoice.buyer_name == "发票创建自动审批测试客户"
    assert invoice.buyer_tax_no == f"TAX{suffix}"
    assert invoice.status == "PENDING_APPROVAL"

    instance = (
        db_session.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == "INVOICE",
            ApprovalInstance.entity_id == invoice.id,
        )
        .one()
    )
    assert instance.status == "PENDING"
    task = (
        db_session.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance.id)
        .one()
    )
    assert task.status == "PENDING"
    assert task.assignee_id == admin.id


def test_invoice_calculate_tax_static_route_precedes_dynamic_invoice_id(
    client: TestClient,
    admin_token: str,
):
    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/calculate-tax",
        headers=_auth_headers(admin_token),
        json={"amount": 1000, "tax_rate": 13},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"] == {
        "amount": 1000,
        "tax_rate": 13,
        "tax_amount": 130,
        "total_amount": 1130,
    }


def test_invoice_update_route_updates_legacy_alias_fields(
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
        opp_code=f"INV-UPD-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name="发票更新测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"INV-UPD-CON-{suffix}",
        contract_name="发票更新测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=1000,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"INV-UPD-{suffix}",
        contract_id=contract.id,
        amount=1000,
        total_amount=1000,
        status="DRAFT",
        buyer_name="发票更新测试客户",
    )
    db_session.add(invoice)
    db_session.commit()

    response = client.put(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}",
        headers=_auth_headers(admin_token),
        json={
            "invoice_amount": 1500,
            "remarks": "更新后的备注",
            "buyer_name": "更新后的购买方",
            "status": "issued",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert Decimal(str(data["invoice_amount"])) == Decimal("1500.00")
    assert data["remark"] == "更新后的备注"
    assert data["buyer_name"] == "更新后的购买方"
    assert data["status"] == "ISSUED"

    db_session.refresh(invoice)
    assert invoice.amount == 1500
    assert invoice.remark == "更新后的备注"
    assert invoice.buyer_name == "更新后的购买方"
    assert invoice.status == "ISSUED"


def test_invoice_approval_approve_uses_unified_engine_task(
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
        opp_code=f"INV-APP-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name="发票审批动作测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"INV-APP-CON-{suffix}",
        contract_name="发票审批动作测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=1000,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"INV-APP-{suffix}",
        contract_id=contract.id,
        amount=1000,
        total_amount=1000,
        status="SUBMITTED",
        buyer_name="发票审批动作测试客户",
    )
    db_session.add(invoice)
    db_session.flush()

    template = ApprovalTemplate(
        template_code=f"INV_APP_TPL_{suffix}",
        template_name="发票审批动作测试模板",
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
        flow_name="发票审批动作测试流程",
        is_default=True,
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(flow)
    db_session.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"INV_APP_NODE_{suffix}",
        node_name="发票审批",
        node_order=1,
        node_type="APPROVAL",
        approval_mode="SINGLE",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [admin.id]},
        is_active=True,
    )
    db_session.add(node)
    db_session.flush()

    instance = ApprovalInstance(
        instance_no=f"APINVAPP{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="INVOICE",
        entity_id=invoice.id,
        initiator_id=admin.id,
        initiator_name=admin.real_name or admin.username,
        status="PENDING",
        current_node_id=node.id,
        title="发票审批动作测试",
        summary="发票审批动作测试",
    )
    db_session.add(instance)
    db_session.flush()

    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        task_type="APPROVAL",
        task_order=1,
        assignee_id=admin.id,
        assignee_name=admin.real_name or admin.username,
        status="PENDING",
    )
    db_session.add(task)
    db_session.commit()

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/approval/action",
        headers=_auth_headers(admin_token),
        json={"action": "APPROVE", "comment": "approve invoice"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "APPROVED"

    db_session.refresh(task)
    db_session.refresh(instance)
    db_session.refresh(invoice)
    assert task.status == "COMPLETED"
    assert task.action == "APPROVE"
    assert instance.status == "APPROVED"
    assert invoice.status == "APPROVED"


def test_invoice_legacy_approve_route_maps_to_unified_engine_task(
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
        opp_code=f"INV-LAPP-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name="发票旧审批入口测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"INV-LAPP-CON-{suffix}",
        contract_name="发票旧审批入口测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=1000,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"INV-LAPP-{suffix}",
        contract_id=contract.id,
        amount=1000,
        total_amount=1000,
        status="SUBMITTED",
        buyer_name="发票旧审批入口测试客户",
    )
    db_session.add(invoice)
    db_session.flush()

    template = ApprovalTemplate(
        template_code=f"INV_LAPP_TPL_{suffix}",
        template_name="发票旧审批入口测试模板",
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
        flow_name="发票旧审批入口测试流程",
        is_default=True,
        is_active=True,
        created_by=admin.id,
    )
    db_session.add(flow)
    db_session.flush()

    node = ApprovalNodeDefinition(
        flow_id=flow.id,
        node_code=f"INV_LAPP_NODE_{suffix}",
        node_name="发票审批",
        node_order=1,
        node_type="APPROVAL",
        approval_mode="SINGLE",
        approver_type="FIXED_USER",
        approver_config={"user_ids": [admin.id]},
        is_active=True,
    )
    db_session.add(node)
    db_session.flush()

    instance = ApprovalInstance(
        instance_no=f"APINVLAPP{suffix}",
        template_id=template.id,
        flow_id=flow.id,
        entity_type="INVOICE",
        entity_id=invoice.id,
        initiator_id=admin.id,
        initiator_name=admin.real_name or admin.username,
        status="PENDING",
        current_node_id=node.id,
        title="发票旧审批入口测试",
        summary="发票旧审批入口测试",
    )
    db_session.add(instance)
    db_session.flush()

    task = ApprovalTask(
        instance_id=instance.id,
        node_id=node.id,
        task_type="APPROVAL",
        task_order=1,
        assignee_id=admin.id,
        assignee_name=admin.real_name or admin.username,
        status="PENDING",
    )
    db_session.add(task)
    db_session.commit()

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/approve",
        headers=_auth_headers(admin_token),
        json={"comments": "legacy approve invoice"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "APPROVED"

    db_session.refresh(task)
    db_session.refresh(instance)
    db_session.refresh(invoice)
    assert task.status == "COMPLETED"
    assert task.action == "APPROVE"
    assert task.comment == "legacy approve invoice"
    assert instance.status == "APPROVED"
    assert invoice.status == "APPROVED"


def test_invoice_legacy_cancel_route_cancels_approved_invoice(
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
        opp_code=f"INV-CAN-OPP-{suffix}",
        customer_id=project.customer_id,
        opp_name="发票旧作废入口测试商机",
        owner_id=admin.id,
    )
    db_session.add(opportunity)
    db_session.flush()

    contract = Contract(
        contract_code=f"INV-CAN-CON-{suffix}",
        contract_name="发票旧作废入口测试合同",
        contract_type="sales",
        customer_id=project.customer_id,
        opportunity_id=opportunity.id,
        total_amount=1000,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    invoice = Invoice(
        invoice_code=f"INV-CAN-{suffix}",
        contract_id=contract.id,
        amount=1000,
        total_amount=1000,
        paid_amount=0,
        status="APPROVED",
        buyer_name="发票旧作废入口测试客户",
    )
    db_session.add(invoice)
    db_session.commit()

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/cancel",
        headers=_auth_headers(admin_token),
        json={"reason": "客户要求作废"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "发票已作废"

    db_session.refresh(invoice)
    assert invoice.status == "CANCELLED"
    assert "客户要求作废" in invoice.remark


def test_invoice_delegate_action_transfers_pending_task_to_delegate_user(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    suffix = uuid4().hex[:8].upper()
    delegate_user = User(
        username=f"invoice_delegate_{suffix.lower()}",
        email=f"invoice_delegate_{suffix.lower()}@example.com",
        password_hash="test-password-hash",
        real_name="发票转办审批人",
        is_active=True,
    )
    db_session.add(delegate_user)
    db_session.flush()

    seeded = _seed_pending_invoice_approval(
        db_session,
        admin=admin,
        project=project,
        suffix=suffix,
        prefix="INVDEL",
    )
    invoice = seeded["invoice"]
    task = seeded["task"]
    instance = seeded["instance"]

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/approval/action",
        headers=_auth_headers(admin_token),
        json={
            "action": "DELEGATE",
            "delegate_to_id": delegate_user.id,
            "comment": "转给其他审批人",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "PENDING"

    db_session.refresh(task)
    db_session.refresh(instance)
    db_session.refresh(invoice)
    delegated_task = (
        db_session.query(ApprovalTask)
        .filter(
            ApprovalTask.instance_id == instance.id,
            ApprovalTask.assignee_id == delegate_user.id,
            ApprovalTask.status == "PENDING",
        )
        .one()
    )
    assert task.status == "TRANSFERRED"
    assert delegated_task.assignee_type == "TRANSFERRED"
    assert delegated_task.original_assignee_id == admin.id
    assert instance.status == "PENDING"
    assert invoice.status == "PENDING_APPROVAL"


def test_invoice_withdraw_action_uses_adapter_state_and_cancels_pending_tasks(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    admin = db_session.query(User).filter(User.username == "admin").first()
    project = db_session.query(Project).first()
    assert admin is not None
    assert project is not None

    suffix = uuid4().hex[:8].upper()
    seeded = _seed_pending_invoice_approval(
        db_session,
        admin=admin,
        project=project,
        suffix=suffix,
        prefix="INVWD",
    )
    invoice = seeded["invoice"]
    task = seeded["task"]
    instance = seeded["instance"]

    response = client.post(
        f"{settings.API_V1_PREFIX}/sales/invoices/{invoice.id}/approval/action",
        headers=_auth_headers(admin_token),
        json={"action": "WITHDRAW", "comment": "发起人撤回"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["status"] == "CANCELLED"

    db_session.refresh(task)
    db_session.refresh(instance)
    db_session.refresh(invoice)
    assert task.status == "CANCELLED"
    assert instance.status == "CANCELLED"
    assert invoice.status == "DRAFT"
