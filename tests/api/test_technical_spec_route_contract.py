# -*- coding: utf-8 -*-
"""Technical specification route compatibility tests."""

import uuid

from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.security import create_access_token, get_password_hash
from app.models.project import Customer, Project, ProjectMember
from app.models.technical_spec import SpecMatchRecord, TechnicalSpecRequirement
from app.models.user import User


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_technical_spec_routes_expose_frontend_compatible_prefixes():
    """The main API router must serve the prefixes used by current frontend pages."""
    paths = {route.path for route in api_router.routes}

    for prefix in ("/technical-spec", "/technical-specs"):
        assert f"{prefix}/requirements" in paths
        assert f"{prefix}/match/records" in paths
        assert f"{prefix}/match/check" in paths


def test_technical_spec_requirements_tolerate_legacy_null_requirement_level(
    client,
    admin_token,
    db_session,
    mock_project,
):
    """Legacy rows with NULL requirement_level should not break the list page."""
    db_session.execute(
        text(
            """
            INSERT INTO technical_spec_requirements (
                project_id,
                material_code,
                material_name,
                specification,
                requirement_level,
                created_at,
                updated_at
            ) VALUES (
                :project_id,
                :material_code,
                :material_name,
                :specification,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "project_id": mock_project.id,
            "material_code": "MAT-LEGACY",
            "material_name": "历史规格物料",
            "specification": "24V DC",
        },
    )
    db_session.commit()

    response = client.get(
        "/api/v1/technical-spec/requirements",
        params={"project_id": mock_project.id, "page": 1, "page_size": 100},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    item = next(
        item for item in response.json()["items"] if item["material_code"] == "MAT-LEGACY"
    )
    assert item["requirement_level"] == "REQUIRED"


def test_technical_spec_match_records_tolerate_legacy_null_requirement_level(
    client,
    admin_token,
    db_session,
    mock_project,
):
    """Nested requirement data in match records must use the same legacy default."""
    material_code = "MAT-MATCH-LEGACY"
    db_session.execute(
        text(
            """
            INSERT INTO technical_spec_requirements (
                project_id,
                material_code,
                material_name,
                specification,
                requirement_level,
                created_at,
                updated_at
            ) VALUES (
                :project_id,
                :material_code,
                :material_name,
                :specification,
                NULL,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {
            "project_id": mock_project.id,
            "material_code": material_code,
            "material_name": "匹配记录历史规格物料",
            "specification": "220V AC",
        },
    )
    requirement_id = db_session.execute(
        text(
            """
            SELECT id FROM technical_spec_requirements
            WHERE project_id = :project_id AND material_code = :material_code
            """
        ),
        {"project_id": mock_project.id, "material_code": material_code},
    ).scalar_one()
    db_session.execute(
        text(
            """
            INSERT INTO spec_match_records (
                project_id,
                spec_requirement_id,
                match_type,
                match_target_id,
                match_status,
                created_at,
                updated_at
            ) VALUES (
                :project_id,
                :spec_requirement_id,
                'BOM',
                999999,
                'UNKNOWN',
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """
        ),
        {"project_id": mock_project.id, "spec_requirement_id": requirement_id},
    )
    db_session.commit()

    response = client.get(
        "/api/v1/technical-spec/match/records",
        params={"project_id": mock_project.id, "page": 1, "page_size": 100},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    item = next(
        item for item in response.json()["items"] if item["spec_requirement_id"] == requirement_id
    )
    assert item["spec_requirement"]["requirement_level"] == "REQUIRED"


def test_regular_member_can_read_project_technical_spec_without_module_permission(
    client,
    db_session,
):
    """Project members can read their own technical spec rows without module-wide read."""
    marker = f"TECH-SPEC-SELF-{uuid.uuid4().hex}"
    actor = User(
        username=f"{marker.lower()}-actor",
        password_hash=get_password_hash("password123"),
        real_name="技术规格自服务用户",
        department="项目部",
        is_active=True,
        is_superuser=False,
    )
    other_user = User(
        username=f"{marker.lower()}-other",
        password_hash=get_password_hash("password123"),
        real_name="其他项目用户",
        department="项目部",
        is_active=True,
        is_superuser=False,
    )
    db_session.add_all([actor, other_user])
    db_session.flush()

    customer = Customer(
        customer_code=f"CUST-{uuid.uuid4().hex[:8].upper()}",
        customer_name=f"{marker}-客户",
        contact_person="QA",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    member_project = Project(
        project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
        project_name=f"{marker}-member",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        is_active=True,
        created_by=other_user.id,
        pm_id=other_user.id,
    )
    unrelated_project = Project(
        project_code=f"PJ-{uuid.uuid4().hex[:8].upper()}",
        project_name=f"{marker}-unrelated",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        is_active=True,
        created_by=other_user.id,
        pm_id=other_user.id,
    )
    db_session.add_all([member_project, unrelated_project])
    db_session.flush()

    db_session.add(
        ProjectMember(
            project_id=member_project.id,
            user_id=actor.id,
            role_code="MEMBER",
            is_active=True,
            created_by=other_user.id,
        )
    )
    own_requirement = TechnicalSpecRequirement(
        project_id=member_project.id,
        material_code=f"OWN-{uuid.uuid4().hex[:6].upper()}",
        material_name=f"{marker}-own-material",
        specification="24V DC",
        requirement_level="REQUIRED",
        extracted_by=other_user.id,
    )
    unrelated_requirement = TechnicalSpecRequirement(
        project_id=unrelated_project.id,
        material_code=f"OTHER-{uuid.uuid4().hex[:6].upper()}",
        material_name=f"{marker}-other-material",
        specification="220V AC",
        requirement_level="STRICT",
        extracted_by=other_user.id,
    )
    db_session.add_all([own_requirement, unrelated_requirement])
    db_session.flush()
    own_match = SpecMatchRecord(
        project_id=member_project.id,
        spec_requirement_id=own_requirement.id,
        match_type="BOM",
        match_target_id=999001,
        match_status="UNKNOWN",
    )
    unrelated_match = SpecMatchRecord(
        project_id=unrelated_project.id,
        spec_requirement_id=unrelated_requirement.id,
        match_type="BOM",
        match_target_id=999002,
        match_status="UNKNOWN",
    )
    db_session.add_all([own_match, unrelated_match])
    db_session.commit()

    headers = _auth_headers_for_user(actor)
    list_response = client.get(
        "/api/v1/technical-spec/requirements",
        params={"page": 1, "page_size": 100},
        headers=headers,
    )
    assert list_response.status_code == 200, list_response.text
    requirement_ids = {item["id"] for item in list_response.json()["items"]}
    assert own_requirement.id in requirement_ids
    assert unrelated_requirement.id not in requirement_ids

    own_project_response = client.get(
        "/api/v1/technical-spec/requirements",
        params={"project_id": member_project.id, "page": 1, "page_size": 100},
        headers=headers,
    )
    assert own_project_response.status_code == 200, own_project_response.text
    assert {item["id"] for item in own_project_response.json()["items"]} == {
        own_requirement.id
    }

    unrelated_project_response = client.get(
        "/api/v1/technical-spec/requirements",
        params={"project_id": unrelated_project.id, "page": 1, "page_size": 100},
        headers=headers,
    )
    assert unrelated_project_response.status_code == 403

    detail_response = client.get(
        f"/api/v1/technical-spec/requirements/{own_requirement.id}",
        headers=headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["id"] == own_requirement.id

    unrelated_detail_response = client.get(
        f"/api/v1/technical-spec/requirements/{unrelated_requirement.id}",
        headers=headers,
    )
    assert unrelated_detail_response.status_code == 403

    match_response = client.get(
        "/api/v1/technical-spec/match/records",
        params={"page": 1, "page_size": 100},
        headers=headers,
    )
    assert match_response.status_code == 200, match_response.text
    match_ids = {item["id"] for item in match_response.json()["items"]}
    assert own_match.id in match_ids
    assert unrelated_match.id not in match_ids

    unrelated_match_response = client.get(
        "/api/v1/technical-spec/match/records",
        params={"project_id": unrelated_project.id, "page": 1, "page_size": 100},
        headers=headers,
    )
    assert unrelated_match_response.status_code == 403

    create_response = client.post(
        "/api/v1/technical-spec/requirements",
        json={
            "project_id": member_project.id,
            "material_name": "new material",
            "specification": "48V DC",
        },
        headers=headers,
    )
    assert create_response.status_code == 403

    check_response = client.post(
        "/api/v1/technical-spec/match/check",
        json={"project_id": member_project.id, "match_type": "BOM"},
        headers=headers,
    )
    assert check_response.status_code == 403
