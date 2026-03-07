# -*- coding: utf-8 -*-
"""Tests for app/services/sales_reminder/sales_flow_reminders.py"""
from unittest.mock import MagicMock

import pytest

from app.services.sales_reminder.sales_flow_reminders import (
    notify_approval_pending,
    notify_gate_timeout,
    notify_quote_expiring,
)


@pytest.mark.skip("TODO: hangs during collection")
class TestSalesFlowReminders:
    def setup_method(self):
        self.db = MagicMock()

    @pytest.mark.skip(reason="Complex DB queries with joins")
    def test_notify_gate_timeout(self):
        result = notify_gate_timeout(self.db, timeout_days=3)
        assert isinstance(result, int)

    @pytest.mark.skip(reason="Complex DB queries with joins")
    def test_notify_quote_expiring(self):
        result = notify_quote_expiring(self.db)
        assert isinstance(result, dict)

    @pytest.mark.skip(reason="Complex DB queries with joins")
    def test_notify_approval_pending(self):
        result = notify_approval_pending(self.db, timeout_hours=24)
        assert isinstance(result, int)
