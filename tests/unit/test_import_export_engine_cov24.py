# -*- coding: utf-8 -*-
"""第二十四批 - import_export_engine 单元测试"""

import io
import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.import_export_engine")

from app.services.import_export_engine import ExcelExportEngine, ImportExportEngine


class TestExcelExportEngine:
    @patch("app.services.import_export_engine.ExcelExportService")
    def test_build_columns_basic(self, mock_service_cls):
        cols = ExcelExportEngine.build_columns(["姓名", "部门", "角色"])
        assert len(cols) == 3
        assert cols[0]["key"] == "姓名"
        assert cols[0]["label"] == "姓名"

    def test_build_columns_with_widths(self):
        cols = ExcelExportEngine.build_columns(["A", "B"], widths=[20, 30])
        assert cols[0]["width"] == 20
        assert cols[1]["width"] == 30

    def test_build_columns_partial_widths(self):
        cols = ExcelExportEngine.build_columns(["X", "Y", "Z"], widths=[15])
        assert cols[0]["width"] == 15
        assert "width" not in cols[1]

    @patch("app.services.import_export_engine.ExcelExportService")
    def test_export_table_calls_service(self, mock_service_cls):
        mock_exporter = MagicMock()
        mock_exporter.export_to_excel.return_value = io.BytesIO(b"data")
        mock_service_cls.return_value = mock_exporter

        result = ExcelExportEngine.export_table(data=[{"A": 1}], sheet_name="Test")
        mock_exporter.export_to_excel.assert_called_once()

    @patch("app.services.import_export_engine.ExcelExportService")
    def test_export_multi_sheet_calls_service(self, mock_service_cls):
        mock_exporter = MagicMock()
        mock_exporter.export_multisheet.return_value = io.BytesIO(b"multi")
        mock_service_cls.return_value = mock_exporter

        sheets = [{"name": "Sheet1", "data": []}]
        result = ExcelExportEngine.export_multi_sheet(sheets)
        mock_exporter.export_multisheet.assert_called_once()


class TestImportExportEngine:
    def test_get_required_columns_project(self):
        cols = ImportExportEngine.get_required_columns("PROJECT")
        assert "项目编码*" in cols
        assert "项目名称*" in cols

    def test_get_required_columns_case_insensitive(self):
        cols = ImportExportEngine.get_required_columns("project")
        assert len(cols) > 0

    def test_get_required_columns_unknown_type(self):
        cols = ImportExportEngine.get_required_columns("UNKNOWN_TYPE")
        assert cols == []

    def test_find_missing_columns_all_present(self):
        df = MagicMock()
        df.columns = ["项目编码*", "项目名称*"]
        missing = ImportExportEngine.find_missing_columns(df, ["项目编码*", "项目名称*"])
        assert missing == []

    def test_find_missing_columns_detects_missing(self):
        df = MagicMock()
        df.columns = ["项目编码*"]
        missing = ImportExportEngine.find_missing_columns(df, ["项目编码*", "项目名称*"])
        assert "项目名称*" in missing

    def test_parse_excel_drops_empty_rows(self):
        import pandas
        df = MagicMock()
        df.dropna.return_value = df
        with patch.object(pandas, "read_excel", return_value=df):
            with patch("app.services.import_export_engine.io.BytesIO") as mock_bio:
                mock_bio.return_value = MagicMock()
                result = ImportExportEngine.parse_excel(b"xlsx_bytes")
        df.dropna.assert_called_with(how="all")
