# -*- coding: utf-8 -*-
"""pdf_export_service单元测试"""
import pytest
from unittest.mock import Mock
from app.services.pdf_export_service import PDFExportService

class TestPDFExportServiceInit:
    def test_init_with_db(self):
        mock_db = Mock()
        service = PDFExportService(mock_db)
        assert hasattr(service, 'db')
