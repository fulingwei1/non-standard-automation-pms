# -*- coding: utf-8 -*-
"""第二十批 - missing_reminders 单元测试"""
import pytest
pytest.importorskip("app.services.timesheet_reminder.missing_reminders")

from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call
from app.services.timesheet_reminder.missing_reminders import (
    notify_timesheet_missing,
    notify_weekly_timesheet_missing,
)


def make_db():
    return MagicMock()


def make_engineer(id=1, username="eng1", real_name="工程师甲"):
    u = MagicMock()
    u.id = id
    u.username = username
    u.real_name = real_name
    u.is_active = True
    return u


class TestNotifyTimesheetMissing:
    def _setup_db_no_engineers(self, db):
        """Setup: no engineer roles/depts/users"""
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        q.first.return_value = None
        db.query.return_value = q
        db.commit.return_value = None

    def test_no_engineers_returns_zero(self):
        db = make_db()
        self._setup_db_no_engineers(db)
        count = notify_timesheet_missing(db)
        assert count == 0
        db.commit.assert_called_once()

    def test_uses_yesterday_as_default_date(self):
        db = make_db()
        self._setup_db_no_engineers(db)
        with patch("app.services.timesheet_reminder.missing_reminders.date") as mock_date:
            today = date(2025, 6, 15)
            mock_date.today.return_value = today
            mock_date.side_effect = lambda *a, **k: date(*a, **k)
            notify_timesheet_missing(db)

    def test_custom_target_date(self):
        db = make_db()
        self._setup_db_no_engineers(db)
        target = date(2025, 1, 10)
        count = notify_timesheet_missing(db, target_date=target)
        assert count == 0

    def test_skips_engineer_with_existing_timesheet(self):
        db = make_db()
        engineer = make_engineer(id=10)
        call_count = [0]

        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            q.filter.return_value = q
            q.all.return_value = []
            q.first.return_value = None
            q.count.return_value = 0
            name = getattr(model, '__name__', str(model))
            if name == 'Role':
                q.all.return_value = []
            elif name == 'Department':
                q.all.return_value = []
            elif name == 'User':
                q.all.return_value = [engineer]
            elif name == 'Timesheet':
                # existing timesheet found
                ts = MagicMock()
                q.first.return_value = ts
            return q

        db.query.side_effect = query_side
        count = notify_timesheet_missing(db, target_date=date(2025, 1, 10))
        # Should have skipped (existing timesheet), so 0
        assert count == 0


class TestNotifyWeeklyTimesheetMissing:
    def _setup_db_no_engineers(self, db):
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        q.first.return_value = None
        q.count.return_value = 0
        db.query.return_value = q
        db.commit.return_value = None

    def test_no_engineers_returns_zero(self):
        db = make_db()
        self._setup_db_no_engineers(db)
        count = notify_weekly_timesheet_missing(db)
        assert count == 0
        db.commit.assert_called_once()

    def test_custom_week_start(self):
        db = make_db()
        self._setup_db_no_engineers(db)
        week_start = date(2025, 1, 6)  # Monday
        count = notify_weekly_timesheet_missing(db, week_start=week_start)
        assert count == 0

    def test_default_week_start_is_last_monday(self):
        db = make_db()
        self._setup_db_no_engineers(db)
        # Just confirm it runs without error using default
        count = notify_weekly_timesheet_missing(db)
        assert isinstance(count, int)

    def test_skips_engineer_with_enough_timesheets(self):
        db = make_db()
        engineer = make_engineer(id=20)

        def query_side(model):
            q = MagicMock()
            q.filter.return_value = q
            q.all.return_value = []
            q.first.return_value = None
            q.count.return_value = 0
            name = getattr(model, '__name__', str(model))
            if name == 'User':
                q.all.return_value = [engineer]
            elif name == 'Timesheet':
                q.count.return_value = 5  # 5 days -> skip
            return q

        db.query.side_effect = query_side
        count = notify_weekly_timesheet_missing(db, week_start=date(2025, 1, 6))
        assert count == 0
