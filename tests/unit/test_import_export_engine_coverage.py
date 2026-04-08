# -*- coding: utf-8 -*-
"""import_export_engine单元测试"""
import pytest
from unittest.mock import Mock
from app.services.import_export_engine import ExcelExportEngine

class TestExcelExportEngineInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = ExcelExportEngine(mock_db)
        assert hasattr(service, 'db')
