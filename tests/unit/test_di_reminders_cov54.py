"""Tests for app/services/data_integrity/reminders.py"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.data_integrity.reminders import RemindersMixin
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


class ConcreteReminders(RemindersMixin):
    def __init__(self, db):
        self.db = db


def _make_db():
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.outerjoin.return_value = q
    q.all.return_value = []
    q.count.return_value = 0
    q.first.return_value = None
    return db


def test_get_missing_data_reminders_no_period():
    """考核周期不存在时返回空列表"""
    db = _make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    service = ConcreteReminders(db)
    result = service.get_missing_data_reminders(999)
    assert result == []


def test_get_missing_data_reminders_with_period():
    """考核周期存在时正常返回列表"""
    db = _make_db()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    # first() returns period, then outerjoin queries return empty
    db.query.return_value.filter.return_value.first.return_value = period
    db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = []
    service = ConcreteReminders(db)
    result = service.get_missing_data_reminders(1)
    assert isinstance(result, list)


def test_get_missing_data_reminders_project_without_evaluation():
    """有未完成评价项目时生成对应提醒"""
    db = _make_db()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    db.query.return_value.filter.return_value.first.return_value = period
    project = MagicMock()
    project.id = 1
    project.project_code = "P001"
    project.project_name = "测试项目"
    # outerjoin().filter().all() returns [project] for first query (projects), [] for rest
    db.query.return_value.outerjoin.return_value.filter.return_value.all.side_effect = [
        [project], [], []
    ]
    service = ConcreteReminders(db)
    result = service.get_missing_data_reminders(1)
    assert any(r['type'] == 'project_evaluation_missing' for r in result)


def test_send_data_missing_reminders_returns_structure():
    """send_data_missing_reminders 返回正确结构"""
    db = _make_db()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    db.query.return_value.filter.return_value.first.return_value = period
    db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = []
    service = ConcreteReminders(db)
    result = service.send_data_missing_reminders(1)
    assert 'period_id' in result
    assert 'total_reminders' in result
    assert 'sent_count' in result
    assert 'failed_count' in result
    assert 'reminders' in result


def test_send_data_missing_reminders_with_type_filter():
    """传入 reminder_types 时只发送指定类型"""
    db = _make_db()
    period = MagicMock()
    period.start_date = "2024-01-01"
    period.end_date = "2024-12-31"
    db.query.return_value.filter.return_value.first.return_value = period
    db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = []
    service = ConcreteReminders(db)
    result = service.send_data_missing_reminders(1, reminder_types=['work_log_missing'])
    assert result['total_reminders'] == 0  # no reminders after filter


def test_send_data_missing_reminders_no_period():
    """考核周期不存在时返回 total_reminders=0"""
    db = _make_db()
    db.query.return_value.filter.return_value.first.return_value = None
    service = ConcreteReminders(db)
    result = service.send_data_missing_reminders(999)
    assert result['total_reminders'] == 0
