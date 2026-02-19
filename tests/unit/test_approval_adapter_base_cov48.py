# -*- coding: utf-8 -*-
"""单元测试 - ApprovalAdapter 基类 (cov48)"""

import pytest
from unittest.mock import MagicMock

try:
    from app.services.approval_engine.adapters.base import ApprovalAdapter
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for ApprovalAdapter")


class _ConcreteAdapter(ApprovalAdapter):
    """用于测试的具体实现"""
    entity_type = "TEST_ENTITY"

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


def _make_adapter():
    db = MagicMock()
    return _ConcreteAdapter(db)


def test_generate_title_includes_entity_type_and_id():
    adapter = _make_adapter()
    title = adapter.generate_title(7)
    assert "TEST_ENTITY" in title
    assert "7" in title


def test_generate_summary_default_empty():
    adapter = _make_adapter()
    assert adapter.generate_summary(1) == ""


def test_validate_submit_default_returns_true():
    adapter = _make_adapter()
    ok, msg = adapter.validate_submit(1)
    assert ok is True
    assert msg is None


def test_get_cc_user_ids_default_empty_list():
    adapter = _make_adapter()
    assert adapter.get_cc_user_ids(1) == []


def test_get_form_data_delegates_to_get_entity_data():
    adapter = _make_adapter()
    result = adapter.get_form_data(5)
    assert result == {"id": 5}


def test_resolve_approvers_default_empty():
    adapter = _make_adapter()
    node = MagicMock()
    result = adapter.resolve_approvers(node, {"key": "val"})
    assert result == []


def test_on_withdrawn_does_not_raise():
    adapter = _make_adapter()
    instance = MagicMock()
    adapter.on_withdrawn(1, instance)  # should not raise


def test_on_terminated_does_not_raise():
    adapter = _make_adapter()
    instance = MagicMock()
    adapter.on_terminated(1, instance)  # should not raise
