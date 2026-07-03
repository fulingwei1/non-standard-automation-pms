from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1.endpoints.business_support_orders.delivery_orders.crud import (
    ship_delivery_order,
)
from app.models.business_support import DeliveryOrder, InvoiceRequest, SalesOrder
from app.models.project import Customer, Project, ProjectPaymentPlan
from app.models.sales import Contract


@pytest.mark.asyncio
async def test_shipping_delivery_order_creates_delivery_payment_invoice_request(db_session):
    """设备发货后应自动触发 DELIVERY 发货款开票申请。"""
    suffix = uuid4().hex[:8].upper()
    today = date.today()

    customer = Customer(
        customer_code=f"CUST-DEL-{suffix}",
        customer_name=f"发货款客户{suffix}",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    project = Project(
        project_code=f"PJ-DEL-{suffix}",
        project_name=f"发货款项目{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        planned_start_date=today,
        planned_end_date=today + timedelta(days=120),
        stage="S6",
        status="ST06",
        health="H1",
    )
    db_session.add(project)
    db_session.flush()

    contract = Contract(
        contract_code=f"CON-DEL-{suffix}",
        contract_name=f"发货款合同{suffix}",
        contract_type="sales",
        customer_id=customer.id,
        project_id=project.id,
        total_amount=Decimal("100000.00"),
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.flush()

    order = SalesOrder(
        order_no=f"SO-DEL-{suffix}",
        contract_id=contract.id,
        contract_no=contract.contract_code,
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_id=project.id,
        project_no=project.project_code,
        order_amount=Decimal("100000.00"),
        order_status="ready",
    )
    db_session.add(order)
    db_session.flush()

    delivery_order = DeliveryOrder(
        delivery_no=f"DO-DEL-{suffix}",
        order_id=order.id,
        order_no=order.order_no,
        contract_id=contract.id,
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_id=project.id,
        delivery_date=today,
        delivery_amount=Decimal("100000.00"),
        approval_status="approved",
        delivery_status="approved",
    )
    db_session.add(delivery_order)

    plan = ProjectPaymentPlan(
        project_id=project.id,
        contract_id=contract.id,
        payment_no=2,
        payment_name="发货款",
        payment_type="DELIVERY",
        payment_ratio=Decimal("40.00"),
        planned_amount=Decimal("40000.00"),
        planned_date=today + timedelta(days=30),
        status="PENDING",
    )
    db_session.add(plan)
    db_session.commit()

    await ship_delivery_order(
        delivery_order.id,
        db=db_session,
        current_user=SimpleNamespace(id=1, username="admin", real_name="系统管理员"),
    )

    db_session.refresh(plan)
    invoice_request = (
        db_session.query(InvoiceRequest)
        .filter(InvoiceRequest.payment_plan_id == plan.id)
        .one()
    )

    assert invoice_request.status == "PENDING"
    assert invoice_request.contract_id == contract.id
    assert invoice_request.project_id == project.id
    assert invoice_request.customer_id == customer.id
    assert invoice_request.amount == Decimal("40000.00")
    assert invoice_request.expected_issue_date == today
    assert invoice_request.reason and "发货" in invoice_request.reason
    assert plan.planned_date == today
