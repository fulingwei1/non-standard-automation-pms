# -*- coding: utf-8 -*-
"""HR-02: resignation approval must deactivate the bound login account."""

from datetime import date
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.v1.endpoints.hr_management.transactions import approve_hr_transaction
from app.models.organization import Employee, EmployeeHrProfile, HrTransaction
from app.models.user import User


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def test_resignation_approval_deactivates_bound_user_account(db_session: Session):
    employee = Employee(
        employee_code=_unique("E")[:10],
        name="离职员工",
        department="研发部",
        is_active=True,
        employment_status="active",
    )
    approver = User(username=_unique("hr02_approver"), password_hash="x", is_active=True)
    db_session.add_all([employee, approver])
    db_session.flush()

    employee_user = User(
        username=_unique("hr02_employee"),
        password_hash="x",
        employee_id=employee.id,
        is_active=True,
    )
    profile = EmployeeHrProfile(employee_id=employee.id)
    transaction = HrTransaction(
        employee_id=employee.id,
        transaction_type="resignation",
        transaction_date=date(2026, 7, 4),
        resignation_date=date(2026, 7, 4),
        status="pending",
    )
    db_session.add_all([employee_user, profile, transaction])
    db_session.commit()

    response = approve_hr_transaction(
        transaction.id,
        db=db_session,
        current_user=approver,
    )

    db_session.refresh(employee)
    db_session.refresh(employee_user)
    db_session.refresh(transaction)

    assert employee.is_active is False
    assert employee.employment_status == "resigned"
    assert transaction.status == "completed"
    assert employee_user.is_active is False
    assert response["deactivated_user_count"] == 1
