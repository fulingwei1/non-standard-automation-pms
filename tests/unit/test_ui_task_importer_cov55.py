# -*- coding: utf-8 -*-
"""
Tests for app/services/unified_import/task_importer.py
"""
import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

try:
    from app.services.unified_import.task_importer import TaskImporter
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


def _make_df(data):
    return pd.DataFrame(data)


def test_import_missing_required_columns(mock_db):
    """缺少必需列时应抛出 HTTPException"""
    from fastapi import HTTPException
    df = _make_df({"其他列": ["value"]})
    with pytest.raises(HTTPException) as exc_info:
        TaskImporter.import_task_data(mock_db, df, current_user_id=1)
    assert exc_info.value.status_code == 400


def test_import_empty_task_name(mock_db):
    """任务名称为空时记录到 failed_rows"""
    df = _make_df({"任务名称*": [""], "项目编码*": ["P001"]})
    imported, updated, failed = TaskImporter.import_task_data(mock_db, df, current_user_id=1)
    assert imported == 0
    assert len(failed) == 1


def test_import_project_not_found(mock_db):
    """项目不存在时记录失败"""
    df = _make_df({"任务名称*": ["Task1"], "项目编码*": ["NONEXISTENT"]})
    mock_db.query.return_value.filter.return_value.first.return_value = None
    imported, updated, failed = TaskImporter.import_task_data(mock_db, df, current_user_id=1)
    assert imported == 0
    assert len(failed) == 1
    assert "未找到项目" in failed[0]["error"]


def test_import_task_success(mock_db):
    """正常导入时计数正确"""
    df = _make_df({"任务名称*": ["Task1"], "项目编码*": ["P001"]})
    project = MagicMock()
    project.id = 1

    # First query (Project) returns project, second (Task) returns None (no existing)
    mock_db.query.return_value.filter.return_value.first.side_effect = [project, None]
    imported, updated, failed = TaskImporter.import_task_data(mock_db, df, current_user_id=1)
    assert imported == 1
    assert updated == 0
    assert failed == []


def test_import_existing_task_no_update(mock_db):
    """任务已存在且 update_existing=False 时记录失败"""
    df = _make_df({"任务名称*": ["ExistingTask"], "项目编码*": ["P001"]})
    project = MagicMock()
    project.id = 1
    existing_task = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [project, existing_task]
    imported, updated, failed = TaskImporter.import_task_data(
        mock_db, df, current_user_id=1, update_existing=False
    )
    assert imported == 0
    assert updated == 0
    assert len(failed) == 1


def test_import_existing_task_with_update(mock_db):
    """update_existing=True 时更新现有任务"""
    df = _make_df({"任务名称*": ["ExistingTask"], "项目编码*": ["P001"]})
    project = MagicMock()
    project.id = 1
    existing_task = MagicMock()
    mock_db.query.return_value.filter.return_value.first.side_effect = [project, existing_task]
    imported, updated, failed = TaskImporter.import_task_data(
        mock_db, df, current_user_id=1, update_existing=True
    )
    assert updated == 1
    assert imported == 0


def test_import_returns_tuple(mock_db):
    """返回值应为三元组"""
    df = _make_df({"任务名称*": [], "项目编码*": []})
    result = TaskImporter.import_task_data(mock_db, df, current_user_id=1)
    assert len(result) == 3
