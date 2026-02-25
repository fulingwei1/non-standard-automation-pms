# -*- coding: utf-8 -*-
"""SLA Service 测试 - Batch 2"""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest

from app.services.sla_service import (
    match_sla_policy, create_sla_monitor, update_sla_monitor_status,
    sync_ticket_to_sla_monitor, check_sla_warnings, mark_warning_sent
)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = MagicMock()
    return db


@pytest.fixture
def mock_policy():
    p = MagicMock()
    p.id = 1
    p.response_time_hours = 4
    p.resolve_time_hours = 24
    p.warning_threshold_percent = Decimal("80")
    return p


@pytest.fixture
def mock_ticket():
    t = MagicMock()
    t.id = 1
    t.reported_time = datetime(2024, 1, 1, 10, 0, 0)
    t.problem_type = "HW"
    t.urgency = "HIGH"
    t.response_time = None
    t.resolved_time = None
    return t


@pytest.fixture
def mock_monitor(mock_ticket, mock_policy):
    m = MagicMock()
    m.response_deadline = datetime(2024, 1, 1, 14, 0, 0)
    m.resolve_deadline = datetime(2024, 1, 2, 10, 0, 0)
    m.actual_response_time = None
    m.actual_resolve_time = None
    m.ticket = mock_ticket
    m.policy = mock_policy
    m.response_warning_sent = False
    m.resolve_warning_sent = False
    return m


class TestMatchSlaPolicy:
    def test_exact(self, mock_db, mock_policy):
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_policy
        assert match_sla_policy(mock_db, "HW", "HIGH") == mock_policy

    def test_fallback_chain(self, mock_db, mock_policy):
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.side_effect = [None, None, None, mock_policy]
        assert match_sla_policy(mock_db, "HW", "HIGH") == mock_policy

    def test_none(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        assert match_sla_policy(mock_db, "X", "X") is None


class TestCreateSlaMonitor:
    @patch('app.services.sla_service.save_obj')
    def test_create(self, mock_save, mock_db, mock_ticket, mock_policy):
        r = create_sla_monitor(mock_db, mock_ticket, mock_policy)
        assert r.response_deadline == mock_ticket.reported_time + timedelta(hours=4)
        mock_save.assert_called_once()


class TestUpdateStatus:
    def test_response_on_time(self, mock_db, mock_monitor):
        mock_monitor.actual_response_time = datetime(2024, 1, 1, 13, 0, 0)
        update_sla_monitor_status(mock_db, mock_monitor)
        assert mock_monitor.response_status == 'ON_TIME'

    def test_response_overdue(self, mock_db, mock_monitor):
        mock_monitor.actual_response_time = datetime(2024, 1, 1, 15, 0, 0)
        update_sla_monitor_status(mock_db, mock_monitor)
        assert mock_monitor.response_status == 'OVERDUE'

    def test_no_response_overdue(self, mock_db, mock_monitor):
        update_sla_monitor_status(mock_db, mock_monitor, datetime(2024, 1, 1, 15, 0, 0))
        assert mock_monitor.response_status == 'OVERDUE'

    def test_no_response_warning(self, mock_db, mock_monitor):
        update_sla_monitor_status(mock_db, mock_monitor, datetime(2024, 1, 1, 13, 30, 0))
        assert mock_monitor.response_status == 'WARNING'

    def test_no_response_on_time(self, mock_db, mock_monitor):
        update_sla_monitor_status(mock_db, mock_monitor, datetime(2024, 1, 1, 11, 0, 0))
        assert mock_monitor.response_status == 'ON_TIME'

    def test_resolve_on_time(self, mock_db, mock_monitor):
        mock_monitor.actual_response_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_monitor.actual_resolve_time = datetime(2024, 1, 2, 8, 0, 0)
        update_sla_monitor_status(mock_db, mock_monitor)
        assert mock_monitor.resolve_status == 'ON_TIME'

    def test_resolve_overdue(self, mock_db, mock_monitor):
        mock_monitor.actual_response_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_monitor.actual_resolve_time = datetime(2024, 1, 2, 12, 0, 0)
        update_sla_monitor_status(mock_db, mock_monitor)
        assert mock_monitor.resolve_status == 'OVERDUE'

    def test_no_warning_threshold(self, mock_db, mock_monitor):
        mock_monitor.policy.warning_threshold_percent = None
        update_sla_monitor_status(mock_db, mock_monitor, datetime(2024, 1, 1, 13, 30, 0))
        assert mock_monitor.response_status == 'ON_TIME'


class TestSyncTicket:
    def test_existing_monitor(self, mock_db, mock_monitor, mock_ticket):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_monitor
        mock_ticket.response_time = datetime(2024, 1, 1, 12, 0, 0)
        r = sync_ticket_to_sla_monitor(mock_db, mock_ticket)
        assert r.actual_response_time == mock_ticket.response_time

    @patch('app.services.sla_service.match_sla_policy', return_value=None)
    def test_no_policy(self, m, mock_db, mock_ticket):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        assert sync_ticket_to_sla_monitor(mock_db, mock_ticket) is None

    def test_dont_overwrite(self, mock_db, mock_monitor, mock_ticket):
        existing = datetime(2024, 1, 1, 11, 0, 0)
        mock_monitor.actual_response_time = existing
        mock_db.query.return_value.filter.return_value.first.return_value = mock_monitor
        mock_ticket.response_time = datetime(2024, 1, 1, 13, 0, 0)
        sync_ticket_to_sla_monitor(mock_db, mock_ticket)
        assert mock_monitor.actual_response_time == existing


class TestWarnings:
    def test_check_warnings(self, mock_db, mock_monitor):
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_monitor]
        assert len(check_sla_warnings(mock_db)) == 1

    def test_mark_response(self, mock_db, mock_monitor):
        mark_warning_sent(mock_db, mock_monitor, 'response')
        assert mock_monitor.response_warning_sent is True

    def test_mark_resolve(self, mock_db, mock_monitor):
        mark_warning_sent(mock_db, mock_monitor, 'resolve')
        assert mock_monitor.resolve_warning_sent is True
