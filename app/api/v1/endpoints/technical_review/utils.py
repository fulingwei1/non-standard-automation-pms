# -*- coding: utf-8 -*-
"""
技术评审 - 辅助工具函数
"""

import json
from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.api.v1.endpoints.issues.utils import generate_issue_no as generate_project_issue_no
from app.models.issue import Issue
from app.models.technical_review import ReviewIssue, TechnicalReview
from app.models.user import User


def generate_review_no(db: Session, review_type: str) -> str:
    """生成评审编号：RV-{TYPE}-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RV-{review_type}-{today}-"
    max_review_query = db.query(TechnicalReview)
    max_review_query = apply_like_filter(
        max_review_query,
        TechnicalReview,
        f"{prefix}%",
        "review_no",
        use_ilike=False,
    )
    max_review = max_review_query.order_by(desc(TechnicalReview.review_no)).first()
    if max_review:
        seq = int(max_review.review_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_issue_no(db: Session) -> str:
    """生成问题编号：RV-ISSUE-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RV-ISSUE-{today}-"
    max_issue_query = db.query(ReviewIssue)
    max_issue_query = apply_like_filter(
        max_issue_query,
        ReviewIssue,
        f"{prefix}%",
        "issue_no",
        use_ilike=False,
    )
    max_issue = max_issue_query.order_by(desc(ReviewIssue.issue_no)).first()
    if max_issue:
        seq = int(max_issue.issue_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def update_review_issue_counts(db: Session, review_id: int):
    """更新评审问题统计"""
    review = db.query(TechnicalReview).filter(TechnicalReview.id == review_id).first()
    if not review:
        return

    issues = db.query(ReviewIssue).filter(ReviewIssue.review_id == review_id).all()
    review.issue_count_a = sum(1 for i in issues if i.issue_level == "A")
    review.issue_count_b = sum(1 for i in issues if i.issue_level == "B")
    review.issue_count_c = sum(1 for i in issues if i.issue_level == "C")
    review.issue_count_d = sum(1 for i in issues if i.issue_level == "D")
    db.commit()


_ISSUE_LEVEL_TO_PROJECT_ISSUE = {
    "A": ("CRITICAL", "URGENT", True),
    "B": ("MAJOR", "HIGH", True),
    "C": ("MINOR", "MEDIUM", False),
    "D": ("MINOR", "LOW", False),
}


def sync_review_issue_to_project_issue(
    db: Session,
    *,
    review: TechnicalReview,
    issue: ReviewIssue,
    reporter: User,
) -> Issue:
    """把技术评审问题同步到统一项目问题池，并回填关联ID。"""
    if issue.linked_issue_id:
        existing_issue = db.query(Issue).filter(Issue.id == issue.linked_issue_id).first()
        if existing_issue:
            return existing_issue

    severity, priority, is_blocking = _ISSUE_LEVEL_TO_PROJECT_ISSUE.get(
        (issue.issue_level or "").upper(),
        ("MINOR", "MEDIUM", False),
    )

    assignee_name = None
    if issue.assignee_id:
        assignee = db.query(User).filter(User.id == issue.assignee_id).first()
        if assignee:
            assignee_name = assignee.real_name or assignee.username

    project_issue = Issue(
        issue_no=generate_project_issue_no(db),
        category="TECHNICAL",
        project_id=review.project_id,
        issue_type="TECHNICAL_REVIEW",
        severity=severity,
        priority=priority,
        title=f"技术评审问题：{issue.description[:80]}",
        description=issue.description,
        reporter_id=reporter.id,
        reporter_name=reporter.real_name or reporter.username,
        report_date=datetime.now(),
        assignee_id=issue.assignee_id,
        assignee_name=assignee_name,
        due_date=issue.deadline,
        status=issue.status,
        solution=issue.suggestion,
        impact_scope=f"技术评审 {review.review_no}",
        impact_level=severity,
        is_blocking=is_blocking,
        responsible_engineer_id=issue.assignee_id,
        responsible_engineer_name=assignee_name,
        tags=json.dumps(["技术评审"], ensure_ascii=False),
    )

    db.add(project_issue)
    db.flush()
    issue.linked_issue_id = project_issue.id
    return project_issue
