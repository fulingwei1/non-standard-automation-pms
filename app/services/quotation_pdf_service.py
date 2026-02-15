"""
报价单PDF生成服务
Team 5: Quotation PDF Generator Service
"""
import os
from typing import Optional
from decimal import Decimal
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.models.presale_ai_quotation import PresaleAIQuotation


class QuotationPDFService:
    """报价单PDF生成服务"""
    
    def __init__(self):
        self.output_dir = "uploads/quotations/"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 注册中文字体（如果可用）
        if REPORTLAB_AVAILABLE:
            try:
                # 尝试注册常见的中文字体
                font_paths = [
                    "/System/Library/Fonts/PingFang.ttc",  # macOS
                    "/usr/share/fonts/truetype/arphic/ukai.ttc",  # Linux
                    "C:\\Windows\\Fonts\\simhei.ttf"  # Windows
                ]
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Chinese', font_path))
                        break
            except Exception:
                pass  # 如果字体注册失败，使用默认字体
    
    def generate_pdf(
        self, 
        quotation: PresaleAIQuotation, 
        company_info: Optional[dict] = None
    ) -> str:
        """
        生成PDF报价单
        Args:
            quotation: 报价单对象
            company_info: 公司信息（logo路径、名称、地址等）
        Returns:
            PDF文件路径
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not installed. Please install it: pip install reportlab")
        
        # 生成PDF文件名
        filename = f"quotation_{quotation.quotation_number}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # 构建PDF内容
        story = []
        
        # 添加公司Logo（如果提供）
        if company_info and company_info.get('logo_path'):
            logo_path = company_info['logo_path']
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=4*cm, height=2*cm)
                story.append(logo)
                story.append(Spacer(1, 0.5*cm))
        
        # 标题
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=1  # 居中
        )
        story.append(Paragraph("报价单", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # 报价单基本信息
        info_data = [
            ['报价单编号:', quotation.quotation_number, '日期:', quotation.created_at.strftime('%Y-%m-%d')],
            ['报价类型:', self._get_type_display(quotation.quotation_type), '有效期:', f'{quotation.validity_days}天'],
            ['版本:', f'V{quotation.version}', '状态:', self._get_status_display(quotation.status)]
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 6*cm, 2*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 1*cm))
        
        # 报价项清单标题
        story.append(Paragraph("报价项清单", styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        
        # 报价项表格
        items_data = [['序号', '项目名称', '数量', '单位', '单价(¥)', '金额(¥)']]
        
        for idx, item in enumerate(quotation.items, 1):
            items_data.append([
                str(idx),
                item['name'],
                str(item['quantity']),
                item['unit'],
                f"{float(item['unit_price']):,.2f}",
                f"{float(item['total_price']):,.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[1.5*cm, 7*cm, 2*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.5*cm))
        
        # 价格汇总
        summary_data = [
            ['小计:', f"¥{float(quotation.subtotal):,.2f}"],
            ['税费:', f"¥{float(quotation.tax):,.2f}"],
            ['折扣:', f"-¥{float(quotation.discount):,.2f}"],
            ['总计:', f"¥{float(quotation.total):,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[14*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 2), 'Helvetica', 11),
            ('FONT', (0, 3), (-1, 3), 'Helvetica-Bold', 13),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#e74c3c')),
            ('LINEABOVE', (0, 3), (-1, 3), 2, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 1*cm))
        
        # 付款条款
        if quotation.payment_terms:
            story.append(Paragraph("付款条款", styles['Heading2']))
            story.append(Spacer(1, 0.3*cm))
            
            # 处理多行付款条款
            terms_lines = quotation.payment_terms.split('\n')
            for line in terms_lines:
                story.append(Paragraph(line, styles['Normal']))
            
            story.append(Spacer(1, 0.5*cm))
        
        # 备注
        if quotation.notes:
            story.append(Paragraph("备注", styles['Heading2']))
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(quotation.notes, styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
        
        # 页脚信息
        footer_text = f"本报价单自{quotation.created_at.strftime('%Y年%m月%d日')}起{quotation.validity_days}天内有效"
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(footer_text, styles['Italic']))
        
        # 生成PDF
        doc.build(story)
        
        return filepath
    
    def generate_comparison_pdf(
        self, 
        quotations: list[PresaleAIQuotation],
        company_info: Optional[dict] = None
    ) -> str:
        """
        生成三档方案对比PDF
        Args:
            quotations: 报价单列表 [基础版, 标准版, 高级版]
            company_info: 公司信息
        Returns:
            PDF文件路径
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is not installed. Please install it: pip install reportlab")
        
        filename = f"quotation_comparison_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # 标题
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=1
        )
        story.append(Paragraph("报价方案对比", title_style))
        story.append(Spacer(1, 1*cm))
        
        # 三档方案对比表
        comparison_data = [['项目', '基础版', '标准版', '高级版']]
        
        # 价格对比
        comparison_data.append([
            '总价',
            f"¥{float(quotations[0].total):,.0f}",
            f"¥{float(quotations[1].total):,.0f}",
            f"¥{float(quotations[2].total):,.0f}"
        ])
        
        # 功能项数量对比
        comparison_data.append([
            '功能项数量',
            f"{len(quotations[0].items)}项",
            f"{len(quotations[1].items)}项",
            f"{len(quotations[2].items)}项"
        ])
        
        # 有效期对比
        comparison_data.append([
            '有效期',
            f"{quotations[0].validity_days}天",
            f"{quotations[1].validity_days}天",
            f"{quotations[2].validity_days}天"
        ])
        
        # 折扣对比
        comparison_data.append([
            '优惠折扣',
            f"¥{float(quotations[0].discount):,.0f}",
            f"¥{float(quotations[1].discount):,.0f}",
            f"¥{float(quotations[2].discount):,.0f}"
        ])
        
        comparison_table = Table(comparison_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        comparison_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 12),
            ('FONT', (0, 1), (-1, -1), 'Helvetica', 11),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        story.append(comparison_table)
        story.append(Spacer(1, 1*cm))
        
        # 推荐方案
        story.append(Paragraph("推荐方案", styles['Heading2']))
        story.append(Spacer(1, 0.3*cm))
        recommendation = Paragraph(
            "我们推荐选择<b>标准版</b>方案，该方案在功能完整性和性价比之间达到了最佳平衡。",
            styles['Normal']
        )
        story.append(recommendation)
        
        # 生成PDF
        doc.build(story)
        
        return filepath
    
    def _get_type_display(self, quotation_type) -> str:
        """获取报价类型显示名称"""
        type_map = {
            'basic': '基础版',
            'standard': '标准版',
            'premium': '高级版'
        }
        return type_map.get(quotation_type.value if hasattr(quotation_type, 'value') else quotation_type, '未知')
    
    def _get_status_display(self, status) -> str:
        """获取状态显示名称"""
        status_map = {
            'draft': '草稿',
            'pending_approval': '待审批',
            'approved': '已审批',
            'sent': '已发送',
            'accepted': '已接受',
            'rejected': '已拒绝'
        }
        return status_map.get(status.value if hasattr(status, 'value') else status, '未知')
