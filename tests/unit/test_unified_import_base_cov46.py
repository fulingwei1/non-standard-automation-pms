# -*- coding: utf-8 -*-
"""第四十六批 - 统一导入基础工具单元测试"""
import pytest
from datetime import date, datetime

pytest.importorskip("app.services.unified_import.base",
                    reason="依赖不满足，跳过")

import pandas as pd
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.services.unified_import.base import ImportBase


class TestValidateFile:
    def test_accepts_xlsx(self):
        ImportBase.validate_file("report.xlsx")  # should not raise

    def test_accepts_xls(self):
        ImportBase.validate_file("data.xls")  # should not raise

    def test_rejects_csv(self):
        with pytest.raises(HTTPException) as exc_info:
            ImportBase.validate_file("data.csv")
        assert exc_info.value.status_code == 400

    def test_rejects_txt(self):
        with pytest.raises(HTTPException):
            ImportBase.validate_file("data.txt")


class TestCheckRequiredColumns:
    def test_returns_empty_when_all_present(self):
        df = pd.DataFrame(columns=["任务名称", "项目编码"])
        missing = ImportBase.check_required_columns(df, ["任务名称*", "项目编码*"])
        assert missing == []

    def test_returns_missing_columns(self):
        df = pd.DataFrame(columns=["任务名称"])
        missing = ImportBase.check_required_columns(df, ["任务名称*", "项目编码*"])
        assert "项目编码*" in missing


class TestParseWorkDate:
    def test_datetime_returns_date(self):
        dt = datetime(2024, 3, 15, 10, 0, 0)
        result = ImportBase.parse_work_date(dt)
        assert result == date(2024, 3, 15)

    def test_date_returned_as_is(self):
        d = date(2024, 3, 15)
        result = ImportBase.parse_work_date(d)
        assert result == d

    def test_string_parsed(self):
        result = ImportBase.parse_work_date("2024-03-15")
        assert result == date(2024, 3, 15)


class TestParseHours:
    def test_valid_hours_returned(self):
        result = ImportBase.parse_hours(8.0)
        assert result == 8.0

    def test_zero_returns_none(self):
        result = ImportBase.parse_hours(0)
        assert result is None

    def test_over_24_returns_none(self):
        result = ImportBase.parse_hours(25)
        assert result is None

    def test_boundary_24_accepted(self):
        result = ImportBase.parse_hours(24)
        assert result == 24.0


class TestParseProgress:
    def test_valid_progress_returned(self):
        row = pd.Series({"进度(%)": 75.0})
        result = ImportBase.parse_progress(row, "进度(%)")
        assert result == 75.0

    def test_nan_returns_none(self):
        row = pd.Series({"进度(%)": float("nan")})
        result = ImportBase.parse_progress(row, "进度(%)")
        assert result is None

    def test_out_of_range_returns_none(self):
        row = pd.Series({"进度(%)": 150.0})
        result = ImportBase.parse_progress(row, "进度(%)")
        assert result is None
