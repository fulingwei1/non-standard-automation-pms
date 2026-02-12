# -*- coding: utf-8 -*-
"""
问题批量操作端点

包含：批量分配、批量状态变更、批量关闭

已迁移到通用批量操作框架
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.user import User
from app.schemas.common import BatchOperationResponse
from app.services.data_scope import DataScopeService
from app.utils.batch_operations import BatchOperationExecutor, create_scope_filter

router = APIRouter()

# 创建数据范围过滤函数
scope_filter = create_scope_filter(
    model=Issue,
    scope_service=DataScopeService,
    filter_method="filter_issues_by_scope"
)


@router.post("/batch-assign", response_model=BatchOperationResponse)
def batch_assign_issues(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    assignee_id: int = Body(..., description="处理人ID"),
    due_date: Optional[date] = Body(None, description="要求完成日期"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> BatchOperationResponse:
    """批量分配问题"""
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")

    executor = BatchOperationExecutor(
        model=Issue,
        db=db,
        current_user=current_user,
        scope_filter_func=scope_filter
    )
    
    def assign_issue(issue: Issue):
        """分配问题的操作函数"""
        issue.assignee_id = assignee_id
        issue.assignee_name = assignee.real_name or assignee.username
        if due_date:
            issue.due_date = due_date
    
    def log_operation(issue: Issue, op_type: str):
        """记录操作日志"""
        follow_up = IssueFollowUpRecord(
            issue_id=issue.id,
            follow_up_type='ASSIGNMENT',
            content=f"批量分配给 {assignee.real_name or assignee.username}",
            operator_id=current_user.id,
            operator_name=current_user.real_name or current_user.username,
            old_status=None,
            new_status=None,
        )
        db.add(follow_up)
    
    result = executor.execute(
        entity_ids=issue_ids,
        operation_func=assign_issue,
        log_func=log_operation,
        operation_type="BATCH_ASSIGN"
    )
    
    return BatchOperationResponse(**result.to_dict(id_field="issue_id"))


@router.post("/batch-status", response_model=BatchOperationResponse)
def batch_change_issue_status(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    new_status: str = Body(..., description="新状态"),
    comment: Optional[str] = Body(None, description="备注"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> BatchOperationResponse:
    """批量更新问题状态"""
    executor = BatchOperationExecutor(
        model=Issue,
        db=db,
        current_user=current_user,
        scope_filter_func=scope_filter
    )
    
    def change_status(issue: Issue):
        """更新状态的操作函数"""
        issue.status = new_status
    
    def log_operation(issue: Issue, op_type: str):
        """记录操作日志"""
        old_status = getattr(issue, '_old_status', issue.status)
        follow_up = IssueFollowUpRecord(
            issue_id=issue.id,
            follow_up_type='STATUS_CHANGE',
            content=comment or f"批量状态变更：{old_status} → {new_status}",
            operator_id=current_user.id,
            operator_name=current_user.real_name or current_user.username,
            old_status=old_status,
            new_status=new_status,
        )
        db.add(follow_up)
    
    result = executor.batch_status_update(
        entity_ids=issue_ids,
        new_status=new_status,
        log_func=log_operation
    )
    
    return BatchOperationResponse(**result.to_dict(id_field="issue_id"))


@router.post("/batch-close", response_model=BatchOperationResponse)
def batch_close_issues(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    comment: Optional[str] = Body(None, description="关闭原因"),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> BatchOperationResponse:
    """批量关闭问题"""
    executor = BatchOperationExecutor(
        model=Issue,
        db=db,
        current_user=current_user,
        scope_filter_func=scope_filter
    )
    
    def log_operation(issue: Issue, op_type: str):
        """记录操作日志"""
        old_status = getattr(issue, '_old_status', issue.status)
        follow_up = IssueFollowUpRecord(
            issue_id=issue.id,
            follow_up_type='STATUS_CHANGE',
            content=comment or "批量关闭",
            operator_id=current_user.id,
            operator_name=current_user.real_name or current_user.username,
            old_status=old_status,
            new_status='CLOSED',
        )
        db.add(follow_up)
    
    result = executor.batch_status_update(
        entity_ids=issue_ids,
        new_status='CLOSED',
        validator_func=lambda issue: issue.status != 'CLOSED',
        error_message="问题已关闭",
        log_func=log_operation
    )
    
    return BatchOperationResponse(**result.to_dict(id_field="issue_id"))
