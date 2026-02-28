#!/usr/bin/env python3
"""生成代码质量分析报告 PDF"""

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


# 注册中文字体
def register_chinese_font():
    """尝试注册中文字体"""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                return "ChineseFont"
            except (OSError, RuntimeError, Exception):
                continue
    return "Helvetica"


def create_pdf(output_path):
    """创建代码分析报告 PDF"""

    font_name = register_chinese_font()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # 自定义样式
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=24,
        spaceAfter=30,
        alignment=1,
    )

    h1_style = ParagraphStyle(
        "CustomH1",
        parent=styles["Heading1"],
        fontName=font_name,
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor("#1a1a2e"),
    )

    h2_style = ParagraphStyle(
        "CustomH2",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor("#16213e"),
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        spaceAfter=8,
        leading=14,
    )

    story = []

    # 标题
    story.append(Paragraph("代码质量分析报告", title_style))
    story.append(
        Paragraph(
            "非标自动化项目管理系统",
            ParagraphStyle(
                "Subtitle",
                parent=body_style,
                fontSize=14,
                alignment=1,
                textColor=colors.gray,
            ),
        )
    )
    story.append(
        Paragraph(
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ParagraphStyle(
                "Date",
                parent=body_style,
                fontSize=10,
                alignment=1,
                textColor=colors.gray,
            ),
        )
    )
    story.append(Spacer(1, 30))

    # 项目概览
    story.append(Paragraph("1. 项目规模统计", h1_style))

    overview_data = [
        ["类别", "数量", "说明"],
        ["前端页面 (Pages)", "269", "frontend/src/pages/*.jsx"],
        ["后端模型 (Models)", "52", "app/models/*.py"],
        ["API 端点模块", "66", "app/api/v1/endpoints/"],
        ["业务服务 (Services)", "143", "app/services/*.py"],
        ["总代码行数", "486,386", "包含所有 .py, .jsx, .js 文件"],
    ]

    overview_table = Table(overview_data, colWidths=[5 * cm, 3 * cm, 8 * cm])
    overview_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f5f5f5")],
                ),
            ]
        )
    )
    story.append(overview_table)
    story.append(Spacer(1, 20))

    # 严重超标文件
    story.append(Paragraph("2. 严重超标文件 (>2000 行)", h1_style))
    story.append(Paragraph("以下文件代码量严重超标，建议优先重构：", body_style))

    critical_data = [
        ["文件路径", "行数", "问题描述"],
        ["app/utils/scheduled_tasks.py", "3845", "定时任务全堆一个文件"],
        ["frontend/src/pages/ECNDetail.jsx", "3546", "单页面组件过大"],
        ["frontend/src/pages/HRManagerDashboard.jsx", "3356", "仪表板功能过多"],
        ["frontend/src/services/api.js", "3068", "API 调用全集中"],
        ["frontend/src/pages/ECNManagement.jsx", "2696", "ECN 管理页面臃肿"],
        ["frontend/src/pages/ServiceTicketManagement.jsx", "2606", "工单管理页面"],
        ["app/api/v1/endpoints/projects/extended.py", "2476", "项目 API 扩展"],
        ["app/api/v1/endpoints/acceptance.py", "2472", "验收端点"],
        ["app/api/v1/endpoints/issues.py", "2408", "问题管理端点"],
        ["app/api/v1/endpoints/alerts.py", "2232", "预警端点"],
    ]

    critical_table = Table(critical_data, colWidths=[8 * cm, 2 * cm, 6 * cm])
    critical_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#c0392b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.HexColor("#ffeaea"), colors.white],
                ),
            ]
        )
    )
    story.append(critical_table)
    story.append(Spacer(1, 20))

    # 需要关注的文件
    story.append(Paragraph("3. 需要关注的文件 (1500-2000 行)", h1_style))

    warning_data = [
        ["文件路径", "行数"],
        ["frontend/src/pages/SalesTeam.jsx", "2092"],
        ["frontend/src/pages/IssueManagement.jsx", "2035"],
        ["app/api/v1/endpoints/management_rhythm.py", "1993"],
        ["frontend/src/pages/QuoteManagement.jsx", "1979"],
        ["frontend/src/pages/ProductionManagerDashboard.jsx", "1944"],
        ["frontend/src/pages/SalesDirectorWorkstation.jsx", "1912"],
        ["app/schemas/sales.py", "1888"],
        ["frontend/src/pages/MaterialAnalysis.jsx", "1867"],
        ["app/api/v1/endpoints/presale.py", "1798"],
        ["frontend/src/components/layout/Sidebar.jsx", "1712"],
        ["frontend/src/pages/PaymentManagement.jsx", "1688"],
        ["frontend/src/pages/WorkerWorkstation.jsx", "1679"],
    ]

    warning_table = Table(warning_data, colWidths=[12 * cm, 4 * cm])
    warning_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e67e22")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.HexColor("#fff5e6"), colors.white],
                ),
            ]
        )
    )
    story.append(warning_table)
    story.append(Spacer(1, 20))

    # 问题分析
    story.append(Paragraph("4. 问题分析", h1_style))

    problems = [
        ("上帝组件", "Dashboard/Detail 页面承担太多职责，应拆分为多个子组件"),
        ("API 集中化", "api.js 3000+ 行，所有接口挤一个文件，应按业务域拆分"),
        ("缺乏拆分", "页面内嵌大量子组件逻辑，未抽离成独立组件"),
        ("Schema 臃肿", "sales.py 1888 行，数据模型过于复杂，应拆分"),
    ]

    for title, desc in problems:
        story.append(Paragraph(f"<b>• {title}</b>: {desc}", body_style))

    story.append(Spacer(1, 20))

    # 重构建议
    story.append(Paragraph("5. 重构优先级建议", h1_style))

    refactor_data = [
        ["优先级", "文件", "建议方案"],
        ["P0", "scheduled_tasks.py", "按任务类型拆分多个模块"],
        ["P0", "api.js", "按业务域拆分 (project/, sales/, hr/)"],
        ["P1", "ECNDetail.jsx", "抽离 Tab 组件、表单组件"],
        ["P1", "HRManagerDashboard.jsx", "拆分成多个子仪表板组件"],
        ["P2", "Sidebar.jsx", "菜单配置抽离成 JSON/常量文件"],
        ["P2", "acceptance.py", "拆分验收相关的子端点"],
    ]

    refactor_table = Table(refactor_data, colWidths=[2 * cm, 5 * cm, 9 * cm])
    refactor_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27ae60")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.HexColor("#e8f8f0"), colors.white],
                ),
            ]
        )
    )
    story.append(refactor_table)
    story.append(Spacer(1, 20))

    # 后端核心模块
    story.append(Paragraph("6. 后端核心模块概览", h1_style))

    backend_data = [
        ["模块", "文件", "说明"],
        ["项目管理", "project.py, machine.py", "项目与设备管理"],
        ["物料采购", "material.py, purchase.py", "物料采购 BOM"],
        ["工程变更", "ecn.py", "工程变更通知 ECN"],
        ["验收管理", "acceptance.py", "FAT/SAT 验收"],
        ["外协管理", "outsourcing.py, supplier.py", "外协与供应商"],
        ["销售管理", "sales.py, presale.py", "销售与售前"],
        ["生产进度", "production.py, progress.py", "生产与进度跟踪"],
        ["组织人员", "user.py, organization.py", "用户与组织架构"],
        ["预警通知", "alert.py, notification.py", "预警与通知"],
        ["绩效工时", "performance.py, timesheet.py", "绩效与工时管理"],
    ]

    backend_table = Table(backend_data, colWidths=[3 * cm, 5 * cm, 8 * cm])
    backend_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#ebf5fb")],
                ),
            ]
        )
    )
    story.append(backend_table)

    # 构建 PDF
    doc.build(story)
    print(f"PDF 报告已生成: {output_path}")


if __name__ == "__main__":
    output_path = "/Users/flw/non-standard-automation-pm/docs/代码质量分析报告.pdf"
    create_pdf(output_path)
