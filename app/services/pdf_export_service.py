# -*- coding: utf-8 -*-
"""
PDF 导出服务
提供报价单、合同、发票的 PDF 导出功能
"""

import io
from typing import Any, Dict, List, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT  # noqa: F401
    from reportlab.lib.pagesizes import A4, letter  # noqa: F401
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm, mm  # noqa: F401
    from reportlab.pdfbase import pdfmetrics  # noqa: F401
    from reportlab.pdfbase.ttfonts import TTFont  # noqa: F401
    from reportlab.platypus import (
        Image,  # noqa: F401
        PageBreak,  # noqa: F401
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PDFExportService:
    """PDF 导出服务类"""

    def __init__(self):
        if not PDF_AVAILABLE:
            raise ImportError("PDF处理库未安装，请安装reportlab: pip install reportlab")

        # 初始化样式
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))

        # 副标题样式
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            spaceBefore=12
        ))

        # 正文样式
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            leading=14
        ))

    def export_quote_to_pdf(
        self,
        quote_data: Dict[str, Any],
        quote_items: List[Dict[str, Any]],
        company_info: Optional[Dict[str, Any]] = None
    ) -> io.BytesIO:
        """
        导出报价单为 PDF

        Args:
            quote_data: 报价主表数据
            quote_items: 报价明细列表
            company_info: 公司信息（可选）

        Returns:
            io.BytesIO: PDF 文件的内存流
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

        story = []

        # 标题
        title = f"报价单 - {quote_data.get('quote_code', '')}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*cm))

        # 基本信息表格
        info_data = [
            ['报价编码', quote_data.get('quote_code', '')],
            ['客户名称', quote_data.get('customer_name', '')],
            ['报价日期', quote_data.get('created_at', '').strftime('%Y-%m-%d') if quote_data.get('created_at') else ''],
            ['有效期至', quote_data.get('valid_until', '').strftime('%Y-%m-%d') if quote_data.get('valid_until') else ''],
            ['报价金额', f"¥{quote_data.get('total_price', 0):,.2f}"],
            ['状态', quote_data.get('status', '')],
        ]

        info_table = Table(info_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))

        # 明细表格
        story.append(Paragraph('报价明细', self.styles['CustomHeading2']))

        item_headers = ['序号', '物料名称', '规格型号', '数量', '单位', '单价', '总价', '备注']
        item_table_data = [item_headers]

        for idx, item in enumerate(quote_items, 1):
            item_table_data.append([
                str(idx),
                item.get('item_name', ''),
                item.get('specification', ''),
                str(item.get('qty', 0)),
                item.get('unit', ''),
                f"¥{float(item.get('unit_price', 0)):,.2f}",
                f"¥{float(item.get('total_price', 0)):,.2f}",
                item.get('remark', ''),
            ])

        # 添加合计行
        total_price = sum([float(item.get('total_price', 0)) for item in quote_items])
        item_table_data.append([
            '', '', '', '', '', '合计：', f"¥{total_price:,.2f}", ''
        ])

        item_table = Table(item_table_data, colWidths=[0.8*cm, 4*cm, 3*cm, 1*cm, 1*cm, 2*cm, 2*cm, 2.2*cm])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (5, -1), (6, -1), 'Helvetica-Bold'),
        ]))
        story.append(item_table)

        # 构建 PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def export_contract_to_pdf(
        self,
        contract_data: Dict[str, Any],
        deliverables: List[Dict[str, Any]],
        company_info: Optional[Dict[str, Any]] = None
    ) -> io.BytesIO:
        """
        导出合同为 PDF

        Args:
            contract_data: 合同主表数据
            deliverables: 交付物列表
            company_info: 公司信息（可选）

        Returns:
            io.BytesIO: PDF 文件的内存流
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

        story = []

        # 标题
        title = f"合同 - {contract_data.get('contract_code', '')}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*cm))

        # 基本信息
        info_data = [
            ['合同编码', contract_data.get('contract_code', '')],
            ['合同名称', contract_data.get('contract_name', '')],
            ['客户名称', contract_data.get('customer_name', '')],
            ['合同金额', f"¥{float(contract_data.get('contract_amount', 0)):,.2f}"],
            ['签订日期', contract_data.get('signed_date', '').strftime('%Y-%m-%d') if contract_data.get('signed_date') else ''],
            ['交期', contract_data.get('delivery_deadline', '').strftime('%Y-%m-%d') if contract_data.get('delivery_deadline') else ''],
            ['状态', contract_data.get('status', '')],
        ]

        info_table = Table(info_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))

        # 交付物清单
        if deliverables:
            story.append(Paragraph('交付物清单', self.styles['CustomHeading2']))

            deliverable_headers = ['序号', '交付物名称', '数量', '单位', '备注']
            deliverable_table_data = [deliverable_headers]

            for idx, item in enumerate(deliverables, 1):
                deliverable_table_data.append([
                    str(idx),
                    item.get('deliverable_name', ''),
                    str(item.get('quantity', 0)),
                    item.get('unit', ''),
                    item.get('remark', ''),
                ])

            deliverable_table = Table(deliverable_table_data, colWidths=[0.8*cm, 6*cm, 2*cm, 2*cm, 5.2*cm])
            deliverable_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(deliverable_table)

        # 构建 PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    def export_invoice_to_pdf(
        self,
        invoice_data: Dict[str, Any],
        company_info: Optional[Dict[str, Any]] = None
    ) -> io.BytesIO:
        """
        导出发票为 PDF

        Args:
            invoice_data: 发票数据
            company_info: 公司信息（可选）

        Returns:
            io.BytesIO: PDF 文件的内存流
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

        story = []

        # 标题
        title = f"发票 - {invoice_data.get('invoice_code', '')}"
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*cm))

        # 基本信息
        total_amount = float(invoice_data.get('total_amount') or invoice_data.get('amount', 0))
        paid_amount = float(invoice_data.get('paid_amount', 0))
        unpaid_amount = total_amount - paid_amount

        info_data = [
            ['发票编码', invoice_data.get('invoice_code', '')],
            ['合同编码', invoice_data.get('contract_code', '')],
            ['客户名称', invoice_data.get('customer_name', '')],
            ['发票类型', invoice_data.get('invoice_type', '')],
            ['发票金额', f"¥{total_amount:,.2f}"],
            ['已收金额', f"¥{paid_amount:,.2f}"],
            ['未收金额', f"¥{unpaid_amount:,.2f}"],
            ['开票日期', invoice_data.get('issue_date', '').strftime('%Y-%m-%d') if invoice_data.get('issue_date') else ''],
            ['到期日期', invoice_data.get('due_date', '').strftime('%Y-%m-%d') if invoice_data.get('due_date') else ''],
            ['收款状态', invoice_data.get('payment_status', '')],
            ['发票状态', invoice_data.get('status', '')],
        ]

        info_table = Table(info_data, colWidths=[4*cm, 10*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(info_table)

        # 构建 PDF
        doc.build(story)
        buffer.seek(0)
        return buffer


def create_pdf_response(
    pdf_data: io.BytesIO,
    filename: str,
    media_type: str = "application/pdf"
) -> Any:
    """
    创建 PDF 下载响应

    Args:
        pdf_data: PDF 文件的内存流
        filename: 文件名
        media_type: MIME 类型

    Returns:
        StreamingResponse: FastAPI 流式响应
    """
    from fastapi.responses import StreamingResponse

    return StreamingResponse(
        pdf_data,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}"
        }
    )
