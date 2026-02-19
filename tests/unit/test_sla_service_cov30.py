# -*- coding: utf-8 -*-
"""
Unit tests for sla_service module (第三十批)
"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

import app.services.sla_service as sla_service


@pytest.fixture
def mock_db():
    return MagicMock()


# ---------------------------------------------------------------------------
# match_sla_policy
# ---------------------------------------------------------------------------

class TestMatchSlaPolicy:
    def test_returns_exact_match(self, mock_db):
        policy = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = policy

        result = sla_service.match_sla_policy(mock_db, "NETWORK", "URGENT")
        assert result is policy

    def test_returns_none_when_no_policy(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = sla_service.match_sla_policy(mock_db, "UNKNOWN", "LOW")
        assert result is None

    def test_falls_through_to_generic_policy(self, mock_db):
        """Test that the function falls through all 4 priority levels"""
        generic_policy = MagicMock()
        call_count = [0]

        def first_side_effect():
            call_count[0] += 1
            if call_count[0] < 4:
                return None
            return generic_policy

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.side_effect = first_side_effect

        result = sla_service.match_sla_policy(mock_db, "HARDWARE", "NORMAL")
        assert result is generic_policy


# ---------------------------------------------------------------------------
# create_sla_monitor
# ---------------------------------------------------------------------------

class TestCreateSlaMonitor:
    @patch("app.services.sla_service.save_obj")
    def test_creates_monitor_with_deadlines(self, mock_save, mock_db):
        ticket = MagicMock()
        ticket.id = 1
        ticket.reported_time = datetime(2024, 1, 1, 9, 0, 0)

        policy = MagicMock()
        policy.id = 10
        policy.response_time_hours = 4
        policy.resolve_time_hours = 24

        monitor = sla_service.create_sla_monitor(mock_db, ticket, policy)

        mock_save.assert_called_once()
        expected_response_deadline = ticket.reported_time + timedelta(hours=4)
        expected_resolve_deadline = ticket.reported_time + timedelta(hours=24)
        assert monitor.response_deadline == expected_response_deadline
        assert monitor.resolve_deadline == expected_resolve_deadline
        assert monitor.response_status == "ON_TIME"
        assert monitor.resolve_status == "ON_TIME"


# ---------------------------------------------------------------------------
# update_sla_monitor_status
# ---------------------------------------------------------------------------

class TestUpdateSlaMonitorStatus:
    def test_sets_response_overdue_when_actual_time_is_late(self, mock_db):
        monitor = MagicMock()
        monitor.actual_response_time = datetime(2024, 1, 1, 14, 0, 0)
        monitor.response_deadline = datetime(2024, 1, 1, 13, 0, 0)
        monitor.actual_resolve_time = datetime(2024, 1, 2, 9, 0, 0)
        monitor.resolve_deadline = datetime(2024, 1, 2, 10, 0, 0)

        sla_service.update_sla_monitor_status(mock_db, monitor)

        assert monitor.response_status == "OVERDUE"
        assert monitor.resolve_status == "ON_TIME"
        mock_db.commit.assert_called_once()

    def test_sets_response_on_time_when_actual_time_is_early(self, mock_db):
        monitor = MagicMock()
        monitor.actual_response_time = datetime(2024, 1, 1, 12, 0, 0)
        monitor.response_deadline = datetime(2024, 1, 1, 13, 0, 0)
        monitor.actual_resolve_time = None
        monitor.resolve_deadline = datetime(2024, 1, 2, 9, 0, 0)
        monitor.ticket.reported_time = datetime(2024, 1, 1, 9, 0, 0)
        monitor.policy = None

        current_time = datetime(2024, 1, 1, 11, 0, 0)
        sla_service.update_sla_monitor_status(mock_db, monitor, current_time)

        assert monitor.response_status == "ON_TIME"

    def test_sets_overdue_when_deadline_passed_and_not_resolved(self, mock_db):
        monitor = MagicMock()
        monitor.actual_response_time = datetime(2024, 1, 1, 10, 0, 0)
        monitor.response_deadline = datetime(2024, 1, 1, 11, 0, 0)
        monitor.actual_resolve_time = None
        monitor.resolve_deadline = datetime(2024, 1, 1, 12, 0, 0)
        monitor.ticket.reported_time = datetime(2024, 1, 1, 9, 0, 0)
        monitor.policy = None

        current_time = datetime(2024, 1, 1, 16, 0, 0)  # past deadline
        sla_service.update_sla_monitor_status(mock_db, monitor, current_time)

        assert monitor.resolve_status == "OVERDUE"


# ---------------------------------------------------------------------------
# sync_ticket_to_sla_monitor
# ---------------------------------------------------------------------------

class TestSyncTicketToSlaMonitor:
    def test_returns_none_when_no_monitor_and_no_policy(self, mock_db):
        ticket = MagicMock()
        ticket.id = 99
        ticket.problem_type = "HARDWARE"
        ticket.urgency = "LOW"

        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(sla_service, "match_sla_policy", return_value=None):
            result = sla_service.sync_ticket_to_sla_monitor(mock_db, ticket)
        assert result is None

    def test_updates_actual_response_time(self, mock_db):
        ticket = MagicMock()
        ticket.id = 1
        ticket.response_time = datetime(2024, 1, 1, 10, 0, 0)
        ticket.resolved_time = None

        monitor = MagicMock()
        monitor.actual_response_time = None
        monitor.actual_resolve_time = None
        mock_db.query.return_value.filter.return_value.first.return_value = monitor

        with patch.object(sla_service, "update_sla_monitor_status") as mock_update:
            result = sla_service.sync_ticket_to_sla_monitor(mock_db, ticket)

        assert monitor.actual_response_time == ticket.response_time
        mock_update.assert_called_once()


# ---------------------------------------------------------------------------
# check_sla_warnings
# ---------------------------------------------------------------------------

class TestCheckSlaWarnings:
    def test_returns_list_of_monitors(self, mock_db):
        monitor = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [monitor]

        result = sla_service.check_sla_warnings(mock_db)
        assert isinstance(result, list)
        assert monitor in result

    def test_returns_empty_when_no_warnings(self, mock_db):
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = sla_service.check_sla_warnings(mock_db)
        assert result == []


# ---------------------------------------------------------------------------
# mark_warning_sent
# ---------------------------------------------------------------------------

class TestMarkWarningSent:
    def test_marks_response_warning_sent(self, mock_db):
        monitor = MagicMock()
        sla_service.mark_warning_sent(mock_db, monitor, "response")
        assert monitor.response_warning_sent is True
        mock_db.commit.assert_called_once()

    def test_marks_resolve_warning_sent(self, mock_db):
        monitor = MagicMock()
        sla_service.mark_warning_sent(mock_db, monitor, "resolve")
        assert monitor.resolve_warning_sent is True
        mock_db.commit.assert_called_once()
