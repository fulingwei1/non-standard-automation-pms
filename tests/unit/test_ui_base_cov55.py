# -*- coding: utf-8 -*-
"""
Tests for app/services/unified_import/base.py
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch
import pandas as pd

try:
    from app.services.unified_import.base import ImportBase
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_validate_file_valid_xlsx():
    """xlsx 文件应通过验证"""
    ImportBase.validate_file("test.xlsx")  # 不应抛出


def test_validate_file_valid_xls():
    """xls 文件应通过验证"""
    ImportBase.validate_file("test.xls")  # 不应抛出


def test_validate_file_invalid_raises():
    """非Excel文件应抛出 HTTPException"""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        ImportBase.validate_file("test.csv")
    assert exc_info.value.status_code == 400


def test_check_required_columns_all_present():
    """所有列都存在时返回空列表"""
    df = pd.DataFrame({"任务名称*": [], "项目编码*": []})
    missing = ImportBase.check_required_columns(df, ["任务名称*", "项目编码*"])
    assert missing == []


def test_check_required_columns_missing():
    """缺少列时返回缺失列列表"""
    df = pd.DataFrame({"任务名称*": []})
    missing = ImportBase.check_required_columns(df, ["任务名称*", "项目编码*"])
    assert "项目编码*" in missing


def test_parse_work_date_datetime():
    """datetime 类型应转换为 date"""
    dt = datetime(2024, 3, 15, 10, 30)
    result = ImportBase.parse_work_date(dt)
    assert result == date(2024, 3, 15)


def test_parse_work_date_date():
    """date 类型应直接返回"""
    d = date(2024, 3, 15)
    result = ImportBase.parse_work_date(d)
    assert result == d


def test_parse_hours_valid():
    """有效工时应返回对应值"""
    result = ImportBase.parse_hours(8)
    assert result == 8.0


def test_parse_hours_zero_returns_none():
    """0 工时应返回 None"""
    result = ImportBase.parse_hours(0)
    assert result is None


def test_parse_hours_too_large_returns_none():
    """超过24小时应返回 None"""
    result = ImportBase.parse_hours(25)
    assert result is None


def test_parse_file_empty_raises():
    """空文件应抛出 HTTPException"""
    from fastapi import HTTPException
    with patch("app.services.unified_import.base.ImportExportEngine") as MockEngine:
        MockEngine.parse_excel.return_value = pd.DataFrame()
        with pytest.raises(HTTPException) as exc_info:
            ImportBase.parse_file(b"fake_content")
        assert exc_info.value.status_code == 400
