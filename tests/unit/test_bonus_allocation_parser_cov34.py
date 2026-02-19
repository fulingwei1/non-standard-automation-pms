# -*- coding: utf-8 -*-
"""奖金分配表解析服务单元测试 - 第三十四批"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date, datetime

pytest.importorskip("app.services.bonus_allocation_parser")

try:
    from app.services.bonus_allocation_parser import (
        validate_file_type,
        validate_required_columns,
        get_column_value,
        parse_date,
        parse_allocation_sheet,
    )
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    validate_file_type = validate_required_columns = get_column_value = None
    parse_date = parse_allocation_sheet = None


class TestValidateFileType:
    def test_xlsx_passes(self):
        validate_file_type("report.xlsx")  # no exception

    def test_xls_passes(self):
        validate_file_type("data.xls")

    def test_csv_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_file_type("data.csv")

    def test_pdf_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_file_type("data.pdf")


class TestValidateRequiredColumns:
    def test_valid_with_calc_id(self):
        import pandas as pd
        df = pd.DataFrame(columns=["计算记录ID*", "受益人ID*", "发放金额*", "发放日期*"])
        validate_required_columns(df)  # no exception

    def test_valid_with_allocation_id(self):
        import pandas as pd
        df = pd.DataFrame(columns=["团队奖金分配ID*", "受益人ID*", "发放金额*", "发放日期*"])
        validate_required_columns(df)  # no exception

    def test_missing_id_column_raises(self):
        from fastapi import HTTPException
        import pandas as pd
        df = pd.DataFrame(columns=["受益人ID*", "发放金额*", "发放日期*"])
        with pytest.raises(HTTPException):
            validate_required_columns(df)

    def test_missing_required_col_raises(self):
        from fastapi import HTTPException
        import pandas as pd
        df = pd.DataFrame(columns=["计算记录ID*", "受益人ID*", "发放金额*"])
        # missing 发放日期*
        with pytest.raises(HTTPException):
            validate_required_columns(df)


class TestGetColumnValue:
    def test_primary_col_found(self):
        import pandas as pd
        row = pd.Series({"受益人ID*": 42, "受益人ID": None})
        assert get_column_value(row, "受益人ID*", "受益人ID") == 42

    def test_alt_col_fallback(self):
        import pandas as pd
        row = pd.Series({"受益人ID": 99})
        assert get_column_value(row, "受益人ID*", "受益人ID") == 99

    def test_missing_returns_none(self):
        import pandas as pd
        row = pd.Series({"other": 1})
        assert get_column_value(row, "受益人ID*", "受益人ID") is None


class TestParseDate:
    def test_string_date(self):
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_datetime_object(self):
        dt = datetime(2024, 3, 10, 12, 0, 0)
        result = parse_date(dt)
        assert result == date(2024, 3, 10)


class TestParseAllocationSheet:
    def test_empty_df_returns_empty(self):
        import pandas as pd
        df = pd.DataFrame(columns=["计算记录ID*", "受益人ID*", "发放金额*", "发放日期*"])
        db = MagicMock()
        valid_rows, errors = parse_allocation_sheet(df, db)
        assert valid_rows == []
        assert errors == {}
