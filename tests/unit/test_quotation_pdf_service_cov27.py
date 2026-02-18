# -*- coding: utf-8 -*-
"""第二十七批 - quotation_pdf_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
import os

pytest.importorskip("app.services.quotation_pdf_service")

from app.services.quotation_pdf_service import QuotationPDFService, REPORTLAB_AVAILABLE


def make_quotation(**kwargs):
    q = MagicMock()
    q.id = kwargs.get("id", 1)
    q.quotation_number = kwargs.get("quotation_number", "QT-2024-001")
    q.project_name = kwargs.get("project_name", "测试项目")
    q.customer_name = kwargs.get("customer_name", "测试客户")
    q.total_amount = kwargs.get("total_amount", 500000.0)
    q.created_at = kwargs.get("created_at", MagicMock())
    q.valid_until = kwargs.get("valid_until", MagicMock())
    q.items = kwargs.get("items", [])
    return q


class TestQuotationPDFServiceInit:
    def test_output_dir_is_set(self):
        with patch("os.makedirs"):
            svc = QuotationPDFService()
            assert svc.output_dir == "uploads/quotations/"

    def test_init_creates_output_dir(self):
        with patch("os.makedirs") as mock_makedirs:
            svc = QuotationPDFService()
            mock_makedirs.assert_called_with("uploads/quotations/", exist_ok=True)

    def test_init_succeeds_without_reportlab(self):
        with patch("app.services.quotation_pdf_service.REPORTLAB_AVAILABLE", False):
            with patch("os.makedirs"):
                svc = QuotationPDFService()
                assert svc is not None


class TestGeneratePDFWithoutReportlab:
    def test_raises_runtime_error_when_reportlab_unavailable(self):
        with patch("os.makedirs"):
            svc = QuotationPDFService()
        with patch("app.services.quotation_pdf_service.REPORTLAB_AVAILABLE", False):
            quotation = make_quotation()
            with pytest.raises(RuntimeError, match="ReportLab"):
                svc.generate_pdf(quotation)


class TestGeneratePDFWithReportlab:
    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    def test_generates_pdf_file(self, tmp_path):
        with patch("os.makedirs"):
            svc = QuotationPDFService()
        svc.output_dir = str(tmp_path) + "/"

        quotation = make_quotation()
        result = svc.generate_pdf(quotation)

        assert result.endswith(".pdf")
        assert "QT-2024-001" in result

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    def test_pdf_filename_includes_quotation_number(self, tmp_path):
        with patch("os.makedirs"):
            svc = QuotationPDFService()
        svc.output_dir = str(tmp_path) + "/"

        quotation = make_quotation(quotation_number="QT-9999")
        result = svc.generate_pdf(quotation)
        assert "QT-9999" in result

    @pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not installed")
    def test_pdf_with_company_info(self, tmp_path):
        with patch("os.makedirs"):
            svc = QuotationPDFService()
        svc.output_dir = str(tmp_path) + "/"

        quotation = make_quotation()
        company_info = {
            "name": "测试科技有限公司",
            "address": "测试地址"
        }
        result = svc.generate_pdf(quotation, company_info=company_info)
        assert result.endswith(".pdf")


class TestReportlabAvailability:
    def test_reportlab_available_is_bool(self):
        assert isinstance(REPORTLAB_AVAILABLE, bool)

    def test_generate_pdf_requires_reportlab(self):
        """测试当REPORTLAB不可用时正确报错"""
        original = __import__("app.services.quotation_pdf_service", fromlist=["REPORTLAB_AVAILABLE"])
        if not original.REPORTLAB_AVAILABLE:
            with patch("os.makedirs"):
                svc = QuotationPDFService()
            quotation = make_quotation()
            with pytest.raises(RuntimeError):
                svc.generate_pdf(quotation)


class TestQuotationPDFServiceAttributes:
    def test_output_dir_ends_with_slash(self):
        with patch("os.makedirs"):
            svc = QuotationPDFService()
        assert svc.output_dir.endswith("/")

    def test_service_is_instantiable(self):
        with patch("os.makedirs"):
            svc = QuotationPDFService()
        assert svc is not None

    def test_generate_pdf_method_exists(self):
        with patch("os.makedirs"):
            svc = QuotationPDFService()
        assert hasattr(svc, "generate_pdf")
        assert callable(svc.generate_pdf)
