# -*- coding: utf-8 -*-
"""excel_export_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.excel_export_service import ExcelExportService

class TestExcelExportServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ExcelExportService(mock_db)
        assert hasattr(service, 'db')
