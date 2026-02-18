# -*- coding: utf-8 -*-
"""第二十七批 - status_update_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.status_update_service")

from app.services.status_update_service import StatusUpdateService, StatusUpdateResult


def make_db():
    return MagicMock()


def make_operator(user_id=1, name="张三"):
    op = MagicMock()
    op.id = user_id
    op.real_name = name
    return op


def make_entity(status="PENDING"):
    entity = MagicMock(spec=["status"])
    entity.status = status
    return entity


class TestStatusUpdateResultClass:
    def test_success_result(self):
        r = StatusUpdateResult(success=True, old_status="A", new_status="B")
        assert r.success is True
        assert r.old_status == "A"
        assert r.new_status == "B"
        assert r.errors == []

    def test_failure_result_with_errors(self):
        r = StatusUpdateResult(success=False, errors=["错误1", "错误2"])
        assert r.success is False
        assert len(r.errors) == 2

    def test_repr_success(self):
        r = StatusUpdateResult(success=True, old_status="PENDING", new_status="APPROVED")
        repr_str = repr(r)
        assert "success=True" in repr_str
        assert "PENDING" in repr_str
        assert "APPROVED" in repr_str

    def test_repr_failure(self):
        r = StatusUpdateResult(success=False, errors=["校验失败"])
        repr_str = repr(r)
        assert "success=False" in repr_str

    def test_default_errors_is_empty_list(self):
        r = StatusUpdateResult(success=True)
        assert r.errors == []

    def test_message_stored(self):
        r = StatusUpdateResult(success=True, message="状态已更新")
        assert r.message == "状态已更新"


class TestUpdateStatusValidation:
    def setup_method(self):
        self.db = make_db()
        self.svc = StatusUpdateService(self.db)
        self.operator = make_operator()

    def test_invalid_status_returns_failure(self):
        entity = make_entity(status="PENDING")
        result = self.svc.update_status(
            entity=entity,
            new_status="INVALID_STATUS",
            operator=self.operator,
            valid_statuses=["PENDING", "APPROVED", "REJECTED"]
        )
        assert result.success is False
        assert len(result.errors) > 0

    def test_valid_status_returns_success(self):
        entity = make_entity(status="PENDING")
        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status(
                entity=entity,
                new_status="APPROVED",
                operator=self.operator,
                valid_statuses=["PENDING", "APPROVED", "REJECTED"]
            )
        assert result.success is True

    def test_no_validation_allows_any_status(self):
        entity = make_entity(status="PENDING")
        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status(
                entity=entity,
                new_status="ANYTHING",
                operator=self.operator
            )
        assert result.success is True

    def test_same_status_returns_success_with_message(self):
        entity = make_entity(status="PENDING")
        result = self.svc.update_status(
            entity=entity,
            new_status="PENDING",
            operator=self.operator,
            valid_statuses=["PENDING", "APPROVED"]
        )
        assert result.success is True
        assert "变化" in (result.message or "")


class TestUpdateStatusTransitionRules:
    def setup_method(self):
        self.db = make_db()
        self.svc = StatusUpdateService(self.db)
        self.operator = make_operator()

    def test_allowed_transition_succeeds(self):
        entity = make_entity(status="PENDING")
        transition_rules = {"PENDING": ["APPROVED", "REJECTED"]}
        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status(
                entity=entity,
                new_status="APPROVED",
                operator=self.operator,
                transition_rules=transition_rules
            )
        assert result.success is True

    def test_disallowed_transition_fails(self):
        entity = make_entity(status="PENDING")
        transition_rules = {"PENDING": ["APPROVED"]}
        result = self.svc.update_status(
            entity=entity,
            new_status="REJECTED",
            operator=self.operator,
            transition_rules=transition_rules
        )
        assert result.success is False
        assert len(result.errors) > 0

    def test_status_not_in_rules_fails(self):
        entity = make_entity(status="COMPLETED")
        transition_rules = {"PENDING": ["APPROVED"]}
        result = self.svc.update_status(
            entity=entity,
            new_status="APPROVED",
            operator=self.operator,
            transition_rules=transition_rules
        )
        assert result.success is False

    def test_error_message_mentions_from_to(self):
        entity = make_entity(status="PENDING")
        transition_rules = {"PENDING": ["APPROVED"]}
        result = self.svc.update_status(
            entity=entity,
            new_status="REJECTED",
            operator=self.operator,
            transition_rules=transition_rules
        )
        assert any("PENDING" in e or "REJECTED" in e for e in result.errors)


class TestUpdateStatusCallbacks:
    def setup_method(self):
        self.db = make_db()
        self.svc = StatusUpdateService(self.db)
        self.operator = make_operator()

    def test_before_update_callback_called(self):
        entity = make_entity(status="PENDING")
        before_cb = MagicMock()
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity=entity,
                new_status="APPROVED",
                operator=self.operator,
                before_update_callback=before_cb
            )
        before_cb.assert_called_once()

    def test_after_update_callback_called(self):
        entity = make_entity(status="PENDING")
        after_cb = MagicMock()
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity=entity,
                new_status="APPROVED",
                operator=self.operator,
                after_update_callback=after_cb
            )
        after_cb.assert_called_once()

    def test_before_callback_failure_returns_error(self):
        entity = make_entity(status="PENDING")
        before_cb = MagicMock(side_effect=RuntimeError("回调失败"))
        result = self.svc.update_status(
            entity=entity,
            new_status="APPROVED",
            operator=self.operator,
            before_update_callback=before_cb
        )
        assert result.success is False
        assert len(result.errors) > 0

    def test_history_callback_called(self):
        entity = make_entity(status="PENDING")
        hist_cb = MagicMock()
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity=entity,
                new_status="APPROVED",
                operator=self.operator,
                history_callback=hist_cb
            )
        hist_cb.assert_called_once()


class TestUpdateStatusSideEffects:
    def setup_method(self):
        self.db = make_db()
        self.svc = StatusUpdateService(self.db)
        self.operator = make_operator()

    def test_status_field_updated_on_entity(self):
        entity = make_entity(status="PENDING")
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity=entity,
                new_status="APPROVED",
                operator=self.operator
            )
        assert entity.status == "APPROVED"

    def test_related_entities_updated(self):
        entity = make_entity(status="PENDING")
        related = MagicMock()
        related.status = "OPEN"
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity=entity,
                new_status="APPROVED",
                operator=self.operator,
                related_entities=[{"entity": related, "field": "status", "value": "CLOSED"}]
            )
        assert related.status == "CLOSED"

    def test_old_status_preserved_in_result(self):
        entity = make_entity(status="PENDING")
        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status(
                entity=entity,
                new_status="APPROVED",
                operator=self.operator
            )
        assert result.old_status == "PENDING"
        assert result.new_status == "APPROVED"

    def test_custom_status_field(self):
        entity = MagicMock()
        entity.approval_status = "DRAFT"
        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status(
                entity=entity,
                new_status="SUBMITTED",
                operator=self.operator,
                status_field="approval_status"
            )
        assert entity.approval_status == "SUBMITTED"
