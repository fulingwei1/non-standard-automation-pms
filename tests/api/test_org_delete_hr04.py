# -*- coding: utf-8 -*-
"""HR-04: frontend delete calls for org employees/departments must resolve."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.organization import Department, Employee


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_delete_employee_soft_deactivates_employee(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid4().hex[:8]
    employee = Employee(
        employee_code=f"E{suffix[:9]}",
        name="HR-04 删除员工",
        department="HR-04",
        is_active=True,
        employment_status="active",
    )
    db_session.add(employee)
    db_session.commit()

    response = client.delete(
        f"{settings.API_V1_PREFIX}/org/employees/{employee.id}",
        headers=_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    db_session.expire_all()
    deleted = db_session.get(Employee, employee.id)
    assert deleted.is_active is False
    assert deleted.employment_status == "resigned"


def test_delete_department_soft_deactivates_empty_department(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid4().hex[:8]
    department = Department(
        dept_code=f"D{suffix[:8]}",
        dept_name=f"HR-04 空部门-{suffix}",
        is_active=True,
    )
    db_session.add(department)
    db_session.commit()

    response = client.delete(
        f"{settings.API_V1_PREFIX}/org/departments/{department.id}",
        headers=_headers(admin_token),
        follow_redirects=False,
    )

    assert response.status_code == 200, response.text
    db_session.expire_all()
    deleted = db_session.get(Department, department.id)
    assert deleted.is_active is False


def test_delete_department_rejects_department_with_active_employee(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid4().hex[:8]
    department = Department(
        dept_code=f"D{suffix[:8]}",
        dept_name=f"HR-04 有人部门-{suffix}",
        is_active=True,
    )
    db_session.add(department)
    db_session.flush()
    employee = Employee(
        employee_code=f"E{suffix[:9]}",
        name="HR-04 部门员工",
        department=department.dept_name,
        is_active=True,
        employment_status="active",
    )
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
