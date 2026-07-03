# -*- coding: utf-8 -*-
"""Purchase goods receipt workflow contract regressions."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inventory_tracking import MaterialStock, MaterialTransaction
from app.models.material import Material
from app.models.purchase import GoodsReceipt, GoodsReceiptItem, PurchaseOrder, PurchaseOrderItem
from app.models.user import User
from app.models.vendor import Vendor
from app.services.kit_rate import KitRateService


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _unwrap(response):
    body = response.json()
    return body.get("data", body) if isinstance(body, dict) else body


def _items(response):
    data = _unwrap(response)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("items", [])
    return []


def _admin_user(db: Session) -> User:
    return db.query(User).filter(User.username == "admin").first()


def _seed_vendor(db: Session, suffix: str, user_id: int) -> Vendor:
    vendor = Vendor(
        supplier_code=f"QA-RCPT-V-{suffix}",
        supplier_name=f"QA 收货供应商 {suffix}",
        vendor_type="MATERIAL",
        supplier_level="A",
        status="ACTIVE",
        created_by=user_id,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


def _create_approved_order(
    client: TestClient,
    headers: dict[str, str],
    vendor_id: int,
    suffix: str,
    quantity: int = 5,
    material_id: int | None = None,
) -> tuple[int, int]:
    item_payload = {
        "material_code": f"QA-RCPT-MAT-{suffix}",
        "material_name": "QA 收货物料",
        "unit": "件",
        "quantity": quantity,
        "unit_price": 10,
        "tax_rate": 13,
    }
    if material_id is not None:
        item_payload["material_id"] = material_id

    response = client.post(
        f"{settings.API_V1_PREFIX}/purchase-orders/",
        headers=headers,
        json={
            "supplier_id": vendor_id,
            "order_title": f"QA 收货订单 {suffix}",
            "items": [item_payload],
        },
        follow_redirects=False,
    )
    assert response.status_code == 200, response.text
    order_id = _unwrap(response)["id"]

    submit = client.put(
        f"{settings.API_V1_PREFIX}/purchase-orders/{order_id}/submit",
        headers=headers,
        follow_redirects=False,
    )
    assert submit.status_code == 200, submit.text
    approve = client.put(
        f"{settings.API_V1_PREFIX}/purchase-orders/{order_id}/approve?approved=true",
        headers=headers,
        follow_redirects=False,
    )
    assert approve.status_code == 200, approve.text

    items_response = client.get(
        f"{settings.API_V1_PREFIX}/purchase-orders/{order_id}/items",
        headers=headers,
        follow_redirects=False,
    )
    assert items_response.status_code == 200, items_response.text
    item_id = _items(items_response)[0]["id"]
    return order_id, item_id


def _create_receipt(
    client: TestClient,
    headers: dict[str, str],
    order_id: int,
    order_item_id: int,
    suffix: str,
    qty: int,
):
    return client.post(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/",
        headers=headers,
        json={
            "order_id": order_id,
            "receipt_date": date.today().isoformat(),
            "receipt_type": "NORMAL",
            "delivery_note_no": f"QA-RCPT-DN-{suffix}",
            "items": [
                {
                    "order_item_id": order_item_id,
                    "delivery_qty": qty,
                    "received_qty": qty,
                }
            ],
        },
        follow_redirects=False,
    )


def test_goods_receipts_list_filters_by_order_and_status(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    vendor = _seed_vendor(db_session, suffix, admin.id)
    headers = _auth_headers(admin_token)
    order_a, item_a = _create_approved_order(client, headers, vendor.id, f"{suffix}-A")
    order_b, item_b = _create_approved_order(client, headers, vendor.id, f"{suffix}-B")

    receipt_a = _create_receipt(client, headers, order_a, item_a, f"{suffix}-A", 1)
    assert receipt_a.status_code == 200, receipt_a.text
    receipt_b = _create_receipt(client, headers, order_b, item_b, f"{suffix}-B", 1)
    assert receipt_b.status_code == 200, receipt_b.text

    response = client.get(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/"
        f"?order_id={order_a}&status=PENDING&page=1&page_size=1000",
        headers=headers,
        follow_redirects=False,
    )
    assert response.status_code == 200, response.text
    rows = _items(response)
    assert rows
    assert all(row["order_id"] == order_a for row in rows)
    assert all(row["status"] == "PENDING" for row in rows)


def test_goods_receipt_rejects_quantity_over_order_remaining(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    vendor = _seed_vendor(db_session, suffix, admin.id)
    headers = _auth_headers(admin_token)
    order_id, item_id = _create_approved_order(client, headers, vendor.id, suffix, quantity=5)

    first = _create_receipt(client, headers, order_id, item_id, f"{suffix}-FIRST", qty=3)
    assert first.status_code == 200, first.text

    second = _create_receipt(client, headers, order_id, item_id, f"{suffix}-OVER", qty=3)
    assert second.status_code == 400, second.text
    assert "剩余" in second.text or "超过" in second.text

    db_session.expire_all()
    order_item = db_session.get(PurchaseOrderItem, item_id)
    assert float(order_item.received_qty) == 3.0


def test_goods_receipt_updates_order_item_status_and_amounts(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    vendor = _seed_vendor(db_session, suffix, admin.id)
    headers = _auth_headers(admin_token)
    order_id, item_id = _create_approved_order(client, headers, vendor.id, suffix, quantity=5)

    first = _create_receipt(client, headers, order_id, item_id, f"{suffix}-FIRST", qty=2)
    assert first.status_code == 200, first.text
    first_receipt_id = _unwrap(first)["id"]

    db_session.expire_all()
    first_item = (
        db_session.query(GoodsReceiptItem)
        .filter(GoodsReceiptItem.receipt_id == first_receipt_id)
        .one()
    )
    order = db_session.get(PurchaseOrder, order_id)
    order_item = db_session.get(PurchaseOrderItem, item_id)
    assert first_item.amount == Decimal("20.00")
    assert order_item.received_qty == Decimal("2.0000")
    assert order_item.status == "PARTIAL_RECEIVED"
    assert order.status == "PARTIAL_RECEIVED"
    assert order.received_amount == Decimal("20.00")

    second = _create_receipt(client, headers, order_id, item_id, f"{suffix}-SECOND", qty=3)
    assert second.status_code == 200, second.text
    second_receipt_id = _unwrap(second)["id"]

    db_session.expire_all()
    second_item = (
        db_session.query(GoodsReceiptItem)
        .filter(GoodsReceiptItem.receipt_id == second_receipt_id)
        .one()
    )
    order = db_session.get(PurchaseOrder, order_id)
    order_item = db_session.get(PurchaseOrderItem, item_id)
    assert second_item.amount == Decimal("30.00")
    assert order_item.received_qty == Decimal("5.0000")
    assert order_item.status == "RECEIVED"
    assert order.status == "RECEIVED"
    assert order.received_amount == Decimal("50.00")


def test_approved_purchase_order_counts_remaining_quantity_as_in_transit(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    vendor = _seed_vendor(db_session, suffix, admin.id)
    material = Material(
        material_code=f"QA-RCPT-TRANSIT-{suffix}",
        material_name=f"QA 在途物料 {suffix}",
        unit="件",
        current_stock=Decimal("0"),
        standard_price=Decimal("10"),
        created_by=admin.id,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)

    headers = _auth_headers(admin_token)
    order_id, item_id = _create_approved_order(
        client,
        headers,
        vendor.id,
        suffix,
        quantity=5,
        material_id=material.id,
    )

    service = KitRateService(db_session)
    assert service._get_in_transit_qty(material.id) == Decimal("5.0000")

    first = _create_receipt(client, headers, order_id, item_id, f"{suffix}-FIRST", qty=2)
    assert first.status_code == 200, first.text
    db_session.expire_all()
    assert service._get_in_transit_qty(material.id) == Decimal("3.0000")

    second = _create_receipt(client, headers, order_id, item_id, f"{suffix}-SECOND", qty=3)
    assert second.status_code == 200, second.text
    db_session.expire_all()
    assert service._get_in_transit_qty(material.id) == Decimal("0")


def test_goods_receipt_creates_purchase_in_stock_transaction(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    vendor = _seed_vendor(db_session, suffix, admin.id)
    material = Material(
        material_code=f"QA-RCPT-MAT-{suffix}",
        material_name=f"QA 收货入库物料 {suffix}",
        unit="件",
        current_stock=Decimal("0"),
        standard_price=Decimal("10"),
        created_by=admin.id,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)

    headers = _auth_headers(admin_token)
    order_id, item_id = _create_approved_order(
        client,
        headers,
        vendor.id,
        suffix,
        quantity=5,
        material_id=material.id,
    )

    receipt = _create_receipt(client, headers, order_id, item_id, suffix, qty=4)
    assert receipt.status_code == 200, receipt.text
    receipt_id = _unwrap(receipt)["id"]

    item_response = client.get(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/{receipt_id}/items",
        headers=headers,
        follow_redirects=False,
    )
    assert item_response.status_code == 200, item_response.text
    receipt_item_id = _items(item_response)[0]["id"]

    inspect = client.put(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/{receipt_id}"
        f"/items/{receipt_item_id}/inspect",
        params={
            "inspect_qty": 4,
            "qualified_qty": 4,
            "rejected_qty": 0,
            "inspect_result": "QUALIFIED",
        },
        headers=headers,
        follow_redirects=False,
    )
    assert inspect.status_code == 200, inspect.text

    db_session.expire_all()
    stock = (
        db_session.query(MaterialStock)
        .filter(MaterialStock.material_id == material.id, MaterialStock.location == "默认仓库")
        .one_or_none()
    )
    assert stock is not None
    assert stock.quantity == Decimal("4.0000")
    assert stock.available_quantity == Decimal("4.0000")
    db_session.refresh(material)
    assert material.current_stock == Decimal("4.0000")

    tx = (
        db_session.query(MaterialTransaction)
        .filter(
            MaterialTransaction.material_id == material.id,
            MaterialTransaction.transaction_type == "PURCHASE_IN",
            MaterialTransaction.related_order_id == order_id,
        )
        .one_or_none()
    )
    assert tx is not None
    assert tx.quantity == Decimal("4.0000")


def test_goods_receipt_partial_inspection_uses_frontend_status_contract(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    admin = _admin_user(db_session)
    vendor = _seed_vendor(db_session, suffix, admin.id)
    headers = _auth_headers(admin_token)
    order_id, item_id = _create_approved_order(client, headers, vendor.id, suffix, quantity=5)

    receipt_response = _create_receipt(client, headers, order_id, item_id, suffix, qty=3)
    assert receipt_response.status_code == 200, receipt_response.text
    receipt_id = _unwrap(receipt_response)["id"]

    receive = client.put(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/{receipt_id}/receive"
        "?status=RECEIVED",
        headers=headers,
        follow_redirects=False,
    )
    assert receive.status_code == 200, receive.text

    item_response = client.get(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/{receipt_id}/items",
        headers=headers,
        follow_redirects=False,
    )
    receipt_item_id = _items(item_response)[0]["id"]

    inspect = client.put(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/{receipt_id}"
        f"/items/{receipt_item_id}/inspect",
        params={
            "inspect_qty": 3,
            "qualified_qty": 2,
            "rejected_qty": 1,
            "inspect_result": "PARTIAL",
        },
        headers=headers,
        follow_redirects=False,
    )
    assert inspect.status_code == 200, inspect.text

    detail = client.get(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/{receipt_id}",
        headers=headers,
        follow_redirects=False,
    )
    assert detail.status_code == 200, detail.text
    receipt = _unwrap(detail)
    assert receipt["inspect_status"] == "PARTIAL"

    items = client.get(
        f"{settings.API_V1_PREFIX}/purchase-orders/goods-receipts/{receipt_id}/items",
        headers=headers,
        follow_redirects=False,
    )
    item = _items(items)[0]
    assert item["inspect_result"] == "PARTIAL"
    assert item["rejected_qty"] == 1.0
