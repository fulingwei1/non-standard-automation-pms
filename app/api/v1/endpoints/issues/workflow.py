# -*- coding: utf-8 -*-
"""
问题管理 - 工作流操作（分配、解决、验证、状态变更）
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.project import Project
from app.models.user import User
from app.schemas.issue import (
    IssueAssignRequest,
    IssueResolveRequest,
    IssueResponse,
    IssueStatusChangeRequest,
    IssueVerifyRequest,
)
from app.services.sales_reminder import create_notification

from .crud import _get_scoped_issue, build_issue_response, get_issue

router = APIRouter()


@router.post("/{issue_id}/assign", response_model=IssueResponse)
def assign_issue(
    issue_id: int,
    assign_req: IssueAssignRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:assign")),
) -> Any:
    """分配问题"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    assignee = db.query(User).filter(User.id == assign_req.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")

    # 更新分配信息
    old_assignee_id = issue.assignee_id
    issue.assignee_id = assign_req.assignee_id
    issue.assignee_name = assignee.real_name or assignee.username
    issue.due_date = assign_req.due_date

    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='ASSIGNMENT',
        content=assign_req.comment or f"问题已分配给 {assignee.real_name or assignee.username}",
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=None,
        new_status=None,
    )
    db.add(follow_up)

    # 发送通知给被分配人
    try:
        create_notification(
            db=db,
            user_id=assign_req.assignee_id,
            notification_type='ISSUE_ASSIGNED',
            title=f'问题已分配给您：{issue.title}',
            content=f'问题 {issue.issue_no} 已分配给您处理，要求完成日期：{assign_req.due_date or "未设置"}',
            source_type='ISSUE',
            source_id=issue_id,
            link_url=f'/issues/{issue_id}',
            priority='HIGH' if issue.priority in ['HIGH', 'URGENT'] else 'NORMAL',
            extra_data={
                'issue_no': issue.issue_no,
                'priority': issue.priority,
                'severity': issue.severity,
                'due_date': assign_req.due_date.isoformat() if assign_req.due_date else None
            }
        )
    except Exception as e:
        logging.error(f"发送分配通知失败: {str(e)}")

    # 如果更换了处理人，通知原处理人
    if old_assignee_id and old_assignee_id != assign_req.assignee_id:
        try:
            create_notification(
                db=db,
                user_id=old_assignee_id,
                notification_type='ISSUE_REASSIGNED',
                title=f'问题已重新分配：{issue.title}',
                content=f'问题 {issue.issue_no} 已重新分配给 {assignee.real_name or assignee.username}',
                source_type='ISSUE',
                source_id=issue_id,
                link_url=f'/issues/{issue_id}',
                priority='NORMAL'
            )
        except Exception as e:
            logging.error(f"发送重新分配通知失败: {str(e)}")

    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: int,
    resolve_req: IssueResolveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:resolve")),
) -> Any:
    """解决问题"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 更新解决信息
    old_status = issue.status
    issue.status = 'RESOLVED'
    issue.solution = resolve_req.solution
    issue.resolved_at = datetime.now()
    issue.resolved_by = current_user.id
    issue.resolved_by_name = current_user.real_name or current_user.username

    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='SOLUTION',
        content=resolve_req.comment or "问题已解决",
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=old_status,
        new_status='RESOLVED',
    )
    db.add(follow_up)

    # 发送通知给提出人
    if issue.reporter_id and issue.reporter_id != current_user.id:
        try:
            create_notification(
                db=db,
                user_id=issue.reporter_id,
                notification_type='ISSUE_RESOLVED',
                title=f'问题已解决：{issue.title}',
                content=f'问题 {issue.issue_no} 已解决，请验证',
                source_type='ISSUE',
                source_id=issue_id,
                link_url=f'/issues/{issue_id}',
                priority='NORMAL'
            )
        except Exception as e:
            logging.error(f"发送解决通知失败: {str(e)}")

    # 如果是阻塞问题，关闭相关预警
    if issue.is_blocking:
        try:
            from .utils import close_blocking_issue_alerts
            closed_count = close_blocking_issue_alerts(db, issue)
            if closed_count > 0:
                logging.info(f"问题 {issue.issue_no} 已解决，自动关闭 {closed_count} 个预警")
        except Exception as e:
            logging.error(f"关闭阻塞问题预警失败: {str(e)}")

    # 如果问题阻塞项目，触发项目健康度更新
    if issue.is_blocking and issue.project_id:
        try:
            from app.services.health_calculator import HealthCalculator
            project = db.query(Project).filter(Project.id == issue.project_id).first()
            if project:
                calculator = HealthCalculator(db)
                calculator.calculate_and_update(project, auto_save=True)
        except Exception as e:
            logging.error(f"更新项目健康度失败: {str(e)}")

    # 如果问题是项目相关的缺陷或Bug，自动同步到调试问题
    if issue.category == 'PROJECT' and issue.issue_type in ['DEFECT', 'BUG']:
        try:
            from app.services.debug_issue_sync_service import DebugIssueSyncService
            sync_service = DebugIssueSyncService(db)
            sync_service.sync_issue(issue.id)
        except Exception as e:
            logging.error(f"调试问题同步失败: {e}")

    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/verify", response_model=IssueResponse)
def verify_issue(
    issue_id: int,
    verify_req: IssueVerifyRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """验证问题"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    if issue.status != 'RESOLVED':
        raise HTTPException(status_code=400, detail="问题必须已解决才能验证")

    # 更新验证信息
    issue.verified_at = datetime.now()
    issue.verified_by = current_user.id
    issue.verified_by_name = current_user.real_name or current_user.username
    issue.verified_result = verify_req.verified_result

    if verify_req.verified_result == 'VERIFIED':
        issue.status = 'CLOSED'

    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='VERIFICATION',
        content=verify_req.comment or f"问题验证结果：{verify_req.verified_result}",
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status='RESOLVED',
        new_status=issue.status,
    )
    db.add(follow_up)

    # 发送通知给解决人
    if issue.resolved_by and issue.resolved_by != current_user.id:
        try:
            create_notification(
                db=db,
                user_id=issue.resolved_by,
                notification_type='ISSUE_VERIFIED',
                title=f'问题验证完成：{issue.title}',
                content=f'问题 {issue.issue_no} 验证结果：{verify_req.verified_result}',
                source_type='ISSUE',
                source_id=issue_id,
                link_url=f'/issues/{issue_id}',
                priority='NORMAL'
            )
        except Exception as e:
            logging.error(f"发送验证通知失败: {str(e)}")

    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/status", response_model=IssueResponse)
def change_issue_status(
    issue_id: int,
    status_req: IssueStatusChangeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """变更问题状态"""
    issue = _get_scoped_issue(db, current_user, issue_id)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 更新状态
    old_status = issue.status
    issue.status = status_req.status

    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='STATUS_CHANGE',
        content=status_req.comment or f"状态从 {old_status} 变更为 {status_req.status}",
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=old_status,
        new_status=status_req.status,
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)
