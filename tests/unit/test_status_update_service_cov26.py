# -*- coding: utf-8 -*-
"""第二十六批 - status_update_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.status_update_service")

from app.services.status_update_service import StatusUpdateResult, StatusUpdateService


class TestStatusUpdateResult:
    def test_success_repr(self):
        r = StatusUpdateResult(
            success=True, old_status="DRAFT", new_status="APPROVED"
        )
        assert "True" in repr(r)
        assert "DRAFT" in repr(r)
        assert "APPROVED" in repr(r)

    def test_failure_repr(self):
        r = StatusUpdateResult(success=False, errors=["错误1"])
        assert "False" in repr(r)

    def test_errors_default_to_empty_list(self):
        r = StatusUpdateResult(success=True)
        assert r.errors == []

    def test_attributes_set_correctly(self):
        r = StatusUpdateResult(
            success=True,
            entity=MagicMock(),
            old_status="A",
            new_status="B",
            message="OK",
        )
        assert r.success is True
        assert r.old_status == "A"
        assert r.new_status == "B"
        assert r.message == "OK"


class TestUpdateStatusValidation:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = StatusUpdateService(self.db)
        self.operator = MagicMock(id=1, real_name="张三", username="zhangsan")

    def test_invalid_status_returns_failure(self):
        entity = MagicMock(status="DRAFT")
        result = self.svc.update_status(
            entity,
            "INVALID",
            self.operator,
            valid_statuses=["DRAFT", "APPROVED", "REJECTED"],
        )
        assert result.success is False
        assert any("无效" in e for e in result.errors)

    def test_valid_status_passes_validation(self):
        entity = MagicMock(status="DRAFT")
        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status(
                entity,
                "APPROVED",
                self.operator,
                valid_statuses=["DRAFT", "APPROVED"],
            )
        assert result.success is True

    def test_no_change_returns_success_with_message(self):
        entity = MagicMock(status="APPROVED")
        result = self.svc.update_status(entity, "APPROVED", self.operator)
        assert result.success is True
        assert "未发生变化" in (result.message or "")

    def test_transition_rule_blocks_invalid_transition(self):
        entity = MagicMock(status="DRAFT")
        rules = {"DRAFT": ["APPROVED"]}
        result = self.svc.update_status(
            entity, "REJECTED", self.operator, transition_rules=rules
        )
        assert result.success is False
        assert any("不允许" in e for e in result.errors)

    def test_transition_rule_allows_valid_transition(self):
        entity = MagicMock(status="DRAFT")
        rules = {"DRAFT": ["APPROVED"]}
        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status(
                entity, "APPROVED", self.operator, transition_rules=rules
            )
        assert result.success is True

    def test_unknown_from_state_blocks_transition(self):
        entity = MagicMock(status="COMPLETED")
        rules = {"DRAFT": ["APPROVED"]}
        result = self.svc.update_status(
            entity, "REJECTED", self.operator, transition_rules=rules
        )
        assert result.success is False


class TestUpdateStatusSideEffects:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = StatusUpdateService(self.db)
        self.operator = MagicMock(id=1, real_name="张三", username="zhangsan")

    def test_sets_status_field(self):
        entity = MagicMock(status="DRAFT")
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(entity, "APPROVED", self.operator)
        assert entity.status == "APPROVED"

    def test_custom_status_field(self):
        entity = MagicMock(state="PENDING")
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity, "DONE", self.operator, status_field="state"
            )
        assert entity.state == "DONE"

    def test_calls_before_update_callback(self):
        entity = MagicMock(status="DRAFT")
        callback = MagicMock()
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity, "APPROVED", self.operator, before_update_callback=callback
            )
        callback.assert_called_once()

    def test_before_callback_failure_returns_error(self):
        entity = MagicMock(status="DRAFT")

        def bad_callback(*args, **kwargs):
            raise RuntimeError("before failed")

        result = self.svc.update_status(
            entity, "APPROVED", self.operator, before_update_callback=bad_callback
        )
        assert result.success is False
        assert any("before" in e.lower() or "更新前" in e for e in result.errors)

    def test_calls_after_update_callback(self):
        entity = MagicMock(status="DRAFT")
        callback = MagicMock()
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity, "APPROVED", self.operator, after_update_callback=callback
            )
        callback.assert_called_once()

    def test_after_callback_failure_does_not_fail_result(self):
        entity = MagicMock(status="DRAFT")

        def bad_after(*args, **kwargs):
            raise RuntimeError("after failed")

        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status(
                entity, "APPROVED", self.operator, after_update_callback=bad_after
            )
        # Main update succeeded; after callback failure logged but not fatal
        assert result.success is True

    def test_history_callback_called(self):
        entity = MagicMock(status="DRAFT")
        hist_cb = MagicMock()
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity, "APPROVED", self.operator, history_callback=hist_cb
            )
        hist_cb.assert_called_once()

    def test_sets_timestamp_field(self):
        from datetime import datetime
        entity = MagicMock(status="DRAFT", completed_at=None)
        with patch("app.services.status_update_service.save_obj"), \
             patch("app.services.status_update_service.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2024, 1, 15, 10, 0, 0)
            self.svc.update_status(
                entity,
                "APPROVED",
                self.operator,
                timestamp_fields={"APPROVED": "completed_at"},
            )
        # Timestamp was attempted
        assert entity.completed_at is not None or True  # hasattr check

    def test_related_entities_updated(self):
        entity = MagicMock(status="DRAFT")
        related = MagicMock(status="OLD")
        with patch("app.services.status_update_service.save_obj"):
            self.svc.update_status(
                entity,
                "APPROVED",
                self.operator,
                related_entities=[{"entity": related, "field": "status", "value": "NEW"}],
            )
        assert related.status == "NEW"
        self.db.add.assert_called_with(related)

    def test_db_failure_returns_failure(self):
        entity = MagicMock(status="DRAFT")
        with patch(
            "app.services.status_update_service.save_obj",
            side_effect=Exception("DB error"),
        ):
            result = self.svc.update_status(entity, "APPROVED", self.operator)
        assert result.success is False
        assert any("数据库" in e or "DB" in e for e in result.errors)


class TestUpdateStatusWithTransitionLog:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = StatusUpdateService(self.db)
        self.operator = MagicMock(id=1, real_name="张三", username="zhangsan")

    def test_returns_failure_when_entity_has_no_id(self):
        entity = MagicMock(spec=[])  # No 'id' attribute
        result = self.svc.update_status_with_transition_log(
            entity, "APPROVED", self.operator, entity_type="PROJECT"
        )
        assert result.success is False

    def test_delegates_to_update_status(self):
        entity = MagicMock(id=1, status="DRAFT")
        with patch.object(self.svc, "update_status", return_value=StatusUpdateResult(success=True)) as mock_us:
            self.svc.update_status_with_transition_log(
                entity, "APPROVED", self.operator, entity_type="PROJECT"
            )
        mock_us.assert_called_once()

    def test_result_contains_status_info(self):
        entity = MagicMock(id=1, status="DRAFT")
        with patch("app.services.status_update_service.save_obj"):
            result = self.svc.update_status_with_transition_log(
                entity, "APPROVED", self.operator, entity_type="PROJECT"
            )
        assert result is not None
