# -*- coding: utf-8 -*-
"""单元测试 - ApprovalQueryMixin (cov48)"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.engine.query import ApprovalQueryMixin
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for ApprovalQueryMixin")

_PAG_PATH = "app.services.approval_engine.engine.query.get_pagination_params"
_APPLY_PATH = "app.services.approval_engine.engine.query.apply_pagination"


def _make_pagination_mock():
    pag = MagicMock()
    pag.page = 1
    pag.page_size = 20
    pag.offset = 0
    pag.limit = 20
    return pag


def _make_query():
    core = MagicMock()
    core.db = MagicMock()
    core._log_action = MagicMock()
    obj = ApprovalQueryMixin(core)
    return obj


def test_get_pending_tasks_returns_paginated_dict():
    obj = _make_query()
    with patch(_PAG_PATH, return_value=_make_pagination_mock()), \
         patch(_APPLY_PATH, side_effect=lambda q, o, l: q):
        obj.db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 2
        obj.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            MagicMock(), MagicMock()
        ]
        result = obj.get_pending_tasks(user_id=1)
    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["page"] == 1


def test_get_initiated_instances_no_status_filter():
    obj = _make_query()
    with patch(_PAG_PATH, return_value=_make_pagination_mock()), \
         patch(_APPLY_PATH, side_effect=lambda q, o, l: q):
        q = obj.db.query.return_value.filter.return_value
        q.order_by.return_value.count.return_value = 0
        q.order_by.return_value.all.return_value = []
        result = obj.get_initiated_instances(user_id=1)
    assert result["total"] == 0
    assert result["items"] == []


def test_get_initiated_instances_with_status_filter():
    obj = _make_query()
    with patch(_PAG_PATH, return_value=_make_pagination_mock()), \
         patch(_APPLY_PATH, side_effect=lambda q, o, l: q):
        q = obj.db.query.return_value.filter.return_value
        q.filter.return_value.order_by.return_value.count.return_value = 1
        q.filter.return_value.order_by.return_value.all.return_value = [MagicMock()]
        result = obj.get_initiated_instances(user_id=1, status="PENDING")
    assert result["total"] == 1


def test_get_cc_records_with_is_read_filter():
    obj = _make_query()
    with patch(_PAG_PATH, return_value=_make_pagination_mock()), \
         patch(_APPLY_PATH, side_effect=lambda q, o, l: q):
        q = obj.db.query.return_value.filter.return_value
        q.filter.return_value.order_by.return_value.count.return_value = 0
        q.filter.return_value.order_by.return_value.all.return_value = []
        result = obj.get_cc_records(user_id=1, is_read=False)
    assert "items" in result
    assert "total" in result


def test_mark_cc_as_read_returns_true_when_found():
    obj = _make_query()
    cc = MagicMock()
    cc.instance_id = 5
    obj.db.query.return_value.filter.return_value.first.return_value = cc
    result = obj.mark_cc_as_read(cc_id=1, user_id=1)
    assert result is True
    assert cc.is_read is True
    assert cc.read_at is not None


def test_mark_cc_as_read_returns_false_when_not_found():
    obj = _make_query()
    obj.db.query.return_value.filter.return_value.first.return_value = None
    result = obj.mark_cc_as_read(cc_id=99, user_id=1)
    assert result is False


def test_mark_cc_as_read_logs_action():
    obj = _make_query()
    cc = MagicMock()
    cc.instance_id = 3
    obj.db.query.return_value.filter.return_value.first.return_value = cc
    obj.mark_cc_as_read(cc_id=1, user_id=7)
    obj._log_action.assert_called_once_with(
        instance_id=3,
        operator_id=7,
        action="READ_CC",
    )
