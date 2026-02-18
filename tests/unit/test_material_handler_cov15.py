# -*- coding: utf-8 -*-
"""第十五批: status_handlers/material_handler 单元测试"""
import pytest

pytest.importorskip("app.services.status_handlers.material_handler")

from unittest.mock import MagicMock
from app.services.status_handlers.material_handler import MaterialStatusHandler


def make_handler():
    db = MagicMock()
    return MaterialStatusHandler(db), db


def test_handle_bom_published_project_not_found():
    handler, db = make_handler()
    db.query.return_value.filter.return_value.first.return_value = None
    result = handler.handle_bom_published(99)
    assert result is False


def test_handle_bom_published_wrong_stage():
    handler, db = make_handler()
    project = MagicMock()
    project.stage = "S3"
    db.query.return_value.filter.return_value.first.return_value = project
    result = handler.handle_bom_published(1)
    assert result is False


def test_handle_bom_published_success():
    handler, db = make_handler()
    project = MagicMock()
    project.stage = "S4"
    project.status = "ST10"
    db.query.return_value.filter.return_value.first.return_value = project
    result = handler.handle_bom_published(1)
    assert result is True
    assert project.stage == "S5"
    assert project.status == "ST12"
    db.commit.assert_called_once()


def test_handle_material_shortage_not_found():
    handler, db = make_handler()
    db.query.return_value.filter.return_value.first.return_value = None
    result = handler.handle_material_shortage(99)
    assert result is False


def test_handle_material_shortage_non_critical():
    handler, db = make_handler()
    project = MagicMock()
    project.stage = "S5"
    db.query.return_value.filter.return_value.first.return_value = project
    # is_critical=False should return False
    result = handler.handle_material_shortage(1, is_critical=False)
    assert result is False


def test_handle_material_shortage_success():
    handler, db = make_handler()
    project = MagicMock()
    project.stage = "S5"
    project.status = "ST12"
    project.health = "H1"
    db.query.return_value.filter.return_value.first.return_value = project
    result = handler.handle_material_shortage(1, is_critical=True)
    assert result is True
    assert project.status == "ST14"
    assert project.health == "H3"
    db.commit.assert_called()


def test_log_status_change_with_callback():
    handler, db = make_handler()
    mock_callback = MagicMock()
    handler._log_status_change(
        project_id=1,
        old_stage="S4",
        new_stage="S5",
        old_status="ST10",
        new_status="ST12",
        change_type="BOM_PUBLISHED",
        log_status_change=mock_callback,
    )
    mock_callback.assert_called_once()


def test_log_status_change_without_callback():
    handler, db = make_handler()
    handler._log_status_change(
        project_id=1,
        old_stage="S4",
        new_stage="S5",
        old_status="ST10",
        new_status="ST12",
        change_type="BOM_PUBLISHED",
        log_status_change=None,
    )
    db.add.assert_called_once()
