# -*- coding: utf-8 -*-
"""
第十四批：奖金分配表解析服务 单元测试
"""
import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock, patch
import pandas as pd

try:
    from app.services import bonus_allocation_parser as parser
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败，跳过")


class TestBonusAllocationParser:
    def test_validate_file_type_valid(self):
        parser.validate_file_type("sheet.xlsx")  # 不抛出

    def test_validate_file_type_invalid(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            parser.validate_file_type("sheet.csv")

    def test_validate_file_type_xls(self):
        parser.validate_file_type("data.xls")  # 不抛出

    def test_get_column_value_primary(self):
        row = pd.Series({"受益人ID*": 101, "受益人ID": None})
        result = parser.get_column_value(row, "受益人ID*", "受益人ID")
        assert result == 101

    def test_get_column_value_alt(self):
        row = pd.Series({"受益人ID": 202})
        result = parser.get_column_value(row, "受益人ID*", "受益人ID")
        assert result == 202

    def test_parse_date_string(self):
        d = parser.parse_date("2025-06-15")
        assert d == date(2025, 6, 15)

    def test_parse_date_datetime(self):
        from datetime import datetime
        dt = datetime(2025, 6, 15, 12, 0)
        d = parser.parse_date(dt)
        assert d == date(2025, 6, 15)

    def test_validate_required_columns_missing_id(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"受益人ID*": [], "发放金额*": [], "发放日期*": []})
        with pytest.raises(HTTPException) as exc_info:
            parser.validate_required_columns(df)
        assert "计算记录ID" in str(exc_info.value.detail)

    def test_validate_required_columns_ok_with_calc_id(self):
        df = pd.DataFrame({"计算记录ID*": [], "受益人ID*": [], "发放金额*": [], "发放日期*": []})
        parser.validate_required_columns(df)  # 不抛出

    def test_validate_row_data_missing_user(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        errors = parser.validate_row_data(db, calc_id=1, team_allocation_id=None, user_id=999,
                                           calc_amount=Decimal("1000"), dist_amount=Decimal("900"))
        assert any("受益人ID" in e for e in errors)

    def test_parse_allocation_sheet_empty(self):
        db = MagicMock()
        df = pd.DataFrame()
        valid, errors = parser.parse_allocation_sheet(df, db)
        assert valid == []
        assert errors == {}
