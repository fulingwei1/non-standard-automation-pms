# -*- coding: utf-8 -*-
"""
验收报告工具函数

从 acceptance_report_service 提取的工具函数
"""

import hashlib
import logging
import os
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.acceptance import AcceptanceOrder, AcceptanceReport
from app.models.user import User

logger = logging.getLogger(__name__)


def generate_report_no(db: Session, report_type: str) -> str:
    """
    生成报告编号

    Args:
        db: 数据库会话
        report_type: 报告类型（FAT/SAT/FINAL）

    Returns:
        str: 报告编号
    """
    today = datetime.now().strftime("%Y%m%d")
    prefix = "FAT" if report_type == "FAT" else "SAT" if report_type == "SAT" else "AR"

    count = db.query(func.count(AcceptanceReport.id)).filter(
        AcceptanceReport.report_no.like(f"{prefix}-{today}-%")
    ).scalar() or 0

    seq = count + 1
    return f"{prefix}-{today}-{seq:03d}"


def get_report_version(db: Session, order_id: int, report_type: str) -> int:
    """
    获取报告版本号

    Args:
        db: 数据库会话
        order_id: 验收单ID
        report_type: 报告类型

    Returns:
        int: 版本号
    """
    existing_report = db.query(AcceptanceReport).filter(
        AcceptanceReport.order_id == order_id,
        AcceptanceReport.report_type == report_type
    ).order_by(desc(AcceptanceReport.version)).first()

    return (existing_report.version + 1) if existing_report else 1


def save_report_file(
    report_content: str,
    report_no: str,
    report_type: str,
    include_signatures: bool,
    order: AcceptanceOrder,
    db: Session,
    current_user: User,
) -> Tuple[str, int, str]:
    """
    保存报告文件

    Args:
        report_content: 报告内容
        report_no: 报告编号
        report_type: 报告类型
        include_signatures: 是否包含签名
        order: 验收单对象
        db: 数据库会话
        current_user: 当前用户

    Returns:
        tuple: (文件相对路径, 文件大小, 文件哈希)
    """
    # 确保上传目录存在
    report_dir = os.path.join(settings.UPLOAD_DIR, "reports")
    os.makedirs(report_dir, exist_ok=True)

    version = get_report_version(db, order.id, report_type)

    try:
        # 尝试生成PDF（如果reportlab可用）
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
            from io import BytesIO

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#366092'),
                spaceAfter=30,
            )

            # 标题
            story.append(Paragraph("验收报告", title_style))
            story.append(Spacer(1, 0.2 * inch))

            # 基本信息
            story.append(Paragraph(f"<b>报告编号：</b>{report_no}", styles['Normal']))
            order_no = order.order_no if hasattr(order, 'order_no') else f'ORDER-{order.id}'
            story.append(Paragraph(f"<b>验收单号：</b>{order_no}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

            # 项目信息
            project_name = order.project.project_name if getattr(order, "project", None) else "N/A"
            machine_name = order.machine.machine_name if getattr(order, "machine", None) else "N/A"

            story.append(Paragraph("<b>项目信息</b>", styles['Heading2']))
            story.append(Paragraph(f"项目名称：{project_name}", styles['Normal']))
            story.append(Paragraph(f"机台名称：{machine_name}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))

            # 验收结果
            story.append(Paragraph("<b>验收结果</b>", styles['Heading2']))
            data = [
                ['验收状态', order.status or 'N/A'],
                ['验收日期', order.actual_end_date.strftime('%Y-%m-%d') if order.actual_end_date else 'N/A'],
                ['合格率', f"{order.pass_rate or 0}%"],
            ]

            table = Table(data, colWidths=[2 * inch, 4 * inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (1, 0), (1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.2 * inch))

            # 生成PDF
            doc.build(story)
            buffer.seek(0)
            pdf_bytes = buffer.read()

            # 保存PDF文件
            file_rel_path = f"reports/{report_no}.pdf"
            file_full_path = os.path.join(settings.UPLOAD_DIR, file_rel_path)
            with open(file_full_path, "wb") as f:
                f.write(pdf_bytes)
            file_size = len(pdf_bytes)
            file_hash = hashlib.sha256(pdf_bytes).hexdigest()

            return file_rel_path, file_size, file_hash
        except ImportError:
            # reportlab未安装，使用文本格式
            pass

    except Exception as e:
        # 如果PDF生成失败，回退到文本格式
        logger.warning(f"PDF生成失败，使用文本格式: {str(e)}", exc_info=True)

    # 生成文本报告
    file_rel_path = f"reports/{report_no}.txt"
    file_full_path = os.path.join(settings.UPLOAD_DIR, file_rel_path)
    file_bytes = report_content.encode("utf-8")
    with open(file_full_path, "wb") as f:
        f.write(file_bytes)
    file_size = len(file_bytes)
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    return file_rel_path, file_size, file_hash


def build_report_content(
    db: Session,
    order: AcceptanceOrder,
    report_no: str,
    version: int,
    current_user: User
) -> str:
    """
    构建报告内容文本

    Args:
        db: 数据库会话
        order: 验收单对象
        report_no: 报告编号
        version: 版本号
        current_user: 当前用户

    Returns:
        str: 报告内容
    """
    from app.models.acceptance import AcceptanceIssue

    project_name = order.project.project_name if getattr(order, "project", None) else None
    machine_name = order.machine.machine_name if getattr(order, "machine", None) else None

    qa_signer_name = None
    if order.qa_signer_id:
        qa_user = db.query(User).filter(User.id == order.qa_signer_id).first()
        if qa_user:
            qa_signer_name = qa_user.real_name or qa_user.username

    total_issues = (
        db.query(func.count(AcceptanceIssue.id))
        .filter(AcceptanceIssue.order_id == order.id)
        .scalar()
    ) or 0

    resolved_issues = (
        db.query(func.count(AcceptanceIssue.id))
        .filter(
            AcceptanceIssue.order_id == order.id,
            AcceptanceIssue.status.in_(["RESOLVED", "CLOSED"]),
        )
        .scalar()
    ) or 0

    order_completed_at = order.actual_end_date

    return f"""
验收报告

报告编号：{report_no}
验收单号：{order.order_no if hasattr(order, 'order_no') else f'ORDER-{order.id}'}
报告类型：{order.acceptance_type if hasattr(order, 'acceptance_type') else report_type}
版本号：{version}

项目信息：
- 项目名称：{project_name or 'N/A'}
- 机台名称：{machine_name or 'N/A'}

验收结果：
- 验收状态：{order.status}
- 验收日期：{order_completed_at.strftime('%Y-%m-%d') if order_completed_at else 'N/A'}
- 合格率：{order.pass_rate or 0}%

检查项统计：
- 总检查项：{order.total_items or 0}
- 合格项：{order.passed_items or 0}
- 不合格项：{order.failed_items or 0}

问题统计：
- 总问题数：{total_issues}
- 已解决：{resolved_issues}
- 待解决：{total_issues - resolved_issues}

签字信息：
- 质检签字：{qa_signer_name or 'N/A'}
- 客户签字：{order.customer_signer if hasattr(order, 'customer_signer') else 'N/A'}

报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
生成人：{current_user.real_name or current_user.username}
"""
