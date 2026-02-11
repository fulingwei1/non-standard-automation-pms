# -*- coding: utf-8 -*-
"""Tests for pdf_export_service.py"""
import io
from unittest.mock import MagicMock, patch
import pytest


class TestPDFExportService:
    @patch("app.services.pdf_export_service.PDF_AVAILABLE", True)
    def test_export_quote_to_pdf(self):
        from app.services.pdf_export_service import PDFExportService
        try:
            service = PDFExportService()
        except ImportError:
            pytest.skip("reportlab not installed")

        quote_data = {
            'quote_code': 'Q-001',
            'customer_name': '测试客户',
            'created_at': MagicMock(strftime=MagicMock(return_value='2025-01-01')),
            'valid_until': MagicMock(strftime=MagicMock(return_value='2025-02-01')),
            'total_price': 100000,
            'status': 'DRAFT',
        }
        items = [
            {'item_name': '物料A', 'specification': 'ABC', 'qty': 10, 'unit': '个',
             'unit_price': 100, 'total_price': 1000, 'remark': ''},
        ]
        result = service.export_quote_to_pdf(quote_data, items)
        assert isinstance(result, io.BytesIO)
        assert result.read(4) == b'%PDF'

    @patch("app.services.pdf_export_service.PDF_AVAILABLE", True)
    def test_export_contract_to_pdf(self):
        from app.services.pdf_export_service import PDFExportService
        try:
            service = PDFExportService()
        except ImportError:
            pytest.skip("reportlab not installed")

        contract_data = {
            'contract_code': 'C-001',
            'contract_name': '测试合同',
            'customer_name': '客户A',
            'contract_amount': 500000,
            'signed_date': None,
            'delivery_deadline': None,
            'status': 'DRAFT',
        }
        result = service.export_contract_to_pdf(contract_data, [])
        assert isinstance(result, io.BytesIO)

    @patch("app.services.pdf_export_service.PDF_AVAILABLE", True)
    def test_export_invoice_to_pdf(self):
        from app.services.pdf_export_service import PDFExportService
        try:
            service = PDFExportService()
        except ImportError:
            pytest.skip("reportlab not installed")

        invoice_data = {
            'invoice_code': 'INV-001',
            'contract_code': 'C-001',
            'customer_name': '客户A',
            'invoice_type': '增值税',
            'total_amount': 100000,
            'paid_amount': 50000,
            'issue_date': None,
            'due_date': None,
            'payment_status': 'PARTIAL',
            'status': 'ISSUED',
        }
        result = service.export_invoice_to_pdf(invoice_data)
        assert isinstance(result, io.BytesIO)

    @patch("app.services.pdf_export_service.PDF_AVAILABLE", False)
    def test_not_available(self):
        from app.services.pdf_export_service import PDFExportService
        with pytest.raises(ImportError):
            PDFExportService()
