# -*- coding: utf-8 -*-
import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock
import pandas as pd
from fastapi import HTTPException

from app.services.unified_import.base import ImportBase


class TestImportBase:
    def test_validate_file_xlsx(self):
        ImportBase.validate_file("test.xlsx")  # no exception

    def test_validate_file_xls(self):
        ImportBase.validate_file("test.xls")  # no exception

    def test_validate_file_invalid(self):
        with pytest.raises(HTTPException):
            ImportBase.validate_file("test.csv")

    def test_parse_file_success(self):
        import io
        df = pd.DataFrame({"a": [1, 2]})
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        result = ImportBase.parse_file(buf.getvalue())
        assert len(result) == 2

    def test_parse_file_empty(self):
        import io
        df = pd.DataFrame()
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        with pytest.raises(HTTPException):
            ImportBase.parse_file(buf.getvalue())

    def test_parse_file_invalid_bytes(self):
        with pytest.raises(HTTPException):
            ImportBase.parse_file(b"not excel")

    def test_check_required_columns_all_present(self):
        df = pd.DataFrame({"A": [], "B": []})
        assert ImportBase.check_required_columns(df, ["A", "B"]) == []

    def test_check_required_columns_missing(self):
        df = pd.DataFrame({"A": []})
        assert ImportBase.check_required_columns(df, ["A", "C"]) == ["C"]

    def test_parse_work_date_datetime(self):
        dt = datetime(2025, 1, 15, 10, 30)
        assert ImportBase.parse_work_date(dt) == date(2025, 1, 15)

    def test_parse_work_date_date(self):
        d = date(2025, 1, 15)
        assert ImportBase.parse_work_date(d) == d

    def test_parse_work_date_string(self):
        assert ImportBase.parse_work_date("2025-01-15") == date(2025, 1, 15)

    def test_parse_hours_valid(self):
        assert ImportBase.parse_hours(8.0) == 8.0

    def test_parse_hours_zero(self):
        assert ImportBase.parse_hours(0) is None

    def test_parse_hours_over_24(self):
        assert ImportBase.parse_hours(25) is None

    def test_parse_progress_valid(self):
        row = pd.Series({"progress": 50.0})
        assert ImportBase.parse_progress(row, "progress") == 50.0

    def test_parse_progress_nan(self):
        row = pd.Series({"progress": float("nan")})
        assert ImportBase.parse_progress(row, "progress") is None

    def test_parse_progress_out_of_range(self):
        row = pd.Series({"progress": 150.0})
        assert ImportBase.parse_progress(row, "progress") is None

    def test_parse_progress_missing_column(self):
        row = pd.Series({"other": 1})
        assert ImportBase.parse_progress(row, "progress") is None
