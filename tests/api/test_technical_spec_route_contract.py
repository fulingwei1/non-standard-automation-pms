# -*- coding: utf-8 -*-
"""Technical specification route compatibility tests."""

from sqlalchemy import text

from app.api.v1.api import api_router


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
