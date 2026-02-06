# -*- coding: utf-8 -*-
"""Shortage arrival tracking API tests."""

from datetime import date, timedelta
from decimal import Decimal
from typing import List
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material import Material
from app.models.shortage import ArrivalFollowUp, MaterialArrival
from app.models.user import User

ARRIVALS_BASE = f"{settings.API_V1_PREFIX}/shortage/handling/arrivals"


def _create_material(db_session: Session) -> Material:
    """Create a bare minimum material record for arrival flows."""
    material = Material(
        material_code=f"ARR-MAT-{uuid4().hex[:6].upper()}",
        material_name="缺料测试物料",
        specification="Spec-ARR",
        unit="件",
        is_active=True,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


def _cleanup_arrivals(db_session: Session, arrival_ids: List[int], material_ids: List[int]) -> None:
    if arrival_ids:
        db_session.query(ArrivalFollowUp).filter(ArrivalFollowUp.arrival_id.in_(arrival_ids)).delete(
            synchronize_session=False
        )
        db_session.query(MaterialArrival).filter(MaterialArrival.id.in_(arrival_ids)).delete(
            synchronize_session=False
        )
    if material_ids:
        db_session.query(Material).filter(Material.id.in_(material_ids)).delete(synchronize_session=False)
    db_session.commit()


@pytest.mark.api
def test_create_arrival_and_filter_by_status_and_keyword(
    client: TestClient,
    admin_auth_headers: dict,
    db_session: Session,
):
    arrival_ids: List[int] = []
    material_ids: List[int] = []
    try:
        material = _create_material(db_session)
        material_ids.append(material.id)

        create_resp = client.post(
            ARRIVALS_BASE,
            json={
                "material_id": material.id,
                "expected_qty": "12",
                "expected_date": date.today().isoformat(),
                "remark": "auto-test arrival",
            },
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        arrival_ids.append(created["id"])
        assert created["material_code"] == material.material_code
        assert created["status"] == "PENDING"

        status_resp = client.put(
            f"{ARRIVALS_BASE}/{created['id']}/status",
            json="IN_TRANSIT",
            headers=admin_auth_headers,
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["status"] == "IN_TRANSIT"

        list_resp = client.get(
            f"{ARRIVALS_BASE}?status=IN_TRANSIT&keyword={material.material_code}&page=1&page_size=5",
            headers=admin_auth_headers,
        )
        assert list_resp.status_code == 200
        payload = list_resp.json()
        assert payload["total"] >= 1
        assert any(item["id"] == created["id"] for item in payload["items"])
        assert all(item["status"] == "IN_TRANSIT" for item in payload["items"])
    finally:
        _cleanup_arrivals(db_session, arrival_ids, material_ids)


@pytest.mark.api
def test_arrival_follow_up_delayed_listing_and_receive(
    client: TestClient,
    admin_auth_headers: dict,
    db_session: Session,
):
    arrival_ids: List[int] = []
    material_ids: List[int] = []
    try:
        material = _create_material(db_session)
        material_ids.append(material.id)
        expected_date = (date.today() - timedelta(days=3)).isoformat()

        create_resp = client.post(
            ARRIVALS_BASE,
            json={
                "material_id": material.id,
                "expected_qty": "4",
                "expected_date": expected_date,
                "remark": "delay scenario",
            },
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        arrival = create_resp.json()
        arrival_ids.append(arrival["id"])

        status_resp = client.put(
            f"{ARRIVALS_BASE}/{arrival['id']}/status",
            json="IN_TRANSIT",
            headers=admin_auth_headers,
        )
        assert status_resp.status_code == 200
        updated = status_resp.json()
        assert updated["status"] == "DELAYED"
        assert updated["is_delayed"] is True
        assert updated["delay_days"] >= 1

        delayed_resp = client.get(
            f"{ARRIVALS_BASE}/delayed?page=1&page_size=5",
            headers=admin_auth_headers,
        )
        assert delayed_resp.status_code == 200
        delayed = delayed_resp.json()
        assert any(item["id"] == arrival["id"] for item in delayed["items"])

        follow_resp = client.post(
            f"{ARRIVALS_BASE}/{arrival['id']}/follow-up",
            json={
                "follow_up_type": "CALL",
                "follow_up_note": "供应商承诺提前发货",
                "supplier_response": "expediting",
            },
            headers=admin_auth_headers,
        )
        assert follow_resp.status_code == 201
        follow_list = client.get(
            f"{ARRIVALS_BASE}/{arrival['id']}/follow-ups?page=1&page_size=5",
            headers=admin_auth_headers,
        )
        assert follow_list.status_code == 200
        follow_payload = follow_list.json()
        assert follow_payload["total"] == 1
        assert follow_payload["items"][0]["follow_up_note"].startswith("供应商承诺")

        receive_resp = client.post(
            f"{ARRIVALS_BASE}/{arrival['id']}/receive",
            json="4",
            headers=admin_auth_headers,
        )
        assert receive_resp.status_code == 200
        received = receive_resp.json()
        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert received["status"] == "RECEIVED"
        assert Decimal(str(received["received_qty"])) == Decimal("4")
        assert received["received_by"] == admin_user.id
        assert received["is_delayed"] is True
        assert received["received_at"] is not None
    finally:
        _cleanup_arrivals(db_session, arrival_ids, material_ids)
