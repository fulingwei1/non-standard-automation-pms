# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/adapters/base.py - batch 41"""
import pytest

pytest.importorskip("app.services.approval_engine.adapters.base")

from unittest.mock import MagicMock, patch


class ConcreteAdapter:
    """Concrete implementation for testing abstract base."""
    entity_type = "TEST"

    def __init__(self, db):
        self.db = db

    def get_entity(self, entity_id):
        return None

    def get_entity_data(self, entity_id):
        return {}

    def on_submit(self, entity_id, instance):
        pass

    def on_approved(self, entity_id, instance):
        pass

    def on_rejected(self, entity_id, instance):
        pass


def _make_adapter(db=None):
    """Create a patched adapter instance."""
    from app.services.approval_engine.adapters.base import ApprovalAdapter

    class TestAdapter(ApprovalAdapter):
        entity_type = "TEST"

        def get_entity(self, entity_id):
            return None

        def get_entity_data(self, entity_id):
            return {"id": entity_id}

        def on_submit(self, entity_id, instance):
            pass

        def on_approved(self, entity_id, instance):
            pass

        def on_rejected(self, entity_id, instance):
            pass

    return TestAdapter(db or MagicMock())


def test_generate_title_default():
    adapter = _make_adapter()
    title = adapter.generate_title(42)
    assert "42" in title
    assert "TEST" in title


def test_generate_summary_empty():
    adapter = _make_adapter()
    summary = adapter.generate_summary(1)
    assert summary == ""


def test_validate_submit_returns_true_by_default():
    adapter = _make_adapter()
    ok, msg = adapter.validate_submit(1)
    assert ok is True
    assert msg is None


def test_get_cc_user_ids_empty():
    adapter = _make_adapter()
    result = adapter.get_cc_user_ids(1)
    assert result == []


def test_resolve_approvers_empty():
    adapter = _make_adapter()
    node = MagicMock()
    context = {}
    result = adapter.resolve_approvers(node, context)
    assert result == []


def test_get_form_data_returns_entity_data():
    adapter = _make_adapter()
    result = adapter.get_form_data(99)
    assert result == {"id": 99}


def test_on_withdrawn_no_error():
    adapter = _make_adapter()
    # Should not raise
    adapter.on_withdrawn(1, MagicMock())


def test_on_terminated_no_error():
    adapter = _make_adapter()
    adapter.on_terminated(1, MagicMock())


def test_get_department_manager_user_id_no_dept():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    adapter = _make_adapter(db)
    with patch("app.models.organization.Department", create=True), \
         patch("app.models.organization.Employee", create=True), \
         patch("app.models.user.User", create=True):
        result = adapter.get_department_manager_user_id("非存在部门")
        assert result is None
