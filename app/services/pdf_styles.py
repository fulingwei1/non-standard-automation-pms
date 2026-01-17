# -*- coding: utf-8 -*-
"""
PDF 样式工具函数
"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

# 检查 reportlab 是否可用
try:
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def get_pdf_styles():
    """
    获取 PDF 样式配置

    Returns:
        dict: 包含各种样式的字典
    """
    if not REPORTLAB_AVAILABLE:
        return {}

    styles = getSampleStyleSheet()

    # 创建自定义样式
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=1,  # 居中
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14

    footer_style = ParagraphStyle(
        'Footer',
        parent=normal_style,
        fontSize=9,
        textColor=colors.grey,
        alignment=2  # 右对齐
    )

    return {
        'title': title_style,
        'heading': heading_style,
        'normal': normal_style,
        'footer': footer_style
    }


def get_table_style_base():
    """
    获取基础表格样式

    Returns:
        TableStyle: 基础表格样式
    """
    if not REPORTLAB_AVAILABLE:
        return None

    from reportlab.platypus import TableStyle

    return TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ])


def get_info_table_style():
    """
    获取基本信息表格样式

    Returns:
        TableStyle: 信息表格样式
    """
    if not REPORTLAB_AVAILABLE:
        return None

    from reportlab.platypus import TableStyle

    base_style = get_table_style_base()
    base_style.add('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6'))
    return base_style


def get_stats_table_style():
    """
    获取统计表格样式

    Returns:
        TableStyle: 统计表格样式
    """
    if not REPORTLAB_AVAILABLE:
        return None

    from reportlab.platypus import TableStyle

    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ])


def get_issue_table_style():
    """
    获取问题表格样式

    Returns:
        TableStyle: 问题表格样式
    """
    if not REPORTLAB_AVAILABLE:
        return None

    from reportlab.platypus import TableStyle

    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ])


def get_signature_table_style():
    """
    获取签字表格样式

    Returns:
        TableStyle: 签字表格样式
    """
    if not REPORTLAB_AVAILABLE:
        return None

    from reportlab.platypus import TableStyle

    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ])
