# -*- coding: utf-8 -*-
"""第二十六批 - milestone_reminders 单元测试"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.sales_reminder.milestone_reminders")

from app.services.sales_reminder.milestone_reminders import (
    notify_milestone_upcoming,
    notify_milestone_overdue,
)


def _make_milestone(
    ms_id=1,
    status="PENDING",
    planned_date=None,
    owner_id=10,
    milestone_name="M1",
    milestone_code="MS-001",
    project_id=5,
    days_ahead=3,
):
    ms = MagicMock()
    ms.id = ms_id
    ms.status = status
    ms.planned_date = planned_date or (date.today() + timedelta(days=days_ahead))
    ms.owner_id = owner_id
    ms.milestone_name = milestone_name
    ms.milestone_code = milestone_code
    ms.project_id = project_id
    return ms


class TestNotifyMilestoneUpcoming:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_zero_when_no_milestones(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = notify_milestone_upcoming(self.db, days_before=7)
        assert result == 0

    def test_creates_notification_for_owner(self):
        ms = _make_milestone(owner_id=10)
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            result = notify_milestone_upcoming(self.db, days_before=7)
        assert result == 1
        mock_create.assert_called_once()

    def test_skips_milestone_without_owner(self):
        ms = _make_milestone(owner_id=None)
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            result = notify_milestone_upcoming(self.db, days_before=7)
        assert result == 0
        mock_create.assert_not_called()

    def test_skips_when_notification_already_exists(self):
        ms = _make_milestone()
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            result = notify_milestone_upcoming(self.db, days_before=7)
        assert result == 0
        mock_create.assert_not_called()

    def test_high_priority_for_days_le_3(self):
        ms = _make_milestone(days_ahead=2)
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            notify_milestone_upcoming(self.db, days_before=3)
        args = mock_create.call_args
        assert args.kwargs.get("priority") == "HIGH"

    def test_normal_priority_for_days_gt_3(self):
        ms = _make_milestone(days_ahead=5)
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            notify_milestone_upcoming(self.db, days_before=7)
        args = mock_create.call_args
        assert args.kwargs.get("priority") == "NORMAL"

    def test_notification_type_is_correct(self):
        ms = _make_milestone()
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            notify_milestone_upcoming(self.db, days_before=7)
        args = mock_create.call_args
        assert args.kwargs.get("notification_type") == "MILESTONE_UPCOMING"

    def test_notification_source_type_is_milestone(self):
        ms = _make_milestone()
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            notify_milestone_upcoming(self.db, days_before=7)
        args = mock_create.call_args
        assert args.kwargs.get("source_type") == "milestone"

    def test_extra_data_contains_days_left(self):
        ms = _make_milestone(days_ahead=5)
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            notify_milestone_upcoming(self.db, days_before=7)
        extra = mock_create.call_args.kwargs.get("extra_data", {})
        assert "days_left" in extra
        assert extra["days_left"] == 5

    def test_counts_multiple_milestones(self):
        milestones = [_make_milestone(ms_id=i, owner_id=i) for i in range(1, 4)]
        self.db.query.return_value.filter.return_value.all.return_value = milestones
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ):
            result = notify_milestone_upcoming(self.db, days_before=7)
        assert result == 3


class TestNotifyMilestoneOverdue:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_zero_when_no_milestones(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = notify_milestone_overdue(self.db)
        assert result == 0

    def test_creates_overdue_notification(self):
        today = date.today()
        ms = _make_milestone(planned_date=today - timedelta(days=5))
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            result = notify_milestone_overdue(self.db)
        assert result == 1
        mock_create.assert_called_once()

    def test_skips_milestone_without_owner(self):
        today = date.today()
        ms = _make_milestone(planned_date=today - timedelta(days=5), owner_id=None)
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            result = notify_milestone_overdue(self.db)
        assert result == 0

    def test_skips_when_today_already_notified(self):
        today = date.today()
        ms = _make_milestone(planned_date=today - timedelta(days=3))
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            result = notify_milestone_overdue(self.db)
        assert result == 0
        mock_create.assert_not_called()

    def test_overdue_notification_priority_is_urgent(self):
        today = date.today()
        ms = _make_milestone(planned_date=today - timedelta(days=10))
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            notify_milestone_overdue(self.db)
        args = mock_create.call_args
        assert args.kwargs.get("priority") == "URGENT"

    def test_overdue_days_in_extra_data(self):
        today = date.today()
        ms = _make_milestone(planned_date=today - timedelta(days=8))
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            notify_milestone_overdue(self.db)
        extra = mock_create.call_args.kwargs.get("extra_data", {})
        assert "overdue_days" in extra
        assert extra["overdue_days"] == 8

    def test_notification_type_is_milestone_overdue(self):
        today = date.today()
        ms = _make_milestone(planned_date=today - timedelta(days=4))
        self.db.query.return_value.filter.return_value.all.return_value = [ms]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.milestone_reminders.create_notification"
        ) as mock_create:
            notify_milestone_overdue(self.db)
        args = mock_create.call_args
        assert args.kwargs.get("notification_type") == "MILESTONE_OVERDUE"
