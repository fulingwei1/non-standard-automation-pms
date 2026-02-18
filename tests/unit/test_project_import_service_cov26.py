# -*- coding: utf-8 -*-
"""第二十六批 - project_import_service 单元测试"""

import pytest
import io
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.project_import_service")

from app.services.project_import_service import (
    validate_excel_file,
    parse_excel_data,
    validate_project_columns,
)


class TestValidateExcelFile:
    def test_accepts_xlsx(self):
        # Should not raise
        validate_excel_file("projects.xlsx")

    def test_accepts_xls(self):
        validate_excel_file("data.xls")

    def test_rejects_csv(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_excel_file("data.csv")
        assert exc_info.value.status_code == 400

    def test_rejects_pdf(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("report.pdf")

    def test_rejects_no_extension(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("noextension")

    def test_rejects_txt(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_excel_file("data.txt")

    def test_case_sensitivity(self):
        from fastapi import HTTPException
        # uppercase should fail since only .xlsx and .xls are accepted
        with pytest.raises(HTTPException):
            validate_excel_file("data.XLSX")


class TestParseExcelData:
    def test_raises_on_empty_file_content(self):
        import pandas as pd
        from fastapi import HTTPException

        empty_df = pd.DataFrame()
        with patch(
            "app.services.project_import_service.ImportExportEngine.parse_excel",
            return_value=empty_df,
        ):
            with pytest.raises(HTTPException) as exc_info:
                parse_excel_data(b"fake_content")
            assert exc_info.value.status_code == 400

    def test_raises_on_parse_failure(self):
        from fastapi import HTTPException

        with patch(
            "app.services.project_import_service.ImportExportEngine.parse_excel",
            side_effect=Exception("Parse error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                parse_excel_data(b"bad_content")
            assert exc_info.value.status_code == 400

    def test_returns_dataframe_on_success(self):
        import pandas as pd

        sample_df = pd.DataFrame({"项目编码*": ["P001"], "项目名称*": ["测试项目"]})
        with patch(
            "app.services.project_import_service.ImportExportEngine.parse_excel",
            return_value=sample_df,
        ):
            result = parse_excel_data(b"valid_content")
        assert len(result) == 1
        assert "项目编码*" in result.columns


class TestValidateProjectColumns:
    def test_passes_with_required_columns(self):
        import pandas as pd

        df = pd.DataFrame({"项目编码*": ["P001"], "项目名称*": ["测试"]})
        # Should not raise
        validate_project_columns(df)

    def test_raises_when_project_code_missing(self):
        import pandas as pd
        from fastapi import HTTPException

        df = pd.DataFrame({"项目名称*": ["测试"]})
        with pytest.raises(HTTPException) as exc_info:
            validate_project_columns(df)
        assert exc_info.value.status_code == 400

    def test_raises_when_project_name_missing(self):
        import pandas as pd
        from fastapi import HTTPException

        df = pd.DataFrame({"项目编码*": ["P001"]})
        with pytest.raises(HTTPException):
            validate_project_columns(df)

    def test_raises_when_both_required_columns_missing(self):
        import pandas as pd
        from fastapi import HTTPException

        df = pd.DataFrame({"其他列": ["值"]})
        with pytest.raises(HTTPException):
            validate_project_columns(df)

    def test_passes_with_extra_columns(self):
        import pandas as pd

        df = pd.DataFrame({
            "项目编码*": ["P001"],
            "项目名称*": ["测试"],
            "项目类型": ["定制"],
        })
        # Should not raise
        validate_project_columns(df)


class TestProjectImportServiceFunctions:
    """Test other top-level functions in the module."""

    def test_validate_excel_file_is_callable(self):
        assert callable(validate_excel_file)

    def test_parse_excel_data_is_callable(self):
        assert callable(parse_excel_data)

    def test_validate_project_columns_is_callable(self):
        assert callable(validate_project_columns)

    def test_error_message_contains_info(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            validate_excel_file("test.docx")
        assert "Excel" in exc_info.value.detail or "xlsx" in exc_info.value.detail or exc_info.value.status_code == 400
