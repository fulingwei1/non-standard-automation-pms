# -*- coding: utf-8 -*-
"""奖金分配表解析服务测试"""
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.services.bonus_allocation_parser import (
    validate_file_type, parse_excel_file, validate_required_columns,
    get_column_value, parse_date, validate_row_data,
    parse_allocation_sheet,
)


class TestValidateFileType:
    def test_valid(self):
        validate_file_type("test.xlsx")

    def test_invalid(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_file_type("test.csv")


class TestParseExcelFile:
    def test_valid(self):
        import io
        # Create a minimal Excel in memory
        df = pd.DataFrame({"A": [1, 2]})
        buf = io.BytesIO()
        df.to_excel(buf, index=False)
        result = parse_excel_file(buf.getvalue())
        assert len(result) == 2

    def test_invalid(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            parse_excel_file(b"not an excel file")


class TestValidateRequiredColumns:
    def test_valid_with_calc_id(self):
        df = pd.DataFrame({
            "计算记录ID*": [1], "受益人ID*": [1],
            "发放金额*": [100], "发放日期*": ["2026-01-01"]
        })
        validate_required_columns(df)

    def test_valid_with_allocation_id(self):
        df = pd.DataFrame({
            "团队奖金分配ID*": [1], "受益人ID*": [1],
            "发放金额*": [100], "发放日期*": ["2026-01-01"]
        })
        validate_required_columns(df)

    def test_missing_id_column(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"受益人ID*": [1], "发放金额*": [100], "发放日期*": ["2026-01-01"]})
        with pytest.raises(HTTPException):
            validate_required_columns(df)


class TestGetColumnValue:
    def test_primary(self):
        row = pd.Series({"计算记录ID*": 1})
        assert get_column_value(row, "计算记录ID*") == 1

    def test_alt(self):
        row = pd.Series({"计算记录ID": 1})
        assert get_column_value(row, "计算记录ID*") == 1


class TestParseDate:
    def test_string(self):
        result = parse_date("2026-01-15")
        assert result == date(2026, 1, 15)

    def test_datetime(self):
        result = parse_date(datetime(2026, 1, 15))
        assert result == date(2026, 1, 15)


class TestValidateRowData:
    def test_valid(self):
        db = MagicMock()
        calc = MagicMock()
        user = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [calc, user]
        errors = validate_row_data(db, 1, None, 1, Decimal("100"), Decimal("100"))
        assert errors == []

    def test_missing_calc(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [None, MagicMock()]
        errors = validate_row_data(db, 999, None, 1, Decimal("100"), Decimal("100"))
        assert len(errors) > 0

    def test_missing_user(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [MagicMock(), None]
        errors = validate_row_data(db, 1, None, 999, Decimal("100"), Decimal("100"))
        assert len(errors) > 0


class TestParseAllocationSheet:
    def test_empty(self):
        db = MagicMock()
        df = pd.DataFrame({
            "计算记录ID*": [], "受益人ID*": [],
            "发放金额*": [], "发放日期*": []
        })
        valid, errors = parse_allocation_sheet(df, db)
        assert valid == []
        assert errors == {}
