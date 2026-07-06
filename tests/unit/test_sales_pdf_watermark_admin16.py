# -*- coding: utf-8 -*-
"""ADMIN-16: 销售 PDF 导出必须接入水印服务。"""

import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def _assert_response_uses_watermarked_pdf(create_response_mock, expected_content: bytes):
    pdf_stream = create_response_mock.call_args.args[0]
    assert isinstance(pdf_stream, io.BytesIO)
    assert pdf_stream.getvalue() == expected_content


def test_contract_pdf_export_applies_watermark_with_current_user():
    from app.api.v1.endpoints.sales.contracts import export as contract_export

    contract = SimpleNamespace(
        contract_code="CT-001",
        contract_name="合同",
        customer=SimpleNamespace(customer_name="客户A"),
        contract_amount=1000,
        signing_date=None,
        status="SIGNED",
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []
    current_user = SimpleNamespace(id=7, real_name="张三", username="zhangsan")

    with (
        patch.object(contract_export, "get_or_404", return_value=contract),
        patch.object(contract_export.security, "check_sales_data_permission", return_value=True),
        patch("app.services.pdf_export_service.PDFExportService") as pdf_service_class,
        patch("app.services.pdf_export_service.create_pdf_response") as create_response,
        patch("app.services.export.watermark_service.add_watermark_to_pdf") as add_watermark,
    ):
        pdf_service_class.return_value.export_contract_to_pdf.return_value = io.BytesIO(
            b"contract-pdf"
        )
        add_watermark.return_value = b"watermarked-contract-pdf"
        create_response.return_value = "response"

        result = contract_export._build_contract_pdf_response(
            db=db,
            contract_id=1,
            current_user=current_user,
        )

    assert result == "response"
    add_watermark.assert_called_once_with(
        b"contract-pdf",
        operator_name="张三",
        custom_text="内部资料",
    )
    _assert_response_uses_watermarked_pdf(create_response, b"watermarked-contract-pdf")


def test_invoice_pdf_export_applies_watermark_with_current_user():
    from app.api.v1.endpoints.sales.invoices import export as invoice_export

    invoice = SimpleNamespace(
        invoice_code="INV-001",
        contract=SimpleNamespace(
            contract_code="CT-001",
            customer=SimpleNamespace(customer_name="客户A"),
        ),
        total_amount=1000,
        amount=None,
        paid_amount=100,
        invoice_type="VAT",
        issue_date=None,
        due_date=None,
        payment_status="PARTIAL",
        status="ISSUED",
    )
    current_user = SimpleNamespace(id=8, real_name="李四", username="lisi")

    with (
        patch.object(invoice_export, "get_or_404", return_value=invoice),
        patch("app.services.pdf_export_service.PDFExportService") as pdf_service_class,
        patch("app.services.pdf_export_service.create_pdf_response") as create_response,
        patch("app.services.export.watermark_service.add_watermark_to_pdf") as add_watermark,
    ):
        pdf_service_class.return_value.export_invoice_to_pdf.return_value = io.BytesIO(
            b"invoice-pdf"
        )
        add_watermark.return_value = b"watermarked-invoice-pdf"
        create_response.return_value = "response"

        result = invoice_export.export_invoice_pdf(
            db=MagicMock(),
            invoice_id=1,
            current_user=current_user,
        )

    assert result == "response"
    add_watermark.assert_called_once_with(
        b"invoice-pdf",
        operator_name="李四",
        custom_text="内部资料",
    )
    _assert_response_uses_watermarked_pdf(create_response, b"watermarked-invoice-pdf")


def test_pdf_watermark_uses_cid_font_for_chinese_text():
    from app.services.export.watermark_service import WatermarkService

    assert WatermarkService.get_pdf_font_name("内部资料 | 操作者: 张三") == "STSong-Light"
    assert WatermarkService.get_pdf_font_name("CONFIDENTIAL") == "Helvetica"


def test_pdf_watermark_uses_installed_pypdf2_fallback():
    import app.services.export.watermark_service as watermark_service

    assert watermark_service.PYPDF_AVAILABLE is True
    assert watermark_service.PdfReader is not None
    assert watermark_service.PdfWriter is not None
