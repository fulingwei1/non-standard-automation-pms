# -*- coding: utf-8 -*-
"""
PERM-17 工时域数据权限过滤测试

覆盖新挂载的 DataScopeService.filter_by_scope：
- app.api.v1.endpoints.timesheet.reports.get_timesheet_report_detail
- app.api.v1.endpoints.timesheet.reports_unified.get_unified_timesheet_report
- app.api.v1.endpoints.timesheet.statistics.get_department_timesheet_summary

对每个改动端点验证：
(a) ALL 范围 / 超级管理员可看到全部记录
(b) OWN 范围仅能看到自己的记录
"""

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.organization import Department
from app.models.timesheet import Timesheet
from app.models.user import User

SCOPE_PATCH_TARGET = "app.services.data_scope.generic_filter.UserScopeService.get_user_data_scope"


def _make_user(db: Session, *, is_superuser: bool = False, department_id=None) -> User:
    unique = uuid.uuid4().hex[:10]
    user = User(
        username=f"perm17_{unique}",
        password_hash=get_password_hash("Test1234!"),
        real_name=f"用户{unique}",
        is_active=True,
        is_superuser=is_superuser,
        department_id=department_id,
    )
    db.add(user)
    db.flush()
    return user


def _make_timesheet(db: Session, *, user: User, department_id=None, hours="8.0") -> Timesheet:
    ts = Timesheet(
        user_id=user.id,
        user_name=user.real_name,
        department_id=department_id,
        work_date=date.today(),
        hours=Decimal(hours),
        status="APPROVED",
        created_by=user.id,
    )
    db.add(ts)
    db.flush()
    return ts


class TestTimesheetReportDetailDataScope:
    """app/api/v1/endpoints/timesheet/reports.py::get_timesheet_report_detail"""

    def test_all_scope_sees_every_users_records(self, db_session: Session):
        from app.api.v1.endpoints.timesheet.reports import get_timesheet_report_detail

        user_a = _make_user(db_session, is_superuser=True)
        user_b = _make_user(db_session)
        _make_timesheet(db_session, user=user_a)
        _make_timesheet(db_session, user=user_b)
        db_session.commit()

        today = date.today()
        result = get_timesheet_report_detail(
            year=today.year,
            month=today.month,
            user_id=None,
            project_id=None,
            db=db_session,
            current_user=user_a,
        )

        seen_user_ids = {row["user_id"] for row in result.data["records"]}
        assert user_a.id in seen_user_ids
        assert user_b.id in seen_user_ids

    def test_own_scope_sees_only_self(self, db_session: Session):
        from app.api.v1.endpoints.timesheet.reports import get_timesheet_report_detail

        user_a = _make_user(db_session)
        user_b = _make_user(db_session)
        _make_timesheet(db_session, user=user_a)
        _make_timesheet(db_session, user=user_b)
        db_session.commit()

        today = date.today()
        with patch(SCOPE_PATCH_TARGET, return_value="OWN"):
            result = get_timesheet_report_detail(
                year=today.year,
                month=today.month,
                user_id=None,
                project_id=None,
                db=db_session,
                current_user=user_a,
            )

        seen_user_ids = {row["user_id"] for row in result.data["records"]}
        assert seen_user_ids == {user_a.id}


class TestUnifiedTimesheetReportDataScope:
    """app/api/v1/endpoints/timesheet/reports_unified.py::get_unified_timesheet_report"""

    def test_all_scope_sees_every_users_records(self, db_session: Session):
        from app.api.v1.endpoints.timesheet.reports_unified import get_unified_timesheet_report

        user_a = _make_user(db_session, is_superuser=True)
        user_b = _make_user(db_session)
        _make_timesheet(db_session, user=user_a)
        _make_timesheet(db_session, user=user_b)
        db_session.commit()

        today = date.today()
        result = get_unified_timesheet_report(
            start_date=today,
            end_date=today,
            report_type="detail",
            department_id=None,
            project_id=None,
            user_id=None,
            db=db_session,
            current_user=user_a,
        )

        seen_user_ids = {row["user_id"] for row in result.data["data"]}
        assert user_a.id in seen_user_ids
        assert user_b.id in seen_user_ids

    def test_own_scope_sees_only_self(self, db_session: Session):
        from app.api.v1.endpoints.timesheet.reports_unified import get_unified_timesheet_report

        user_a = _make_user(db_session)
        user_b = _make_user(db_session)
        _make_timesheet(db_session, user=user_a)
        _make_timesheet(db_session, user=user_b)
        db_session.commit()

        today = date.today()
        with patch(SCOPE_PATCH_TARGET, return_value="OWN"):
            result = get_unified_timesheet_report(
                start_date=today,
                end_date=today,
                report_type="detail",
                department_id=None,
                project_id=None,
                user_id=None,
                db=db_session,
                current_user=user_a,
            )

        seen_user_ids = {row["user_id"] for row in result.data["data"]}
        assert seen_user_ids == {user_a.id}


class TestDepartmentTimesheetSummaryDataScope:
    """app/api/v1/endpoints/timesheet/statistics.py::get_department_timesheet_summary"""

    def _make_department(self, db: Session) -> Department:
        unique = uuid.uuid4().hex[:10]
        dept = Department(dept_code=f"D{unique}", dept_name=f"部门{unique}")
        db.add(dept)
        db.flush()
        return dept

    def test_all_scope_sees_every_users_records(self, db_session: Session):
        from app.api.v1.endpoints.timesheet.statistics import get_department_timesheet_summary

        dept = self._make_department(db_session)
        user_a = _make_user(db_session, is_superuser=True, department_id=dept.id)
        user_b = _make_user(db_session, department_id=dept.id)
        _make_timesheet(db_session, user=user_a, department_id=dept.id)
        _make_timesheet(db_session, user=user_b, department_id=dept.id)
        db_session.commit()

        result = get_department_timesheet_summary(
            db=db_session,
            dept_id=dept.id,
            start_date=None,
            end_date=None,
            current_user=user_a,
        )

        assert result.data["total_participants"] == 2

    def test_own_scope_sees_only_self(self, db_session: Session):
        from app.api.v1.endpoints.timesheet.statistics import get_department_timesheet_summary

        dept = self._make_department(db_session)
        user_a = _make_user(db_session, department_id=dept.id)
        user_b = _make_user(db_session, department_id=dept.id)
        _make_timesheet(db_session, user=user_a, department_id=dept.id)
        _make_timesheet(db_session, user=user_b, department_id=dept.id)
        db_session.commit()

        with patch(SCOPE_PATCH_TARGET, return_value="OWN"):
            result = get_department_timesheet_summary(
                db=db_session,
                dept_id=dept.id,
                start_date=None,
                end_date=None,
                current_user=user_a,
            )

        assert result.data["total_participants"] == 1
        seen_user_ids = {row["user_id"] for row in result.data["by_user"]}
        assert seen_user_ids == {user_a.id}
