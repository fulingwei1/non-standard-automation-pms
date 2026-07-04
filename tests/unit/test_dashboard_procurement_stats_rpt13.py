# -*- coding: utf-8 -*-
"""RPT-13: procurement dashboard savings must come from purchase data."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.v1.endpoints.dashboard.stats import get_procurement_stats
from app.models.purchase import PurchaseOrder, PurchaseRequest
from app.models.vendor import Vendor


def _make_supplier(db: Session) -> Vendor:
    supplier = Vendor(
        supplier_code=f"SUP-RPT13-{uuid4().hex[:8].upper()}",
        supplier_name="RPT13采购看板供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
    )
    db.add(supplier)
    db.flush()
    return supplier


def _make_request(db: Session, amount: str) -> PurchaseRequest:
    request = PurchaseRequest(
        request_no=f"PR-RPT13-{uuid4().hex[:8].upper()}",
        request_type="NORMAL",
        source_type="MANUAL",
        request_reason="采购看板节省金额测试",
        total_amount=Decimal(amount),
        status="APPROVED",
        created_by=1,
        requested_by=1,
    )
    db.add(request)
    db.flush()
    return request


def _make_order(
    db: Session,
    supplier: Vendor,
    request: PurchaseRequest,
    *,
    total_amount: str,
    amount_with_tax: str = "0",
    status: str = "CONFIRMED",
) -> PurchaseOrder:
    order = PurchaseOrder(
        order_no=f"PO-RPT13-{uuid4().hex[:8].upper()}",
        supplier_id=supplier.id,
        source_request_id=request.id,
        order_type="NORMAL",
        order_title="RPT13采购看板订单",
        status=status,
        order_date=date.today(),
        required_date=date.today(),
        total_amount=Decimal(total_amount),
        amount_with_tax=Decimal(amount_with_tax),
        created_by=1,
    )
    db.add(order)
    db.flush()
    return order


def _stat_by_key(result: dict, key: str) -> dict:
    return next(card for card in result["stats"] if card["key"] == key)


def test_procurement_stats_reports_positive_request_delta_as_savings(db_session: Session):
    supplier = _make_supplier(db_session)
    request = _make_request(db_session, "1000.00")
    _make_order(db_session, supplier, request, total_amount="400.00")
    _make_order(db_session, supplier, request, total_amount="0", amount_with_tax="300.00")
    db_session.commit()

    result = get_procurement_stats(db_session, MagicMock())

    assert _stat_by_key(result, "savings")["value"] == "¥300"
