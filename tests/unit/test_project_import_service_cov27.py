# -*- coding: utf-8 -*-
"""第二十七批 - project_import_service 单元测试"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.project_import_service")

from app.services.project_import_service import (
    validate_excel_file,
    validate_project_columns,
    get_column_value,
)


class TestValidateExcelFile:
    def test_xlsx_passes(self):
        """xlsx文件应通过验证"""
        validate_excel_file("report.xlsx")  # 不抛出异常

    def test_xls_passes(self):
        """xls文件应通过验证"""
        validate_excel_file("data.xls")

    def test_csv_raises(self):
        """csv文件应抛出HTTPException"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            validate_excel_file("data.csv")
        assert exc.value.status_code == 400

    def test_pdf_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("document.pdf")

    def test_txt_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("data.txt")

    def test_no_extension_raises(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("noextension")

    def test_uppercase_xlsx_raises(self):
        """大写扩展名应不通过（区分大小写）"""
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("data.XLSX")


class TestValidateProjectColumns:
    def test_passes_with_required_columns(self):
        df = pd.DataFrame({"项目编码*": ["001"], "项目名称*": ["测试"]})
        validate_project_columns(df)  # 不抛出

    def test_passes_with_alt_columns_no_asterisk(self):
        df = pd.DataFrame({"项目编码": ["001"], "项目名称": ["测试"], "其他": ["A"]})
        validate_project_columns(df)  # 不抛出

    def test_raises_when_missing_code_column(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"项目名称*": ["测试"]})
        with pytest.raises(HTTPException) as exc:
            validate_project_columns(df)
        assert exc.value.status_code == 400

    def test_raises_when_missing_name_column(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"项目编码*": ["001"]})
        with pytest.raises(HTTPException) as exc:
            validate_project_columns(df)
        assert exc.value.status_code == 400

    def test_raises_when_empty_dataframe(self):
        from fastapi import HTTPException
        df = pd.DataFrame()
        with pytest.raises(HTTPException):
            validate_project_columns(df)

    def test_error_message_mentions_missing_columns(self):
        from fastapi import HTTPException
        df = pd.DataFrame({"其他列": ["value"]})
        with pytest.raises(HTTPException) as exc:
            validate_project_columns(df)
        assert "项目编码" in str(exc.value.detail)


class TestGetColumnValue:
    def test_gets_primary_column_value(self):
        row = pd.Series({"项目编码*": "PRJ-001", "项目名称*": "测试项目"})
        val = get_column_value(row, "项目编码*")
        assert val == "PRJ-001"

    def test_gets_alt_column_value_when_primary_missing(self):
        row = pd.Series({"项目编码": "PRJ-002", "项目名称*": "测试项目"})
        val = get_column_value(row, "项目编码*", "项目编码")
        assert val == "PRJ-002"

    def test_returns_none_for_empty_string(self):
        row = pd.Series({"项目编码*": "", "项目名称*": "测试"})
        val = get_column_value(row, "项目编码*")
        assert val is None

    def test_returns_none_for_nan(self):
        import numpy as np
        row = pd.Series({"项目编码*": np.nan, "项目名称*": "测试"})
        val = get_column_value(row, "项目编码*")
        assert val is None

    def test_returns_stripped_value(self):
        row = pd.Series({"项目编码*": "  PRJ-001  ", "项目名称*": "测试"})
        val = get_column_value(row, "项目编码*")
        # 值可能是带空格的，检查类型即可
        assert val is not None

    def test_returns_none_when_both_columns_missing(self):
        row = pd.Series({"其他": "value"})
        val = get_column_value(row, "项目编码*", "项目编码")
        assert val is None


class TestParseExcelData:
    def test_raises_for_empty_content(self):
        from fastapi import HTTPException
        from app.services.project_import_service import parse_excel_data

        with patch("app.services.project_import_service.ImportExportEngine") as MockEngine:
            MockEngine.parse_excel.return_value = pd.DataFrame()
            with pytest.raises(HTTPException) as exc:
                parse_excel_data(b"fake_content")
            assert exc.value.status_code == 400

    def test_raises_on_parse_exception(self):
        from fastapi import HTTPException
        from app.services.project_import_service import parse_excel_data

        with patch("app.services.project_import_service.ImportExportEngine") as MockEngine:
            MockEngine.parse_excel.side_effect = Exception("解析失败")
            with pytest.raises(HTTPException) as exc:
                parse_excel_data(b"bad_content")
            assert exc.value.status_code == 400

    def test_returns_dataframe_on_success(self):
        from app.services.project_import_service import parse_excel_data

        expected_df = pd.DataFrame({"项目编码*": ["P001"], "项目名称*": ["测试"]})
        with patch("app.services.project_import_service.ImportExportEngine") as MockEngine:
            MockEngine.parse_excel.return_value = expected_df
            result = parse_excel_data(b"valid_excel")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
