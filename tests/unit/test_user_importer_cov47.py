# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - unified_import/user_importer.py
"""
import pytest

pytest.importorskip("app.services.unified_import.user_importer")

from unittest.mock import MagicMock, patch

import pandas as pd

from app.services.unified_import.user_importer import UserImporter


def test_import_user_data_success():
    db = MagicMock()
    df = pd.DataFrame({"姓名": ["张三"]})
    mock_result = {"imported": 1, "updated": 0, "errors": []}
    with patch(
        "app.services.unified_import.user_importer.import_employees_from_dataframe",
        return_value=mock_result,
    ):
        imported, updated, failed = UserImporter.import_user_data(db, df, current_user_id=1)
    assert imported == 1
    assert updated == 0
    assert failed == []


def test_import_user_data_with_errors():
    db = MagicMock()
    df = pd.DataFrame({"姓名": ["张三"]})
    mock_result = {"imported": 0, "updated": 0, "errors": ["手机号格式错误", "邮箱重复"]}
    with patch(
        "app.services.unified_import.user_importer.import_employees_from_dataframe",
        return_value=mock_result,
    ):
        imported, updated, failed = UserImporter.import_user_data(db, df, current_user_id=1)
    assert imported == 0
    assert len(failed) == 2
    assert failed[0]["row_index"] == 2


def test_import_user_data_exception():
    db = MagicMock()
    df = pd.DataFrame({"姓名": ["张三"]})
    with patch(
        "app.services.unified_import.user_importer.import_employees_from_dataframe",
        side_effect=RuntimeError("DB error"),
    ):
        imported, updated, failed = UserImporter.import_user_data(db, df, current_user_id=1)
    assert imported == 0
    assert updated == 0
    assert len(failed) == 1
    assert "DB error" in failed[0]["error"]


def test_import_user_data_update_existing():
    db = MagicMock()
    df = pd.DataFrame({"姓名": ["李四"]})
    mock_result = {"imported": 0, "updated": 1, "errors": []}
    with patch(
        "app.services.unified_import.user_importer.import_employees_from_dataframe",
        return_value=mock_result,
    ):
        imported, updated, failed = UserImporter.import_user_data(
            db, df, current_user_id=1, update_existing=True
        )
    assert updated == 1


def test_import_user_data_empty_df():
    db = MagicMock()
    df = pd.DataFrame()
    mock_result = {"imported": 0, "updated": 0, "errors": []}
    with patch(
        "app.services.unified_import.user_importer.import_employees_from_dataframe",
        return_value=mock_result,
    ):
        imported, updated, failed = UserImporter.import_user_data(db, df, current_user_id=1)
    assert imported == 0
    assert failed == []
