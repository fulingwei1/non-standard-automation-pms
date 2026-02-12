# -*- coding: utf-8 -*-
"""
PDF 内容构建工具函数
"""

from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

try:
    from reportlab.lib import colors  # noqa: F401
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Spacer, Table  # noqa: F401
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.models.acceptance import (
    AcceptanceIssue,
    AcceptanceOrder,
    AcceptanceOrderItem,
    AcceptanceSignature,
)
from app.models.project import Machine, Project
from app.services.pdf_styles import (
    get_info_table_style,
    get_issue_table_style,
    get_signature_table_style,
    get_stats_table_style,
)


def build_basic_info_section(
    order: AcceptanceOrder,
    project: Project,
    machine: Machine,
    report_no: str,
    version: int,
    styles: Dict[str, Any]
) -> List[Any]:
    """
    构建基本信息部分

    Returns:
        List[Any]: PDF 内容元素列表
    """
    if not REPORTLAB_AVAILABLE:
        return []

    from reportlab.platypus import Paragraph, Spacer, Table

    story = []

    # 标题
    story.append(Paragraph("设备验收报告", styles['title']))
    story.append(Spacer(1, 0.5*cm))

    # 验收类型中文
    type_map = {
        "FAT": "出厂验收",
        "SAT": "现场验收",
        "FINAL": "终验收"
    }
    acceptance_type_cn = type_map.get(order.acceptance_type, order.acceptance_type)

    # 基本信息表格
    info_data = [
        ["报告编号", report_no],
        ["验收单号", order.order_no],
        ["验收类型", acceptance_type_cn],
        ["版本号", f"V{version}"],
        ["项目名称", project.project_name if project else "N/A"],
        ["设备名称", machine.machine_name if machine else "N/A"],
        ["验收日期", order.actual_end_date.strftime('%Y年%m月%d日') if order.actual_end_date else "N/A"],
        ["验收地点", order.location or "N/A"],
    ]

    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(get_info_table_style())
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))

    return story


def build_statistics_section(
    order: AcceptanceOrder,
    db: Session,
    styles: Dict[str, Any]
) -> List[Any]:
    """
    构建验收项目统计部分

    Returns:
        List[Any]: PDF 内容元素列表
    """
    if not REPORTLAB_AVAILABLE:
        return []

    from reportlab.platypus import Paragraph, Spacer, Table

    story = []

    story.append(Paragraph("一、验收项目统计", styles['heading']))

    # 获取检查项按分类统计
    items = db.query(AcceptanceOrderItem).filter(
        AcceptanceOrderItem.order_id == order.id
    ).order_by(
        AcceptanceOrderItem.category_code,
        AcceptanceOrderItem.sort_order
    ).all()

    # 按分类统计
    category_stats = {}
    for item in items:
        cat_code = item.category_code
        if cat_code not in category_stats:
            category_stats[cat_code] = {
                'name': item.category_name,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'na': 0,
                'conditional': 0
            }

        stats = category_stats[cat_code]
        stats['total'] += 1
        if item.result_status == 'PASSED':
            stats['passed'] += 1
        elif item.result_status == 'FAILED':
            stats['failed'] += 1
        elif item.result_status == 'NA':
            stats['na'] += 1
        elif item.result_status == 'CONDITIONAL':
            stats['conditional'] += 1

    # 构建统计表格
    stats_data = [['分类', '总数', '通过', '不通过', '不适用', '有条件通过', '通过率']]

    total_all = {'total': 0, 'passed': 0, 'failed': 0, 'na': 0, 'conditional': 0}

    for cat_code, stats in sorted(category_stats.items()):
        # 计算通过率（不适用不计入总数，有条件通过按0.8权重）
        valid_total = stats['total'] - stats['na']
        if valid_total > 0:
            effective_passed = stats['passed'] + stats['conditional'] * 0.8
            pass_rate = (effective_passed / valid_total) * 100
        else:
            pass_rate = 100.0

        stats_data.append([
            stats['name'],
            str(stats['total']),
            str(stats['passed']),
            str(stats['failed']),
            str(stats['na']),
            str(stats['conditional']),
            f"{pass_rate:.1f}%"
        ])

        # 累计总计
        for key in total_all:
            total_all[key] += stats[key]

    # 添加合计行
    valid_total_all = total_all['total'] - total_all['na']
    if valid_total_all > 0:
        effective_passed_all = total_all['passed'] + total_all['conditional'] * 0.8
        pass_rate_all = (effective_passed_all / valid_total_all) * 100
    else:
        pass_rate_all = 100.0

    stats_data.append([
        '<b>合计</b>',
        str(total_all['total']),
        str(total_all['passed']),
        str(total_all['failed']),
        str(total_all['na']),
        str(total_all['conditional']),
        f"<b>{pass_rate_all:.1f}%</b>"
    ])

    stats_table = Table(stats_data, colWidths=[3*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 2*cm])
    stats_table.setStyle(get_stats_table_style())
    story.append(stats_table)
    story.append(Spacer(1, 0.5*cm))

    return story


