# -*- coding: utf-8 -*-
"""
Tests for pdf_export_service service
Covers: app/services/pdf_export_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
File Size: 95 lines
Batch: 2
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, date, timedelta
from decimal import Decimal
import io

from app.services.pdf_export_service import PDFExportService, PDF_AVAILABLE


@pytest.fixture
def pdf_export_service():
    """创建 PDFExportService 实例"""
    if not PDF_AVAILABLE:
        pytest.skip("PDF libraries not available")
    return PDFExportService()


class TestPDFExportService:
    """Test suite for PDFExportService."""

    def test_init_success(self):
        """测试服务初始化 - 成功"""
        if not PDF_AVAILABLE:
            pytest.skip("PDF libraries not available")
        
        service = PDFExportService()
        assert service is not None
        assert service.styles is not None

    def test_init_without_libraries(self):
        """测试服务初始化 - 缺少库"""
        with patch('app.services.pdf_export_service.PDF_AVAILABLE', False):
            with pytest.raises(ImportError, match="PDF处理库未安装"):
                PDFExportService()

    def test_export_quote_to_pdf_basic(self, pdf_export_service):
        """测试导出报价单 - 基础场景"""
        quote_data = {
            'quote_code': 'QT001',
            'quote_date': date.today(),
            'customer_name': '测试客户',
            'total_amount': Decimal('100000.00')
        }
        
        quote_items = [
            {
                'item_name': '产品A',
                'quantity': 10,
                'unit_price': Decimal('10000.00'),
                'amount': Decimal('100000.00')
            }
        ]
        
        result = pdf_export_service.export_quote_to_pdf(
            quote_data=quote_data,
            quote_items=quote_items
        )
        
        assert result is not None
        assert isinstance(result, io.BytesIO)
        assert result.tell() == 0  # 文件已写入

    def test_export_quote_to_pdf_with_company_info(self, pdf_export_service):
        """测试导出报价单 - 带公司信息"""
        quote_data = {
            'quote_code': 'QT002',
            'quote_date': date.today(),
            'customer_name': '测试客户'
        }
        
        quote_items = []
        
        company_info = {
            'company_name': '测试公司',
            'address': '测试地址',
            'phone': '123456789'
        }
        
        result = pdf_export_service.export_quote_to_pdf(
            quote_data=quote_data,
            quote_items=quote_items,
            company_info=company_info
        )
        
        assert result is not None
        assert isinstance(result, io.BytesIO)

    def test_export_quote_to_pdf_empty_items(self, pdf_export_service):
        """测试导出报价单 - 空明细"""
        quote_data = {
            'quote_code': 'QT003',
            'quote_date': date.today()
        }
        
        result = pdf_export_service.export_quote_to_pdf(
            quote_data=quote_data,
            quote_items=[]
        )
        
        assert result is not None

    def test_export_contract_to_pdf_basic(self, pdf_export_service):
        """测试导出合同 - 基础场景"""
        contract_data = {
            'contract_no': 'CT001',
            'contract_date': date.today(),
            'customer_name': '测试客户',
            'contract_amount': Decimal('200000.00')
        }
        
        result = pdf_export_service.export_contract_to_pdf(contract_data)
        
        assert result is not None
        assert isinstance(result, io.BytesIO)

    def test_export_invoice_to_pdf_basic(self, pdf_export_service):
        """测试导出发票 - 基础场景"""
        invoice_data = {
            'invoice_no': 'INV001',
            'invoice_date': date.today(),
            'customer_name': '测试客户',
            'amount': Decimal('50000.00'),
            'tax_amount': Decimal('6500.00')
        }
        
        invoice_items = [
            {
                'item_name': '服务费',
                'quantity': 1,
                'unit_price': Decimal('50000.00'),
                'amount': Decimal('50000.00')
            }
        ]
        
        result = pdf_export_service.export_invoice_to_pdf(
            invoice_data=invoice_data,
            invoice_items=invoice_items
        )
        
        assert result is not None
        assert isinstance(result, io.BytesIO)

    def test_export_invoice_to_pdf_with_tax(self, pdf_export_service):
        """测试导出发票 - 含税"""
        invoice_data = {
            'invoice_no': 'INV002',
            'invoice_date': date.today(),
            'amount': Decimal('100000.00'),
            'tax_rate': Decimal('0.13'),
            'tax_amount': Decimal('13000.00'),
            'total_amount': Decimal('113000.00')
        }
        
        result = pdf_export_service.export_invoice_to_pdf(
            invoice_data=invoice_data,
            invoice_items=[]
        )
        
        assert result is not None
