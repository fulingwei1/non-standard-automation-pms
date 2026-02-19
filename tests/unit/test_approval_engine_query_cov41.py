# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/engine/query.py - batch 41"""
import pytest

pytest.importorskip("app.services.approval_engine.engine.query")

from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_core():
    core = MagicMock()
    core.db = MagicMock()
    core._log_action = MagicMock()
    return core


@pytest.fixture
def query_mixin(mock_core):
    from app.services.approval_engine.engine.query import ApprovalQueryMixin
    return ApprovalQueryMixin(mock_core)


def test_query_mixin_init_sets_db(query_mixin, mock_core):
    assert query_mixin.db is mock_core.db


def test_get_pending_tasks_returns_dict(query_mixin):
    query_mixin.db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 0
    query_mixin.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    with patch("app.services.approval_engine.engine.query.get_pagination_params") as mock_pag, \
         patch("app.services.approval_engine.engine.query.apply_pagination") as mock_apply:
        mock_pag.return_value = MagicMock(page=1, page_size=20, offset=0, limit=20)
        mock_apply.return_value = query_mixin.db.query.return_value.filter.return_value.order_by.return_value
        result = query_mixin.get_pending_tasks(user_id=1)

    assert "total" in result
    assert "items" in result


def test_get_initiated_instances_returns_dict(query_mixin):
    query_mixin.db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 1
    query_mixin.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [MagicMock()]

    with patch("app.services.approval_engine.engine.query.get_pagination_params") as mock_pag, \
         patch("app.services.approval_engine.engine.query.apply_pagination") as mock_apply:
        mock_pag.return_value = MagicMock(page=1, page_size=20, offset=0, limit=20)
        mock_apply.return_value = query_mixin.db.query.return_value.filter.return_value.order_by.return_value
        result = query_mixin.get_initiated_instances(user_id=1)

    assert result["total"] == 1


def test_get_cc_records_returns_dict(query_mixin):
    query_mixin.db.query.return_value.filter.return_value.order_by.return_value.count.return_value = 0
    query_mixin.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    with patch("app.services.approval_engine.engine.query.get_pagination_params") as mock_pag, \
         patch("app.services.approval_engine.engine.query.apply_pagination") as mock_apply:
        mock_pag.return_value = MagicMock(page=1, page_size=20, offset=0, limit=20)
        mock_apply.return_value = query_mixin.db.query.return_value.filter.return_value.order_by.return_value
        result = query_mixin.get_cc_records(user_id=1)

    assert "items" in result


def test_mark_cc_as_read_returns_true(query_mixin):
    cc = MagicMock()
    cc.instance_id = 5
    query_mixin.db.query.return_value.filter.return_value.first.return_value = cc
    result = query_mixin.mark_cc_as_read(cc_id=1, user_id=1)
    assert result is True
    assert cc.is_read is True


def test_mark_cc_as_read_returns_false_not_found(query_mixin):
    query_mixin.db.query.return_value.filter.return_value.first.return_value = None
    result = query_mixin.mark_cc_as_read(cc_id=999, user_id=1)
    assert result is False
