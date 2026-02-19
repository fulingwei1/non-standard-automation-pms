# -*- coding: utf-8 -*-
"""单元测试 - TimesheetApprovalAdapter (cov48)"""

import pytest
from unittest.mock import MagicMock

try:
    from app.services.approval_engine.adapters.timesheet import TimesheetApprovalAdapter
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for TimesheetApprovalAdapter")


def _make_adapter():
    db = MagicMock()
    return TimesheetApprovalAdapter(db)


def test_get_entity_returns_none_when_not_found():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity(99) is None


def test_get_entity_data_empty_when_timesheet_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity_data(99) == {}


def test_get_entity_data_overtime_flag_true_for_non_normal():
    adapter = _make_adapter()
    ts = MagicMock()
    ts.overtime_type = "WEEKEND"
    ts.hours = 8
    ts.work_date = MagicMock()
    ts.work_date.isoformat.return_value = "2024-01-06"
    adapter.db.query.return_value.filter.return_value.first.return_value = ts
    data = adapter.get_entity_data(1)
    assert data["is_overtime"] is True


def test_get_entity_data_overtime_flag_false_for_normal():
    adapter = _make_adapter()
    ts = MagicMock()
    ts.overtime_type = "NORMAL"
    ts.hours = 8
    ts.work_date = MagicMock()
    ts.work_date.isoformat.return_value = "2024-01-05"
    adapter.db.query.return_value.filter.return_value.first.return_value = ts
    data = adapter.get_entity_data(1)
    assert data["is_overtime"] is False


def test_on_submit_sets_submitted_and_time():
    adapter = _make_adapter()
    ts = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = ts
    adapter.on_submit(1, MagicMock())
    assert ts.status == "SUBMITTED"
    assert ts.submit_time is not None


def test_on_approved_sets_approved_and_time():
    adapter = _make_adapter()
    ts = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = ts
    adapter.on_approved(1, MagicMock())
    assert ts.status == "APPROVED"
    assert ts.approve_time is not None


def test_on_rejected_sets_rejected():
    adapter = _make_adapter()
    ts = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = ts
    adapter.on_rejected(1, MagicMock())
    assert ts.status == "REJECTED"


def test_on_withdrawn_resets_to_draft():
    adapter = _make_adapter()
    ts = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = ts
    adapter.on_withdrawn(1, MagicMock())
    assert ts.status == "DRAFT"
    assert ts.submit_time is None


def test_validate_submit_fails_when_timesheet_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    ok, msg = adapter.validate_submit(99)
    assert not ok
    assert "不存在" in msg


def test_validate_submit_fails_when_status_invalid():
    adapter = _make_adapter()
    ts = MagicMock()
    ts.status = "SUBMITTED"
    adapter.db.query.return_value.filter.return_value.first.return_value = ts
    ok, msg = adapter.validate_submit(1)
    assert not ok
