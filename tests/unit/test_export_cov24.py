# -*- coding: utf-8 -*-
"""第二十四批 - data_integrity/export 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.data_integrity.export")

from app.services.data_integrity.export import ExportMixin


class ConcreteExportService(ExportMixin):
    """用于测试的具体实现类"""

    def generate_data_quality_report(self, period_id, department_id=None):
        return {
            "period_id": period_id,
            "overall_completeness": 85.5,
            "total_engineers": 20,
            "engineers_with_data": 17,
            "average_completeness": 83.0,
            "details": [
                {"name": "工程师A", "completeness": 90.0},
            ],
            "missing_summary": [
                {"field": "工时", "count": 3},
            ],
        }


class TestExportDataQualityReport:
    def test_json_format_returns_dict(self):
        svc = ConcreteExportService()
        result = svc.export_data_quality_report(period_id=1, format="json")
        assert isinstance(result, dict)
        assert result["period_id"] == 1

    @patch("app.services.data_integrity.export.ExcelExportEngine")
    def test_excel_format(self, mock_engine):
        mock_output = MagicMock()
        mock_output.getvalue.return_value = b"xlsx_bytes"
        mock_engine.export_multi_sheet.return_value = mock_output
        mock_engine.build_columns.return_value = [{"key": "指标", "label": "指标"}]

        svc = ConcreteExportService()
        result = svc.export_data_quality_report(period_id=2, format="excel")
        assert result["format"] == "excel"
        assert "content" in result
        assert "filename" in result

    @patch("app.services.data_integrity.export.SimpleDocTemplate")
    def test_pdf_format(self, mock_doc):
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance

        svc = ConcreteExportService()
        result = svc.export_data_quality_report(period_id=3, format="pdf")
        assert result["format"] == "pdf"
        assert result["content_type"] == "application/pdf"

    def test_unknown_format_returns_dict(self):
        svc = ConcreteExportService()
        result = svc.export_data_quality_report(period_id=4, format="unknown")
        assert isinstance(result, dict)

    def test_department_id_passed_through(self):
        svc = ConcreteExportService()
        result = svc.export_data_quality_report(period_id=5, department_id=10, format="json")
        assert result["period_id"] == 5
