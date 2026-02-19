# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/adapters/timesheet.py - batch 41"""
import pytest

pytest.importorskip("app.services.approval_engine.adapters.timesheet")

from unittest.mock import MagicMock
from datetime import date


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def adapter(db):
    from app.services.approval_engine.adapters.timesheet import TimesheetApprovalAdapter
    return TimesheetApprovalAdapter(db)


def test_entity_type(adapter):
    assert adapter.entity_type == "TIMESHEET"


def test_get_entity_not_found(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity(999) is None


def test_get_entity_data_empty_when_missing(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity_data(999) == {}


def test_on_submit_sets_submitted(adapter, db):
    ts = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = ts
    adapter.on_submit(1, MagicMock())
    assert ts.status == "SUBMITTED"


def test_on_approved_sets_approved(adapter, db):
    ts = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = ts
    adapter.on_approved(1, MagicMock())
    assert ts.status == "APPROVED"


def test_on_rejected_sets_rejected(adapter, db):
    ts = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = ts
    adapter.on_rejected(1, MagicMock())
    assert ts.status == "REJECTED"


def test_on_withdrawn_resets_draft(adapter, db):
    ts = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = ts
    adapter.on_withdrawn(1, MagicMock())
    assert ts.status == "DRAFT"
    assert ts.submit_time is None


def test_validate_submit_not_found(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    ok, msg = adapter.validate_submit(999)
    assert ok is False
    assert "不存在" in msg


def test_validate_submit_success(adapter, db):
    ts = MagicMock()
    ts.status = "DRAFT"
    ts.hours = 8
    ts.work_date = date.today()
    db.query.return_value.filter.return_value.first.return_value = ts
    ok, msg = adapter.validate_submit(1)
    assert ok is True
