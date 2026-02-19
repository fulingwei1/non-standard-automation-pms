# -*- coding: utf-8 -*-
"""
Unit tests for app/services/strategy/annual_work_service/crud.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.strategy.annual_work_service.crud import (
        create_annual_work,
        get_annual_work,
        list_annual_works,
        update_annual_work,
        delete_annual_work,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_create_data():
    d = MagicMock()
    d.csf_id = 1
    d.code = "AW001"
    d.name = "Test Work"
    d.description = "Description"
    d.voc_source = None
    d.pain_point = None
    d.solution = None
    d.year = 2024
    d.priority = 1
    d.start_date = None
    d.end_date = None
    d.owner_dept_id = None
    d.owner_user_id = None
    return d


# ---------------------------------------------------------------------------
# create_annual_work
# ---------------------------------------------------------------------------

def test_create_annual_work_adds_and_commits():
    db = MagicMock()
    data = _make_create_data()
    create_annual_work(db, data)
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


# ---------------------------------------------------------------------------
# get_annual_work
# ---------------------------------------------------------------------------

def test_get_annual_work_found():
    db = MagicMock()
    mock_work = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = mock_work
    result = get_annual_work(db, work_id=1)
    assert result is mock_work


def test_get_annual_work_not_found():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = get_annual_work(db, work_id=999)
    assert result is None


# ---------------------------------------------------------------------------
# update_annual_work
# ---------------------------------------------------------------------------

def test_update_annual_work_not_found_returns_none():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    update_data = MagicMock()
    update_data.model_dump.return_value = {}
    result = update_annual_work(db, work_id=999, data=update_data)
    assert result is None


def test_update_annual_work_applies_fields():
    db = MagicMock()
    work_mock = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = work_mock
    update_data = MagicMock()
    update_data.model_dump.return_value = {"name": "Updated Name", "priority": 2}
    update_annual_work(db, work_id=1, data=update_data)
    assert work_mock.name == "Updated Name"
    assert work_mock.priority == 2
    db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# delete_annual_work
# ---------------------------------------------------------------------------

def test_delete_annual_work_not_found_returns_false():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = delete_annual_work(db, work_id=999)
    assert result is False


def test_delete_annual_work_soft_deletes():
    db = MagicMock()
    work_mock = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = work_mock
    result = delete_annual_work(db, work_id=1)
    assert result is True
    assert work_mock.is_active is False
    db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# list_annual_works
# ---------------------------------------------------------------------------

def test_list_annual_works_returns_items_and_total():
    db = MagicMock()
    mock_items = [MagicMock(), MagicMock()]
    q = MagicMock()
    q.filter.return_value = q
    q.join.return_value = q
    q.count.return_value = 2
    q.order_by.return_value = q
    db.query.return_value = q
    with patch("app.services.strategy.annual_work_service.crud.apply_pagination") as mock_pag:
        mock_pag.return_value.all.return_value = mock_items
        items, total = list_annual_works(db)
    assert total == 2
    assert items == mock_items
