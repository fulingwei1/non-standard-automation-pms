# -*- coding: utf-8 -*-
"""
Shortage detection (inventory alerts) API tests.

These tests cover the `/shortage/detection` endpoints, ensuring that
listing, updating, acknowledging, resolving, and follow-up flows work
with realistic data.
"""
from datetime import date
from decimal import Decimal
from typing import Callable, List, Optional, Tuple
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material import Material, MaterialShortage
from app.models.project import Project
from app.models.user import User
from tests.factories import ProjectFactory

DETECTION_BASE = f"{settings.API_V1_PREFIX}/shortage/detection"


def _create_material(db_session: Session) -> Material:
    """Create a minimal material record."""
    material = Material(
        material_code=f"MAT-{uuid4().hex[:8].upper()}",
        material_name="测试物料",
        specification="Spec-A",
        unit="件",
        is_active=True,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def shortage_alert_factory(db_session: Session) -> Callable[..., Tuple[MaterialShortage, Project, Material]]:
    """
    Factory fixture that creates `MaterialShortage` records and tracks them for cleanup.
    """
    created_alert_ids: List[int] = []
    project_ids: List[int] = []
    material_ids: List[int] = []

    def _create_alert(
        *,
        status: str = "OPEN",
        alert_level: str = "WARNING",
        handler_id: Optional[int] = None,
        remark: Optional[str] = None,
    ) -> Tuple[MaterialShortage, Project, Material]:
        project = ProjectFactory()
        material = _create_material(db_session)
        alert = MaterialShortage(
            project_id=project.id,
            bom_item_id=None,
            material_id=material.id,
            material_code=material.material_code,
            material_name=material.material_name,
            required_qty=Decimal("12"),
            available_qty=Decimal("3"),
            shortage_qty=Decimal("9"),
            required_date=date.today(),
            status=status,
            alert_level=alert_level,
            handler_id=handler_id,
            remark=remark,
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        created_alert_ids.append(alert.id)
        project_ids.append(project.id)
        material_ids.append(material.id)
        return alert, project, material

    yield _create_alert

    if created_alert_ids:
        db_session.query(MaterialShortage).filter(MaterialShortage.id.in_(created_alert_ids)).delete(
            synchronize_session=False
        )
    if project_ids:
        db_session.query(Project).filter(Project.id.in_(project_ids)).delete(synchronize_session=False)
    if material_ids:
        db_session.query(Material).filter(Material.id.in_(material_ids)).delete(synchronize_session=False)
    db_session.commit()


@pytest.mark.api
def test_list_alerts_supports_filters(
    client: TestClient,
    admin_auth_headers: dict,
    shortage_alert_factory: Callable[..., Tuple[MaterialShortage, Project, Material]],
):
    """The alerts list should honor project + alert level filters."""
    primary_alert, project, _ = shortage_alert_factory(alert_level="CRITICAL")
    shortage_alert_factory(alert_level="LOW")  # noise record

    response = client.get(
        f"{DETECTION_BASE}/alerts?project_id={project.id}&alert_level=CRITICAL&page=1&page_size=10",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert any(item["id"] == primary_alert.id for item in body["items"])
    assert all(item["alert_level"] == "CRITICAL" for item in body["items"])


@pytest.mark.api
def test_acknowledge_and_resolve_alert(
    client: TestClient,
    admin_auth_headers: dict,
    db_session: Session,
    shortage_alert_factory: Callable[..., Tuple[MaterialShortage, Project, Material]],
):
    """Acknowledge then resolve an alert and ensure status transitions are persisted."""
    alert, _, _ = shortage_alert_factory(status="OPEN")
    admin_user = db_session.query(User).filter(User.username == "admin").first()

    ack_response = client.put(
        f"{DETECTION_BASE}/alerts/{alert.id}/acknowledge",
        headers=admin_auth_headers,
    )
    assert ack_response.status_code == 200

    resolved_response = client.post(
        f"{DETECTION_BASE}/alerts/{alert.id}/resolve",
        json="Expedite supplier delivery",
        headers=admin_auth_headers,
    )
    assert resolved_response.status_code == 200

    db_session.expire_all()
    updated = db_session.query(MaterialShortage).filter(MaterialShortage.id == alert.id).first()
    assert updated.status == "RESOLVED"
    assert updated.handler_id == admin_user.id
    assert updated.solution == "Expedite supplier delivery"
    assert updated.resolved_at is not None


@pytest.mark.api
def test_follow_up_creation_and_listing(
    client: TestClient,
    admin_auth_headers: dict,
    shortage_alert_factory: Callable[..., Tuple[MaterialShortage, Project, Material]],
):
    """Adding a follow-up note should be returned by the listing endpoint."""
    alert, _, _ = shortage_alert_factory(status="OPEN")

    add_response = client.post(
        f"{DETECTION_BASE}/alerts/{alert.id}/follow-ups",
        json={
            "follow_up_note": "Called supplier, waiting for confirmation",
            "follow_up_type": "CALL",
        },
        headers=admin_auth_headers,
    )
    assert add_response.status_code == 200
    payload = add_response.json()
    assert payload["data"]["follow_up_count"] == 1

    list_response = client.get(
        f"{DETECTION_BASE}/alerts/{alert.id}/follow-ups",
        headers=admin_auth_headers,
    )
    assert list_response.status_code == 200
    follow_ups = list_response.json()["data"]["follow_ups"]
    assert len(follow_ups) == 1
    assert follow_ups[0]["type"] == "CALL"
    assert "waiting for confirmation" in follow_ups[0]["note"]


@pytest.mark.api
def test_update_alert_handler_and_level(
    client: TestClient,
    admin_auth_headers: dict,
    engineer_user: User,
    db_session: Session,
    shortage_alert_factory: Callable[..., Tuple[MaterialShortage, Project, Material]],
):
    """Updating alert metadata should change handler, solution, and level."""
    alert, _, _ = shortage_alert_factory(status="OPEN", alert_level="LOW")

    response = client.patch(
        f"{DETECTION_BASE}/alerts/{alert.id}",
        json={
            "solution": "Switch to backup inventory",
            "handler_id": engineer_user.id,
            "alert_level": "CRITICAL",
            "remark": "Needs daily tracking",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 200

    db_session.expire_all()
    updated = db_session.query(MaterialShortage).filter(MaterialShortage.id == alert.id).first()
    assert updated.solution == "Switch to backup inventory"
    assert updated.handler_id == engineer_user.id
    assert updated.alert_level == "CRITICAL"
    assert updated.remark == "Needs daily tracking"
