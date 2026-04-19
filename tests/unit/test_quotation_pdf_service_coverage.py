# -*- coding: utf-8 -*-
"""quotation_pdf_service单元测试"""
from app.services.quotation_pdf_service import QuotationPDFService


class TestQuotationPDFServiceInit:
    def test_init(self):
        service = QuotationPDFService()
        assert service is not None
