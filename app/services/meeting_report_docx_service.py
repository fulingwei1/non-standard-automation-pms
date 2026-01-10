# -*- coding: utf-8 -*-
"""
会议报告Word文档生成服务
基于python-docx生成格式化的Word报告文档
"""
from datetime import datetime, date
from typing import Dict, Any, Optional
from io import BytesIO
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class MeetingReportDocxService:
    """会议报告Word文档生成服务"""
    
    def __init__(self):
        if not DOCX_AVAILABLE:
            raise ImportError("Word处理库未安装，请安装python-docx: pip install python-docx")
    
    def generate_annual_report_docx(
        self,
        report_data: Dict[str, Any],
        report_title: str,
        period_year: int,
        rhythm_level: Optional[str] = None
    ) -> BytesIO:
        """
        生成年度会议报告Word文档
        
        Args:
            report_data: 报告数据（从MeetingReport.report_data）
            report_title: 报告标题
            period_year: 报告年份
            rhythm_level: 节律层级
            
        Returns:
            BytesIO: Word文档的内存流
        """
        from app.services.docx_content_builders import (
            setup_document_formatting,
            add_document_header,
            add_summary_section,
            add_level_statistics_section,
            add_action_items_section,
            add_key_decisions_section,
            add_strategic_structures_section,
            add_meetings_list_section,
            add_document_footer
        )
        
        doc = Document()
        
        # 设置中文字体
        self._setup_chinese_fonts(doc)
        
        # 设置文档格式
        setup_document_formatting(doc)
        
        # 添加标题和报告信息
        add_document_header(
            doc,
            report_title,
            f"报告周期：{period_year}年1月1日 - {period_year}年12月31日",
            rhythm_level
        )
        
        # 添加各个部分
        add_summary_section(doc, report_data.get('summary', {}))
        add_level_statistics_section(
            doc,
            report_data.get('by_level', {}),
            self._format_rhythm_level
        )
        add_action_items_section(doc, report_data.get('action_items_summary', {}))
        add_key_decisions_section(doc, report_data.get('key_decisions', []), "本年度")
        add_strategic_structures_section(doc, report_data.get('strategic_structures', []))
        add_meetings_list_section(
            doc,
            report_data.get('meetings', []),
            self._format_rhythm_level,
            self._format_cycle_type,
            self._format_status,
            "本年度"
        )
        
        # 添加页脚
        add_document_footer(doc)
        
        # 保存到内存流
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
    
    def generate_monthly_report_docx(
        self,
        report_data: Dict[str, Any],
        comparison_data: Dict[str, Any],
        report_title: str,
        period_year: int,
        period_month: int,
        rhythm_level: Optional[str] = None
    ) -> BytesIO:
        """
        生成月度会议报告Word文档（包含与上月对比）
        
        Args:
            report_data: 报告数据（从MeetingReport.report_data）
            comparison_data: 对比数据（从MeetingReport.comparison_data）
            report_title: 报告标题
            period_year: 报告年份
            period_month: 报告月份
            rhythm_level: 节律层级
            
        Returns:
            BytesIO: Word文档的内存流
        """
        from app.services.docx_content_builders import (
            setup_document_formatting,
            add_document_header,
            add_summary_section,
            add_comparison_section,
            add_level_statistics_section,
            add_action_items_section,
            add_key_decisions_section,
            add_meetings_list_section,
            add_document_footer
        )
        
        doc = Document()
        
        # 设置中文字体
        self._setup_chinese_fonts(doc)
        
        # 设置文档格式
        setup_document_formatting(doc)
        
        # 添加标题和报告信息
        add_document_header(
            doc,
            report_title,
            f"报告周期：{period_year}年{period_month}月",
            rhythm_level
        )
        
        # 添加各个部分
        add_summary_section(doc, report_data.get('summary', {}))
        add_comparison_section(doc, comparison_data)
        add_level_statistics_section(
            doc,
            report_data.get('by_level', {}),
            self._format_rhythm_level
        )
        add_action_items_section(doc, report_data.get('action_items_summary', {}))
        add_key_decisions_section(doc, report_data.get('key_decisions', []), "本月")
        add_meetings_list_section(
            doc,
            report_data.get('meetings', []),
            self._format_rhythm_level,
            self._format_cycle_type,
            self._format_status,
            "本月"
        )
        
        # 添加页脚
        add_document_footer(doc)
        
        # 保存到内存流
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        return buffer
    
    def _setup_chinese_fonts(self, doc):
        """设置中文字体"""
        try:
            # 设置默认字体
            doc.styles['Normal'].font.name = '微软雅黑'
            doc.styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
            
            # 设置标题字体
            for i in range(1, 10):
                heading_style = doc.styles[f'Heading {i}']
                heading_style.font.name = '微软雅黑'
                heading_style._element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
        except:
            # 如果设置失败，使用默认字体
            pass
    
    def _format_rhythm_level(self, level: str) -> str:
        """格式化节律层级"""
        level_map = {
            'STRATEGIC': '战略层',
            'OPERATIONAL': '经营层',
            'OPERATION': '运营层',
            'TASK': '任务层',
            'ALL': '全部层级'
        }
        return level_map.get(level, level)
    
    def _format_cycle_type(self, cycle_type: str) -> str:
        """格式化周期类型"""
        cycle_map = {
            'QUARTERLY': '季度',
            'MONTHLY': '月度',
            'WEEKLY': '周度',
            'DAILY': '每日'
        }
        return cycle_map.get(cycle_type, cycle_type)
    
    def _format_status(self, status: str) -> str:
        """格式化状态"""
        status_map = {
            'SCHEDULED': '已安排',
            'ONGOING': '进行中',
            'COMPLETED': '已完成',
            'CANCELLED': '已取消'
        }
        return status_map.get(status, status)
