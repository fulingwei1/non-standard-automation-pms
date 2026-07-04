# -*- coding: utf-8 -*-
"""HR-06/07: admin attendance must not synthesize fake attendance data."""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints import admin_attendance
from app.models.organization import Employee
from app.models.user import User


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


def _make_user(db: Session) -> User:
    user = User(username=_unique("attn_user"), password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return user


def test_attendance_list_returns_empty_state_instead_of_synthesized_stats(
    db_session: Session,
):
    user = _make_user(db_session)
    db_session.add_all(
        [
            Employee(
                employee_code=_unique("A")[:10],
                name="考勤员工A",
                department="研发部",
                is_active=True,
            ),
            Employee(
                employee_code=_unique("B")[:10],
                name="考勤员工B",
                department="质量部",
                is_active=True,
            ),
        ]
    )
    db_session.commit()

    response = admin_attendance.list_attendance(
        date_filter="2026-07-04",
        db=db_session,
        _current_user=user,
    )

    assert response["items"] == []
    assert response["total"] == 0
    assert response["employee_total"] >= 2
    assert response["attendance_data_available"] is False
    assert response["source"] == "attendance-not-configured"


def test_my_records_and_clock_in_do_not_return_fake_success(db_session: Session):
    user = _make_user(db_session)

    records = admin_attendance.get_my_attendance_records(_current_user=user)
    assert records["items"] == []
    assert records["total"] == 0
    assert records["attendance_data_available"] is False

    with pytest.raises(HTTPException) as exc_info:
        admin_attendance.clock_in(_current_user=user)

    assert exc_info.value.status_code == 501
