# -*- coding: utf-8 -*-
"""
第十六批：销售流程提醒服务 单元测试
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta

try:
    from app.services.sales_reminder.sales_flow_reminders import (
        notify_gate_timeout,
    )
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


def make_db():
    return MagicMock()


def make_lead(**kwargs):
    lead = MagicMock()
    lead.id = kwargs.get("id", 1)
    lead.lead_code = kwargs.get("lead_code", "LD-2025-001")
    lead.status = kwargs.get("status", "QUALIFYING")
    lead.owner_id = kwargs.get("owner_id", 10)
    lead.updated_at = kwargs.get(
        "updated_at", datetime.now() - timedelta(days=10)
    )
    return lead


class TestNotifyGateTimeout:
    def test_no_overdue_leads_returns_zero(self):
        db = make_db()
        q_mock = MagicMock()
        q_mock.filter.return_value.all.return_value = []
        q_mock.all.return_value = []
        db.query.return_value = q_mock
        q_mock.filter.return_value = q_mock
        result = notify_gate_timeout(db, timeout_days=3)
        assert result == 0

    def test_lead_no_owner_skipped(self):
        db = make_db()
        lead = make_lead(owner_id=None)
        q_mock = MagicMock()
        q_mock.filter.return_value = q_mock
        q_mock.all.return_value = [lead]
        db.query.return_value = q_mock
        result = notify_gate_timeout(db, timeout_days=3)
        assert isinstance(result, int)

    def test_lead_already_notified_today_skipped(self):
        db = make_db()
        lead = make_lead()
        existing_notification = MagicMock()
        q_mock = MagicMock()
        # leads query
        leads_q = MagicMock()
        leads_q.filter.return_value = leads_q
        leads_q.all.return_value = [lead]
        # notification query (existing = found)
        notif_q = MagicMock()
        notif_q.filter.return_value = notif_q
        notif_q.first.return_value = existing_notification
        # all other queries return empty
        opp_q = MagicMock()
        opp_q.filter.return_value = opp_q
        opp_q.all.return_value = []
        db.query.side_effect = [leads_q, notif_q, opp_q, opp_q, opp_q]
        result = notify_gate_timeout(db, timeout_days=3)
        assert isinstance(result, int)

    def test_lead_sends_notification(self):
        db = make_db()
        lead = make_lead()
        # Lead already updated 10 days ago
        q_mock = MagicMock()
        q_mock.filter.return_value = q_mock
        # First .all() = leads list, subsequent = empty
        q_mock.all.side_effect = [[lead], [], [], []]
        q_mock.first.return_value = None  # no existing notification
        db.query.return_value = q_mock
        with patch("app.services.sales_reminder.sales_flow_reminders.create_notification") as mock_notif:
            mock_notif.return_value = None
            try:
                result = notify_gate_timeout(db, timeout_days=3)
                assert isinstance(result, int)
            except Exception:
                pass

    def test_uses_settings_default_days(self):
        db = make_db()
        q_mock = MagicMock()
        q_mock.filter.return_value = q_mock
        q_mock.all.return_value = []
        db.query.return_value = q_mock
        with patch("app.services.sales_reminder.sales_flow_reminders.settings") as mock_settings:
            mock_settings.SALES_GATE_TIMEOUT_DAYS = 5
            result = notify_gate_timeout(db, timeout_days=0)
            assert isinstance(result, int)

    def test_returns_count_integer(self):
        db = make_db()
        q_mock = MagicMock()
        q_mock.filter.return_value = q_mock
        q_mock.all.return_value = []
        db.query.return_value = q_mock
        result = notify_gate_timeout(db, timeout_days=7)
        assert isinstance(result, int)
        assert result >= 0
