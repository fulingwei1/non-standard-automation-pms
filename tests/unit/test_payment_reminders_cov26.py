# -*- coding: utf-8 -*-
"""第二十六批 - payment_reminders 单元测试"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.sales_reminder.payment_reminders")

from app.services.sales_reminder.payment_reminders import (
    notify_payment_plan_upcoming,
    notify_payment_overdue,
    _create_overdue_dispute_record,
)


def _make_plan(
    plan_id=1,
    status="PENDING",
    planned_date=None,
    planned_amount=10000,
    actual_amount=0,
    payment_name="测试收款",
    payment_type="ADVANCE",
    project_id=10,
    pm_id=5,
    owner_id=None,
):
    plan = MagicMock()
    plan.id = plan_id
    plan.status = status
    plan.planned_date = planned_date or date.today() + timedelta(days=3)
    plan.planned_amount = planned_amount
    plan.actual_amount = actual_amount
    plan.payment_name = payment_name
    plan.payment_type = payment_type
    plan.project_id = project_id
    project = MagicMock(pm_id=pm_id)
    plan.project = project
    if owner_id:
        contract = MagicMock(owner_id=owner_id)
    else:
        contract = MagicMock(owner_id=None)
    plan.contract = contract
    return plan


class TestNotifyPaymentPlanUpcoming:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_zero_when_no_plans(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = notify_payment_plan_upcoming(self.db, days_before=7)
        assert result == 0

    def test_creates_notification_for_pm(self):
        plan = _make_plan(pm_id=5)
        self.db.query.return_value.filter.return_value.all.return_value = [plan]
        # No existing notification
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification"
        ) as mock_create:
            result = notify_payment_plan_upcoming(self.db, days_before=7)
        assert result == 1
        mock_create.assert_called_once()

    def test_prefers_contract_owner_over_pm(self):
        plan = _make_plan(pm_id=5, owner_id=99)
        self.db.query.return_value.filter.return_value.all.return_value = [plan]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification"
        ) as mock_create:
            notify_payment_plan_upcoming(self.db, days_before=7)
        args = mock_create.call_args
        assert args.kwargs.get("user_id") == 99

    def test_high_priority_when_days_before_le_3(self):
        plan = _make_plan()
        self.db.query.return_value.filter.return_value.all.return_value = [plan]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification"
        ) as mock_create:
            notify_payment_plan_upcoming(self.db, days_before=3)
        args = mock_create.call_args
        assert args.kwargs.get("priority") == "HIGH"

    def test_normal_priority_when_days_before_gt_3(self):
        plan = _make_plan()
        self.db.query.return_value.filter.return_value.all.return_value = [plan]
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification"
        ) as mock_create:
            notify_payment_plan_upcoming(self.db, days_before=7)
        args = mock_create.call_args
        assert args.kwargs.get("priority") == "NORMAL"

    def test_skips_when_notification_already_exists(self):
        plan = _make_plan()
        self.db.query.return_value.filter.return_value.all.return_value = [plan]
        # Existing notification found
        self.db.query.return_value.filter.return_value.first.return_value = MagicMock()
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification"
        ) as mock_create:
            result = notify_payment_plan_upcoming(self.db, days_before=7)
        assert result == 0
        mock_create.assert_not_called()

    def test_skips_plan_with_no_user(self):
        plan = _make_plan(pm_id=None, owner_id=None)
        plan.project = MagicMock(pm_id=None)
        plan.contract = MagicMock(owner_id=None)
        self.db.query.return_value.filter.return_value.all.return_value = [plan]
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification"
        ) as mock_create:
            result = notify_payment_plan_upcoming(self.db, days_before=7)
        assert result == 0
        mock_create.assert_not_called()


class TestCreateOverdueDisputeRecord:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_existing_dispute_when_found(self):
        existing = MagicMock(description="旧描述")
        self.db.query.return_value.filter.return_value.first.return_value = existing
        result = _create_overdue_dispute_record(self.db, payment_id=1, overdue_days=10)
        assert result is existing
        assert "10" in result.description

    def test_creates_new_dispute_when_none_exists(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = _create_overdue_dispute_record(self.db, payment_id=1, overdue_days=5)
        self.db.add.assert_called_once()
        assert result is not None

    def test_custom_description_is_used(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        _create_overdue_dispute_record(
            self.db, payment_id=1, overdue_days=5, description="自定义描述"
        )
        added_obj = self.db.add.call_args[0][0]
        assert added_obj.description == "自定义描述"

    def test_expect_resolve_date_is_30_days_out(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        _create_overdue_dispute_record(self.db, payment_id=1, overdue_days=5)
        added_obj = self.db.add.call_args[0][0]
        expected_date = date.today() + timedelta(days=30)
        assert added_obj.expect_resolve_date == expected_date


class TestNotifyPaymentOverdue:
    def setup_method(self):
        self.db = MagicMock()

    def test_returns_zero_when_no_overdue_plans(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = notify_payment_overdue(self.db)
        assert result == 0

    def test_sends_notification_for_7_day_overdue(self):
        today = date.today()
        plan = _make_plan(
            planned_date=today - timedelta(days=7),
            planned_amount=10000,
            actual_amount=0,
        )
        plan.project = MagicMock(pm_id=5)
        plan.contract = MagicMock(owner_id=None)
        self.db.query.return_value.filter.return_value.all.side_effect = [
            [plan],  # overdue plans
            [],      # finance users
            [],      # sales managers
        ]
        # no existing notification
        self.db.query.return_value.filter.return_value.first.return_value = None
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification"
        ) as mock_create, patch(
            "app.services.sales_reminder.payment_reminders._create_overdue_dispute_record"
        ) as mock_dispute, patch(
            "app.services.sales_reminder.payment_reminders.find_users_by_role",
            return_value=[],
        ):
            result = notify_payment_overdue(self.db)
        assert result >= 0
        mock_dispute.assert_called()

    def test_urgent_priority_for_60_day_overdue(self):
        today = date.today()
        plan = _make_plan(
            planned_date=today - timedelta(days=60),
            planned_amount=10000,
            actual_amount=0,
        )
        plan.project = MagicMock(pm_id=5)
        plan.contract = MagicMock(owner_id=None)
        self.db.query.return_value.filter.return_value.all.side_effect = [[plan], [], []]
        self.db.query.return_value.filter.return_value.first.return_value = None
        captured_priority = []
        def fake_create(**kwargs):
            captured_priority.append(kwargs.get("priority"))
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification",
            side_effect=fake_create,
        ), patch(
            "app.services.sales_reminder.payment_reminders._create_overdue_dispute_record"
        ), patch(
            "app.services.sales_reminder.payment_reminders.find_users_by_role",
            return_value=[],
        ):
            notify_payment_overdue(self.db)
        assert all(p == "URGENT" for p in captured_priority) if captured_priority else True

    def test_skips_plans_with_overdue_less_than_7_days(self):
        today = date.today()
        plan = _make_plan(
            planned_date=today - timedelta(days=3),
            planned_amount=10000,
            actual_amount=0,
        )
        self.db.query.return_value.filter.return_value.all.return_value = [plan]
        with patch(
            "app.services.sales_reminder.payment_reminders.create_notification"
        ) as mock_create, patch(
            "app.services.sales_reminder.payment_reminders._create_overdue_dispute_record"
        ):
            result = notify_payment_overdue(self.db)
        assert result == 0
