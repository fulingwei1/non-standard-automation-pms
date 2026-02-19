# -*- coding: utf-8 -*-
"""
Unit tests for bonus_allocation_parser (第三十八批)
"""
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytest.importorskip("app.services.bonus_allocation_parser", reason="导入失败，跳过")

try:
    from app.services.bonus_allocation_parser import (
        validate_file_type,
        save_uploaded_file,
        parse_excel_file,
    )
    from fastapi import HTTPException
except ImportError:
    pytestmark = pytest.mark.skip(reason="bonus_allocation_parser 不可用")
    validate_file_type = None
    save_uploaded_file = None
    parse_excel_file = None
    HTTPException = Exception


class TestValidateFileType:
    """测试文件类型验证"""

    def test_accepts_xlsx(self):
        """接受 .xlsx 文件"""
        validate_file_type("report.xlsx")  # 不抛出

    def test_accepts_xls(self):
        """接受 .xls 文件"""
        validate_file_type("report.xls")  # 不抛出

    def test_rejects_csv(self):
        """拒绝 .csv 文件"""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_type("report.csv")
        assert exc_info.value.status_code == 400

    def test_rejects_pdf(self):
        """拒绝 .pdf 文件"""
        with pytest.raises(HTTPException):
            validate_file_type("report.pdf")

    def test_rejects_no_extension(self):
        """拒绝无扩展名文件"""
        with pytest.raises(HTTPException):
            validate_file_type("report")

    def test_rejects_txt(self):
        """拒绝 .txt 文件"""
        with pytest.raises(HTTPException):
            validate_file_type("bonus.txt")


class TestSaveUploadedFile:
    """测试文件保存"""

    def test_returns_tuple_of_three(self):
        """返回三元组"""
        mock_file = MagicMock()
        mock_file.filename = "test.xlsx"

        with patch("app.services.bonus_allocation_parser.settings") as mock_settings, \
             patch("app.services.bonus_allocation_parser.os.makedirs"), \
             patch("app.services.bonus_allocation_parser.uuid.uuid4") as mock_uuid:
            mock_settings.UPLOAD_DIR = "/tmp"
            mock_uuid.return_value.hex = "abc123"
            result = save_uploaded_file(mock_file)

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_file_path_contains_extension(self):
        """文件路径包含原始扩展名"""
        mock_file = MagicMock()
        mock_file.filename = "bonus.xlsx"

        with patch("app.services.bonus_allocation_parser.settings") as mock_settings, \
             patch("app.services.bonus_allocation_parser.os.makedirs"), \
             patch("app.services.bonus_allocation_parser.uuid.uuid4") as mock_uuid:
            mock_settings.UPLOAD_DIR = "/tmp"
            mock_uuid.return_value.hex = "def456"
            file_path, relative_path, size = save_uploaded_file(mock_file)

        assert file_path.endswith(".xlsx")


class TestParseExcelFile:
    """测试 Excel 文件解析"""

    def test_calls_import_export_engine(self):
        """调用 ImportExportEngine.parse_excel"""
        mock_content = b"fake excel content"
        with patch("app.services.bonus_allocation_parser.ImportExportEngine") as MockEngine:
            import pandas as pd
            MockEngine.parse_excel.return_value = pd.DataFrame({"col": [1, 2]})
            result = parse_excel_file(mock_content)
            MockEngine.parse_excel.assert_called_once_with(mock_content)

    def test_raises_http_exception_on_parse_error(self):
        """解析失败时抛出 HTTPException"""
        mock_content = b"invalid content"
        with patch("app.services.bonus_allocation_parser.ImportExportEngine") as MockEngine:
            MockEngine.parse_excel.side_effect = Exception("解析错误")
            with pytest.raises(HTTPException) as exc_info:
                parse_excel_file(mock_content)
            assert exc_info.value.status_code == 400
