# -*- coding: utf-8 -*-
"""HR-05: organization department linkage must prefer department_id over legacy names."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Department, Employee
from app.models.user import User


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_delete_department_rejects_active_employee_by_department_id(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid4().hex[:8]
    department = Department(
        dept_code=f"H5D{suffix[:7]}",
        dept_name=f"HR-05 新部门-{suffix}",
        is_active=True,
    )
    db_session.add(department)
    db_session.flush()

    employee = Employee(
        employee_code=f"H5E{suffix[:7]}",
        name="HR-05 部门 ID 员工",
        department=f"HR-05 旧部门-{suffix}",
        is_active=True,
        employment_status="active",
    )
    employee.department_id = department.id
    db_session.add(employee)
    db_session.commit()

    response = client.delete(
        f"{settings.API_V1_PREFIX}/org/departments/{department.id}",
        headers=_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 400, response.text
    assert "在职员工" in response.json()["detail"]
    db_session.expire_all()
    assert db_session.get(Department, department.id).is_active is True


def test_department_users_route_uses_user_department_id_before_legacy_name(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid4().hex[:8]
    department = Department(
        dept_code=f"H5U{suffix[:7]}",
        dept_name=f"HR-05 用户部门-{suffix}",
        is_active=True,
    )
    db_session.add(department)
    db_session.flush()

    user = User(
        username=f"hr05_user_{suffix}",
        password_hash="not-used",
        real_name="HR-05 部门 ID 用户",
        employee_no=f"H5U{suffix[:7]}",
        department_id=department.id,
        department=f"HR-05 旧用户部门-{suffix}",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()

    response = client.get(
        f"{settings.API_V1_PREFIX}/org/departments/{department.id}/users",
        headers=_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    usernames = {item["username"] for item in payload["items"]}
    assert user.username in usernames
