# -*- coding: utf-8 -*-
"""
Tests for app/utils/db_helpers.py
Uses MagicMock to simulate SQLAlchemy Session – no real DB needed.
"""
import pytest
from unittest.mock import MagicMock, patch, call
from fastapi import HTTPException

from app.utils.db_helpers import (
    get_or_404,
    save_obj,
    delete_obj,
    update_obj,
    safe_commit,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db():
    db = MagicMock()
    return db


def _make_model_class(name="MockModel"):
    """Create a fake SQLAlchemy-like model class."""
    model_cls = MagicMock()
    model_cls.__name__ = name
    # Simulate attribute access for filtering
    model_cls.id = MagicMock()
    model_cls.code = MagicMock()
    return model_cls


def _make_obj(**attrs):
    obj = MagicMock()
    for k, v in attrs.items():
        setattr(obj, k, v)
    return obj


# ---------------------------------------------------------------------------
# get_or_404
# ---------------------------------------------------------------------------

class TestGetOr404:
    def test_found_returns_object(self):
        db = _make_db()
        model = _make_model_class()
        expected = _make_obj(id=1)
        db.query.return_value.filter.return_value.first.return_value = expected

        result = get_or_404(db, model, 1)
        assert result is expected

    def test_not_found_raises_404(self):
        db = _make_db()
        model = _make_model_class()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db, model, 99)
        assert exc_info.value.status_code == 404

    def test_default_detail_message(self):
        db = _make_db()
        model = _make_model_class("Project")
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db, model, 5)
        assert "Project" in exc_info.value.detail
        assert "5" in exc_info.value.detail

    def test_custom_detail_message(self):
        db = _make_db()
        model = _make_model_class()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_or_404(db, model, 5, detail="Custom error")
        assert exc_info.value.detail == "Custom error"

    def test_custom_id_field(self):
        db = _make_db()
        model = _make_model_class()
        expected = _make_obj(code="ABC")
        db.query.return_value.filter.return_value.first.return_value = expected

        result = get_or_404(db, model, "ABC", id_field="code")
        assert result is expected


# ---------------------------------------------------------------------------
# save_obj
# ---------------------------------------------------------------------------

class TestSaveObj:
    def test_add_commit_refresh_called(self):
        db = _make_db()
        obj = _make_obj()

        result = save_obj(db, obj)

        db.add.assert_called_once_with(obj)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(obj)
        assert result is obj

    def test_no_refresh_when_disabled(self):
        db = _make_db()
        obj = _make_obj()

        save_obj(db, obj, refresh=False)

        db.add.assert_called_once_with(obj)
        db.commit.assert_called_once()
        db.refresh.assert_not_called()

    def test_returns_obj(self):
        db = _make_db()
        obj = _make_obj(id=42)
        result = save_obj(db, obj)
        assert result is obj


# ---------------------------------------------------------------------------
# delete_obj
# ---------------------------------------------------------------------------

class TestDeleteObj:
    def test_delete_and_commit_called(self):
        db = _make_db()
        obj = _make_obj()

        delete_obj(db, obj)

        db.delete.assert_called_once_with(obj)
        db.commit.assert_called_once()

    def test_returns_none(self):
        db = _make_db()
        obj = _make_obj()
        result = delete_obj(db, obj)
        assert result is None


# ---------------------------------------------------------------------------
# update_obj
# ---------------------------------------------------------------------------

class TestUpdateObj:
    def test_updates_existing_fields(self):
        db = _make_db()
        obj = MagicMock()
        obj.name = "old_name"
        obj.status = "draft"

        update_obj(db, obj, {"name": "new_name", "status": "active"})

        assert obj.name == "new_name"
        assert obj.status == "active"

    def test_ignores_missing_fields(self):
        db = _make_db()
        obj = MagicMock(spec=["name"])
        obj.name = "test"

        # "nonexistent" not in spec → hasattr returns False → should be ignored
        update_obj(db, obj, {"name": "updated", "nonexistent": "value"})
        assert obj.name == "updated"

    def test_calls_save_obj(self):
        db = _make_db()
        obj = MagicMock()

        with patch("app.utils.db_helpers.save_obj") as mock_save:
            mock_save.return_value = obj
            result = update_obj(db, obj, {"name": "new"})

        mock_save.assert_called_once_with(db, obj, refresh=True)
        assert result is obj

    def test_refresh_false_passed_through(self):
        db = _make_db()
        obj = MagicMock()

        with patch("app.utils.db_helpers.save_obj") as mock_save:
            mock_save.return_value = obj
            update_obj(db, obj, {}, refresh=False)

        mock_save.assert_called_once_with(db, obj, refresh=False)


# ---------------------------------------------------------------------------
# safe_commit
# ---------------------------------------------------------------------------

class TestSafeCommit:
    def test_success_returns_true(self):
        db = _make_db()
        assert safe_commit(db) is True
        db.commit.assert_called_once()

    def test_failure_rolls_back_and_returns_false(self):
        db = _make_db()
        db.commit.side_effect = Exception("DB error")

        result = safe_commit(db)

        assert result is False
        db.rollback.assert_called_once()

    def test_no_exception_no_rollback(self):
        db = _make_db()
        safe_commit(db)
        db.rollback.assert_not_called()
