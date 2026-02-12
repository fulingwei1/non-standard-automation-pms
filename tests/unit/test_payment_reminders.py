# -*- coding: utf-8 -*-
"""Tests for sales_reminder/payment_reminders.py"""

from unittest.mock import MagicMock, patch

import pytest


class TestPaymentReminders:
    def setup_method(self):
        self.db = MagicMock()

    def test_notify_payment_plan_upcoming_no_plans(self):
        from app.services.sales_reminder.payment_reminders import notify_payment_plan_upcoming
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = notify_payment_plan_upcoming(self.db)
        assert result == 0

    def test_notify_payment_overdue_no_plans(self):
        from app.services.sales_reminder.payment_reminders import notify_payment_overdue
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = notify_payment_overdue(self.db)
        assert result == 0
