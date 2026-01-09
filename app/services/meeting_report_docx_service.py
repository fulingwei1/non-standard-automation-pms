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
        doc = Document()
        
        # 设置中文字体
        self._setup_chinese_fonts(doc)
        
        # 设置页面边距
        sections = doc.sections
        for section in sections:
            section.top_margin = Cm(2.5)
            section.bottom_margin = Cm(2.5)
            section.left_margin = Cm(3)
            section.right_margin = Cm(3)
        
        # 标题
        title = doc.add_heading(report_title, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 报告信息
        info_para = doc.add_paragraph()
        info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info_run = info_para.add_run(f"报告周期：{period_year}年1月1日 - {period_year}年12月31日")
        info_run.font.size = Pt(12)
        info_run.font.color.rgb = RGBColor(102, 102, 102)
        
        if rhythm_level:
            level_para = doc.add_paragraph()
            level_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            level_run = level_para.add_run(f"节律层级：{rhythm_level}")
            level_run.font.size = Pt(12)
            level_run.font.color.rgb = RGBColor(102, 102, 102)
        
        doc.add_paragraph()  # 空行
        
        # 一、执行摘要
        doc.add_heading('一、执行摘要', 1)
        
        summary = report_data.get('summary', {})
        summary_table = doc.add_table(rows=7, cols=2)
        summary_table.style = 'Light Grid Accent 1'
        summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        summary_data = [
            ('会议总数', f"{summary.get('total_meetings', 0)}"),
            ('已完成会议数', f"{summary.get('completed_meetings', 0)}"),
            ('会议完成率', summary.get('completion_rate', '0%')),
            ('行动项总数', f"{summary.get('total_action_items', 0)}"),
            ('已完成行动项数', f"{summary.get('completed_action_items', 0)}"),
            ('逾期行动项数', f"{summary.get('overdue_action_items', 0)}"),
            ('行动项完成率', summary.get('action_completion_rate', '0%')),
        ]
        
        for i, (label, value) in enumerate(summary_data):
            summary_table.rows[i].cells[0].text = label
            summary_table.rows[i].cells[1].text = value
            # 设置单元格样式
            summary_table.rows[i].cells[0].paragraphs[0].runs[0].font.bold = True
            summary_table.rows[i].cells[1].paragraphs[0].runs[0].font.size = Pt(11)
        
        doc.add_paragraph()  # 空行
        
        # 二、按层级统计
        doc.add_heading('二、按层级统计', 1)
        
        by_level = report_data.get('by_level', {})
        if by_level:
            level_table = doc.add_table(rows=len(by_level) + 1, cols=3)
            level_table.style = 'Light Grid Accent 1'
            level_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # 表头
            header_cells = level_table.rows[0].cells
            header_cells[0].text = '节律层级'
            header_cells[1].text = '会议总数'
            header_cells[2].text = '已完成会议数'
            for cell in header_cells:
                cell.paragraphs[0].runs[0].font.bold = True
            
            # 数据行
            for idx, (level, data) in enumerate(by_level.items(), start=1):
                row_cells = level_table.rows[idx].cells
                row_cells[0].text = self._format_rhythm_level(level)
                row_cells[1].text = str(data.get('total', 0))
                row_cells[2].text = str(data.get('completed', 0))
        
        doc.add_paragraph()  # 空行
        
        # 三、行动项统计
        doc.add_heading('三、行动项统计', 1)
        
        action_summary = report_data.get('action_items_summary', {})
        action_table = doc.add_table(rows=5, cols=2)
        action_table.style = 'Light Grid Accent 1'
        action_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        action_data = [
            ('行动项总数', f"{action_summary.get('total', 0)}"),
            ('已完成', f"{action_summary.get('completed', 0)}"),
            ('逾期', f"{action_summary.get('overdue', 0)}"),
            ('进行中', f"{action_summary.get('in_progress', 0)}"),
        ]
        
        for i, (label, value) in enumerate(action_data):
            action_table.rows[i].cells[0].text = label
            action_table.rows[i].cells[1].text = value
            action_table.rows[i].cells[0].paragraphs[0].runs[0].font.bold = True
        
        doc.add_paragraph()  # 空行
        
        # 四、关键决策
        doc.add_heading('四、关键决策', 1)
        
        key_decisions = report_data.get('key_decisions', [])
        if key_decisions:
            for idx, decision in enumerate(key_decisions[:20], 1):  # 最多显示20条
                decision_para = doc.add_paragraph(
                    f"{idx}. {decision.get('decision', '')}",
                    style='List Number'
                )
                if decision.get('maker'):
                    maker_run = decision_para.add_run(f"（决策人：{decision.get('maker')}）")
                    maker_run.font.size = Pt(10)
                    maker_run.font.color.rgb = RGBColor(102, 102, 102)
        else:
            doc.add_paragraph('本年度无关键决策记录', style='Intense Quote')
        
        doc.add_paragraph()  # 空行
        
        # 五、战略结构（年度报告特有）
        doc.add_heading('五、战略结构', 1)
        
        strategic_structures = report_data.get('strategic_structures', [])
        if strategic_structures:
            doc.add_paragraph('本年度共记录了以下战略结构：', style='Intense Quote')
            for structure in strategic_structures[:10]:  # 最多显示10个
                doc.add_paragraph(
                    f"• {structure.get('meeting_name', '')}（{structure.get('meeting_date', '')}）",
                    style='List Bullet'
                )
        else:
            doc.add_paragraph('本年度无战略结构记录', style='Intense Quote')
        
        doc.add_paragraph()  # 空行
        
        # 六、会议列表
        doc.add_heading('六、会议列表', 1)
        
        meetings = report_data.get('meetings', [])
        if meetings:
            meetings_table = doc.add_table(rows=len(meetings) + 1, cols=6)
            meetings_table.style = 'Light Grid Accent 1'
            meetings_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # 表头
            header_cells = meetings_table.rows[0].cells
            headers = ['会议名称', '日期', '层级', '周期类型', '状态', '行动项数']
            for i, header in enumerate(headers):
                header_cells[i].text = header
                header_cells[i].paragraphs[0].runs[0].font.bold = True
            
            # 数据行
            for idx, meeting in enumerate(meetings[:50], 1):  # 最多显示50条
                row_cells = meetings_table.rows[idx].cells
                row_cells[0].text = meeting.get('meeting_name', '')
                row_cells[1].text = meeting.get('meeting_date', '')[:10] if meeting.get('meeting_date') else ''
                row_cells[2].text = self._format_rhythm_level(meeting.get('rhythm_level', ''))
                row_cells[3].text = self._format_cycle_type(meeting.get('cycle_type', ''))
                row_cells[4].text = self._format_status(meeting.get('status', ''))
                row_cells[5].text = str(meeting.get('action_items_count', 0))
        else:
            doc.add_paragraph('本年度无会议记录', style='Intense Quote')
        
        # 页脚
        doc.add_paragraph()  # 空行
        footer_para = doc.add_paragraph()
        footer_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        footer_run = footer_para.add_run(f"报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        footer_run.font.size = Pt(9)
        footer_run.font.color.rgb = RGBColor(153, 153, 153)
        
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
        doc = Document()
        
        # 设置中文字体
        self._setup_chinese_fonts(doc)
        
        # 设置页面边距
        sections = doc.sections
        for section in sections:
            section.top_margin = Cm(2.5)
            section.bottom_margin = Cm(2.5)
            section.left_margin = Cm(3)
            section.right_margin = Cm(3)
        
        # 标题
        title = doc.add_heading(report_title, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 报告信息
        info_para = doc.add_paragraph()
        info_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info_run = info_para.add_run(f"报告周期：{period_year}年{period_month}月")
        info_run.font.size = Pt(12)
        info_run.font.color.rgb = RGBColor(102, 102, 102)
        
        if rhythm_level:
            level_para = doc.add_paragraph()
            level_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            level_run = level_para.add_run(f"节律层级：{rhythm_level}")
            level_run.font.size = Pt(12)
            level_run.font.color.rgb = RGBColor(102, 102, 102)
        
        doc.add_paragraph()  # 空行
        
        # 一、执行摘要
        doc.add_heading('一、执行摘要', 1)
        
        summary = report_data.get('summary', {})
        summary_table = doc.add_table(rows=7, cols=2)
        summary_table.style = 'Light Grid Accent 1'
        summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        summary_data = [
            ('会议总数', f"{summary.get('total_meetings', 0)}"),
            ('已完成会议数', f"{summary.get('completed_meetings', 0)}"),
            ('会议完成率', summary.get('completion_rate', '0%')),
            ('行动项总数', f"{summary.get('total_action_items', 0)}"),
            ('已完成行动项数', f"{summary.get('completed_action_items', 0)}"),
            ('逾期行动项数', f"{summary.get('overdue_action_items', 0)}"),
            ('行动项完成率', summary.get('action_completion_rate', '0%')),
        ]
        
        for i, (label, value) in enumerate(summary_data):
            summary_table.rows[i].cells[0].text = label
            summary_table.rows[i].cells[1].text = value
            summary_table.rows[i].cells[0].paragraphs[0].runs[0].font.bold = True
            summary_table.rows[i].cells[1].paragraphs[0].runs[0].font.size = Pt(11)
        
        doc.add_paragraph()  # 空行
        
        # 二、与上月对比（月度报告独有）
        doc.add_heading('二、与上月对比', 1)
        
        if comparison_data:
            prev_period = comparison_data.get('previous_period', '')
            current_period = comparison_data.get('current_period', '')
            
            comparison_para = doc.add_paragraph()
            comparison_para.add_run(f"对比周期：{prev_period} vs {current_period}")
            comparison_para.runs[0].font.bold = True
            comparison_para.runs[0].font.size = Pt(12)
            
            doc.add_paragraph()  # 空行
            
            # 对比表格
            comparison_table = doc.add_table(rows=6, cols=4)
            comparison_table.style = 'Light Grid Accent 1'
            comparison_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # 表头
            header_cells = comparison_table.rows[0].cells
            headers = ['指标', '本月', '上月', '变化']
            for i, header in enumerate(headers):
                header_cells[i].text = header
                header_cells[i].paragraphs[0].runs[0].font.bold = True
            
            # 对比数据
            comparisons = [
                ('会议总数', comparison_data.get('meetings_comparison', {})),
                ('已完成会议数', comparison_data.get('completed_meetings_comparison', {})),
                ('行动项总数', comparison_data.get('action_items_comparison', {})),
                ('已完成行动项数', comparison_data.get('completed_action_items_comparison', {})),
                ('完成率', comparison_data.get('completion_rate_comparison', {})),
            ]
            
            for idx, (label, comp_data) in enumerate(comparisons, 1):
                row_cells = comparison_table.rows[idx].cells
                row_cells[0].text = label
                
                if label == '完成率':
                    row_cells[1].text = comp_data.get('current', '0%')
                    row_cells[2].text = comp_data.get('previous', '0%')
                    change = comp_data.get('change', '0%')
                else:
                    row_cells[1].text = str(comp_data.get('current', 0))
                    row_cells[2].text = str(comp_data.get('previous', 0))
                    change_value = comp_data.get('change', 0)
                    change_rate = comp_data.get('change_rate', '0%')
                    change = f"{change_value:+d} ({change_rate})"
                
                row_cells[3].text = change
                
                # 根据变化值设置颜色
                if isinstance(comp_data, dict):
                    change_value = comp_data.get('change', 0) if label != '完成率' else comp_data.get('change_value', 0)
                    if change_value > 0:
                        row_cells[3].paragraphs[0].runs[0].font.color.rgb = RGBColor(0, 128, 0)  # 绿色
                    elif change_value < 0:
                        row_cells[3].paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 0, 0)  # 红色
        
        doc.add_paragraph()  # 空行
        
        # 三、按层级统计
        doc.add_heading('三、按层级统计', 1)
        
        by_level = report_data.get('by_level', {})
        if by_level:
            level_table = doc.add_table(rows=len(by_level) + 1, cols=3)
            level_table.style = 'Light Grid Accent 1'
            level_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # 表头
            header_cells = level_table.rows[0].cells
            header_cells[0].text = '节律层级'
            header_cells[1].text = '会议总数'
            header_cells[2].text = '已完成会议数'
            for cell in header_cells:
                cell.paragraphs[0].runs[0].font.bold = True
            
            # 数据行
            for idx, (level, data) in enumerate(by_level.items(), start=1):
                row_cells = level_table.rows[idx].cells
                row_cells[0].text = self._format_rhythm_level(level)
                row_cells[1].text = str(data.get('total', 0))
                row_cells[2].text = str(data.get('completed', 0))
        
        doc.add_paragraph()  # 空行
        
        # 四、行动项统计
        doc.add_heading('四、行动项统计', 1)
        
        action_summary = report_data.get('action_items_summary', {})
        action_table = doc.add_table(rows=5, cols=2)
        action_table.style = 'Light Grid Accent 1'
        action_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        action_data = [
            ('行动项总数', f"{action_summary.get('total', 0)}"),
            ('已完成', f"{action_summary.get('completed', 0)}"),
            ('逾期', f"{action_summary.get('overdue', 0)}"),
            ('进行中', f"{action_summary.get('in_progress', 0)}"),
        ]
        
        for i, (label, value) in enumerate(action_data):
            action_table.rows[i].cells[0].text = label
            action_table.rows[i].cells[1].text = value
            action_table.rows[i].cells[0].paragraphs[0].runs[0].font.bold = True
        
        doc.add_paragraph()  # 空行
        
        # 五、关键决策
        doc.add_heading('五、关键决策', 1)
        
        key_decisions = report_data.get('key_decisions', [])
        if key_decisions:
            for idx, decision in enumerate(key_decisions[:20], 1):  # 最多显示20条
                decision_para = doc.add_paragraph(
                    f"{idx}. {decision.get('decision', '')}",
                    style='List Number'
                )
                if decision.get('maker'):
                    maker_run = decision_para.add_run(f"（决策人：{decision.get('maker')}）")
                    maker_run.font.size = Pt(10)
                    maker_run.font.color.rgb = RGBColor(102, 102, 102)
        else:
            doc.add_paragraph('本月无关键决策记录', style='Intense Quote')
        
        doc.add_paragraph()  # 空行
        
        # 六、会议列表
        doc.add_heading('六、会议列表', 1)
        
        meetings = report_data.get('meetings', [])
        if meetings:
            meetings_table = doc.add_table(rows=len(meetings) + 1, cols=6)
            meetings_table.style = 'Light Grid Accent 1'
            meetings_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            # 表头
            header_cells = meetings_table.rows[0].cells
            headers = ['会议名称', '日期', '层级', '周期类型', '状态', '行动项数']
            for i, header in enumerate(headers):
                header_cells[i].text = header
                header_cells[i].paragraphs[0].runs[0].font.bold = True
            
            # 数据行
            for idx, meeting in enumerate(meetings[:50], 1):  # 最多显示50条
                row_cells = meetings_table.rows[idx].cells
                row_cells[0].text = meeting.get('meeting_name', '')
                row_cells[1].text = meeting.get('meeting_date', '')[:10] if meeting.get('meeting_date') else ''
                row_cells[2].text = self._format_rhythm_level(meeting.get('rhythm_level', ''))
                row_cells[3].text = self._format_cycle_type(meeting.get('cycle_type', ''))
                row_cells[4].text = self._format_status(meeting.get('status', ''))
                row_cells[5].text = str(meeting.get('action_items_count', 0))
        else:
            doc.add_paragraph('本月无会议记录', style='Intense Quote')
        
        # 页脚
        doc.add_paragraph()  # 空行
        footer_para = doc.add_paragraph()
        footer_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        footer_run = footer_para.add_run(f"报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        footer_run.font.size = Pt(9)
        footer_run.font.color.rgb = RGBColor(153, 153, 153)
        
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
