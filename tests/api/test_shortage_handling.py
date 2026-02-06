# -*- coding: utf-8 -*-
"""
Shortage handling (reports) API tests.

Exercises the `/shortage/handling/reports` endpoints to verify creation,
listing with filters, and status transitions (confirm -> handle -> resolve / reject).
"""
from decimal import Decimal
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material import Material
from app.models.project import Project
from app.models.shortage.reports import ShortageReport
from app.models.user import User
from tests.factories import ProjectFactory

HANDLING_BASE = f"{settings.API_V1_PREFIX}/shortage/handling"


def _create_material(db_session: Session) -> Material:
    material = Material(
        material_code=f"MAT-{uuid4().hex[:8].upper()}",
        material_name="测试物料",
        specification="Spec-B",
        unit="件",
        is_active=True,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def shortage_test_context(db_session: Session) -> Dict[str, Any]:
    """
    Provide a dedicated project + material for shortage report tests and clean them up afterwards.
    """
    project = ProjectFactory()
    material = _create_material(db_session)
    context = {"project": project, "material": material}
    yield context
    db_session.query(Project).filter(Project.id == project.id).delete()
    db_session.query(Material).filter(Material.id == material.id).delete()
    db_session.commit()


def _cleanup_reports(db_session: Session, report_ids: List[int]) -> None:
    if report_ids:
        db_session.query(ShortageReport).filter(ShortageReport.id.in_(report_ids)).delete(
            synchronize_session=False
        )
        db_session.commit()


def _create_report_payload(project: Project, material: Material, urgent_level: str = "NORMAL") -> Dict:
    return {
        "project_id": project.id,
        "material_id": material.id,
        "required_qty": "5",
        "shortage_qty": "3",
        "urgent_level": urgent_level,
        "report_location": "Assembly Line 1",
        "remark": f"{urgent_level} shortage auto-test",
    }


@pytest.mark.api
def test_create_and_get_shortage_report(
    client: TestClient,
    admin_auth_headers: dict,
    shortage_test_context: Dict[str, Any],
    db_session: Session,
):
    """Full create + detail retrieval flow should return consistent payload."""
    project = shortage_test_context["project"]
    material = shortage_test_context["material"]
    report_ids: List[int] = []

    try:
        create_resp = client.post(
            f"{HANDLING_BASE}/reports",
            json=_create_report_payload(project, material, urgent_level="CRITICAL"),
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        report_ids.append(created["id"])
        assert created["project_id"] == project.id
        assert created["material_code"] == material.material_code
        assert created["urgent_level"] == "CRITICAL"

        detail_resp = client.get(
            f"{HANDLING_BASE}/reports/{created['id']}",
            headers=admin_auth_headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["id"] == created["id"]
        assert detail["project_name"] == project.project_name
        assert Decimal(str(detail["required_qty"])) == Decimal("5")
    finally:
        _cleanup_reports(db_session, report_ids)


@pytest.mark.api
def test_list_shortage_reports_with_filters(
    client: TestClient,
    admin_auth_headers: dict,
    shortage_test_context: Dict[str, Any],
    db_session: Session,
):
    """List endpoint should filter by urgent_level."""
    project = shortage_test_context["project"]
    material = shortage_test_context["material"]
    report_ids: List[int] = []

    try:
        for level in ("CRITICAL", "NORMAL"):
            resp = client.post(
                f"{HANDLING_BASE}/reports",
                json=_create_report_payload(project, material, urgent_level=level),
                headers=admin_auth_headers,
            )
            assert resp.status_code == 201
            report_ids.append(resp.json()["id"])

        list_resp = client.get(
            f"{HANDLING_BASE}/reports?urgent_level=CRITICAL&page=1&page_size=10",
            headers=admin_auth_headers,
        )
        assert list_resp.status_code == 200
        payload = list_resp.json()
        assert payload["total"] >= 1
        assert all(item["urgent_level"] == "CRITICAL" for item in payload["items"])
    finally:
        _cleanup_reports(db_session, report_ids)


@pytest.mark.api
def test_report_status_flow_confirm_handle_resolve(
    client: TestClient,
    admin_auth_headers: dict,
    shortage_test_context: Dict[str, Any],
    engineer_user: User,
    db_session: Session,
):
    """Verify confirm -> handle -> resolve transitions update fields correctly."""
    project = shortage_test_context["project"]
    material = shortage_test_context["material"]
    admin_user = db_session.query(User).filter(User.username == "admin").first()

    report_ids: List[int] = []
    try:
        create_resp = client.post(
            f"{HANDLING_BASE}/reports",
            json=_create_report_payload(project, material),
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        report_id = create_resp.json()["id"]
        report_ids.append(report_id)

        confirm_resp = client.put(
            f"{HANDLING_BASE}/reports/{report_id}/confirm",
            headers=admin_auth_headers,
        )
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "CONFIRMED"
        assert confirm_resp.json()["confirmed_by"] == admin_user.id

        handle_resp = client.put(
            f"{HANDLING_BASE}/reports/{report_id}/handle",
            json={
                "solution_type": "PURCHASE",
                "solution_note": "Order expedited lot",
                "handler_id": engineer_user.id,
            },
            headers=admin_auth_headers,
        )
        assert handle_resp.status_code == 200
        handled = handle_resp.json()
        assert handled["status"] == "HANDLING"
        assert handled["handler_id"] == engineer_user.id
        assert handled["solution_type"] == "PURCHASE"

        resolve_resp = client.put(
            f"{HANDLING_BASE}/reports/{report_id}/resolve",
            headers=admin_auth_headers,
        )
        assert resolve_resp.status_code == 200
        assert resolve_resp.json()["status"] == "RESOLVED"
    finally:
        _cleanup_reports(db_session, report_ids)


@pytest.mark.api
def test_reject_shortage_report(
    client: TestClient,
    admin_auth_headers: dict,
    shortage_test_context: Dict[str, Any],
    db_session: Session,
):
    """Reject endpoint should mark the record and capture the reason."""
    project = shortage_test_context["project"]
    material = shortage_test_context["material"]
    report_ids: List[int] = []

    try:
        create_resp = client.post(
            f"{HANDLING_BASE}/reports",
            json=_create_report_payload(project, material),
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        report_id = create_resp.json()["id"]
        report_ids.append(report_id)

        reject_resp = client.put(
            f"{HANDLING_BASE}/reports/{report_id}/reject",
            json="Duplicated request",
            headers=admin_auth_headers,
        )
        assert reject_resp.status_code == 200
        body = reject_resp.json()
        assert body["status"] == "REJECTED"
        assert "Duplicated request" in (body.get("solution_note") or "")
    finally:
        _cleanup_reports(db_session, report_ids)
