# -*- coding: utf-8 -*-
"""
Tests for bonus_allocation_parser - testing actual exported functions
"""

import pytest
from datetime import date, datetime
from fastapi import HTTPException

import pandas as pd

from app.services.bonus_allocation_parser import (
    validate_file_type,
    parse_date,
    validate_required_columns,
)


class TestValidateFileType:
    """Test suite for validate_file_type function."""

    def test_validate_xlsx_file(self):
        """Test validating .xlsx file type - should not raise."""
        validate_file_type("bonus.xlsx")

    def test_validate_xls_file(self):
        """Test validating .xls file type - should not raise."""
        validate_file_type("bonus.xls")

    def test_validate_invalid_file_type(self):
        """Test validating invalid file type raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_type("bonus.txt")
        assert exc_info.value.status_code == 400

    def test_validate_empty_filename(self):
        """Test validating empty filename raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_type("")
        assert exc_info.value.status_code == 400


class TestParseDate:
    """Test suite for parse_date function."""

    def test_parse_standard_date(self):
        """Test parsing standard date format."""
        result = parse_date("2025-01-21")
        assert result == date(2025, 1, 21)

    def test_parse_datetime_object(self):
        """Test parsing datetime object."""
        dt = datetime(2025, 6, 15, 10, 30)
        result = parse_date(dt)
        assert result == date(2025, 6, 15)

    def test_parse_none_date(self):
        """Test parsing None value returns NaT (pandas Not a Time)."""
        result = parse_date(None)
        assert pd.isna(result)

    def test_parse_empty_string(self):
        """Test parsing empty string raises an error."""
        with pytest.raises((ValueError, TypeError)):
            parse_date("")


class TestValidateRequiredColumns:
    """Test suite for validate_required_columns function."""

    def test_validate_with_required_columns_present(self):
        """Test validation passes when required columns exist."""
        df = pd.DataFrame(columns=["计算记录ID*", "受益人ID*", "发放金额*", "发放日期*"])
        # Should not raise
        validate_required_columns(df)

    def test_validate_with_missing_columns(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame(columns=["无关列"])
        with pytest.raises(HTTPException) as exc_info:
            validate_required_columns(df)
        assert exc_info.value.status_code == 400
