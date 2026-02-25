# -*- coding: utf-8 -*-
"""
验收问题管理 - CRUD操作
"""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import (
    AcceptanceIssue,
    AcceptanceOrder,
    AcceptanceOrderItem,
)
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceIssueCreate,
    AcceptanceIssueResponse,
    AcceptanceIssueUpdate,
)

from ..utils import generate_issue_no
from .utils import build_issue_response
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/acceptance-issues/{issue_id}", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def read_acceptance_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取问题详情
    """
    issue = get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    return build_issue_response(issue, db)


@router.get("/acceptance-orders/{order_id}/issues", response_model=List[AcceptanceIssueResponse], status_code=status.HTTP_200_OK)
def read_acceptance_issues(
    order_id: int,
    db: Session = Depends(deps.get_db),
    issue_status: Optional[str] = Query(None, alias="status", description="问题状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收问题列表
    """
    order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

    query = db.query(AcceptanceIssue).filter(AcceptanceIssue.order_id == order_id)

    if issue_status:
        query = query.filter(AcceptanceIssue.status == issue_status)

    issues = query.order_by(desc(AcceptanceIssue.found_at)).all()

    items = []
    for issue in issues:
        items.append(build_issue_response(issue, db))

    return items


@router.post("/acceptance-orders/{order_id}/issues", response_model=AcceptanceIssueResponse, status_code=status.HTTP_201_CREATED)
def create_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    issue_in: AcceptanceIssueCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建验收问题
    """
    order = get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

    if issue_in.order_id != order_id:
        raise HTTPException(status_code=400, detail="问题所属验收单ID不匹配")

    # 验证检查项（如果提供）
    if issue_in.order_item_id:
        item = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.id == issue_in.order_item_id).first()
        if not item or item.order_id != order_id:
            raise HTTPException(status_code=400, detail="检查项不存在或不属于该验收单")

    # 生成问题编号（符合设计规范）
    issue_no = generate_issue_no(db, order.order_no)

    issue = AcceptanceIssue(
        issue_no=issue_no,
        order_id=order_id,
        order_item_id=issue_in.order_item_id,
        issue_type=issue_in.issue_type,
        severity=issue_in.severity,
        title=issue_in.title,
        description=issue_in.description,
        found_by=current_user.id,
        found_at=datetime.now(),
        status="OPEN",
        assigned_to=issue_in.assigned_to,
        due_date=issue_in.due_date,
        is_blocking=issue_in.is_blocking,
        attachments=issue_in.attachments
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.put("/acceptance-issues/{issue_id}", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def update_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    issue_in: AcceptanceIssueUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新问题状态
    """
    issue = get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    update_data = issue_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(issue, field, value)

    # 如果状态更新为已解决，记录解决时间和解决人
    if issue_in.status == "RESOLVED" and not issue.resolved_at:
        issue.resolved_at = datetime.now()
        issue.resolved_by = current_user.id

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.put("/acceptance-issues/{issue_id}/close", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def close_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    solution: Optional[str] = Query(None, description="解决方案"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭问题
    """
    issue = get_or_404(db, AcceptanceIssue, issue_id, "验收问题不存在")

    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="问题已经关闭")

    issue.status = "CLOSED"
    issue.solution = solution
    issue.resolved_at = datetime.now()
    issue.resolved_by = current_user.id

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)
