# -*- coding: utf-8 -*-
"""
验收问题管理 - 工具函数
"""
from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceIssue
from app.models.user import User
from app.schemas.acceptance import AcceptanceIssueResponse


def build_issue_response(issue: AcceptanceIssue, db: Session) -> AcceptanceIssueResponse:
    """构建问题响应对象"""
    found_by_name = None
    if issue.found_by:
        user = db.query(User).filter(User.id == issue.found_by).first()
        found_by_name = user.real_name or user.username if user else None

    assigned_to_name = None
    if issue.assigned_to:
        user = db.query(User).filter(User.id == issue.assigned_to).first()
        assigned_to_name = user.real_name or user.username if user else None

    resolved_by_name = None
    if issue.resolved_by:
        user = db.query(User).filter(User.id == issue.resolved_by).first()
        resolved_by_name = user.real_name or user.username if user else None

    verified_by_name = None
    if issue.verified_by:
        user = db.query(User).filter(User.id == issue.verified_by).first()
        verified_by_name = user.real_name or user.username if user else None

    return AcceptanceIssueResponse(
        id=issue.id,
        issue_no=issue.issue_no,
        order_id=issue.order_id,
        order_item_id=issue.order_item_id,
        issue_type=issue.issue_type,
        severity=issue.severity,
        title=issue.title,
        description=issue.description,
        found_at=issue.found_at,
        found_by=issue.found_by,
        found_by_name=found_by_name,
        status=issue.status,
        assigned_to=issue.assigned_to,
        assigned_to_name=assigned_to_name,
        due_date=issue.due_date,
        solution=issue.solution,
        resolved_at=issue.resolved_at,
        resolved_by=issue.resolved_by,
        resolved_by_name=resolved_by_name,
        verified_at=issue.verified_at,
        verified_by=issue.verified_by,
        verified_by_name=verified_by_name,
        verified_result=issue.verified_result,
        is_blocking=issue.is_blocking,
        attachments=issue.attachments,
        created_at=issue.created_at,
        updated_at=issue.updated_at
    )
