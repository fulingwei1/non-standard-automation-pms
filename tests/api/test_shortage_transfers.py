# -*- coding: utf-8 -*-
"""Shortage material transfer API tests."""

from decimal import Decimal
from typing import List
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material import Material
from app.models.project import Project
from app.models.shortage import MaterialTransfer
from app.models.user import User
from tests.factories import ProjectFactory

TRANSFERS_BASE = f"{settings.API_V1_PREFIX}/shortage/handling/transfers"


def _create_project(db_session: Session) -> Project:
    project = ProjectFactory()
    # Detach to reuse inside session-backed cleanup
    return project


def _create_material(db_session: Session) -> Material:
    material = Material(
        material_code=f"TRF-{uuid4().hex[:5].upper()}",
        material_name="调拨物料",
        specification="Spec-TRF",
        unit="件",
        standard_price=Decimal("15"),
        last_price=Decimal("12"),
        current_stock=Decimal("20"),
        is_active=True,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


def _cleanup_transfers(db_session: Session, transfer_ids: List[int], project_ids: List[int], material_ids: List[int]) -> None:
    if transfer_ids:
        db_session.query(MaterialTransfer).filter(MaterialTransfer.id.in_(transfer_ids)).delete(
            synchronize_session=False
        )
    if project_ids:
        db_session.query(Project).filter(Project.id.in_(project_ids)).delete(synchronize_session=False)
    if material_ids:
        db_session.query(Material).filter(Material.id.in_(material_ids)).delete(synchronize_session=False)
    db_session.commit()


@pytest.mark.api
def test_transfer_creation_and_listing_filters(
    client: TestClient,
    admin_auth_headers: dict,
    db_session: Session,
):
    transfer_ids: List[int] = []
    project_ids: List[int] = []
    material_ids: List[int] = []
    try:
        to_project = ProjectFactory()
        project_ids.append(to_project.id)
        from_project = ProjectFactory()
        project_ids.append(from_project.id)
        material = _create_material(db_session)
        material_ids.append(material.id)

        create_resp = client.post(
            TRANSFERS_BASE,
            json={
                "from_project_id": from_project.id,
                "to_project_id": to_project.id,
                "material_id": material.id,
                "transfer_qty": "5",
                "transfer_reason": "转移至关键项目",
                "urgent_level": "CRITICAL",
                "remark": "test transfer",
            },
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        transfer_ids.append(created["id"])
        assert created["status"] == "DRAFT"
        assert created["material_code"] == material.material_code

        list_resp = client.get(
            f"{TRANSFERS_BASE}?status=DRAFT&keyword={created['transfer_no']}&from_project_id={from_project.id}&to_project_id={to_project.id}",
            headers=admin_auth_headers,
        )
        assert list_resp.status_code == 200
        payload = list_resp.json()
        assert payload["total"] >= 1
        assert any(item["id"] == created["id"] for item in payload["items"])
    finally:
        _cleanup_transfers(db_session, transfer_ids, project_ids, material_ids)


@pytest.mark.api
def test_transfer_approval_and_execution_flow(
    client: TestClient,
    admin_auth_headers: dict,
    db_session: Session,
    engineer_user: User,
):
    transfer_ids: List[int] = []
    project_ids: List[int] = []
    material_ids: List[int] = []
    try:
        to_project = ProjectFactory()
        from_project = ProjectFactory()
        project_ids.extend([to_project.id, from_project.id])
        material = _create_material(db_session)
        material_ids.append(material.id)

        create_resp = client.post(
            TRANSFERS_BASE,
            json={
                "from_project_id": from_project.id,
                "to_project_id": to_project.id,
                "material_id": material.id,
                "transfer_qty": "6",
                "transfer_reason": "紧急支援",
            },
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        transfer = create_resp.json()
        transfer_ids.append(transfer["id"])

        approve_resp = client.put(
            f"{TRANSFERS_BASE}/{transfer['id']}/approve",
            json={"approved": True, "approval_note": "允许调拨"},
            headers=admin_auth_headers,
        )
        assert approve_resp.status_code == 200
        approved = approve_resp.json()
        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert approved["status"] == "APPROVED"
        assert approved["approver_id"] == admin_user.id

        execute_resp = client.put(
            f"{TRANSFERS_BASE}/{transfer['id']}/execute",
            json={"actual_qty": "6", "execution_note": "完成调拨"},
            headers=admin_auth_headers,
        )
        assert execute_resp.status_code == 200
        executed = execute_resp.json()
        assert executed["status"] == "EXECUTED"
        assert Decimal(str(executed["actual_qty"])) == Decimal("6")
        assert executed["executed_at"] is not None
        assert executed["approver_id"] == admin_user.id
    finally:
        _cleanup_transfers(db_session, transfer_ids, project_ids, material_ids)
