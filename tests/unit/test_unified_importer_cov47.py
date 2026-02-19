# -*- coding: utf-8 -*-
"""
第四十七批覆盖测试 - unified_import/unified_importer.py
"""
import pytest

pytest.importorskip("app.services.unified_import.unified_importer")

from unittest.mock import MagicMock, patch

import pandas as pd
from fastapi import HTTPException

from app.services.unified_import.unified_importer import UnifiedImporter


def _make_db():
    return MagicMock()


def test_import_data_invalid_file():
    db = _make_db()
    with pytest.raises(HTTPException):
        UnifiedImporter.import_data(db, b"data", "file.txt", "USER", 1)


def test_import_data_unsupported_type():
    db = _make_db()
    with (
        patch.object(UnifiedImporter, "validate_file"),
        patch.object(UnifiedImporter, "parse_file", return_value=pd.DataFrame()),
        pytest.raises(HTTPException) as exc_info,
    ):
        UnifiedImporter.import_data(db, b"data", "file.xlsx", "UNKNOWN_TYPE", 1)
    assert exc_info.value.status_code == 400


def test_import_data_user_type():
    db = _make_db()
    df = pd.DataFrame({"col": [1]})
    with (
        patch.object(UnifiedImporter, "validate_file"),
        patch.object(UnifiedImporter, "parse_file", return_value=df),
        patch("app.services.unified_import.unified_importer.UserImporter.import_user_data",
              return_value=(2, 1, [])) as mock_user,
    ):
        result = UnifiedImporter.import_data(db, b"data", "file.xlsx", "user", 1)
    assert result["imported_count"] == 2
    assert result["updated_count"] == 1


def test_import_data_timesheet_type():
    db = _make_db()
    df = pd.DataFrame({"col": [1]})
    with (
        patch.object(UnifiedImporter, "validate_file"),
        patch.object(UnifiedImporter, "parse_file", return_value=df),
        patch("app.services.unified_import.unified_importer.TimesheetImporter.import_timesheet_data",
              return_value=(3, 0, [])),
    ):
        result = UnifiedImporter.import_data(db, b"data", "file.xlsx", "TIMESHEET", 1)
    assert result["imported_count"] == 3


def test_import_data_project_type():
    db = _make_db()
    df = pd.DataFrame({"col": [1]})
    with (
        patch.object(UnifiedImporter, "validate_file"),
        patch.object(UnifiedImporter, "parse_file", return_value=df),
        patch("app.services.project_import_service.import_projects_from_dataframe",
              return_value=(5, 0, [])),
    ):
        result = UnifiedImporter.import_data(db, b"data", "file.xlsx", "PROJECT", 1)
    assert result["imported_count"] == 5


def test_import_data_failed_rows_capped():
    """返回的 failed_rows 最多20条"""
    db = _make_db()
    df = pd.DataFrame({"col": [1]})
    many_errors = [{"row_index": i, "error": "err"} for i in range(30)]
    with (
        patch.object(UnifiedImporter, "validate_file"),
        patch.object(UnifiedImporter, "parse_file", return_value=df),
        patch("app.services.unified_import.unified_importer.UserImporter.import_user_data",
              return_value=(0, 0, many_errors)),
    ):
        result = UnifiedImporter.import_data(db, b"data", "file.xlsx", "USER", 1)
    assert len(result["failed_rows"]) == 20
    assert result["failed_count"] == 30


def test_import_data_bom_type():
    db = _make_db()
    df = pd.DataFrame({"col": [1]})
    with (
        patch.object(UnifiedImporter, "validate_file"),
        patch.object(UnifiedImporter, "parse_file", return_value=df),
        patch("app.services.unified_import.unified_importer.BomImporter.import_bom_data",
              return_value=(1, 0, [])),
    ):
        result = UnifiedImporter.import_data(db, b"data", "file.xlsx", "BOM", 1)
    assert result["imported_count"] == 1
