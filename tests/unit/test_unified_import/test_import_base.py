"""
Unit tests for unified import base service
"""

import pytest
from datetime import date, datetime
from fastapi import HTTPException
import pandas as pd

from app.services.unified_import.base import ImportBase


class TestValidateFile:
    def test_validate_file_xlsx_valid(self):
        result = ImportBase.validate_file("report.xlsx")
        assert result is None

    def test_validate_file_csv_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            ImportBase.validate_file("data.csv")
            assert exc_info.value.status_code == 400


class TestCheckRequiredColumns:
    def test_check_columns_all_present(self):
        sample_df = pd.DataFrame({
        'employee_id': [1, 2],
        'name': ['Alice', 'Bob']
        })
        required = ['employee_id', 'name']
        missing = ImportBase.check_required_columns(sample_df, required)
        assert missing == []


class TestParseWorkDate:
    @pytest.mark.parametrize("input_val,expected", [
        (date(2026, 1, 15), date(2026, 1, 15)),
        (datetime(2026, 1, 15, 10, 30), date(2026, 1, 15)),
        ("2026-01-15", date(2026, 1, 15)),
    ])
    def test_parse_work_date_valid(self, input_val, expected):
        result = ImportBase.parse_work_date(input_val)
        assert result == expected


class TestParseHours:
    @pytest.mark.parametrize("hours,expected", [
        (8.0, 8.0),
        (0, None),
        (24.0, 24.0),
    ])
    def test_parse_hours_valid(self, hours, expected):
        result = ImportBase.parse_hours(hours)
        assert result == expected

    def test_parse_hours_invalid(self):
        # parse_hours 在无效输入时抛出 ValueError
        with pytest.raises(ValueError):
            ImportBase.parse_hours("invalid")
