# -*- coding: utf-8 -*-
"""
PDF 渲染器

使用 reportlab 生成 PDF 报告
"""

import os
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.report_framework.renderers.base import Renderer, ReportResult, RenderError


class PdfRenderer(Renderer):
    """
    PDF 渲染器

    使用 reportlab 将报告数据渲染为 PDF 格式
    """

    # 中文字体路径（可配置）
    FONT_PATHS = [
        "/System/Library/Fonts/PingFang.ttc",  # macOS
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux
        "C:/Windows/Fonts/msyh.ttc",  # Windows
    ]

    def __init__(self, output_dir: str = "reports/pdf"):
        """
        初始化 PDF 渲染器

        Args:
            output_dir: PDF 输出目录
        """
        self.output_dir = output_dir
        self._font_registered = False
        self._font_name = "Helvetica"  # 默认字体
        self._register_fonts()

    @property
    def format_name(self) -> str:
        return "pdf"

    @property
    def content_type(self) -> str:
        return "application/pdf"

    def _register_fonts(self) -> None:
        """注册中文字体"""
        if self._font_registered:
            return

        for font_path in self.FONT_PATHS:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont("Chinese", font_path))
                    self._font_registered = True
                    self._font_name = "Chinese"
                    return
                except Exception:
                    continue

        # 如果没有找到中文字体，使用默认字体
        self._font_registered = True
        self._font_name = "Helvetica"

    def _get_styles(self) -> Dict[str, ParagraphStyle]:
        """获取样式"""
        styles = getSampleStyleSheet()
        font_name = self._font_name

        return {
            "title": ParagraphStyle(
                "Title",
                parent=styles["Title"],
                fontName=font_name,
                fontSize=18,
                spaceAfter=20,
            ),
            "section_title": ParagraphStyle(
                "SectionTitle",
                parent=styles["Heading2"],
                fontName=font_name,
                fontSize=14,
                spaceBefore=15,
                spaceAfter=10,
            ),
            "normal": ParagraphStyle(
                "Normal",
                parent=styles["Normal"],
                fontName=font_name,
                fontSize=10,
            ),
            "metric_label": ParagraphStyle(
                "MetricLabel",
                parent=styles["Normal"],
                fontName=font_name,
                fontSize=9,
                textColor=colors.gray,
            ),
            "metric_value": ParagraphStyle(
                "MetricValue",
                parent=styles["Normal"],
                fontName=font_name,
                fontSize=14,
                textColor=colors.black,
            ),
        }

    def render(
        self,
        sections: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> ReportResult:
        """
        渲染报告为 PDF

        Args:
            sections: 渲染后的 section 数据
            metadata: 报告元数据

        Returns:
            ReportResult: PDF 格式的报告结果
        """
        try:
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_code = metadata.get("code", "report")
            file_name = f"{report_code}_{timestamp}.pdf"
            file_path = os.path.join(self.output_dir, file_name)

            # 获取页面方向
            orientation = metadata.get("orientation", "portrait")
            page_size = landscape(A4) if orientation == "landscape" else A4

            # 创建 PDF 文档
            doc = SimpleDocTemplate(
                file_path,
                pagesize=page_size,
                leftMargin=20 * mm,
                rightMargin=20 * mm,
                topMargin=20 * mm,
                bottomMargin=20 * mm,
            )

            # 构建内容
            elements = self._build_content(sections, metadata)

            # 生成 PDF
            doc.build(elements)

            return ReportResult(
                data={"file_path": file_path, "sections": sections},
                format=self.format_name,
                file_path=file_path,
                file_name=file_name,
                content_type=self.content_type,
                metadata=metadata,
            )

        except Exception as e:
            raise RenderError(f"PDF rendering failed: {e}")

    def _build_content(
        self,
        sections: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> List:
        """构建 PDF 内容"""
        styles = self._get_styles()
        elements = []

        # 标题
        title = metadata.get("name", "报告")
        elements.append(Paragraph(title, styles["title"]))

        # 生成时间
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"生成时间: {gen_time}", styles["normal"]))
        elements.append(Spacer(1, 10 * mm))

        # 渲染各 section
        for section in sections:
            section_elements = self._render_section(section, styles)
            elements.extend(section_elements)

        return elements

    def _render_section(
        self,
        section: Dict[str, Any],
        styles: Dict[str, ParagraphStyle],
    ) -> List:
        """渲染单个 section"""
        elements = []
        section_type = section.get("type")
        title = section.get("title")

        if title:
            elements.append(Paragraph(title, styles["section_title"]))

        if section_type == "metrics":
            elements.extend(self._render_metrics(section, styles))
        elif section_type == "table":
            elements.extend(self._render_table(section, styles))
        elif section_type == "chart":
            elements.append(Paragraph("[图表: 需要集成图表库]", styles["normal"]))

        elements.append(Spacer(1, 5 * mm))
        return elements

    def _render_metrics(
        self,
        section: Dict[str, Any],
        styles: Dict[str, ParagraphStyle],
    ) -> List:
        """渲染指标卡片"""
        elements = []
        items = section.get("items", [])

        if not items:
            return elements

        # 将指标排列成表格（每行 4 个）
        cols = 4
        rows = []
        current_row = []

        for item in items:
            label = str(item.get("label", ""))
            value = str(item.get("value", ""))
            cell_content = f"{label}\n{value}"
            current_row.append(cell_content)

            if len(current_row) >= cols:
                rows.append(current_row)
                current_row = []

        if current_row:
            # 补齐空单元格
            while len(current_row) < cols:
                current_row.append("")
            rows.append(current_row)

        if rows:
            table = Table(rows, colWidths=[45 * mm] * cols)
            table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, -1), self._font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("BACKGROUND", (0, 0), (-1, -1), colors.Color(0.95, 0.95, 0.95)),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(table)

        return elements

    def _render_table(
        self,
        section: Dict[str, Any],
        styles: Dict[str, ParagraphStyle],
    ) -> List:
        """渲染数据表格"""
        elements = []
        data = section.get("data", [])
        columns = section.get("columns", [])

        if not data or not columns:
            elements.append(Paragraph("无数据", styles["normal"]))
            return elements

        # 构建表头
        headers = [col.get("label", col.get("field", "")) for col in columns]
        table_data = [headers]

        # 构建数据行
        for row in data[:50]:  # 限制最多 50 行
            row_data = []
            for col in columns:
                field = col.get("field", "")
                value = row.get(field, "")
                # 格式化值
                if value is None:
                    value = ""
                else:
                    value = str(value)[:30]  # 截断过长的值
                row_data.append(value)
            table_data.append(row_data)

        # 计算列宽
        col_count = len(columns)
        available_width = 170 * mm  # A4 宽度减去边距
        col_width = available_width / col_count

        table = Table(table_data, colWidths=[col_width] * col_count)
        table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, -1), self._font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            # 表头样式
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            # 数据行样式
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)

        # 显示数据量提示
        if len(data) > 50:
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(f"(显示前 50 条，共 {len(data)} 条)", styles["normal"]))

        return elements
