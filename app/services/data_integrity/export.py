# -*- coding: utf-8 -*-
"""
导出功能模块
提供数据质量报告的导出功能（JSON/Excel/PDF）
"""

import io
from typing import Any, Dict, Optional

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ExportMixin:
    """导出功能混入类"""

    def export_data_quality_report(
        self,
        period_id: int,
        department_id: Optional[int] = None,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """
        导出数据质量报告

        Args:
            period_id: 考核周期ID
            department_id: 部门ID（可选）
            format: 导出格式（json/excel/pdf）

        Returns:
            报告数据（格式根据format参数）
        """
        report = self.generate_data_quality_report(period_id, department_id)

        if format == 'json':
            return report
        elif format == 'excel':
            # 使用pandas生成Excel
            return self._export_to_excel(report)
        elif format == 'pdf':
            # 使用reportlab生成PDF
            return self._export_to_pdf(report)
        else:
            return report

    def _export_to_excel(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        导出报告为Excel格式

        Args:
            report: 报告数据

        Returns:
            包含Excel文件内容的字典
        """
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 概览信息
            summary_data = {
                '指标': ['数据完整率', '工程师总数', '有数据的工程师', '平均完整率'],
                '值': [
                    f"{report.get('overall_completeness', 0):.1f}%",
                    report.get('total_engineers', 0),
                    report.get('engineers_with_data', 0),
                    f"{report.get('average_completeness', 0):.1f}%"
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='概览', index=False)

            # 详细数据
            if 'details' in report and report['details']:
                details_df = pd.DataFrame(report['details'])
                details_df.to_excel(writer, sheet_name='详细数据', index=False)

            # 缺失数据统计
            if 'missing_summary' in report and report['missing_summary']:
                missing_df = pd.DataFrame(report['missing_summary'])
                missing_df.to_excel(writer, sheet_name='缺失统计', index=False)

        output.seek(0)
        return {
            'format': 'excel',
            'content': output.getvalue(),
            'filename': f"data_quality_report_{report.get('period_id', 'unknown')}.xlsx",
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

    def _export_to_pdf(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        导出报告为PDF格式

        Args:
            report: 报告数据

        Returns:
            包含PDF文件内容的字典
        """
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        elements = []

        # 标题
        title_style = styles['Heading1']
        elements.append(Paragraph("数据质量报告", title_style))
        elements.append(Spacer(1, 10*mm))

        # 概览表格
        overview_data = [
            ['指标', '值'],
            ['数据完整率', f"{report.get('overall_completeness', 0):.1f}%"],
            ['工程师总数', str(report.get('total_engineers', 0))],
            ['有数据的工程师', str(report.get('engineers_with_data', 0))],
            ['平均完整率', f"{report.get('average_completeness', 0):.1f}%"]
        ]

        overview_table = Table(overview_data, colWidths=[80*mm, 60*mm])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(overview_table)

        doc.build(elements)
        output.seek(0)

        return {
            'format': 'pdf',
            'content': output.getvalue(),
            'filename': f"data_quality_report_{report.get('period_id', 'unknown')}.pdf",
            'content_type': 'application/pdf'
        }
