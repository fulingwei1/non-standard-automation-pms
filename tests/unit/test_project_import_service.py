# -*- coding: utf-8 -*-
"""项目导入服务测试"""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.services.project_import_service import (
    validate_excel_file, parse_excel_data, validate_project_columns,
    get_column_value, parse_project_row, find_or_create_customer,
    find_project_manager, parse_date_value, parse_decimal_value,
    import_projects_from_dataframe,
)


class TestValidateExcelFile:
    def test_valid(self):
        validate_excel_file("test.xlsx")

    def test_invalid(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("test.csv")


class TestValidateProjectColumns:
    def test_valid(self):
        df = pd.DataFrame({"项目编码*": [], "项目名称*": []})
        validate_project_columns(df)

    def test_alt_columns(self):
        df = pd.DataFrame({"项目编码": [], "项目名称": []})
        validate_project_columns(df)

    def test_missing(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"其他": []})
        with pytest.raises(HTTPException):
            validate_project_columns(df)


class TestGetColumnValue:
    def test_primary(self):
        row = pd.Series({"项目编码*": "P001"})
        assert get_column_value(row, "项目编码*") == "P001"

    def test_alt(self):
        row = pd.Series({"项目编码": "P001"})
        assert get_column_value(row, "项目编码*") == "P001"

    def test_nan(self):
        import numpy as np
        row = pd.Series({"项目编码*": np.nan})
        assert get_column_value(row, "项目编码*") is None


class TestParseProjectRow:
    def test_valid(self):
        row = pd.Series({"项目编码*": "P001", "项目名称*": "Test"})
        code, name, errors = parse_project_row(row, 0)
        assert code == "P001"
        assert name == "Test"
        assert errors == []

    def test_missing(self):
        import numpy as np
        row = pd.Series({"项目编码*": np.nan, "项目名称*": np.nan})
        code, name, errors = parse_project_row(row, 0)
        assert len(errors) > 0


class TestParseDateValue:
    def test_valid(self):
        result = parse_date_value("2026-01-15")
        assert result == date(2026, 1, 15)

    def test_nan(self):
        import numpy as np
        assert parse_date_value(np.nan) is None

    def test_invalid(self):
        assert parse_date_value("not-a-date") is None


class TestParseDecimalValue:
    def test_valid(self):
        assert parse_decimal_value("100.50") == Decimal("100.50")

    def test_nan(self):
        import numpy as np
        assert parse_decimal_value(np.nan) is None

    def test_invalid(self):
        assert parse_decimal_value("abc") is None


class TestFindOrCreateCustomer:
    def test_found(self):
        db = MagicMock()
        customer = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = customer
        assert find_or_create_customer(db, "Test") == customer

    def test_empty_name(self):
        assert find_or_create_customer(MagicMock(), "") is None


class TestFindProjectManager:
    def test_found_by_name(self):
        db = MagicMock()
        user = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = user
        assert find_project_manager(db, "Alice") == user

    def test_empty(self):
        assert find_project_manager(MagicMock(), "") is None


class TestImportProjects:
    def test_empty_dataframe(self):
        db = MagicMock()
        df = pd.DataFrame({"项目编码*": [], "项目名称*": []})
        imported, updated, failed = import_projects_from_dataframe(db, df, False)
        assert imported == 0
        assert updated == 0

    def test_missing_code(self):
        db = MagicMock()
        import numpy as np
        df = pd.DataFrame({"项目编码*": [np.nan], "项目名称*": [np.nan]})
        imported, updated, failed = import_projects_from_dataframe(db, df, False)
        assert len(failed) == 1
