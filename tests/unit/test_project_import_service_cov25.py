# -*- coding: utf-8 -*-
"""第二十五批 - project_import_service 单元测试"""

import pytest
import pandas as pd
from decimal import Decimal
from unittest.mock import MagicMock, patch
from datetime import date

pytest.importorskip("app.services.project_import_service")

from app.services.project_import_service import (
    validate_excel_file,
    validate_project_columns,
    get_column_value,
    parse_project_row,
    find_or_create_customer,
    find_project_manager,
    parse_date_value,
    parse_decimal_value,
)


# ── validate_excel_file ───────────────────────────────────────────────────────

class TestValidateExcelFile:
    def test_accepts_xlsx_extension(self):
        # Should not raise
        validate_excel_file("projects.xlsx")

    def test_accepts_xls_extension(self):
        validate_excel_file("projects.xls")

    def test_raises_for_csv_extension(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_excel_file("projects.csv")
        assert exc_info.value.status_code == 400

    def test_raises_for_txt_extension(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("data.txt")

    def test_raises_for_no_extension(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("datafile")


# ── validate_project_columns ──────────────────────────────────────────────────

class TestValidateProjectColumns:
    def test_accepts_starred_columns(self):
        df = pd.DataFrame({"项目编码*": ["P001"], "项目名称*": ["测试"]})
        validate_project_columns(df)  # Should not raise

    def test_accepts_unstarred_columns(self):
        df = pd.DataFrame({"项目编码": ["P001"], "项目名称": ["测试"]})
        validate_project_columns(df)  # Should not raise

    def test_raises_when_project_code_missing(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"项目名称*": ["测试"]})
        with pytest.raises(HTTPException) as exc_info:
            validate_project_columns(df)
        assert exc_info.value.status_code == 400

    def test_raises_when_project_name_missing(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"项目编码*": ["P001"]})
        with pytest.raises(HTTPException):
            validate_project_columns(df)

    def test_raises_when_both_columns_missing(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"其他列": ["值"]})
        with pytest.raises(HTTPException):
            validate_project_columns(df)


# ── get_column_value ──────────────────────────────────────────────────────────

class TestGetColumnValue:
    def test_returns_primary_col_value(self):
        row = pd.Series({"项目编码*": "P001", "项目编码": None})
        result = get_column_value(row, "项目编码*", "项目编码")
        assert result == "P001"

    def test_falls_back_to_alt_col(self):
        row = pd.Series({"项目编码": "P002"})
        result = get_column_value(row, "项目编码*", "项目编码")
        assert result == "P002"

    def test_returns_none_for_nan(self):
        row = pd.Series({"项目编码*": float("nan")})
        result = get_column_value(row, "项目编码*", "项目编码")
        assert result is None

    def test_strips_whitespace(self):
        row = pd.Series({"项目编码*": "  P003  "})
        result = get_column_value(row, "项目编码*", "项目编码")
        assert result == "P003"

    def test_default_alt_col_removes_asterisk(self):
        row = pd.Series({"项目名称": "测试项目"})
        result = get_column_value(row, "项目名称*")
        assert result == "测试项目"


# ── parse_project_row ─────────────────────────────────────────────────────────

class TestParseProjectRow:
    def test_returns_code_and_name(self):
        row = pd.Series({"项目编码*": "P001", "项目名称*": "测试项目"})
        code, name, errors = parse_project_row(row, 0)
        assert code == "P001"
        assert name == "测试项目"
        assert errors == []

    def test_returns_error_when_code_empty(self):
        row = pd.Series({"项目编码*": None, "项目名称*": "项目名"})
        code, name, errors = parse_project_row(row, 0)
        assert code is None
        assert len(errors) > 0

    def test_returns_error_when_name_empty(self):
        row = pd.Series({"项目编码*": "P001", "项目名称*": None})
        code, name, errors = parse_project_row(row, 0)
        assert name is None
        assert len(errors) > 0

    def test_returns_none_tuple_on_validation_failure(self):
        row = pd.Series({"项目编码*": float("nan"), "项目名称*": float("nan")})
        code, name, errors = parse_project_row(row, 1)
        assert code is None
        assert name is None
        assert len(errors) > 0


# ── find_or_create_customer ───────────────────────────────────────────────────

class TestFindOrCreateCustomer:
    def test_returns_none_when_no_name(self):
        db = MagicMock()
        result = find_or_create_customer(db, "")
        assert result is None

    def test_returns_none_when_name_is_none(self):
        db = MagicMock()
        result = find_or_create_customer(db, None)
        assert result is None

    def test_returns_existing_customer(self):
        db = MagicMock()
        customer = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = customer
        result = find_or_create_customer(db, "客户A")
        assert result is customer

    def test_returns_none_when_customer_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = find_or_create_customer(db, "不存在的客户")
        assert result is None


# ── find_project_manager ──────────────────────────────────────────────────────

class TestFindProjectManager:
    def test_returns_none_when_no_name(self):
        db = MagicMock()
        result = find_project_manager(db, "")
        assert result is None

    def test_returns_none_when_name_is_none(self):
        db = MagicMock()
        result = find_project_manager(db, None)
        assert result is None

    def test_finds_by_real_name(self):
        db = MagicMock()
        user = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user
        result = find_project_manager(db, "张三")
        assert result is user

    def test_falls_back_to_username(self):
        db = MagicMock()
        user = MagicMock()
        # First call (real_name) returns None, second (username) returns user
        db.query.return_value.filter.return_value.first.side_effect = [None, user]
        result = find_project_manager(db, "zhangsan")
        assert result is user


# ── parse_date_value ──────────────────────────────────────────────────────────

class TestParseDateValue:
    def test_parses_valid_date_string(self):
        result = parse_date_value("2025-06-01")
        assert result == date(2025, 6, 1)

    def test_returns_none_for_nan(self):
        result = parse_date_value(float("nan"))
        assert result is None

    def test_returns_none_for_none(self):
        result = parse_date_value(None)
        assert result is None

    def test_returns_none_for_invalid_string(self):
        result = parse_date_value("not-a-date")
        assert result is None

    def test_parses_date_object(self):
        d = date(2025, 3, 15)
        result = parse_date_value(d)
        assert result == d


# ── parse_decimal_value ───────────────────────────────────────────────────────

class TestParseDecimalValue:
    def test_parses_integer_string(self):
        result = parse_decimal_value("1000")
        assert result == Decimal("1000")

    def test_parses_float_string(self):
        result = parse_decimal_value("1234.56")
        assert result == Decimal("1234.56")

    def test_returns_none_for_nan(self):
        result = parse_decimal_value(float("nan"))
        assert result is None

    def test_returns_none_for_invalid_string(self):
        result = parse_decimal_value("not_a_number")
        assert result is None

    def test_returns_none_for_none(self):
        result = parse_decimal_value(None)
        assert result is None

    def test_parses_integer_value(self):
        result = parse_decimal_value(5000)
        assert result == Decimal("5000")

    def test_parses_float_value(self):
        result = parse_decimal_value(3.14)
        assert result is not None
        assert abs(float(result) - 3.14) < 0.001
