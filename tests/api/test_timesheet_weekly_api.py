# -*- coding: utf-8 -*-
"""周工时 API 自服务权限边界测试"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models.timesheet import Timesheet
from app.models.user import User


def _auth_headers_for_user(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _create_timesheet_user(db_session: Session, suffix: str, real_name: str) -> User:
    user = User(
        username=f"weekly_self_{suffix}",
        password_hash=get_password_hash("weekly123"),
        email=f"weekly_self_{suffix}@example.com",
        real_name=real_name,
        department="交付部",
        position="项目成员",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_timesheet(
    db_session: Session,
    user: User,
    suffix: str,
    work_date: date,
    hours: Decimal,
    status: str = "DRAFT",
) -> Timesheet:
    timesheet = Timesheet(
        timesheet_no=f"TS-WEEK-{suffix}",
        user_id=user.id,
        user_name=user.real_name,
        department_name=user.department,
        work_date=work_date,
        hours=hours,
        overtime_type="NORMAL",
        work_content=f"周工时自服务测试-{suffix}",
        status=status,
        created_by=user.id,
    )
    db_session.add(timesheet)
    db_session.flush()
    return timesheet


def test_regular_user_can_read_own_week_timesheet_without_timesheet_read(
    client: TestClient,
    db_session: Session,
):
    """周工时默认读取本人数据，显式查询他人仍拒绝"""
    suffix = uuid4().hex[:8].upper()
    week_start = date(2026, 6, 22)
    owner = _create_timesheet_user(db_session, f"OWNER-{suffix}", "周工时本人")
    other = _create_timesheet_user(db_session, f"OTHER-{suffix}", "周工时他人")
    own_ts = _create_timesheet(db_session, owner, f"OWN-{suffix}", week_start, Decimal("7.50"))
    other_ts = _create_timesheet(
        db_session, other, f"OTHER-{suffix}", week_start, Decimal("8.00")
    )
    db_session.commit()

    headers = _auth_headers_for_user(owner)

    other_response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/weekly/week",
        params={"week_start": week_start.isoformat(), "user_id": other.id},
        headers=headers,
    )
    assert other_response.status_code == 403

    response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/weekly/week",
        params={"week_start": week_start.isoformat()},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()

    timesheet_ids = {item["id"] for item in data["timesheets"]}
    assert own_ts.id in timesheet_ids
    assert other_ts.id not in timesheet_ids
    assert data["total_hours"] == "7.50"


def test_regular_user_can_read_own_month_summary_without_timesheet_read(
    client: TestClient,
    db_session: Session,
):
    """月度汇总默认读取本人数据，显式查询他人仍拒绝"""
    suffix = uuid4().hex[:8].upper()
    work_date = date(2026, 6, 15)
    owner = _create_timesheet_user(db_session, f"MOWNER-{suffix}", "月汇总本人")
    other = _create_timesheet_user(db_session, f"MOTHER-{suffix}", "月汇总他人")
    _create_timesheet(db_session, owner, f"MOWN-{suffix}", work_date, Decimal("9.25"))
    _create_timesheet(db_session, other, f"MOTHER-{suffix}", work_date, Decimal("8.00"))
    db_session.commit()

    headers = _auth_headers_for_user(owner)

    other_response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/monthly/month-summary",
        params={"year": 2026, "month": 6, "user_id": other.id},
        headers=headers,
    )
    assert other_response.status_code == 403

    response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/monthly/month-summary",
        params={"year": 2026, "month": 6},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["total_hours"] == "9.25"
    assert data["billable_hours"] == "9.25"
    assert data["by_date"] == {work_date.isoformat(): "9.25"}


def test_regular_user_can_read_scoped_statistics_without_timesheet_read(
    client: TestClient,
    db_session: Session,
):
    """工时统计使用统一范围过滤，不泄漏他人数据"""
    suffix = uuid4().hex[:8].upper()
    work_date = date(2026, 6, 16)
    owner = _create_timesheet_user(db_session, f"SOWNER-{suffix}", "统计本人")
    other = _create_timesheet_user(db_session, f"SOTHER-{suffix}", "统计他人")
    _create_timesheet(
        db_session, owner, f"SOWN-{suffix}", work_date, Decimal("6.25"), status="APPROVED"
    )
    _create_timesheet(
        db_session, other, f"SOTHER-{suffix}", work_date, Decimal("8.00"), status="APPROVED"
    )
    db_session.commit()

    headers = _auth_headers_for_user(owner)

    response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/statistics",
        params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["total_hours"] == "6.25"
    assert data["billable_hours"] == "6.25"
    assert data["by_user"] == {owner.real_name: "6.25"}
    assert other.real_name not in data["by_user"]

    other_response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/statistics",
        params={
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
            "user_id": other.id,
        },
        headers=headers,
    )
    assert other_response.status_code == 200, other_response.text
    other_data = other_response.json()
    assert other_data["total_hours"] == "0"
    assert other_data["by_user"] == {}


def test_regular_user_can_read_scoped_anomalies_without_timesheet_read(
    client: TestClient,
    db_session: Session,
):
    """异常检测使用统一范围过滤，不泄漏他人异常"""
    suffix = uuid4().hex[:8].upper()
    work_date = date(2026, 6, 18)
    owner = _create_timesheet_user(db_session, f"AOWNER-{suffix}", "异常本人")
    other = _create_timesheet_user(db_session, f"AOTHER-{suffix}", "异常他人")
    _create_timesheet(
        db_session, owner, f"AOWN-{suffix}", work_date, Decimal("17.25"), status="APPROVED"
    )
    _create_timesheet(
        db_session, other, f"AOTHER-{suffix}", work_date, Decimal("18.00"), status="APPROVED"
    )
    db_session.commit()

    headers = _auth_headers_for_user(owner)

    response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/anomalies",
        params={"start_date": "2026-06-01", "end_date": "2026-06-30"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]

    assert len(data) == 1
    assert data[0]["user_id"] == owner.id
    assert data[0]["type"] == "EXCESSIVE_DAILY_HOURS"
    assert data[0]["hours"] == 17.25

    other_response = client.get(
        f"{settings.API_V1_PREFIX}/timesheet/anomalies",
        params={
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
            "user_id": other.id,
        },
        headers=headers,
    )
    assert other_response.status_code == 200, other_response.text
    assert other_response.json()["data"] == []
