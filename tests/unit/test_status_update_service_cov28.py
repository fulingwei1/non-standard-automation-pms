# -*- coding: utf-8 -*-
"""第二十八批 - status_update_service 单元测试（通用状态更新服务）"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

pytest.importorskip("app.services.status_update_service")

from app.services.status_update_service import (
    StatusUpdateResult,
    StatusUpdateService,
)


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_entity(status="DRAFT"):
    e = MagicMock()
    e.status = status
    return e


def _make_operator(user_id=1, name="操作人"):
    u = MagicMock()
    u.id = user_id
    u.real_name = name
    return u


def _make_service(db=None):
    if db is None:
        db = MagicMock()
    return StatusUpdateService(db)


# ─── StatusUpdateResult ──────────────────────────────────────

class TestStatusUpdateResult:

    def test_repr_success(self):
        r = StatusUpdateResult(success=True, old_status="DRAFT", new_status="ACTIVE")
        assert "True" in repr(r)
        assert "DRAFT" in repr(r)

    def test_repr_failure(self):
        r = StatusUpdateResult(success=False, errors=["验证失败"])
        assert "False" in repr(r)

    def test_errors_default_to_empty_list(self):
        r = StatusUpdateResult(success=True)
        assert r.errors == []

    def test_stores_all_fields(self):
        entity = _make_entity()
        r = StatusUpdateResult(
            success=True,
            entity=entity,
            old_status="A",
            new_status="B",
            message="OK",
            errors=["e1"],
        )
        assert r.entity is entity
        assert r.old_status == "A"
        assert r.new_status == "B"


# ─── update_status ───────────────────────────────────────────

class TestUpdateStatus:

    @patch("app.services.status_update_service.save_obj")
    def test_basic_status_update_succeeds(self, mock_save):
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()

        result = svc.update_status(entity, "ACTIVE", operator)

        assert result.success is True
        assert entity.status == "ACTIVE"
        mock_save.assert_called_once()

    def test_fails_on_invalid_status(self):
        svc = _make_service()
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()

        result = svc.update_status(
            entity, "INVALID", operator,
            valid_statuses=["DRAFT", "ACTIVE", "CLOSED"]
        )

        assert result.success is False
        assert any("INVALID" in e for e in result.errors)

    @patch("app.services.status_update_service.save_obj")
    def test_succeeds_with_valid_status(self, mock_save):
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()

        result = svc.update_status(
            entity, "ACTIVE", operator,
            valid_statuses=["DRAFT", "ACTIVE", "CLOSED"]
        )

        assert result.success is True

    def test_fails_on_invalid_transition(self):
        svc = _make_service()
        entity = _make_entity(status="CLOSED")
        operator = _make_operator()

        rules = {"DRAFT": ["ACTIVE"], "ACTIVE": ["CLOSED"]}
        result = svc.update_status(
            entity, "DRAFT", operator,
            transition_rules=rules
        )

        assert result.success is False
        assert any("转换" in e for e in result.errors)

    @patch("app.services.status_update_service.save_obj")
    def test_succeeds_on_valid_transition(self, mock_save):
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()

        rules = {"DRAFT": ["ACTIVE"], "ACTIVE": ["CLOSED"]}
        result = svc.update_status(
            entity, "ACTIVE", operator,
            transition_rules=rules
        )

        assert result.success is True
        assert entity.status == "ACTIVE"

    @patch("app.services.status_update_service.save_obj")
    def test_same_status_returns_success_without_save(self, mock_save):
        """状态未变化时不触发保存，直接返回成功"""
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="ACTIVE")
        operator = _make_operator()

        result = svc.update_status(entity, "ACTIVE", operator)

        assert result.success is True
        assert "未发生变化" in (result.message or "")
        mock_save.assert_not_called()

    @patch("app.services.status_update_service.save_obj")
    def test_timestamp_field_set_on_status_match(self, mock_save):
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        entity.activated_at = None
        operator = _make_operator()

        result = svc.update_status(
            entity, "ACTIVE", operator,
            timestamp_fields={"ACTIVE": "activated_at"}
        )

        assert result.success is True
        assert entity.activated_at is not None

    @patch("app.services.status_update_service.save_obj")
    def test_timestamp_not_overwritten_if_already_set(self, mock_save):
        """时间戳字段已有值时不覆盖"""
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        existing_ts = datetime(2023, 1, 1)
        entity.activated_at = existing_ts
        operator = _make_operator()

        svc.update_status(
            entity, "ACTIVE", operator,
            timestamp_fields={"ACTIVE": "activated_at"}
        )

        assert entity.activated_at == existing_ts

    @patch("app.services.status_update_service.save_obj")
    def test_before_callback_called(self, mock_save):
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()
        before_cb = MagicMock()

        svc.update_status(entity, "ACTIVE", operator, before_update_callback=before_cb)

        before_cb.assert_called_once_with(entity, "DRAFT", "ACTIVE", operator)

    @patch("app.services.status_update_service.save_obj")
    def test_after_callback_not_invoked_by_default(self, mock_save):
        """after_update_callback 未传时不报错"""
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()

        # Should not raise
        result = svc.update_status(entity, "ACTIVE", operator)
        assert result.success is True

    @patch("app.services.status_update_service.save_obj")
    def test_history_callback_called(self, mock_save):
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()
        history_cb = MagicMock()

        svc.update_status(
            entity, "ACTIVE", operator,
            history_callback=history_cb,
            reason="测试原因"
        )

        history_cb.assert_called_once()
        kwargs = history_cb.call_args[1]
        assert kwargs["old_status"] == "DRAFT"
        assert kwargs["new_status"] == "ACTIVE"
        assert kwargs["reason"] == "测试原因"

    @patch("app.services.status_update_service.save_obj")
    def test_related_entity_updated(self, mock_save):
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()

        related = MagicMock()
        related.status = "OLD"

        svc.update_status(
            entity, "ACTIVE", operator,
            related_entities=[{"entity": related, "field": "status", "value": "SYNCED"}]
        )

        assert related.status == "SYNCED"
        db.add.assert_called_with(related)

    @patch("app.services.status_update_service.save_obj")
    def test_before_callback_failure_returns_error(self, mock_save):
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()

        def bad_callback(*args, **kwargs):
            raise ValueError("回调异常")

        result = svc.update_status(
            entity, "ACTIVE", operator,
            before_update_callback=bad_callback
        )

        assert result.success is False
        assert any("回调" in e for e in result.errors)

    @patch("app.services.status_update_service.save_obj")
    def test_db_failure_returns_error(self, mock_save):
        mock_save.side_effect = Exception("DB Error")
        db = MagicMock()
        svc = _make_service(db)
        entity = _make_entity(status="DRAFT")
        operator = _make_operator()

        result = svc.update_status(entity, "ACTIVE", operator)

        assert result.success is False
        assert any("数据库" in e for e in result.errors)
        db.rollback.assert_called_once()

    def test_old_status_not_in_transition_rules_fails(self):
        """当前状态不在转换规则中时，不允许任何转换"""
        svc = _make_service()
        entity = _make_entity(status="ARCHIVED")
        operator = _make_operator()

        rules = {"DRAFT": ["ACTIVE"], "ACTIVE": ["CLOSED"]}
        result = svc.update_status(
            entity, "ACTIVE", operator,
            transition_rules=rules
        )

        assert result.success is False
