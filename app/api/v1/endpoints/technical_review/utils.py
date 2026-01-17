# -*- coding: utf-8 -*-
"""
技术评审 - 辅助工具函数
"""

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.technical_review import ReviewIssue, TechnicalReview


def generate_review_no(db: Session, review_type: str) -> str:
    """生成评审编号：RV-{TYPE}-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RV-{review_type}-{today}-"
    max_review = (
        db.query(TechnicalReview)
        .filter(TechnicalReview.review_no.like(f"{prefix}%"))
        .order_by(desc(TechnicalReview.review_no))
        .first()
    )
    if max_review:
        seq = int(max_review.review_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def generate_issue_no(db: Session) -> str:
    """生成问题编号：RV-ISSUE-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    prefix = f"RV-ISSUE-{today}-"
    max_issue = (
        db.query(ReviewIssue)
        .filter(ReviewIssue.issue_no.like(f"{prefix}%"))
        .order_by(desc(ReviewIssue.issue_no))
        .first()
    )
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
    review.issue_count_a = sum(1 for i in issues if i.issue_level == 'A')
    review.issue_count_b = sum(1 for i in issues if i.issue_level == 'B')
    review.issue_count_c = sum(1 for i in issues if i.issue_level == 'C')
    review.issue_count_d = sum(1 for i in issues if i.issue_level == 'D')
    db.commit()
