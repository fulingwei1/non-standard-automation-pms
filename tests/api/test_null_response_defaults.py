# -*- coding: utf-8 -*-
"""历史演示数据 NULL 值响应兜底回归。"""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Employee
from app.models.outsourcing import OutsourcingOrder
from app.models.qualification import (
    EmployeeQualification,
    PositionCompetencyModel,
    QualificationLevel,
)
from app.models.staff_matching import HrTagDict
from app.models.technical_review import TechnicalReview
from app.models.user import Role, User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_list_endpoints_coerce_legacy_null_response_fields(
    client: TestClient, db_session: Session, admin_token: str
):
    if not admin_token:
        pytest.skip("Admin token not available")

    headers = _auth_headers(admin_token)
    unique = uuid4().hex[:8].upper()
    admin_user = db_session.query(User).filter(User.username == "admin").first()
    assert admin_user is not None

    review = TechnicalReview(
        review_no=f"RV-NULL-{unique}",
        review_type="PDR",
        review_name=f"空计数评审-{unique}",
        project_id=999001,
        project_no=f"PRJ-NULL-{unique}",
        status="DRAFT",
        scheduled_date=datetime(2026, 6, 20, 9, 0, 0),
        meeting_type="ONSITE",
        host_id=admin_user.id,
        presenter_id=admin_user.id,
        recorder_id=admin_user.id,
        created_by=admin_user.id,
    )
    order = OutsourcingOrder(
        order_no=f"OS-NULL-{unique}",
        vendor_id=999002,
        project_id=999003,
        order_type="PROCESS",
        order_title=f"空状态外协-{unique}",
    )
    tag = HrTagDict(
        tag_code=f"TAG-NULL-{unique}",
        tag_name=f"空启用标签-{unique}",
        tag_type="SKILL",
    )
    level = QualificationLevel(
        level_code=f"QL{unique[:6]}",
        level_name=f"空启用等级-{unique}",
        level_order=99,
    )
    employee = Employee(
        employee_code=f"N{unique[:6]}",
        name=f"空状态员工-{unique}",
        department="测试部",
        role="测试工程师",
        is_active=True,
    )
    qualification = EmployeeQualification(
        employee=employee,
        position_type="ENGINEER",
        level=level,
    )
    competency_model = PositionCompetencyModel(
        position_type=f"NULL_TYPE_{unique}",
        position_subtype="SMOKE",
        level=level,
        competency_dimensions={},
    )
    role = Role(
        role_code=f"ROLE_NULL_{unique}",
        role_name=f"空排序角色-{unique}",
    )
    db_session.add_all([review, order, tag, level, employee, qualification, competency_model, role])
    db_session.commit()

    db_session.execute(
        text(
            """
            UPDATE technical_reviews
            SET issue_count_a = NULL, issue_count_b = NULL,
                issue_count_c = NULL, issue_count_d = NULL
            WHERE id = :id
            """
        ),
        {"id": review.id},
    )
    db_session.execute(
        text(
            """
            UPDATE outsourcing_orders
            SET status = NULL, payment_status = NULL
            WHERE id = :id
            """
        ),
        {"id": order.id},
    )
    db_session.execute(
        text("UPDATE hr_tag_dict SET is_active = NULL WHERE id = :id"),
        {"id": tag.id},
    )
    db_session.execute(
        text("UPDATE qualification_level SET is_active = NULL WHERE id = :id"),
        {"id": level.id},
    )
    db_session.execute(
        text("UPDATE employee_qualification SET status = NULL WHERE id = :id"),
        {"id": qualification.id},
    )
    db_session.execute(
        text("UPDATE position_competency_model SET is_active = NULL WHERE id = :id"),
        {"id": competency_model.id},
    )
    db_session.execute(
        text("UPDATE roles SET sort_order = NULL WHERE id = :id"),
        {"id": role.id},
    )
    db_session.commit()

    roles_response = client.get(
        f"{settings.API_V1_PREFIX}/roles/",
        params={"keyword": role.role_code},
        headers=headers,
    )
    assert roles_response.status_code == 200, roles_response.text
    role_item = roles_response.json()["data"]["items"][0]
    assert role_item["sort_order"] == 0

    technical_response = client.get(
        f"{settings.API_V1_PREFIX}/technical-reviews",
        params={"keyword": review.review_no},
        headers=headers,
    )
    assert technical_response.status_code == 200, technical_response.text
    technical_item = technical_response.json()["items"][0]
    assert technical_item["issue_count_a"] == 0
    assert technical_item["issue_count_d"] == 0

    outsourcing_response = client.get(
        f"{settings.API_V1_PREFIX}/outsourcing-orders",
        params={"keyword": order.order_no},
        headers=headers,
    )
    assert outsourcing_response.status_code == 200, outsourcing_response.text
    outsourcing_item = outsourcing_response.json()["items"][0]
    assert outsourcing_item["vendor_name"] == "未指定"
    assert outsourcing_item["status"] == "DRAFT"
    assert outsourcing_item["payment_status"] == "UNPAID"

    tag_response = client.get(
        f"{settings.API_V1_PREFIX}/staff-matching/tags/",
        params={"keyword": tag.tag_code, "page_size": 500},
        headers=headers,
    )
    assert tag_response.status_code == 200, tag_response.text
    tag_item = tag_response.json()[0]
    assert tag_item["is_active"] is True

    level_response = client.get(
        f"{settings.API_V1_PREFIX}/qualifications/levels",
        params={"page_size": 50},
        headers=headers,
    )
    assert level_response.status_code == 200, level_response.text
    level_item = next(
        item for item in level_response.json()["items"] if item["level_code"] == level.level_code
    )
    assert level_item["is_active"] is True

    model_response = client.get(
        f"{settings.API_V1_PREFIX}/qualifications/models",
        params={"position_type": competency_model.position_type, "page_size": 1},
        headers=headers,
    )
    assert model_response.status_code == 200, model_response.text
    model_item = model_response.json()["items"][0]
    assert model_item["is_active"] is True
    assert model_item["level"]["is_active"] is True

    qualification_response = client.get(
        f"{settings.API_V1_PREFIX}/qualifications/employees",
        params={"employee_id": employee.id, "page_size": 1},
        headers=headers,
    )
    assert qualification_response.status_code == 200, qualification_response.text
    qualification_item = qualification_response.json()["items"][0]
    assert qualification_item["status"] == "PENDING"
    assert qualification_item["level"]["is_active"] is True
