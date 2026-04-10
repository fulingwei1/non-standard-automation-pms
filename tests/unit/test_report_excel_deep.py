# -*- coding: utf-8 -*-
"""深入业务逻辑测试 - 报表Excel服务"""
import pytest
from unittest.mock import MagicMock, patch


class TestReportExcelServiceBusinessLogic:
    """报表Excel服务业务逻辑测试"""

    def test_export_to_excel(self):
        """测试导出Excel"""
        try:
            from app.services.report_excel_service import ReportExcelService

            mock_db = MagicMock()
            service = ReportExcelService(mock_db)

            result = service.export_to_excel([{"name": "test"}])

            assert result is not None
        except ImportError:
            pytest.skip("Module not found")