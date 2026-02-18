# -*- coding: utf-8 -*-
"""第二十五批 - status_update_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.status_update_service")

from app.services.status_update_service import StatusUpdateService, StatusUpdateResult


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return StatusUpdateService(db)


@pytest.fixture
def operator():
    user = MagicMock()
    user.id = 1
    user.username = "admin"
    return user


def _make_entity(status="DRAFT"):
    entity = MagicMock()
    entity.status = status
    return entity


# ── StatusUpdateResult ────────────────────────────────────────────────────────

class TestStatusUpdateResult:
    def test_success_result(self):
        result = StatusUpdateResult(success=True, old_status="A", new_status="B", message="OK")
        assert result.success is True
        assert result.old_status == "A"
        assert result.new_status == "B"
        assert result.message == "OK"
        assert result.errors == []

    def test_failure_result(self):
        result = StatusUpdateResult(success=False, errors=["错误1", "错误2"])
        assert result.success is False
        assert len(result.errors) == 2

    def test_success_repr(self):
        result = StatusUpdateResult(success=True, old_status="A", new_status="B")
        r = repr(result)
        assert "True" in r

    def test_failure_repr(self):
        result = StatusUpdateResult(success=False, errors=["err"])
        r = repr(result)
        assert "False" in r

    def test_default_errors_empty_list(self):
        result = StatusUpdateResult(success=True)
        assert result.errors == []


# ── update_status - valid_statuses validation ─────────────────────────────────

class TestUpdateStatusValidation:
    def test_rejects_invalid_status(self, service, operator):
        entity = _make_entity("DRAFT")
        result = service.update_status(
            entity, "INVALID", operator,
            valid_statuses=["DRAFT", "SUBMITTED", "APPROVED"]
        )
        assert result.success is False
        assert len(result.errors) > 0
        assert "INVALID" in result.errors[0]

    def test_accepts_valid_status(self, service, operator):
        entity = _make_entity("DRAFT")
        result = service.update_status(
            entity, "SUBMITTED", operator,
            valid_statuses=["DRAFT", "SUBMITTED", "APPROVED"]
        )
        assert result.success is True

    def test_no_valid_statuses_check_skipped(self, service, operator):
        entity = _make_entity("DRAFT")
        result = service.update_status(entity, "ANYTHING", operator)
        assert result.success is True

    def test_returns_entity_in_result(self, service, operator):
        entity = _make_entity("DRAFT")
        result = service.update_status(entity, "SUBMITTED", operator)
        assert result.entity is entity


# ── update_status - transition_rules ─────────────────────────────────────────

class TestUpdateStatusTransitionRules:
    def test_allows_valid_transition(self, service, operator):
        entity = _make_entity("DRAFT")
        rules = {"DRAFT": ["SUBMITTED"], "SUBMITTED": ["APPROVED", "REJECTED"]}
        result = service.update_status(
            entity, "SUBMITTED", operator,
            transition_rules=rules
        )
        assert result.success is True

    def test_rejects_invalid_transition(self, service, operator):
        entity = _make_entity("DRAFT")
        rules = {"DRAFT": ["SUBMITTED"]}
        result = service.update_status(
            entity, "APPROVED", operator,
            transition_rules=rules
        )
        assert result.success is False
        assert "不允许的状态转换" in result.errors[0]

    def test_rejects_when_status_not_in_rules(self, service, operator):
        entity = _make_entity("ARCHIVED")
        rules = {"DRAFT": ["SUBMITTED"]}
        result = service.update_status(
            entity, "DRAFT", operator,
            transition_rules=rules
        )
        assert result.success is False

    def test_no_transition_rules_skips_check(self, service, operator):
        entity = _make_entity("DRAFT")
        result = service.update_status(entity, "APPROVED", operator)
        assert result.success is True


# ── update_status - same status ───────────────────────────────────────────────

class TestUpdateStatusSameStatus:
    def test_same_status_returns_success_with_message(self, service, operator):
        entity = _make_entity("DRAFT")
        result = service.update_status(entity, "DRAFT", operator)
        assert result.success is True
        assert "未发生变化" in result.message

    def test_same_status_does_not_change_entity(self, service, operator):
        entity = _make_entity("DRAFT")
        result = service.update_status(entity, "DRAFT", operator)
        assert result.old_status == result.new_status


# ── update_status - timestamp_fields ─────────────────────────────────────────

class TestUpdateStatusTimestampFields:
    def test_sets_timestamp_on_matching_status(self, service, operator):
        entity = MagicMock()
        entity.status = "DRAFT"
        entity.submitted_at = None

        with patch("app.services.status_update_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 6, 1, 12, 0)
            service.update_status(
                entity, "SUBMITTED", operator,
                timestamp_fields={"SUBMITTED": "submitted_at"}
            )
        # submitted_at should have been set
        assert entity.submitted_at == datetime(2025, 6, 1, 12, 0)

    def test_does_not_overwrite_existing_timestamp(self, service, operator):
        entity = MagicMock()
        entity.status = "DRAFT"
        entity.submitted_at = datetime(2025, 1, 1)  # Already has value

        service.update_status(
            entity, "SUBMITTED", operator,
            timestamp_fields={"SUBMITTED": "submitted_at"}
        )
        # Should NOT be overwritten
        assert entity.submitted_at == datetime(2025, 1, 1)


# ── update_status - callbacks ─────────────────────────────────────────────────

class TestUpdateStatusCallbacks:
    def test_before_callback_called(self, service, operator):
        entity = _make_entity("DRAFT")
        callback = MagicMock()
        service.update_status(entity, "SUBMITTED", operator, before_update_callback=callback)
        callback.assert_called_once()

    def test_after_callback_called(self, service, operator):
        entity = _make_entity("DRAFT")
        callback = MagicMock()
        service.update_status(entity, "SUBMITTED", operator, after_update_callback=callback)
        callback.assert_called_once()

    def test_before_callback_failure_returns_error(self, service, operator):
        entity = _make_entity("DRAFT")
        def bad_callback(*args, **kwargs):
            raise ValueError("回调失败")
        result = service.update_status(
            entity, "SUBMITTED", operator,
            before_update_callback=bad_callback
        )
        assert result.success is False
        assert len(result.errors) > 0

    def test_history_callback_called(self, service, operator):
        entity = _make_entity("DRAFT")
        history_cb = MagicMock()
        service.update_status(entity, "SUBMITTED", operator, history_callback=history_cb)
        history_cb.assert_called_once()


# ── update_status - related_entities ─────────────────────────────────────────

class TestUpdateStatusRelatedEntities:
    def test_updates_related_entity_status(self, service, operator):
        entity = _make_entity("DRAFT")
        related = MagicMock()
        related.status = "DRAFT"
        result = service.update_status(
            entity, "SUBMITTED", operator,
            related_entities=[{"entity": related, "field": "status", "value": "LINKED"}]
        )
        assert result.success is True
        assert related.status == "LINKED"
