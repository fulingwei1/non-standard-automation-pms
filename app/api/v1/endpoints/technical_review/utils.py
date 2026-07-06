# -*- coding: utf-8 -*-
"""
技术评审 - 辅助工具函数
"""

from __future__ import annotations

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

_REVIEW_STATUS_TO_PROJECT_STATUS = {
    "OPEN": "OPEN",
    "PROCESSING": "IN_PROGRESS",
    "IN_PROGRESS": "IN_PROGRESS",
    "RESOLVED": "RESOLVED",
    "VERIFIED": "CLOSED",
    "CLOSED": "CLOSED",
}

_VERIFY_PASS_VALUES = {"PASS", "PASSED", "VERIFIED"}
_VERIFY_FAIL_VALUES = {"FAIL", "FAILED", "REJECTED"}


def _project_issue_status_for_review_issue(issue: ReviewIssue) -> str:
    verify_result = (issue.verify_result or "").upper()
    if verify_result in _VERIFY_PASS_VALUES:
        return "CLOSED"
    if verify_result in _VERIFY_FAIL_VALUES:
        return "IN_PROGRESS"
    return _REVIEW_STATUS_TO_PROJECT_STATUS.get((issue.status or "").upper(), "OPEN")


def _project_issue_verified_result_for_review_issue(issue: ReviewIssue) -> str | None:
    verify_result = (issue.verify_result or "").upper()
    if verify_result in _VERIFY_PASS_VALUES:
        return "VERIFIED"
    if verify_result in _VERIFY_FAIL_VALUES:
        return "REJECTED"
    return None


def _apply_review_issue_to_project_issue(
    *,
    db: Session,
    project_issue: Issue,
    review: TechnicalReview,
    issue: ReviewIssue,
    actor: User,
) -> None:
    project_issue.status = _project_issue_status_for_review_issue(issue)
    project_issue.solution = issue.solution or issue.suggestion
    project_issue.due_date = issue.deadline
    project_issue.impact_scope = f"技术评审 {review.review_no}"

    if project_issue.status in {"RESOLVED", "CLOSED"}:
        project_issue.resolved_at = project_issue.resolved_at or datetime.now()
        project_issue.resolved_by = project_issue.resolved_by or actor.id
        project_issue.resolved_by_name = project_issue.resolved_by_name or (
            actor.real_name or actor.username
        )

    verified_result = _project_issue_verified_result_for_review_issue(issue)
    if verified_result:
        project_issue.verified_result = verified_result
        project_issue.verified_at = issue.verify_time or datetime.now()
        verified_by = issue.verifier_id or actor.id
        project_issue.verified_by = verified_by
        verifier_name = actor.real_name or actor.username
        if verified_by != actor.id:
            verifier = db.query(User).filter(User.id == verified_by).first()
            if verifier:
                verifier_name = verifier.real_name or verifier.username
        project_issue.verified_by_name = verifier_name


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
            _apply_review_issue_to_project_issue(
                db=db,
                project_issue=existing_issue,
                review=review,
                issue=issue,
                actor=reporter,
            )
            db.flush()
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
    _apply_review_issue_to_project_issue(
        db=db,
        project_issue=project_issue,
        review=review,
        issue=issue,
        actor=reporter,
    )

    db.add(project_issue)
    db.flush()
    issue.linked_issue_id = project_issue.id
    return project_issue


def update_linked_project_issue_from_review_issue(
    db: Session,
    *,
    issue: ReviewIssue,
    current_user: User,
) -> Issue | None:
    """评审问题处理状态变化后，同步更新项目问题池中的关联问题。"""
    if not issue.linked_issue_id:
        return None

    review = db.query(TechnicalReview).filter(TechnicalReview.id == issue.review_id).first()
    if not review:
        return None

    return sync_review_issue_to_project_issue(
        db,
        review=review,
        issue=issue,
        reporter=current_user,
    )
