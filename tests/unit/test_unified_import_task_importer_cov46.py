# -*- coding: utf-8 -*-
"""第四十六批 - 统一导入任务导入器单元测试"""
import pytest

pytest.importorskip("app.services.unified_import.task_importer",
                    reason="依赖不满足，跳过")

import pandas as pd
from decimal import Decimal
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.services.unified_import.task_importer import TaskImporter


def _make_db(project=None):
    db = MagicMock()
    call_count = [0]

    def query_side(model):
        call_count[0] += 1
        q = MagicMock()
        name = getattr(model, '__name__', str(model))
        if 'Project' in name:
            q.filter.return_value.first.return_value = project
        elif 'User' in name:
            q.filter.return_value.first.return_value = None
        elif 'Task' in name:
            q.filter.return_value.first.return_value = None
        return q

    db.query.side_effect = query_side
    return db


def _make_valid_df(rows=None):
    rows = rows or [{"任务名称*": "任务A", "项目编码*": "P001"}]
    return pd.DataFrame(rows)


class TestImportTaskData:
    def test_raises_on_missing_required_columns(self):
        db = _make_db()
        df = pd.DataFrame({"其他列": ["value"]})
        with pytest.raises(HTTPException) as exc:
            TaskImporter.import_task_data(db, df, current_user_id=1)
        assert exc.value.status_code == 400

    def test_project_not_found_goes_to_failed(self):
        db = _make_db(project=None)
        df = _make_valid_df()
        imported, updated, failed = TaskImporter.import_task_data(db, df, current_user_id=1)
        assert imported == 0
        assert len(failed) == 1
        assert "未找到项目" in failed[0]["error"]

    def test_creates_task_when_project_found(self):
        project = MagicMock()
        project.id = 10
        db = _make_db(project=project)
        df = _make_valid_df()
        imported, updated, failed = TaskImporter.import_task_data(db, df, current_user_id=1)
        assert imported == 1
        assert updated == 0
        assert failed == []
        db.add.assert_called_once()

    def test_empty_task_name_goes_to_failed(self):
        project = MagicMock()
        project.id = 10
        db = _make_db(project=project)
        df = pd.DataFrame([{"任务名称*": "", "项目编码*": "P001"}])
        imported, updated, failed = TaskImporter.import_task_data(db, df, current_user_id=1)
        assert imported == 0
        assert len(failed) == 1

    def test_existing_task_goes_to_failed_without_update_flag(self):
        project = MagicMock()
        project.id = 10
        db = MagicMock()

        existing_task = MagicMock()
        call_count = [0]

        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            name = getattr(model, '__name__', str(model))
            if 'Project' in name:
                q.filter.return_value.first.return_value = project
            elif 'User' in name:
                q.filter.return_value.first.return_value = None
            elif 'Task' in name:
                q.filter.return_value.first.return_value = existing_task
            return q

        db.query.side_effect = query_side

        df = _make_valid_df()
        imported, updated, failed = TaskImporter.import_task_data(
            db, df, current_user_id=1, update_existing=False
        )
        assert "已存在" in failed[0]["error"]

    def test_updates_existing_task_with_update_flag(self):
        project = MagicMock()
        project.id = 10
        db = MagicMock()

        existing_task = MagicMock()
        call_count = [0]

        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            name = getattr(model, '__name__', str(model))
            if 'Project' in name:
                q.filter.return_value.first.return_value = project
            elif 'User' in name:
                q.filter.return_value.first.return_value = None
            elif 'Task' in name:
                q.filter.return_value.first.return_value = existing_task
            return q

        db.query.side_effect = query_side

        df = _make_valid_df()
        imported, updated, failed = TaskImporter.import_task_data(
            db, df, current_user_id=1, update_existing=True
        )
        assert updated == 1
        assert failed == []

    def test_weight_default_is_one(self):
        project = MagicMock()
        project.id = 10
        db = _make_db(project=project)
        df = _make_valid_df()
        TaskImporter.import_task_data(db, df, current_user_id=1)
        added = db.add.call_args[0][0]
        assert added.weight == Decimal("1.00")
