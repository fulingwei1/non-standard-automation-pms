# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/db_helpers.py  (L4组)

Covers:
- get_or_404: 找到 / 找不到两种情况，自定义 detail，自定义 id_field
- save_obj:   db.add / commit / refresh 都被调用；refresh=False 时跳过
- delete_obj: db.delete / commit 都被调用
- update_obj: 字段更新逻辑；unknown 字段被跳过；refresh 参数
- safe_commit: 成功返回 True；失败回滚并返回 False
"""

import pytest
from unittest.mock import MagicMock, call, patch

from fastapi import HTTPException

from app.utils.db_helpers import (
    delete_obj,
    get_or_404,
    safe_commit,
    save_obj,
    update_obj,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db():
    """Return a mock SQLAlchemy Session."""
    return MagicMock()


def _make_model(name: str = "FakeModel"):
    """Return a mock SQLAlchemy Model class with a given __name__."""
    model = MagicMock()
    model.__name__ = name
    return model


# ---------------------------------------------------------------------------
# get_or_404
# ---------------------------------------------------------------------------

class TestGetOr404:
    """Tests for get_or_404."""

    def test_returns_object_when_found(self):
        """Returns the object when db.query().filter().first() is not None."""
        db = _make_db()
        model = _make_model("Project")
        fake_obj = MagicMock()

        db.query.return_value.filter.return_value.first.return_value = fake_obj

        result = get_or_404(db, model, obj_id=42)

        assert result is fake_obj
        db.query.assert_called_once_with(model)

    def test_raises_404_when_not_found(self):
        """Raises HTTPException(404) when first() returns None."""
        db = _make_db()
        model = _make_model("Task")

        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db, model, obj_id=99)

        assert exc_info.value.status_code == 404

    def test_default_error_message_contains_model_name(self):
        """Default 404 detail includes model name and id."""
        db = _make_db()
        model = _make_model("Invoice")
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db, model, obj_id=7)

        assert "Invoice" in exc_info.value.detail
        assert "7" in exc_info.value.detail

    def test_custom_detail_message(self):
        """Custom detail string is used when provided."""
        db = _make_db()
        model = _make_model("User")
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db, model, obj_id=1, detail="自定义错误消息")

        assert exc_info.value.detail == "自定义错误消息"

    def test_custom_id_field(self):
        """Supports custom id_field (e.g. 'code')."""
        db = _make_db()
        # model needs the attribute for getattr to work
        model = MagicMock()
        model.__name__ = "Product"
        fake_field = MagicMock()
        model.code = fake_field
        fake_obj = MagicMock()

        db.query.return_value.filter.return_value.first.return_value = fake_obj

        result = get_or_404(db, model, obj_id="P001", id_field="code")

        assert result is fake_obj

    def test_raises_404_with_custom_id_field_not_found(self):
        """Raises 404 with custom id_field when not found."""
        db = _make_db()
        model = MagicMock()
        model.__name__ = "Employee"
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db, model, obj_id="E999", id_field="employee_no")

        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# save_obj
# ---------------------------------------------------------------------------

class TestSaveObj:
    """Tests for save_obj."""

    def test_calls_add_commit_refresh(self):
        """save_obj calls db.add, db.commit, db.refresh in order."""
        db = _make_db()
        obj = MagicMock()

        result = save_obj(db, obj)

        db.add.assert_called_once_with(obj)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(obj)
        assert result is obj

    def test_refresh_false_skips_refresh(self):
        """When refresh=False, db.refresh is not called."""
        db = _make_db()
        obj = MagicMock()

        result = save_obj(db, obj, refresh=False)

        db.add.assert_called_once_with(obj)
        db.commit.assert_called_once()
        db.refresh.assert_not_called()
        assert result is obj

    def test_returns_same_object(self):
        """save_obj returns the same object that was passed in."""
        db = _make_db()

        class FakeModel:
            id = None

        obj = FakeModel()
        returned = save_obj(db, obj)
        assert returned is obj

    def test_commit_called_exactly_once(self):
        """db.commit is called exactly once, not multiple times."""
        db = _make_db()
        obj = MagicMock()
        save_obj(db, obj)
        assert db.commit.call_count == 1

    def test_add_called_with_correct_object(self):
        """db.add receives the exact object."""
        db = _make_db()
        obj = object()
        save_obj(db, obj, refresh=False)
        db.add.assert_called_with(obj)


# ---------------------------------------------------------------------------
# delete_obj
# ---------------------------------------------------------------------------

class TestDeleteObj:
    """Tests for delete_obj."""

    def test_calls_delete_and_commit(self):
        """delete_obj calls db.delete and db.commit."""
        db = _make_db()
        obj = MagicMock()

        delete_obj(db, obj)

        db.delete.assert_called_once_with(obj)
        db.commit.assert_called_once()

    def test_delete_called_before_commit(self):
        """db.delete is called before db.commit."""
        db = _make_db()
        obj = MagicMock()
        call_order = []

        db.delete.side_effect = lambda x: call_order.append("delete")
        db.commit.side_effect = lambda: call_order.append("commit")

        delete_obj(db, obj)

        assert call_order == ["delete", "commit"]

    def test_returns_none(self):
        """delete_obj returns None."""
        db = _make_db()
        obj = MagicMock()
        result = delete_obj(db, obj)
        assert result is None

    def test_delete_with_different_objects(self):
        """Works for any type of object."""
        db = _make_db()
        for val in [MagicMock(), "some_string", 42, {"key": "val"}]:
            delete_obj(db, val)
        assert db.delete.call_count == 4
        assert db.commit.call_count == 4


# ---------------------------------------------------------------------------
# update_obj
# ---------------------------------------------------------------------------

class TestUpdateObj:
    """Tests for update_obj."""

    def test_updates_known_fields(self):
        """Sets valid fields on the object via setattr."""
        db = _make_db()

        class FakeModel:
            name = "old"
            status = "pending"

        obj = FakeModel()
        data = {"name": "new_name", "status": "active"}

        update_obj(db, obj, data, refresh=False)

        assert obj.name == "new_name"
        assert obj.status == "active"

    def test_skips_unknown_fields(self):
        """Fields not on the object are silently ignored."""
        db = _make_db()

        class FakeModel:
            title = "original"

        obj = FakeModel()
        data = {"title": "updated", "nonexistent_field": "ignored"}

        update_obj(db, obj, data, refresh=False)

        assert obj.title == "updated"
        assert not hasattr(obj, "nonexistent_field")

    def test_calls_save_obj(self):
        """update_obj delegates to save_obj (db.add + commit called)."""
        db = _make_db()

        class FakeModel:
            value = 0

        obj = FakeModel()
        update_obj(db, obj, {"value": 99}, refresh=False)

        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_returns_updated_object(self):
        """Returns the same object after update."""
        db = _make_db()

        class FakeModel:
            x = 1

        obj = FakeModel()
        result = update_obj(db, obj, {"x": 2}, refresh=False)
        assert result is obj

    def test_empty_data_dict(self):
        """Empty data dict leaves object unchanged."""
        db = _make_db()

        class FakeModel:
            name = "unchanged"

        obj = FakeModel()
        update_obj(db, obj, {}, refresh=False)
        assert obj.name == "unchanged"

    def test_refresh_true_calls_db_refresh(self):
        """When refresh=True (default), db.refresh is called."""
        db = _make_db()

        class FakeModel:
            name = "x"

        obj = FakeModel()
        update_obj(db, obj, {"name": "y"}, refresh=True)
        db.refresh.assert_called_once_with(obj)


# ---------------------------------------------------------------------------
# safe_commit
# ---------------------------------------------------------------------------

class TestSafeCommit:
    """Tests for safe_commit."""

    def test_returns_true_on_success(self):
        """Returns True when commit succeeds."""
        db = _make_db()
        result = safe_commit(db)
        assert result is True
        db.commit.assert_called_once()

    def test_returns_false_on_exception(self):
        """Returns False when commit raises an exception."""
        db = _make_db()
        db.commit.side_effect = Exception("DB error")

        result = safe_commit(db)

        assert result is False

    def test_calls_rollback_on_failure(self):
        """Calls db.rollback() when commit raises."""
        db = _make_db()
        db.commit.side_effect = RuntimeError("connection lost")

        safe_commit(db)

        db.rollback.assert_called_once()

    def test_no_rollback_on_success(self):
        """db.rollback is NOT called on successful commit."""
        db = _make_db()
        safe_commit(db)
        db.rollback.assert_not_called()

    def test_handles_various_exceptions(self):
        """Works correctly for different exception types."""
        for exc_type in [ValueError, KeyError, RuntimeError, Exception]:
            db = _make_db()
            db.commit.side_effect = exc_type("error")
            result = safe_commit(db)
            assert result is False
            db.rollback.assert_called_once()