def build_conclusion_section(
    order: AcceptanceOrder,
    styles: Dict[str, Any]
) -> List[Any]:
    """
    构建验收结论部分

    Returns:
        List[Any]: PDF 内容元素列表
    """
    if not REPORTLAB_AVAILABLE:
        return []

    from reportlab.platypus import Paragraph, Spacer

    story = []

    story.append(Paragraph("二、验收结论", styles['heading']))

    result_map = {
        "PASSED": "通过",
        "FAILED": "不通过",
        "CONDITIONAL": "有条件通过"
    }
    result_cn = result_map.get(order.overall_result, order.overall_result or "未填写")

    conclusion_text = f"本次验收结果：<b>{result_cn}</b>"
    if order.conclusion:
        conclusion_text += f"<br/><br/>{order.conclusion}"
    if order.conditions:
        conclusion_text += f"<br/><br/>条件说明：{order.conditions}"

    story.append(Paragraph(conclusion_text, styles['normal']))
    story.append(Spacer(1, 0.3*cm))

    return story


def build_issues_section(
    order: AcceptanceOrder,
    db: Session,
    styles: Dict[str, Any]
) -> List[Any]:
    """
    构建验收问题部分

    Returns:
        List[Any]: PDF 内容元素列表
    """
    if not REPORTLAB_AVAILABLE:
        return []

    from reportlab.platypus import Paragraph, Spacer, Table

    story = []

    issues = db.query(AcceptanceIssue).filter(
        AcceptanceIssue.order_id == order.id
    ).all()

    if issues:
        story.append(Paragraph("三、验收问题", styles['heading']))

        total_issues = len(issues)
        resolved_issues = len([i for i in issues if i.status in ["RESOLVED", "CLOSED"]])
        blocking_issues = len([i for i in issues if i.is_blocking])

        issue_summary = f"""
        总问题数：{total_issues}个<br/>
        已解决：{resolved_issues}个<br/>
        待解决：{total_issues - resolved_issues}个<br/>
        阻塞问题：{blocking_issues}个
        """
        story.append(Paragraph(issue_summary, styles['normal']))
        story.append(Spacer(1, 0.3*cm))

        # 问题列表（仅显示前10个）
        if len(issues) > 0:
            issue_data = [['问题编号', '标题', '严重程度', '状态', '是否阻塞']]
            for issue in issues[:10]:  # 最多显示10个问题
                severity_map = {
                    "CRITICAL": "严重",
                    "MAJOR": "一般",
                    "MINOR": "轻微"
                }
                status_map = {
                    "OPEN": "待处理",
                    "PROCESSING": "处理中",
                    "RESOLVED": "已解决",
                    "CLOSED": "已关闭",
                    "DEFERRED": "已延期"
                }
                issue_data.append([
                    issue.issue_no,
                    issue.title[:20] + "..." if len(issue.title) > 20 else issue.title,
                    severity_map.get(issue.severity, issue.severity),
                    status_map.get(issue.status, issue.status),
                    "是" if issue.is_blocking else "否"
                ])

            if len(issues) > 10:
                issue_data.append([f"（还有 {len(issues) - 10} 个问题未显示）", "", "", "", ""])

            issue_table = Table(issue_data, colWidths=[2.5*cm, 5*cm, 2*cm, 2*cm, 2*cm])
            issue_table.setStyle(get_issue_table_style())
            story.append(issue_table)
            story.append(Spacer(1, 0.3*cm))

    return story


def build_signatures_section(
    order: AcceptanceOrder,
    db: Session,
    styles: Dict[str, Any]
) -> List[Any]:
    """
    构建签字信息部分

    Returns:
        List[Any]: PDF 内容元素列表
    """
    if not REPORTLAB_AVAILABLE:
        return []

    from reportlab.platypus import Paragraph, Spacer, Table

    story = []

    story.append(Paragraph("四、签字确认", styles['heading']))

    signatures = db.query(AcceptanceSignature).filter(
        AcceptanceSignature.order_id == order.id
    ).all()

    if signatures:
        signature_data = [['签字人类型', '签字人', '角色', '公司', '签字时间']]
        for sig in signatures:
            signer_type_map = {
                "QA": "质检",
                "PM": "项目经理",
                "CUSTOMER": "客户",
                "WITNESS": "见证人"
            }
            signature_data.append([
                signer_type_map.get(sig.signer_type, sig.signer_type),
                sig.signer_name,
                sig.signer_role or "N/A",
                sig.signer_company or "N/A",
                sig.signed_at.strftime('%Y-%m-%d %H:%M') if sig.signed_at else "N/A"
            ])

        sig_table = Table(signature_data, colWidths=[2.5*cm, 3*cm, 2.5*cm, 3*cm, 3*cm])
        sig_table.setStyle(get_signature_table_style())
        story.append(sig_table)
    else:
        story.append(Paragraph("暂无签字记录", styles['normal']))

    story.append(Spacer(1, 0.3*cm))

    return story


def build_footer_section(
    current_user: Any,
    styles: Dict[str, Any]
) -> List[Any]:
    """
    构建页脚部分

    Returns:
        List[Any]: PDF 内容元素列表
    """
    if not REPORTLAB_AVAILABLE:
        return []

    from reportlab.platypus import Paragraph, Spacer

    story = []

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}<br/>"
        f"生成人：{current_user.real_name or current_user.username}",
        styles['footer']
    ))

    return story
