# -*- coding: utf-8 -*-
"""Business support delivery route ordering contracts."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.business_support import DeliveryOrder, SalesOrder
from app.models.project import Customer, Project


def test_delivery_statistics_static_route_is_not_captured_by_detail_route(
    client: TestClient, admin_token: str
):
    response = client.get(
        f"{settings.API_V1_PREFIX}/business-support-orders/delivery-orders/statistics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert {"pending_shipments", "shipped_today", "in_transit", "total_orders"} <= set(data)


def test_delivery_order_workflow_routes(
    client: TestClient, db_session: Session, admin_token: str
):
    suffix = uuid.uuid4().hex[:8].upper()
    customer = Customer(
        customer_code=f"CUS-DEL-{suffix}",
        customer_name=f"发货测试客户-{suffix}",
        contact_person="测试联系人",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    sales_order = SalesOrder(
        order_no=f"SO-DEL-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        order_type="standard",
        order_amount=Decimal("88000.00"),
        currency="CNY",
        order_status="ready",
    )
    db_session.add(sales_order)
    db_session.flush()

    delivery = DeliveryOrder(
        delivery_no=f"DO-DEL-{suffix}",
        order_id=sales_order.id,
        order_no=sales_order.order_no,
        customer_id=customer.id,
        customer_name=customer.customer_name,
        delivery_date=date.today(),
        delivery_type="freight",
        delivery_amount=Decimal("88000.00"),
        approval_status="pending",
        delivery_status="draft",
    )
    db_session.add(delivery)
    db_session.commit()
    db_session.refresh(delivery)

    headers = {"Authorization": f"Bearer {admin_token}"}

    pending = client.get(
        f"{settings.API_V1_PREFIX}/business-support-orders/delivery-orders/pending-approval",
        headers=headers,
    )
    assert pending.status_code == 200, pending.text
    pending_items = pending.json()["data"]["items"]
    assert any(item["id"] == delivery.id for item in pending_items)

    approved = client.post(
        f"{settings.API_V1_PREFIX}/business-support-orders/delivery-orders/{delivery.id}/approve",
        headers=headers,
        json={"approved": True, "approval_comment": "同意发货"},
    )
    assert approved.status_code == 200, approved.text
    approved_data = approved.json()["data"]
    assert approved_data["approval_status"] == "approved"
    assert approved_data["delivery_status"] == "approved"

    printed = client.post(
        f"{settings.API_V1_PREFIX}/business-support-orders/delivery-orders/{delivery.id}/print",
        headers=headers,
    )
    assert printed.status_code == 200, printed.text
    assert printed.json()["data"]["delivery_status"] == "printed"

    shipped = client.post(
        f"{settings.API_V1_PREFIX}/business-support-orders/delivery-orders/{delivery.id}/ship",
        headers=headers,
    )
    assert shipped.status_code == 200, shipped.text
    assert shipped.json()["data"]["delivery_status"] == "shipped"
    assert shipped.json()["data"]["ship_date"] is not None

    received = client.post(
        f"{settings.API_V1_PREFIX}/business-support-orders/delivery-orders/{delivery.id}/receive",
        headers=headers,
    )
    assert received.status_code == 200, received.text
    assert received.json()["data"]["delivery_status"] == "received"
    assert received.json()["data"]["receive_date"] is not None


def test_delivery_order_create_requires_project_derived_sales_order(
    client: TestClient, db_session: Session, admin_token: str
):
    suffix = uuid.uuid4().hex[:8].upper()
    customer = Customer(
        customer_code=f"CUS-DEL-PROJ-{suffix}",
        customer_name=f"项目发货客户-{suffix}",
        contact_person="测试联系人",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    standalone_order = SalesOrder(
        order_no=f"SO-DEL-STANDALONE-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        order_type="standard",
        order_amount=Decimal("68000.00"),
        currency="CNY",
        order_status="ready",
    )
    db_session.add(standalone_order)
    db_session.commit()
    db_session.refresh(standalone_order)

    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "order_id": standalone_order.id,
        "delivery_date": str(date.today()),
        "delivery_type": "freight",
        "delivery_amount": "68000.00",
    }
    blocked = client.post(
        f"{settings.API_V1_PREFIX}/business-support-orders/delivery-orders",
        headers=headers,
        json=payload,
    )

    assert blocked.status_code == 400, blocked.text
    assert "项目" in blocked.json()["detail"]

    project = Project(
        project_code=f"PJ-DEL-{suffix}",
        project_name=f"发货测试项目-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_type="NEW",
        product_category="ICT",
        project_category="销售",
    )
    db_session.add(project)
    db_session.flush()

    project_order = SalesOrder(
        order_no=f"SO-DEL-PROJ-{suffix}",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        project_id=project.id,
        project_no=project.project_code,
        order_type="standard",
        order_amount=Decimal("98000.00"),
        currency="CNY",
        order_status="ready",
    )
    db_session.add(project_order)
    db_session.commit()
    db_session.refresh(project_order)

    created = client.post(
        f"{settings.API_V1_PREFIX}/business-support-orders/delivery-orders",
        headers=headers,
        json={
            **payload,
            "order_id": project_order.id,
            "delivery_amount": "98000.00",
        },
    )

    assert created.status_code == 200, created.text
    data = created.json()["data"]
    assert data["order_id"] == project_order.id
    assert data["project_id"] == project.id
    assert data["delivery_date"] == str(date.today())
    assert data["ship_date"] is None
