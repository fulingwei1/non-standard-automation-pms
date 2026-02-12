# -*- coding: utf-8 -*-
"""统一导入导出引擎 单元测试"""
import io
from unittest.mock import MagicMock, patch

import pytest

from app.services.import_export_engine import ExcelExportEngine, ImportExportEngine


class TestExcelExportEngine:
    @patch("app.services.import_export_engine.ExcelExportService")
    def test_export_table(self, MockService):
        instance = MagicMock()
        instance.export_to_excel.return_value = io.BytesIO(b"data")
        MockService.return_value = instance

        result = ExcelExportEngine.export_table(data=[{"a": 1}])
        assert isinstance(result, io.BytesIO)

    @patch("app.services.import_export_engine.ExcelExportService")
    def test_export_multi_sheet(self, MockService):
        instance = MagicMock()
        instance.export_multisheet.return_value = io.BytesIO(b"data")
        MockService.return_value = instance

        result = ExcelExportEngine.export_multi_sheet([{"name": "Sheet1"}])
        assert isinstance(result, io.BytesIO)

    def test_build_columns(self):
        cols = ExcelExportEngine.build_columns(["Name", "Age"], widths=[20, 10])
        assert len(cols) == 2
        assert cols[0]["label"] == "Name"
        assert cols[0]["width"] == 20
        assert cols[1]["label"] == "Age"

    def test_build_columns_no_widths(self):
        cols = ExcelExportEngine.build_columns(["A", "B"])
        assert len(cols) == 2
        assert "width" not in cols[0]


class TestImportExportEngine:
    def test_get_required_columns(self):
        cols = ImportExportEngine.get_required_columns("PROJECT")
        assert "项目编码*" in cols
        assert "项目名称*" in cols

    def test_get_required_columns_unknown(self):
        cols = ImportExportEngine.get_required_columns("UNKNOWN")
        assert cols == []

    def test_find_missing_columns(self):
        df = MagicMock()
        df.columns = ["项目编码*"]
        missing = ImportExportEngine.find_missing_columns(df, ["项目编码*", "项目名称*"])
        assert "项目名称*" in missing

    def test_find_missing_columns_without_asterisk(self):
        df = MagicMock()
        df.columns = ["项目编码"]
        missing = ImportExportEngine.find_missing_columns(df, ["项目编码*"])
        assert len(missing) == 0  # "项目编码" matches "项目编码*"

    @patch("app.services.import_export_engine.ExcelExportService")
    def test_get_exporter_import_error(self, MockService):
        MockService.side_effect = ImportError("no openpyxl")
        with pytest.raises(Exception):
            ExcelExportEngine.export_table(data=[])
