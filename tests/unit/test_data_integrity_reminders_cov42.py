# -*- coding: utf-8 -*-
"""第四十二批：data_integrity/reminders.py 单元测试"""
import pytest

pytest.importorskip("app.services.data_integrity.reminders")

from unittest.mock import MagicMock, patch
from app.services.data_integrity.reminders import RemindersMixin


class ConcreteReminders(RemindersMixin):
    def __init__(self, db):
        self.db = db


def make_service():
    db = MagicMock()
    return ConcreteReminders(db), db


# ------------------------------------------------------------------ tests ---

def test_get_reminders_returns_empty_when_no_period():
    svc, db = make_service()
    db.query.return_value.filter.return_value.first.return_value = None
    result = svc.get_missing_data_reminders(999)
    assert result == []


def test_get_reminders_contains_project_eval_type():
    svc, db = make_service()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"

    from app.models.performance import PerformancePeriod
    from app.models.project import Project
    from app.models.engineer_performance import EngineerProfile

    period_q = MagicMock()
    period_q.filter.return_value.first.return_value = period

    proj = MagicMock()
    proj.id = 1
    proj.project_code = "P001"
    proj.project_name = "测试项目"

    project_q = MagicMock()
    project_q.outerjoin.return_value.filter.return_value.all.return_value = [proj]

    engineer_q = MagicMock()
    engineer_q.outerjoin.return_value.filter.return_value.all.return_value = []

    call_count = [0]

    def q_router(*args):
        call_count[0] += 1
        if call_count[0] == 1:
            return period_q
        elif call_count[0] == 2:
            return project_q
        else:
            return engineer_q

    db.query.side_effect = q_router
    reminders = svc.get_missing_data_reminders(1)
    types = {r["type"] for r in reminders}
    assert "project_evaluation_missing" in types


def test_send_reminders_skips_when_no_period():
    svc, db = make_service()
    db.query.return_value.filter.return_value.first.return_value = None
    with patch.object(svc, "get_missing_data_reminders", return_value=[]):
        result = svc.send_data_missing_reminders(999)
    assert result["total_reminders"] == 0


def test_send_reminders_filters_by_type():
    svc, db = make_service()
    two_reminders = [
        {"type": "project_evaluation_missing", "priority": "high", "message": "test", "engineer_id": 1},
        {"type": "work_log_missing", "priority": "low", "message": "test2", "engineer_id": 2},
    ]
    with patch.object(svc, "get_missing_data_reminders", return_value=two_reminders):
        with patch("app.services.notification_dispatcher.NotificationDispatcher") as MockDisp:
            mock_dispatcher = MagicMock()
            mock_dispatcher.send_notification_request.return_value = {"success": True}
            MockDisp.return_value = mock_dispatcher
            result = svc.send_data_missing_reminders(1, reminder_types=["work_log_missing"])
    assert result["total_reminders"] == 1


def test_send_reminders_counts_sent():
    svc, db = make_service()
    reminders = [{"type": "x", "priority": "high", "message": "m", "engineer_id": 1}]
    with patch.object(svc, "get_missing_data_reminders", return_value=reminders):
        with patch("app.services.notification_dispatcher.NotificationDispatcher") as MockDisp:
            mock_dispatcher = MagicMock()
            mock_dispatcher.send_notification_request.return_value = {"success": True}
            MockDisp.return_value = mock_dispatcher
            result = svc.send_data_missing_reminders(1)
    assert result["sent_count"] == 1
    assert result["failed_count"] == 0


def test_send_reminders_handles_failed_send():
    svc, db = make_service()
    reminders = [{"type": "x", "priority": "high", "message": "m", "engineer_id": 1}]
    with patch.object(svc, "get_missing_data_reminders", return_value=reminders):
        with patch("app.services.notification_dispatcher.NotificationDispatcher") as MockDisp:
            mock_dispatcher = MagicMock()
            mock_dispatcher.send_notification_request.return_value = {"success": False}
            MockDisp.return_value = mock_dispatcher
            result = svc.send_data_missing_reminders(1)
    assert result["failed_count"] == 1
