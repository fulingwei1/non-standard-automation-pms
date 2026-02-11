# -*- coding: utf-8 -*-
"""
验收报告生成服务

提供验收报告编号生成、内容构建、版本管理和文件保存功能
"""

import os
from datetime import datetime
from typing import Any, Optional, Tuple

from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter

# 标记 reportlab 是否可用
try:
    import reportlab  # noqa: F401
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_report_no(db: Session, report_type: str) -> str:
    """
    生成验收报告编号

    格式：{type}-{yyyymmdd}-{seq:03d}

    Args:
        db: 数据库会话
        report_type: 报告类型（如 'FAT', 'SAT'）

    Returns:
        报告编号字符串
    """
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    prefix = f"{report_type}-{date_str}-"

    # 查询当天该类型的报告数量
    from app.models.acceptance import AcceptanceReport
    count_query = db.query(AcceptanceReport)
    count_query = apply_like_filter(
        count_query,
        AcceptanceReport,
        f"{prefix}%",
        "report_no",
        use_ilike=False,
    )
    count = count_query.scalar() or 0

    if isinstance(count, int):
        seq = count + 1
    else:
        seq = 1

    return f"{prefix}{str(seq).zfill(3)}"


def build_report_content(
    db: Session,
    order: Any,
    report_no: str,
    version: int,
    user: Any,
) -> str:
    """
    构建验收报告文本内容

    Args:
        db: 数据库会话
        order: 验收单对象
        report_no: 报告编号
        version: 版本号
        user: 报告生成用户

    Returns:
        报告内容字符串
    """
    lines = [
        f"验收报告: {report_no}",
        f"版本: V{version}",
        f"验收单号: {order.order_no}",
        f"验收类型: {order.acceptance_type}",
        f"通过率: {order.pass_rate}%",
        f"总检测项: {order.total_items}",
        f"通过项: {order.passed_items}",
        f"未通过项: {order.failed_items}",
    ]

    if order.customer_signer:
        lines.append(f"客户签字: {order.customer_signer}")

    if user:
        signer_name = getattr(user, 'real_name', None) or getattr(user, 'username', '')
        lines.append(f"生成人: {signer_name}")

    return "\n".join(lines)


def get_report_version(db: Session, order_id: int, report_type: str) -> int:
    """
    获取报告版本号

    Args:
        db: 数据库会话
        order_id: 验收单ID
        report_type: 报告类型

    Returns:
        下一个版本号（如果没有已有报告则返回1）
    """
    from app.models.acceptance import AcceptanceReport

    latest = db.query(AcceptanceReport).filter(
        AcceptanceReport.order_id == order_id,
        AcceptanceReport.report_type == report_type,
    ).order_by(
        AcceptanceReport.version.desc()
    ).first()

    if latest:
        return latest.version + 1
    return 1


def save_report_file(
    content: str,
    order_no: str,
    report_type: str,
    use_pdf: bool,
    order: Any,
    db: Session,
    user: Any,
) -> Optional[Tuple[str, str]]:
    """
    保存报告文件

    如果 reportlab 不可用则降级为文本格式

    Args:
        content: 报告内容
        order_no: 验收单号
        report_type: 报告类型
        use_pdf: 是否使用PDF格式
        order: 验收单对象
        db: 数据库会话
        user: 用户对象

    Returns:
        (相对路径, 文件名) 元组
    """
    upload_dir = os.path.join("uploads", "reports")
    os.makedirs(upload_dir, exist_ok=True)

    if REPORTLAB_AVAILABLE and use_pdf:
        ext = "pdf"
    else:
        ext = "txt"

    filename = f"{order_no}_{report_type}.{ext}"
    file_path = os.path.join(upload_dir, filename)
    relative_path = os.path.join("reports", filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return (relative_path, filename)
