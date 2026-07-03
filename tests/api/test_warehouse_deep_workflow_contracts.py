# -*- coding: utf-8 -*-
"""Warehouse write-chain contract regressions."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.warehouse import Inventory, Warehouse, WarehouseLocation


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_warehouse(db: Session, suffix: str) -> tuple[Warehouse, WarehouseLocation]:
    warehouse = Warehouse(
        warehouse_code=f"QA-WH-{suffix}",
        warehouse_name=f"QA 仓库 {suffix}",
        warehouse_type="NORMAL",
        is_active=True,
    )
    db.add(warehouse)
    db.flush()
    location = WarehouseLocation(
        warehouse_id=warehouse.id,
        location_code=f"QA-LOC-{suffix}",
        location_name=f"QA 库位 {suffix}",
        is_active=True,
    )
    db.add(location)
    db.commit()
    db.refresh(warehouse)
    db.refresh(location)
    return warehouse, location


def test_completing_inbound_creates_inventory_and_received_quantities(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    warehouse, location = _create_warehouse(db_session, suffix)
    material_code = f"QA-IN-{suffix}"
    headers = _auth_headers(admin_token)

    create_response = client.post(
        f"{settings.API_V1_PREFIX}/warehouse/inbound",
        headers=headers,
        json={
            "warehouse_id": warehouse.id,
            "source_no": f"SRC-{suffix}",
            "supplier_name": "QA 供应商",
            "items": [
                {
                    "material_code": material_code,
                    "material_name": "QA 入库物料",
                    "specification": "SPEC-A",
                    "unit": "件",
                    "planned_quantity": 10,
                    "location_id": location.id,
                }
            ],
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 200, create_response.text
    order_id = create_response.json()["id"]

    complete_response = client.put(
        f"{settings.API_V1_PREFIX}/warehouse/inbound/{order_id}/status?status=COMPLETED",
        headers=headers,
        follow_redirects=False,
    )
    assert complete_response.status_code == 200, complete_response.text

    db_session.expire_all()
    inventory = (
        db_session.query(Inventory)
        .filter(
            Inventory.warehouse_id == warehouse.id,
            Inventory.location_id == location.id,
            Inventory.material_code == material_code,
        )
        .one()
    )
    assert float(inventory.quantity) == 10
    assert float(inventory.available_quantity) == 10
    assert inventory.last_inbound_date is not None

    detail_response = client.get(
        f"{settings.API_V1_PREFIX}/warehouse/inbound/{order_id}",
        headers=headers,
        follow_redirects=False,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["status"] == "COMPLETED"
    assert detail["received_quantity"] == 10
    assert detail["items"][0]["received_quantity"] == 10

    idempotent_response = client.put(
        f"{settings.API_V1_PREFIX}/warehouse/inbound/{order_id}/status?status=COMPLETED",
        headers=headers,
        follow_redirects=False,
    )
    assert idempotent_response.status_code == 200, idempotent_response.text
    db_session.expire_all()
    assert float(db_session.get(Inventory, inventory.id).quantity) == 10


def test_completing_outbound_deducts_inventory_and_rejects_short_stock(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    warehouse, location = _create_warehouse(db_session, suffix)
    material_code = f"QA-OUT-{suffix}"
    inventory = Inventory(
        warehouse_id=warehouse.id,
        location_id=location.id,
        material_code=material_code,
        material_name="QA 出库物料",
        specification="SPEC-B",
        unit="件",
        quantity=10,
        available_quantity=10,
        reserved_quantity=0,
    )
    db_session.add(inventory)
    db_session.commit()
    db_session.refresh(inventory)
    headers = _auth_headers(admin_token)

    create_response = client.post(
        f"{settings.API_V1_PREFIX}/warehouse/outbound",
        headers=headers,
        json={
            "warehouse_id": warehouse.id,
            "target_no": f"TGT-{suffix}",
            "department": "QA 部门",
            "items": [
                {
                    "material_code": material_code,
                    "material_name": "QA 出库物料",
                    "specification": "SPEC-B",
                    "unit": "件",
                    "planned_quantity": 4,
                    "location_id": location.id,
                }
            ],
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 200, create_response.text
    order_id = create_response.json()["id"]

    complete_response = client.put(
        f"{settings.API_V1_PREFIX}/warehouse/outbound/{order_id}/status?status=COMPLETED",
        headers=headers,
        follow_redirects=False,
    )
    assert complete_response.status_code == 200, complete_response.text

    db_session.expire_all()
    inventory = db_session.get(Inventory, inventory.id)
    assert float(inventory.quantity) == 6
    assert float(inventory.available_quantity) == 6
    assert inventory.last_outbound_date is not None

    detail_response = client.get(
        f"{settings.API_V1_PREFIX}/warehouse/outbound/{order_id}",
        headers=headers,
        follow_redirects=False,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["status"] == "COMPLETED"
    assert detail["picked_quantity"] == 4
    assert detail["items"][0]["picked_quantity"] == 4

    idempotent_response = client.put(
        f"{settings.API_V1_PREFIX}/warehouse/outbound/{order_id}/status?status=COMPLETED",
        headers=headers,
        follow_redirects=False,
    )
    assert idempotent_response.status_code == 200, idempotent_response.text
    db_session.expire_all()
    assert float(db_session.get(Inventory, inventory.id).quantity) == 6

    short_response = client.post(
        f"{settings.API_V1_PREFIX}/warehouse/outbound",
        headers=headers,
        json={
            "warehouse_id": warehouse.id,
            "target_no": f"TGT-SHORT-{suffix}",
            "department": "QA 部门",
            "items": [
                {
                    "material_code": material_code,
                    "planned_quantity": 7,
                    "location_id": location.id,
                }
            ],
        },
        follow_redirects=False,
    )
    assert short_response.status_code == 200, short_response.text
    short_id = short_response.json()["id"]
    reject_response = client.put(
        f"{settings.API_V1_PREFIX}/warehouse/outbound/{short_id}/status?status=COMPLETED",
        headers=headers,
        follow_redirects=False,
    )
    assert reject_response.status_code == 400, reject_response.text
    db_session.expire_all()
    assert float(db_session.get(Inventory, inventory.id).quantity) == 6


def test_stock_count_create_update_and_complete_returns_serializable_contract(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid4().hex[:8]
    warehouse, location = _create_warehouse(db_session, suffix)
    headers = _auth_headers(admin_token)

    create_response = client.post(
        f"{settings.API_V1_PREFIX}/warehouse/stock-count",
        headers=headers,
        json={
            "warehouse_id": warehouse.id,
            "count_type": "FULL",
            "items": [
                {
                    "material_code": f"QA-SC-{suffix}",
                    "material_name": "QA 盘点物料",
                    "location_id": location.id,
                    "system_quantity": 6,
                }
            ],
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 200, create_response.text
    count_order = create_response.json()
    assert isinstance(count_order["created_at"], str)
    item_id = count_order["items"][0]["id"]

    update_response = client.put(
        f"{settings.API_V1_PREFIX}/warehouse/stock-count/{count_order['id']}/items/{item_id}",
        headers=headers,
        json={"actual_quantity": 6},
        follow_redirects=False,
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["diff_quantity"] == 0

    complete_response = client.put(
        f"{settings.API_V1_PREFIX}/warehouse/stock-count/{count_order['id']}/status?status=COMPLETED",
        headers=headers,
        follow_redirects=False,
    )
    assert complete_response.status_code == 200, complete_response.text

    detail_response = client.get(
        f"{settings.API_V1_PREFIX}/warehouse/stock-count/{count_order['id']}",
        headers=headers,
        follow_redirects=False,
    )
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["status"] == "COMPLETED"
    assert detail["matched_items"] == 1
    assert detail["diff_items"] == 0
