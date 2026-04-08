# -*- coding: utf-8 -*-
"""SLA服务单元测试 - 覆盖所有函数分支"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.sla_service import (
    match_sla_policy,
    create_sla_monitor,
    update_sla_monitor_status,
    sync_ticket_to_sla_monitor,
    check_sla_warnings,
    mark_warning_sent,
)


def _make_policy(**kwargs):
    p = MagicMock()
    p.id = kwargs.get("id", 1)
    p.problem_type = kwargs.get("problem_type", "BUG")
    p.urgency = kwargs.get("urgency", "HIGH")
    p.is_active = kwargs.get("is_active", True)
    p.priority = kwargs.get("priority", 1)
    p.response_time_hours = kwargs.get("response_time_hours", 4)
    p.resolve_time_hours = kwargs.get("resolve_time_hours", 24)
    p.warning_threshold_percent = kwargs.get("warning_threshold_percent", Decimal("80"))
    return p


def _make_ticket(**kwargs):
    t = MagicMock()
    t.id = kwargs.get("id", 100)
    t.problem_type = kwargs.get("problem_type", "BUG")
    t.urgency = kwargs.get("urgency", "HIGH")
    t.reported_time = kwargs.get("reported_time", datetime(2026, 1, 1, 10, 0))
    t.response_time = kwargs.get("response_time", None)
    t.resolved_time = kwargs.get("resolved_time", None)
    return t


def _make_monitor(**kwargs):
    m = MagicMock()
    m.id = kwargs.get("id", 10)
    m.ticket_id = kwargs.get("ticket_id", 100)
    m.policy_id = kwargs.get("policy_id", 1)
    m.response_deadline = kwargs.get("response_deadline", datetime(2026, 1, 1, 14, 0))
    m.resolve_deadline = kwargs.get("resolve_deadline", datetime(2026, 1, 2, 10, 0))
    m.actual_response_time = kwargs.get("actual_response_time", None)
    m.actual_resolve_time = kwargs.get("actual_resolve_time", None)
    m.response_status = kwargs.get("response_status", "ON_TIME")
    m.resolve_status = kwargs.get("resolve_status", "ON_TIME")
    m.response_time_diff_hours = kwargs.get("response_time_diff_hours", None)
    m.resolve_time_diff_hours = kwargs.get("resolve_time_diff_hours", None)
    m.response_warning_sent = kwargs.get("response_warning_sent", False)
    m.resolve_warning_sent = kwargs.get("resolve_warning_sent", False)
    m.response_warning_sent_at = None
    m.resolve_warning_sent_at = None
    m.ticket = kwargs.get("ticket", _make_ticket())
    m.policy = kwargs.get("policy", _make_policy())
    return m


class TestMatchSlaPolicy:
    def test_exact_match(self):
        policy = _make_policy()
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = policy
        assert match_sla_policy(db, "BUG", "HIGH") == policy

    def test_fallback_problem_type(self):
        db = MagicMock()
        policy = _make_policy(urgency=None)
        db.query.return_value.filter.return_value.order_by.return_value.first.side_effect = [
            None, policy
        ]
        assert match_sla_policy(db, "BUG", "HIGH") == policy

    def test_fallback_urgency(self):
        db = MagicMock()
        policy = _make_policy(problem_type=None)
        db.query.return_value.filter.return_value.order_by.return_value.first.side_effect = [
            None, None, policy
        ]
        assert match_sla_policy(db, "BUG", "HIGH") == policy

    def test_fallback_generic(self):
        db = MagicMock()
        policy = _make_policy(problem_type=None, urgency=None)
        db.query.return_value.filter.return_value.order_by.return_value.first.side_effect = [
            None, None, None, policy
        ]
        assert match_sla_policy(db, "BUG", "HIGH") == policy

    def test_no_match(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        assert match_sla_policy(db, "X", "X") is None


class TestCreateSlaMonitor:
    @patch("app.services.sla_service.save_obj")
    def test_deadlines_and_initial_status(self, mock_save):
        db = MagicMock()
        ticket = _make_ticket(reported_time=datetime(2026, 1, 1, 10, 0))
        policy = _make_policy(response_time_hours=4, resolve_time_hours=24)

        monitor = create_sla_monitor(db, ticket, policy)

        assert monitor.response_deadline == datetime(2026, 1, 1, 14, 0)
        assert monitor.resolve_deadline == datetime(2026, 1, 2, 10, 0)
        assert monitor.response_status == "ON_TIME"
        assert monitor.resolve_status == "ON_TIME"
        mock_save.assert_called_once()


class TestUpdateSlaMonitorStatus:
    def test_response_on_time(self):
        db = MagicMock()
        m = _make_monitor(
            response_deadline=datetime(2026, 1, 1, 14, 0),
            actual_response_time=datetime(2026, 1, 1, 13, 0),
            actual_resolve_time=None,
        )
        update_sla_monitor_status(db, m, datetime(2026, 1, 1, 13, 0))
        assert m.response_status == "ON_TIME"

    def test_response_overdue_with_actual(self):
        db = MagicMock()
        m = _make_monitor(
            response_deadline=datetime(2026, 1, 1, 14, 0),
            actual_response_time=datetime(2026, 1, 1, 16, 0),
            actual_resolve_time=None,
        )
        update_sla_monitor_status(db, m, datetime(2026, 1, 1, 16, 0))
        assert m.response_status == "OVERDUE"

    def test_not_responded_overdue(self):
        db = MagicMock()
        m = _make_monitor(
            response_deadline=datetime(2026, 1, 1, 14, 0),
            actual_response_time=None,
        )
        update_sla_monitor_status(db, m, datetime(2026, 1, 1, 15, 0))
        assert m.response_status == "OVERDUE"

    def test_not_responded_warning_threshold(self):
        db = MagicMock()
        ticket = _make_ticket(reported_time=datetime(2026, 1, 1, 10, 0))
        policy = _make_policy(warning_threshold_percent=Decimal("80"))
        m = _make_monitor(
            response_deadline=datetime(2026, 1, 1, 14, 0),
            actual_response_time=None,
            ticket=ticket,
            policy=policy,
        )
        # 83% elapsed > 80% threshold
        update_sla_monitor_status(db, m, datetime(2026, 1, 1, 13, 20))
        assert m.response_status == "WARNING"

    def test_not_responded_still_on_time(self):
        db = MagicMock()
        ticket = _make_ticket(reported_time=datetime(2026, 1, 1, 10, 0))
        policy = _make_policy(warning_threshold_percent=Decimal("80"))
        m = _make_monitor(
            response_deadline=datetime(2026, 1, 1, 14, 0),
            actual_response_time=None,
            ticket=ticket,
            policy=policy,
        )
        # 50% elapsed < 80% threshold
        update_sla_monitor_status(db, m, datetime(2026, 1, 1, 12, 0))
        assert m.response_status == "ON_TIME"

    def test_no_policy_stays_on_time(self):
        db = MagicMock()
        m = _make_monitor(
            response_deadline=datetime(2026, 1, 1, 14, 0),
            actual_response_time=None,
            policy=None,
        )
        update_sla_monitor_status(db, m, datetime(2026, 1, 1, 13, 50))
        assert m.response_status == "ON_TIME"

    def test_resolve_on_time(self):
        db = MagicMock()
        m = _make_monitor(
            actual_response_time=datetime(2026, 1, 1, 13, 0),
            actual_resolve_time=datetime(2026, 1, 2, 8, 0),
            resolve_deadline=datetime(2026, 1, 2, 10, 0),
        )
        update_sla_monitor_status(db, m, datetime(2026, 1, 2, 8, 0))
        assert m.resolve_status == "ON_TIME"

    def test_resolve_overdue(self):
        db = MagicMock()
        m = _make_monitor(
            actual_response_time=datetime(2026, 1, 1, 13, 0),
            actual_resolve_time=datetime(2026, 1, 2, 14, 0),
            resolve_deadline=datetime(2026, 1, 2, 10, 0),
        )
        update_sla_monitor_status(db, m, datetime(2026, 1, 2, 14, 0))
        assert m.resolve_status == "OVERDUE"

    def test_not_resolved_overdue(self):
        db = MagicMock()
        m = _make_monitor(
            actual_response_time=datetime(2026, 1, 1, 13, 0),
            actual_resolve_time=None,
            resolve_deadline=datetime(2026, 1, 2, 10, 0),
        )
        update_sla_monitor_status(db, m, datetime(2026, 1, 2, 12, 0))
        assert m.resolve_status == "OVERDUE"

    def test_default_current_time(self):
        db = MagicMock()
        m = _make_monitor(
            response_deadline=datetime(2099, 1, 1),
            resolve_deadline=datetime(2099, 1, 2),
            actual_response_time=datetime(2026, 1, 1, 13, 0),
            actual_resolve_time=datetime(2026, 1, 2, 8, 0),
        )
        update_sla_monitor_status(db, m)
        db.commit.assert_called_once()


class TestSyncTicketToSlaMonitor:
    @patch("app.services.sla_service.update_sla_monitor_status")
    def test_updates_existing(self, mock_update):
        db = MagicMock()
        ticket = _make_ticket(
            response_time=datetime(2026, 1, 1, 13, 0),
            resolved_time=datetime(2026, 1, 2, 8, 0),
        )
        monitor = _make_monitor(actual_response_time=None, actual_resolve_time=None)
        db.query.return_value.filter.return_value.first.return_value = monitor

        result = sync_ticket_to_sla_monitor(db, ticket)
        assert result.actual_response_time == ticket.response_time
        assert result.actual_resolve_time == ticket.resolved_time

    @patch("app.services.sla_service.update_sla_monitor_status")
    @patch("app.services.sla_service.create_sla_monitor")
    @patch("app.services.sla_service.match_sla_policy")
    def test_creates_new_if_no_monitor(self, mock_match, mock_create, mock_update):
        db = MagicMock()
        ticket = _make_ticket()
        db.query.return_value.filter.return_value.first.return_value = None
        mock_match.return_value = _make_policy()
        mock_create.return_value = _make_monitor()

        result = sync_ticket_to_sla_monitor(db, ticket)
        assert result is not None

    def test_returns_none_no_policy(self):
        db = MagicMock()
        ticket = _make_ticket()
        db.query.return_value.filter.return_value.first.return_value = None
        with patch("app.services.sla_service.match_sla_policy", return_value=None):
            assert sync_ticket_to_sla_monitor(db, ticket) is None

    @patch("app.services.sla_service.update_sla_monitor_status")
    def test_preserves_existing_times(self, mock_update):
        db = MagicMock()
        ticket = _make_ticket(response_time=datetime(2026, 1, 1, 15, 0))
        existing_time = datetime(2026, 1, 1, 13, 0)
        monitor = _make_monitor(actual_response_time=existing_time)
        db.query.return_value.filter.return_value.first.return_value = monitor

        result = sync_ticket_to_sla_monitor(db, ticket)
        assert result.actual_response_time == existing_time


class TestCheckSlaWarnings:
    def test_returns_monitors(self):
        db = MagicMock()
        monitors = [_make_monitor(), _make_monitor()]
        db.query.return_value.join.return_value.filter.return_value.all.return_value = monitors
        assert len(check_sla_warnings(db, datetime(2026, 1, 1))) == 2

    def test_empty(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        assert check_sla_warnings(db) == []


class TestMarkWarningSent:
    def test_response(self):
        db = MagicMock()
        m = _make_monitor()
        mark_warning_sent(db, m, "response")
        assert m.response_warning_sent is True
        assert m.response_warning_sent_at is not None
        db.commit.assert_called_once()

    def test_resolve(self):
        db = MagicMock()
        m = _make_monitor()
        mark_warning_sent(db, m, "resolve")
        assert m.resolve_warning_sent is True
        assert m.resolve_warning_sent_at is not None
        db.commit.assert_called_once()

    def test_unknown_type(self):
        db = MagicMock()
        m = _make_monitor()
        mark_warning_sent(db, m, "unknown")
        assert m.response_warning_sent is False
        assert m.resolve_warning_sent is False
