# -*- coding: utf-8 -*-
"""
验收问题管理端点

包含：问题CRUD、问题指派、问题解决、问题验证、问题延期、跟进记录
"""

from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.acceptance import (
    AcceptanceOrder, AcceptanceOrderItem,
    AcceptanceIssue, IssueFollowUp
)
from app.schemas.acceptance import (
    AcceptanceIssueCreate, AcceptanceIssueUpdate, AcceptanceIssueResponse,
    AcceptanceIssueAssign, AcceptanceIssueResolve, AcceptanceIssueVerify, AcceptanceIssueDefer,
    IssueFollowUpCreate, IssueFollowUpResponse
)
from app.schemas.common import ResponseModel

from .utils import generate_issue_no

router = APIRouter()


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


@router.get("/acceptance-issues/{issue_id}", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def read_acceptance_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取问题详情
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

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
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

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
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

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
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

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
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

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


@router.post("/acceptance-issues/{issue_id}/assign", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def assign_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    assign_in: AcceptanceIssueAssign,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    指派问题
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

    # 验证被指派人是否存在
    assigned_user = db.query(User).filter(User.id == assign_in.assigned_to).first()
    if not assigned_user:
        raise HTTPException(status_code=404, detail="被指派人不存在")

    # 记录原值
    old_assigned_to = issue.assigned_to
    old_due_date = issue.due_date

    # 更新问题
    issue.assigned_to = assign_in.assigned_to
    issue.due_date = assign_in.due_date
    issue.status = "PROCESSING" if issue.status == "OPEN" else issue.status

    db.add(issue)
    db.flush()

    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="ASSIGN",
        action_content=assign_in.remark or f"问题已指派给 {assigned_user.real_name or assigned_user.username}",
        old_value=str(old_assigned_to) if old_assigned_to else None,
        new_value=str(assign_in.assigned_to),
        created_by=current_user.id
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/resolve", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def resolve_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    resolve_in: AcceptanceIssueResolve,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    解决问题
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="问题已经关闭，无法解决")

    # 保存旧状态（用于跟进记录）
    old_status = issue.status

    # 更新问题
    issue.status = "RESOLVED"
    issue.solution = resolve_in.solution
    issue.resolved_at = datetime.now()
    issue.resolved_by = current_user.id
    if resolve_in.attachments:
        # 合并附件
        if issue.attachments:
            issue.attachments = list(issue.attachments) + resolve_in.attachments
        else:
            issue.attachments = resolve_in.attachments

    db.add(issue)
    db.flush()

    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="RESOLVE",
        action_content=f"问题已解决：{resolve_in.solution}",
        old_value=old_status,
        new_value="RESOLVED",
        attachments=resolve_in.attachments,
        created_by=current_user.id
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/verify", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def verify_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    verify_in: AcceptanceIssueVerify,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    验证问题

    验证结果：
    - VERIFIED: 验证通过，问题已解决
    - REJECTED: 验证不通过，问题需要重新处理
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

    if issue.status != "RESOLVED":
        raise HTTPException(status_code=400, detail="只能验证已解决的问题")

    if verify_in.verified_result not in ["VERIFIED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="验证结果必须是 VERIFIED 或 REJECTED")

    # 记录原值
    old_status = issue.status
    old_verified_result = issue.verified_result

    # 更新问题
    issue.verified_at = datetime.now()
    issue.verified_by = current_user.id
    issue.verified_result = verify_in.verified_result

    if verify_in.verified_result == "VERIFIED":
        # 验证通过，关闭问题
        issue.status = "CLOSED"
    else:
        # 验证不通过，重新打开问题
        issue.status = "OPEN"
        issue.resolved_at = None
        issue.resolved_by = None

    db.add(issue)
    db.flush()

    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="VERIFY",
        action_content=f"验证结果：{verify_in.verified_result}。{verify_in.remark or ''}",
        old_value=old_verified_result or old_status,
        new_value=verify_in.verified_result,
        created_by=current_user.id
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.post("/acceptance-issues/{issue_id}/defer", response_model=AcceptanceIssueResponse, status_code=status.HTTP_200_OK)
def defer_acceptance_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    defer_in: AcceptanceIssueDefer,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    延期问题
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

    if issue.status == "CLOSED":
        raise HTTPException(status_code=400, detail="已关闭的问题不能延期")

    # 记录原值
    old_due_date = issue.due_date

    # 更新问题
    issue.due_date = defer_in.new_due_date
    issue.status = "DEFERRED" if issue.status != "DEFERRED" else issue.status

    db.add(issue)
    db.flush()

    # 创建跟进记录
    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type="STATUS_CHANGE",
        action_content=f"问题延期：{defer_in.reason}。新完成日期：{defer_in.new_due_date}",
        old_value=str(old_due_date) if old_due_date else None,
        new_value=str(defer_in.new_due_date),
        created_by=current_user.id
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return build_issue_response(issue, db)


@router.get("/acceptance-issues/{issue_id}/follow-ups", response_model=List[IssueFollowUpResponse], status_code=status.HTTP_200_OK)
def read_issue_follow_ups(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取问题跟进记录
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

    follow_ups = db.query(IssueFollowUp).filter(IssueFollowUp.issue_id == issue_id).order_by(IssueFollowUp.created_at).all()

    items = []
    for follow_up in follow_ups:
        created_by_name = None
        if follow_up.created_by:
            user = db.query(User).filter(User.id == follow_up.created_by).first()
            created_by_name = user.real_name or user.username if user else None

        items.append(IssueFollowUpResponse(
            id=follow_up.id,
            issue_id=follow_up.issue_id,
            action_type=follow_up.action_type,
            action_content=follow_up.action_content,
            old_value=follow_up.old_value,
            new_value=follow_up.new_value,
            attachments=follow_up.attachments,
            created_by=follow_up.created_by,
            created_by_name=created_by_name,
            created_at=follow_up.created_at
        ))

    return items


@router.post("/acceptance-issues/{issue_id}/follow-ups", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_issue_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int,
    follow_up_in: IssueFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加跟进记录
    """
    issue = db.query(AcceptanceIssue).filter(AcceptanceIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="验收问题不存在")

    follow_up = IssueFollowUp(
        issue_id=issue_id,
        action_type=follow_up_in.action_type,
        action_content=follow_up_in.action_content,
        attachments=follow_up_in.attachments,
        created_by=current_user.id
    )

    db.add(follow_up)
    db.commit()

    return ResponseModel(message="跟进记录添加成功")
