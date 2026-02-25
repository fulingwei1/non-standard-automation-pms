# -*- coding: utf-8 -*-
"""
评审问题管理端点
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.technical_review import ReviewIssue, TechnicalReview
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.technical_review import (
    ReviewIssueCreate,
    ReviewIssueResponse,
    ReviewIssueUpdate,
)

from .utils import generate_issue_no, update_review_issue_counts
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _build_issue_response(issue: ReviewIssue) -> ReviewIssueResponse:
    """构建问题响应"""
    return ReviewIssueResponse(
        id=issue.id,
        review_id=issue.review_id,
        issue_no=issue.issue_no,
        issue_level=issue.issue_level,
        category=issue.category,
        description=issue.description,
        suggestion=issue.suggestion,
        assignee_id=issue.assignee_id,
        deadline=issue.deadline,
        status=issue.status,
        solution=issue.solution,
        verify_result=issue.verify_result,
        verifier_id=issue.verifier_id,
        verify_time=issue.verify_time,
        linked_issue_id=issue.linked_issue_id,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


@router.post("/technical-reviews/{review_id}/issues", response_model=ReviewIssueResponse, status_code=status.HTTP_201_CREATED)
def create_review_issue(
    review_id: int,
    issue_in: ReviewIssueCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建评审问题"""
    review = get_or_404(db, TechnicalReview, review_id, "技术评审不存在")

    issue_no = generate_issue_no(db)

    issue = ReviewIssue(
        review_id=review_id,
        issue_no=issue_no,
        issue_level=issue_in.issue_level,
        category=issue_in.category,
        description=issue_in.description,
        suggestion=issue_in.suggestion,
        assignee_id=issue_in.assignee_id,
        deadline=issue_in.deadline,
        status='OPEN',
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    # 更新问题统计
    update_review_issue_counts(db, review_id)

    return _build_issue_response(issue)


@router.put("/technical-reviews/issues/{issue_id}", response_model=ReviewIssueResponse, status_code=status.HTTP_200_OK)
def update_review_issue(
    issue_id: int,
    issue_in: ReviewIssueUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新评审问题"""
    issue = get_or_404(db, ReviewIssue, issue_id, "评审问题不存在")

    update_data = issue_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)

    # 如果验证，记录验证时间
    if issue_in.verify_result and not issue.verify_time:
        issue.verify_time = datetime.now()
        if not issue.verifier_id:
            issue.verifier_id = current_user.id

    db.commit()
    db.refresh(issue)

    # 更新问题统计
    update_review_issue_counts(db, issue.review_id)

    return _build_issue_response(issue)


@router.get("/technical-reviews/issues", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_review_issues(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    review_id: Optional[int] = Query(None, description="评审ID筛选"),
    issue_level: Optional[str] = Query(None, description="问题等级筛选"),
    issue_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    assignee_id: Optional[int] = Query(None, description="责任人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取评审问题列表"""

    query = db.query(ReviewIssue)

    if review_id:
        query = query.filter(ReviewIssue.review_id == review_id)

    if issue_level:
        query = query.filter(ReviewIssue.issue_level == issue_level)

    if issue_status:
        query = query.filter(ReviewIssue.status == issue_status)

    if assignee_id:
        query = query.filter(ReviewIssue.assignee_id == assignee_id)

    total = query.count()
    issues = apply_pagination(query.order_by(desc(ReviewIssue.created_at)), pagination.offset, pagination.limit).all()

    items = [_build_issue_response(issue) for issue in issues]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )
