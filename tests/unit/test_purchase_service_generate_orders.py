# -*- coding: utf-8 -*-
"""PurchaseService.generate_orders_from_request contracts."""

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Customer, Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, PurchaseRequest, PurchaseRequestItem
from app.models.vendor import Vendor
from app.services.purchase.purchase_service import PurchaseService


def _make_project(db: Session) -> Project:
    suffix = uuid4().hex[:8].upper()
    customer = Customer(
        customer_code=f"CUST-PO-{suffix}",
        customer_name="采购转单测试客户",
        contact_person="测试联系人",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db.add(customer)
    db.flush()

    project = Project(
        project_code=f"PJ-PO-{suffix}",
        project_name="采购转单测试项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
    )
    db.add(project)
    db.flush()
    return project


def _make_supplier(db: Session) -> Vendor:
    supplier = Vendor(
        supplier_code=f"SUP-PO-{uuid4().hex[:8].upper()}",
        supplier_name="采购转单测试供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
    )
    db.add(supplier)
    db.flush()
    return supplier


def _make_purchase_request(
    db: Session,
    *,
    status: str = "APPROVED",
    ordered_qty: Decimal = Decimal("0"),
) -> tuple[PurchaseRequest, PurchaseRequestItem, Vendor]:
    project = _make_project(db)
    supplier = _make_supplier(db)
    request = PurchaseRequest(
        request_no=f"PR-PO-{uuid4().hex[:8].upper()}",
        project_id=project.id,
        supplier_id=supplier.id,
        request_type="NORMAL",
        source_type="MANUAL",
        request_reason="采购申请转订单测试",
        total_amount=Decimal("500.00"),
        status=status,
        approved_by=1 if status == "APPROVED" else None,
        created_by=1,
        requested_by=1,
    )
    db.add(request)
    db.flush()

    item = PurchaseRequestItem(
        request_id=request.id,
        material_code=f"MAT-PO-{uuid4().hex[:6].upper()}",
        material_name="采购转单测试物料",
        specification="Spec-A",
        unit="件",
        quantity=Decimal("5"),
        unit_price=Decimal("100.00"),
        amount=Decimal("500.00"),
        ordered_qty=ordered_qty,
    )
    db.add(item)
    db.commit()
    db.refresh(request)
    db.refresh(item)
    return request, item, supplier


def test_generate_orders_from_request_requires_approved_request(db_session: Session):
    """未审批采购申请不能直接生成采购订单。"""
    request, _item, supplier = _make_purchase_request(db_session, status="SUBMITTED")

    with pytest.raises(HTTPException) as exc:
        PurchaseService(db_session).generate_orders_from_request(request.id, supplier.id)

    assert exc.value.status_code == 400
    assert "已审批" in exc.value.detail
    assert (
        db_session.query(PurchaseOrder)
        .filter(PurchaseOrder.source_request_id == request.id)
        .count()
        == 0
    )


def test_generate_orders_from_request_rejects_duplicate_generation(db_session: Session):
    """已有有效来源订单时，不能重复生成采购订单。"""
    request, item, supplier = _make_purchase_request(db_session, status="APPROVED")
    existing = PurchaseOrder(
        order_no=f"PO-EXIST-{uuid4().hex[:8].upper()}",
        supplier_id=supplier.id,
        project_id=request.project_id,
        source_request_id=request.id,
        total_amount=Decimal("500.00"),
        status=None,
    )
    db_session.add(existing)
    db_session.flush()
    db_session.add(
        PurchaseOrderItem(
            order_id=existing.id,
            item_no=1,
            material_code=item.material_code,
            material_name=item.material_name,
            specification=item.specification,
            unit=item.unit,
            quantity=item.quantity,
            unit_price=item.unit_price,
            amount=item.amount,
        )
    )
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        PurchaseService(db_session).generate_orders_from_request(request.id, supplier.id)

    assert exc.value.status_code == 400
    assert "已生成" in exc.value.detail
    assert (
        db_session.query(PurchaseOrder)
        .filter(PurchaseOrder.source_request_id == request.id)
        .count()
        == 1
    )


def test_generate_orders_from_request_syncs_ordered_qty_and_request_flags(db_session: Session):
    """转单成功后应回写申请明细 ordered_qty 和申请自动转单标记。"""
    request, item, supplier = _make_purchase_request(db_session, status="APPROVED")

    result = PurchaseService(db_session).generate_orders_from_request(request.id, supplier.id)
    db_session.commit()

    db_session.refresh(request)
    db_session.refresh(item)
    order = (
        db_session.query(PurchaseOrder)
        .filter(PurchaseOrder.source_request_id == request.id)
        .one()
    )

    assert result is True
    assert order.supplier_id == supplier.id
    assert order.total_amount == Decimal("500.00")
    assert item.ordered_qty == Decimal("5")
    assert request.auto_po_created is True
    assert request.auto_po_created_at is not None
