# -*- coding: utf-8 -*-
"""PROD-19: outsourcing delivery quantity, receipt confirmation, work order link."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.outsourcing import deliveries as delivery_api
from app.api.v1.endpoints.outsourcing import orders as order_api
from app.models.outsourcing import (
    OutsourcingDelivery,
    OutsourcingDeliveryItem,
    OutsourcingOrder,
    OutsourcingOrderItem,
)
from app.models.production import WorkOrder
from app.models.project import Project
from app.models.vendor import Vendor
from app.schemas.outsourcing import (
    OutsourcingDeliveryCreate,
    OutsourcingDeliveryItemCreate,
    OutsourcingOrderCreate,
    OutsourcingOrderItemCreate,
)


def _current_user(user_id=1):
    return SimpleNamespace(id=user_id, real_name="测试用户", username="tester")


def _seed_vendor_project_work_order(db_session):
    vendor = Vendor(
        supplier_code="OS-VENDOR-001",
        supplier_name="外协供应商",
        vendor_type="OUTSOURCING",
        status="ACTIVE",
    )
    project = Project(project_code="OS-PROJ-001", project_name="外协测试项目")
    db_session.add_all([vendor, project])
    db_session.flush()

    work_order = WorkOrder(
        work_order_no="WO-OS-001",
        task_name="外协加工工单",
        task_type="MACHINING",
        project_id=project.id,
        status="PENDING",
    )
    db_session.add(work_order)
    db_session.flush()
    return vendor, project, work_order


def _seed_order_with_item(db_session, *, quantity=Decimal("10"), delivered=Decimal("0")):
    vendor, project, work_order = _seed_vendor_project_work_order(db_session)
    order = OutsourcingOrder(
        order_no="OS-ORDER-001",
        vendor_id=vendor.id,
        project_id=project.id,
        order_type="MACHINING",
        order_title="外协加工",
        status="APPROVED",
    )
    db_session.add(order)
    db_session.flush()
    item = OutsourcingOrderItem(
        order_id=order.id,
        item_no=1,
        material_code="MAT-001",
        material_name="加工件",
        quantity=quantity,
        unit_price=Decimal("10"),
        amount=quantity * Decimal("10"),
        delivered_quantity=delivered,
    )
    db_session.add(item)
    db_session.commit()
    return order, item, work_order


def test_order_create_schema_accepts_work_order_id():
    payload = OutsourcingOrderCreate(
        vendor_id=1,
        project_id=1,
        work_order_id=99,
        order_type="MACHINING",
        order_title="外协加工",
        items=[
            OutsourcingOrderItemCreate(
                material_code="MAT-001",
                material_name="加工件",
                quantity=Decimal("1"),
                unit_price=Decimal("10"),
            )
        ],
    )

    assert payload.work_order_id == 99


def test_create_delivery_rejects_over_delivery_quantity(db_session):
    order, item, _work_order = _seed_order_with_item(
        db_session,
        quantity=Decimal("10"),
        delivered=Decimal("4"),
    )
    delivery_in = OutsourcingDeliveryCreate(
        order_id=order.id,
        delivery_date=date.today(),
        items=[
            OutsourcingDeliveryItemCreate(
                order_item_id=item.id,
                delivery_quantity=Decimal("7"),
            )
        ],
    )

    with pytest.raises(HTTPException) as exc:
        delivery_api.create_outsourcing_delivery(
            db=db_session,
            delivery_in=delivery_in,
            current_user=_current_user(),
        )

    assert exc.value.status_code == 400
    assert "超出订单剩余数量" in exc.value.detail


def test_receive_delivery_marks_received_quantities_and_order_status(db_session):
    order, item, _work_order = _seed_order_with_item(db_session, quantity=Decimal("5"))
    delivery = OutsourcingDelivery(
        delivery_no="OS-DEL-001",
        order_id=order.id,
        vendor_id=order.vendor_id,
        delivery_date=date.today(),
        status="PENDING",
    )
    db_session.add(delivery)
    db_session.flush()
    delivery_item = OutsourcingDeliveryItem(
        delivery_id=delivery.id,
        order_item_id=item.id,
        material_code=item.material_code,
        material_name=item.material_name,
        delivery_quantity=Decimal("5"),
    )
    db_session.add(delivery_item)
    db_session.commit()

    result = delivery_api.receive_outsourcing_delivery(
        delivery_id=delivery.id,
        payload={},
        db=db_session,
        current_user=_current_user(42),
    )

    db_session.refresh(delivery)
    db_session.refresh(delivery_item)
    db_session.refresh(order)
    assert result.status == "RECEIVED"
    assert delivery.status == "RECEIVED"
    assert delivery.received_by == 42
    assert delivery_item.received_quantity == Decimal("5")
    assert order.status == "RECEIVED"


def test_create_order_persists_work_order_link(db_session):
    vendor, project, work_order = _seed_vendor_project_work_order(db_session)
    order_in = OutsourcingOrderCreate(
        vendor_id=vendor.id,
        project_id=project.id,
        work_order_id=work_order.id,
        order_type="MACHINING",
        order_title="外协加工",
        items=[
            OutsourcingOrderItemCreate(
                material_code="MAT-001",
                material_name="加工件",
                quantity=Decimal("2"),
                unit_price=Decimal("10"),
            )
        ],
    )

    response = order_api.create_outsourcing_order(
        db=db_session,
        order_in=order_in,
        current_user=_current_user(),
    )
    order = db_session.query(OutsourcingOrder).filter_by(id=response.id).first()

    assert order.work_order_id == work_order.id
    assert response.work_order_id == work_order.id
