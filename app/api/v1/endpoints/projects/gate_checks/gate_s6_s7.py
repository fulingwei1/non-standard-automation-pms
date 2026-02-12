# -*- coding: utf-8 -*-
"""
gate_s6_s7 阶段门检查

包含gate_s6_s7相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from typing import List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Machine, Project



def check_gate_s6_to_s7(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """
    G6: S6→S7 阶段门校验 - 装配完成、联调通过
    """
    missing = []

    machines = db.query(Machine).filter(Machine.project_id == project.id).all()

    if not machines:
        missing.append("项目下没有机台")
        return (False, missing)

    for machine in machines:
        if machine.progress_pct < 100:
            missing.append(f"机台 {machine.machine_code} 装配未完成（进度：{machine.progress_pct}%，需达到100%）")

        if machine.status not in ["ASSEMBLED", "READY", "COMPLETED"]:
            missing.append(f"机台 {machine.machine_code} 状态未达到装配完成（当前状态：{machine.status}）")

    # 检查联调已通过
    from app.models.project import ProjectDocument
    debug_docs = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project.id,
        ProjectDocument.doc_type.in_(["DEBUG", "TEST", "COMMISSIONING"]),
        ProjectDocument.status == "APPROVED"
    ).count()

    if debug_docs == 0:
        missing.append("联调测试报告未提交或未通过（请上传联调报告并标记为已确认）")

    # 检查技术问题已解决
    from app.models.issue import Issue
    blocking_issues = db.query(Issue).filter(
        Issue.project_id == project.id,
        Issue.is_blocking,
        Issue.status.notin_(["RESOLVED", "CLOSED"])
    ).count()

    if blocking_issues > 0:
        missing.append(f"存在 {blocking_issues} 个未解决的阻塞问题（请先解决所有阻塞问题）")

    # 检查技术评审问题
    from app.models.technical_review import ReviewIssue, TechnicalReview
    unresolved_review_issues = db.query(ReviewIssue).join(
        TechnicalReview, ReviewIssue.review_id == TechnicalReview.id
    ).filter(
        TechnicalReview.project_id == project.id,
        ReviewIssue.status.notin_(["RESOLVED", "VERIFIED", "CLOSED"]),
        ReviewIssue.issue_level.in_(["A", "B"])
    ).count()

    if unresolved_review_issues > 0:
        missing.append(f"存在 {unresolved_review_issues} 个未解决的评审问题（A/B级问题必须解决）")

    return (len(missing) == 0, missing)


