# -*- coding: utf-8 -*-
"""
预警PDF导出服务
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.alert import AlertRecord, AlertRule
from app.models.user import User


def build_alert_query(
    db: Session,
    project_id: Optional[int] = None,
    alert_level: Optional[str] = None,
    status: Optional[str] = None,
    rule_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    构建预警查询
    
    Returns:
        Query: SQLAlchemy查询对象
    """
    query = db.query(AlertRecord).filter(AlertRecord.triggered_at.isnot(None))
    
    if project_id:
        query = query.filter(AlertRecord.project_id == project_id)
    if alert_level:
        query = query.filter(AlertRecord.alert_level == alert_level)
    if status:
        query = query.filter(AlertRecord.status == status)
    if rule_type:
        query = query.join(AlertRule).filter(AlertRule.rule_type == rule_type)
    if start_date:
        query = query.filter(AlertRecord.triggered_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(AlertRecord.triggered_at <= datetime.combine(end_date, datetime.max.time()))
    
    return query.order_by(AlertRecord.triggered_at.desc())


def calculate_alert_statistics(alerts: List[AlertRecord]) -> Dict[str, Any]:
    """
    计算预警统计信息
    
    Returns:
        Dict[str, Any]: 统计信息字典
    """
    total_count = len(alerts)
    by_level = {}
    by_status = {}
    by_type = {}
    
    for alert in alerts:
        level = alert.alert_level
        by_level[level] = by_level.get(level, 0) + 1
        
        status_val = alert.status
        by_status[status_val] = by_status.get(status_val, 0) + 1
        
        rule = alert.rule
        rule_type = rule.rule_type if rule else 'UNKNOWN'
        by_type[rule_type] = by_type.get(rule_type, 0) + 1
    
    return {
        'total': total_count,
        'by_level': by_level,
        'by_status': by_status,
        'by_type': by_type,
    }


def get_pdf_styles():
    """
    获取PDF样式
    
    Returns:
        tuple: (title_style, heading_style, normal_style, styles)
    """
    try:
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib import colors
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
            alignment=TA_CENTER,
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
        
        return title_style, heading_style, normal_style, styles
    except ImportError:
        raise ImportError("PDF处理库未安装，请安装reportlab: pip install reportlab")


def build_summary_table(statistics: Dict[str, Any]):
    """
    构建统计摘要表格
    
    Returns:
        Table: ReportLab表格对象
    """
    try:
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        
        summary_data = [
            ['统计项', '数量'],
            ['总预警数', str(statistics['total'])],
            ['', ''],
        ]
        
        summary_data.append(['按级别统计', ''])
        for level, count in sorted(statistics['by_level'].items()):
            summary_data.append([level, str(count)])
        
        summary_data.append(['', ''])
        summary_data.append(['按状态统计', ''])
        for status_val, count in sorted(statistics['by_status'].items()):
            summary_data.append([status_val, str(count)])
        
        summary_table = Table(summary_data, colWidths=[6*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return summary_table
    except ImportError:
        raise ImportError("PDF处理库未安装，请安装reportlab: pip install reportlab")


def build_alert_list_tables(
    db: Session,
    alerts: List[AlertRecord],
    page_size: int = 20
) -> List:
    """
    构建预警列表表格（分页）
    
    Returns:
        List: 表格和分页符列表
    """
    try:
        from reportlab.platypus import Table, TableStyle, PageBreak
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        
        tables = []
        
        for page_idx in range(0, len(alerts), page_size):
            if page_idx > 0:
                tables.append(PageBreak())
            
            page_alerts = alerts[page_idx:page_idx + page_size]
            
            # 表头
            table_data = [[
                '预警编号', '级别', '标题', '项目', '触发时间', '状态', '处理人'
            ]]
            
            # 数据行
            for alert in page_alerts:
                project = alert.project
                handler = None
                if alert.handler_id:
                    handler = db.query(User).filter(User.id == alert.handler_id).first()
                elif alert.acknowledged_by:
                    handler = db.query(User).filter(User.id == alert.acknowledged_by).first()
                
                table_data.append([
                    alert.alert_no,
                    alert.alert_level,
                    alert.alert_title[:30] + '...' if len(alert.alert_title) > 30 else alert.alert_title,
                    project.project_name if project else '',
                    alert.triggered_at.strftime('%Y-%m-%d %H:%M') if alert.triggered_at else '',
                    alert.status,
                    handler.username if handler else '',
                ])
            
            # 创建表格
            alert_table = Table(table_data, colWidths=[3*cm, 2*cm, 5*cm, 3*cm, 3*cm, 2*cm, 2*cm])
            alert_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            tables.append(alert_table)
        
        return tables
    except ImportError:
        raise ImportError("PDF处理库未安装，请安装reportlab: pip install reportlab")


def build_pdf_content(
    db: Session,
    alerts: List[AlertRecord],
    title_style,
    heading_style,
    normal_style
) -> List:
    """
    构建PDF内容
    
    Returns:
        List: PDF内容元素列表
    """
    try:
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.units import cm
        
        story = []
        
        # 标题
        story.append(Paragraph("预警报表", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        # 统计摘要
        story.append(Paragraph("统计摘要", heading_style))
        
        statistics = calculate_alert_statistics(alerts)
        summary_table = build_summary_table(statistics)
        story.append(summary_table)
        story.append(Spacer(1, 1*cm))
        
        # 预警列表
        story.append(Paragraph("预警列表", heading_style))
        
        alert_tables = build_alert_list_tables(db, alerts)
        story.extend(alert_tables)
        
        return story
    except ImportError:
        raise ImportError("PDF处理库未安装，请安装reportlab: pip install reportlab")
