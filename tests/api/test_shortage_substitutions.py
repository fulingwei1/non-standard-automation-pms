# -*- coding: utf-8 -*-
"""Shortage material substitution API tests."""

from decimal import Decimal
from typing import List
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.material import Material
from app.models.project import Project
from app.models.shortage import MaterialSubstitution
from app.models.user import User
from tests.factories import ProjectFactory

SUBSTITUTIONS_BASE = f"{settings.API_V1_PREFIX}/shortage/handling/substitutions"


def _make_material(db_session: Session, name_suffix: str) -> Material:
    material = Material(
        material_code=f"SUB-{name_suffix}-{uuid4().hex[:4].upper()}",
        material_name=f"替代物料{name_suffix}",
        specification="Spec-SUB",
        unit="件",
        standard_price=Decimal("10"),
        last_price=Decimal("10"),
        current_stock=Decimal("50"),
        is_active=True,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


def _cleanup_substitutions(db_session: Session, substitution_ids: List[int], material_ids: List[int], project_ids: List[int]) -> None:
    if substitution_ids:
        db_session.query(MaterialSubstitution).filter(MaterialSubstitution.id.in_(substitution_ids)).delete(
            synchronize_session=False
        )
    if project_ids:
        db_session.query(Project).filter(Project.id.in_(project_ids)).delete(synchronize_session=False)
    if material_ids:
        db_session.query(Material).filter(Material.id.in_(material_ids)).delete(synchronize_session=False)
    db_session.commit()


@pytest.mark.api
def test_substitution_creation_and_listing_filters(
    client: TestClient,
    admin_auth_headers: dict,
    db_session: Session,
):
    substitution_ids: List[int] = []
    material_ids: List[int] = []
    project_ids: List[int] = []
    try:
        project = ProjectFactory()
        project_ids.append(project.id)
        original = _make_material(db_session, "ORIG")
        substitute = _make_material(db_session, "SUB")
        material_ids.extend([original.id, substitute.id])

        create_resp = client.post(
            SUBSTITUTIONS_BASE,
            json={
                "project_id": project.id,
                "original_material_id": original.id,
                "substitute_material_id": substitute.id,
                "original_qty": "10",
                "substitute_qty": "8",
                "substitution_reason": "库存不足",
                "technical_impact": "无需变更",
            },
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        created = create_resp.json()
        substitution_ids.append(created["id"])
        assert created["status"] == "DRAFT"
        assert created["original_material_code"] == original.material_code

        list_resp = client.get(
            f"{SUBSTITUTIONS_BASE}?status=DRAFT&keyword={original.material_code}&project_id={project.id}",
            headers=admin_auth_headers,
        )
        assert list_resp.status_code == 200
        payload = list_resp.json()
        assert payload["total"] >= 1
        assert any(item["id"] == created["id"] for item in payload["items"])
    finally:
        _cleanup_substitutions(db_session, substitution_ids, material_ids, project_ids)


@pytest.mark.api
def test_substitution_approval_and_execution_flow(
    client: TestClient,
    admin_auth_headers: dict,
    db_session: Session,
    engineer_user: User,
):
    substitution_ids: List[int] = []
    material_ids: List[int] = []
    project_ids: List[int] = []
    try:
        project = ProjectFactory()
        project_ids.append(project.id)
        original = _make_material(db_session, "ORIG2")
        substitute = _make_material(db_session, "SUB2")
        material_ids.extend([original.id, substitute.id])

        create_resp = client.post(
            SUBSTITUTIONS_BASE,
            json={
                "project_id": project.id,
                "original_material_id": original.id,
                "substitute_material_id": substitute.id,
                "original_qty": "5",
                "substitute_qty": "5",
                "substitution_reason": "处理紧急缺料",
            },
            headers=admin_auth_headers,
        )
        assert create_resp.status_code == 201
        substitution = create_resp.json()
        substitution_ids.append(substitution["id"])

        tech_resp = client.put(
            f"{SUBSTITUTIONS_BASE}/{substitution['id']}/tech-approve",
            json={"approved": True, "approval_note": "技术同意"},
            headers=admin_auth_headers,
        )
        assert tech_resp.status_code == 200
        tech_payload = tech_resp.json()
        admin_user = db_session.query(User).filter(User.username == "admin").first()
        assert tech_payload["status"] == "PROD_PENDING"
        assert tech_payload["tech_approver_id"] == admin_user.id

        prod_resp = client.put(
            f"{SUBSTITUTIONS_BASE}/{substitution['id']}/prod-approve",
            json={"approved": True, "approval_note": "生产同意"},
            headers=admin_auth_headers,
        )
        assert prod_resp.status_code == 200
        assert prod_resp.json()["status"] == "APPROVED"

        execute_resp = client.put(
            f"{SUBSTITUTIONS_BASE}/{substitution['id']}/execute",
            json="替代执行说明",
            headers=admin_auth_headers,
        )
        assert execute_resp.status_code == 200
        executed = execute_resp.json()
        assert executed["status"] == "EXECUTED"
        assert executed["executed_at"] is not None
    finally:
        _cleanup_substitutions(db_session, substitution_ids, material_ids, project_ids)
