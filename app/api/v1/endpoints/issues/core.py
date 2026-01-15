# -*- coding: utf-8 -*-
"""
问题管理核心端点

包含：基础CRUD、状态管理、分配、解决、验证、跟进记录
"""

from typing import Any, List, Optional
from datetime import datetime, date
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, and_

from app.api import deps
from app.core import security
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.user import User
from app.models.project import Project
from app.services.sales_reminder_service import create_notification
from app.schemas.issue import (
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    IssueListResponse,
    IssueFollowUpCreate,
    IssueFollowUpResponse,
    IssueAssignRequest,
    IssueResolveRequest,
    IssueVerifyRequest,
    IssueStatusChangeRequest,
)

from .utils import (
    generate_issue_no,
    create_blocking_issue_alert,
    close_blocking_issue_alerts
)

router = APIRouter()


@router.get("/", response_model=IssueListResponse)
def list_issues(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    category: Optional[str] = Query(None, description="问题分类"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    machine_id: Optional[int] = Query(None, description="机台ID"),
    task_id: Optional[int] = Query(None, description="任务ID"),
    issue_type: Optional[str] = Query(None, description="问题类型"),
    severity: Optional[str] = Query(None, description="严重程度"),
    priority: Optional[str] = Query(None, description="优先级"),
    issue_status: Optional[str] = Query(None, alias="status", description="状态"),
    assignee_id: Optional[int] = Query(None, description="处理人ID"),
    reporter_id: Optional[int] = Query(None, description="提出人ID"),
    responsible_engineer_id: Optional[int] = Query(None, description="责任工程师ID"),
    root_cause: Optional[str] = Query(None, description="问题原因"),
    is_blocking: Optional[bool] = Query(None, description="是否阻塞"),
    is_overdue: Optional[bool] = Query(None, description="是否逾期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """获取问题列表"""
    query = db.query(Issue)

    # 排除已删除的问题
    query = query.filter(Issue.status != 'DELETED')

    # 筛选条件
    if category:
        query = query.filter(Issue.category == category)
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if machine_id:
        query = query.filter(Issue.machine_id == machine_id)
    if task_id:
        query = query.filter(Issue.task_id == task_id)
    if issue_type:
        query = query.filter(Issue.issue_type == issue_type)
    if severity:
        query = query.filter(Issue.severity == severity)
    if priority:
        query = query.filter(Issue.priority == priority)
    if issue_status:
        query = query.filter(Issue.status == issue_status)
    if assignee_id:
        query = query.filter(Issue.assignee_id == assignee_id)
    if reporter_id:
        query = query.filter(Issue.reporter_id == reporter_id)
    if responsible_engineer_id:
        query = query.filter(Issue.responsible_engineer_id == responsible_engineer_id)
    if root_cause:
        query = query.filter(Issue.root_cause == root_cause)
    if is_blocking is not None:
        query = query.filter(Issue.is_blocking == is_blocking)
    if is_overdue:
        query = query.filter(
            and_(
                Issue.due_date.isnot(None),
                Issue.due_date < date.today(),
                Issue.status.in_(['OPEN', 'PROCESSING'])
            )
        )
    if keyword:
        query = query.filter(
            or_(
                Issue.title.like(f'%{keyword}%'),
                Issue.description.like(f'%{keyword}%'),
                Issue.issue_no.like(f'%{keyword}%')
            )
        )

    # 总数
    total = query.count()

    # 分页
    issues = query.order_by(desc(Issue.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    # 构建响应
    items = []
    for issue in issues:
        item = build_issue_response(issue)
        items.append(item)

    return IssueListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


def build_issue_response(issue: Issue) -> IssueResponse:
    """构建问题响应对象"""
    return IssueResponse(
        id=issue.id,
        issue_no=issue.issue_no,
        category=issue.category,
        project_id=issue.project_id,
        machine_id=issue.machine_id,
        task_id=issue.task_id,
        acceptance_order_id=issue.acceptance_order_id,
        related_issue_id=issue.related_issue_id,
        issue_type=issue.issue_type,
        severity=issue.severity,
        priority=issue.priority,
        title=issue.title,
        description=issue.description,
        reporter_id=issue.reporter_id,
        reporter_name=issue.reporter_name,
        report_date=issue.report_date,
        assignee_id=issue.assignee_id,
        assignee_name=issue.assignee_name,
        due_date=issue.due_date,
        status=issue.status,
        solution=issue.solution,
        resolved_at=issue.resolved_at,
        resolved_by=issue.resolved_by,
        resolved_by_name=issue.resolved_by_name,
        verified_at=issue.verified_at,
        verified_by=issue.verified_by,
        verified_by_name=issue.verified_by_name,
        verified_result=issue.verified_result,
        impact_scope=issue.impact_scope,
        impact_level=issue.impact_level,
        is_blocking=issue.is_blocking,
        root_cause=issue.root_cause,
        responsible_engineer_id=issue.responsible_engineer_id,
        responsible_engineer_name=issue.responsible_engineer_name,
        estimated_inventory_loss=issue.estimated_inventory_loss,
        estimated_extra_hours=issue.estimated_extra_hours,
        attachments=json.loads(issue.attachments) if issue.attachments else [],
        tags=json.loads(issue.tags) if issue.tags else [],
        follow_up_count=issue.follow_up_count,
        last_follow_up_at=issue.last_follow_up_at,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        project_code=issue.project.project_code if issue.project else None,
        project_name=issue.project.project_name if issue.project else None,
        machine_code=issue.machine.machine_code if issue.machine else None,
        machine_name=issue.machine.machine_name if issue.machine else None,
    )


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题详情"""
    issue = db.query(Issue).options(
        joinedload(Issue.project),
        joinedload(Issue.machine)
    ).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    return build_issue_response(issue)


@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue_in: IssueCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:create")),
) -> Any:
    """创建问题"""
    # 生成问题编号
    issue_no = generate_issue_no(db)

    # 获取处理人名称
    assignee_name = None
    if issue_in.assignee_id:
        assignee = db.query(User).filter(User.id == issue_in.assignee_id).first()
        if assignee:
            assignee_name = assignee.real_name or assignee.username

    # 获取责任工程师名称
    responsible_engineer_name = None
    if issue_in.responsible_engineer_id:
        engineer = db.query(User).filter(User.id == issue_in.responsible_engineer_id).first()
        if engineer:
            responsible_engineer_name = engineer.real_name or engineer.username

    # 创建问题
    issue = Issue(
        issue_no=issue_no,
        category=issue_in.category,
        project_id=issue_in.project_id,
        machine_id=issue_in.machine_id,
        task_id=issue_in.task_id,
        acceptance_order_id=issue_in.acceptance_order_id,
        related_issue_id=issue_in.related_issue_id,
        issue_type=issue_in.issue_type,
        severity=issue_in.severity,
        priority=issue_in.priority,
        title=issue_in.title,
        description=issue_in.description,
        reporter_id=current_user.id,
        reporter_name=current_user.real_name or current_user.username,
        report_date=datetime.now(),
        assignee_id=issue_in.assignee_id,
        assignee_name=assignee_name,
        due_date=issue_in.due_date,
        status='OPEN',
        impact_scope=issue_in.impact_scope,
        impact_level=issue_in.impact_level,
        is_blocking=issue_in.is_blocking,
        root_cause=issue_in.root_cause,
        responsible_engineer_id=issue_in.responsible_engineer_id,
        responsible_engineer_name=responsible_engineer_name,
        estimated_inventory_loss=issue_in.estimated_inventory_loss,
        estimated_extra_hours=issue_in.estimated_extra_hours,
        attachments=str(issue_in.attachments) if issue_in.attachments else None,
        tags=str(issue_in.tags) if issue_in.tags else None,
    )

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)


@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:update")),
) -> Any:
    """更新问题"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 记录阻塞状态变化
    old_is_blocking = issue.is_blocking

    # 更新字段
    update_data = issue_in.dict(exclude_unset=True)
    if 'attachments' in update_data:
        update_data['attachments'] = str(update_data['attachments'])
    if 'tags' in update_data:
        update_data['tags'] = str(update_data['tags'])
    if 'assignee_id' in update_data and update_data['assignee_id']:
        assignee = db.query(User).filter(User.id == update_data['assignee_id']).first()
        if assignee:
            update_data['assignee_name'] = assignee.real_name or assignee.username
    if 'responsible_engineer_id' in update_data and update_data['responsible_engineer_id']:
        responsible_engineer = db.query(User).filter(User.id == update_data['responsible_engineer_id']).first()
        if responsible_engineer:
            update_data['responsible_engineer_name'] = responsible_engineer.real_name or responsible_engineer.username
        elif update_data['responsible_engineer_id'] is None:
            update_data['responsible_engineer_name'] = None

    for field, value in update_data.items():
        setattr(issue, field, value)

    db.flush()

    # 处理阻塞状态变化
    try:
        new_is_blocking = issue.is_blocking
        if not old_is_blocking and new_is_blocking:
            create_blocking_issue_alert(db, issue)
        elif old_is_blocking and not new_is_blocking:
            close_blocking_issue_alerts(db, issue)
        elif old_is_blocking and new_is_blocking:
            create_blocking_issue_alert(db, issue)
    except Exception as e:
        import logging
        logging.error(f"处理阻塞问题预警失败: {str(e)}")

    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/assign", response_model=IssueResponse)
def assign_issue(
    issue_id: int,
    assign_req: IssueAssignRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:assign")),
) -> Any:
    """分配问题"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
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
        import logging
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
            import logging
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
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
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
            import logging
            logging.error(f"发送解决通知失败: {str(e)}")

    # 如果是阻塞问题，关闭相关预警
    if issue.is_blocking:
        try:
            closed_count = close_blocking_issue_alerts(db, issue)
            if closed_count > 0:
                import logging
                logging.info(f"问题 {issue.issue_no} 已解决，自动关闭 {closed_count} 个预警")
        except Exception as e:
            import logging
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
            import logging
            logging.error(f"更新项目健康度失败: {str(e)}")

    # 如果问题是项目相关的缺陷或Bug，自动同步到调试问题
    if issue.category == 'PROJECT' and issue.issue_type in ['DEFECT', 'BUG']:
        try:
            from app.services.debug_issue_sync_service import DebugIssueSyncService
            sync_service = DebugIssueSyncService(db)
            sync_service.sync_issue(issue.id)
        except Exception as e:
            import logging
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
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
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
            import logging
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
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
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


@router.get("/{issue_id}/follow-ups", response_model=List[IssueFollowUpResponse])
def get_issue_follow_ups(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题跟进记录"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    follow_ups = db.query(IssueFollowUpRecord).filter(
        IssueFollowUpRecord.issue_id == issue_id
    ).order_by(desc(IssueFollowUpRecord.created_at)).all()

    return [
        IssueFollowUpResponse(
            id=fu.id,
            issue_id=fu.issue_id,
            follow_up_type=fu.follow_up_type,
            content=fu.content,
            operator_id=fu.operator_id,
            operator_name=fu.operator_name,
            old_status=fu.old_status,
            new_status=fu.new_status,
            attachments=fu.attachments or [],
            created_at=fu.created_at,
        )
        for fu in follow_ups
    ]


@router.post("/{issue_id}/follow-ups", response_model=IssueFollowUpResponse, status_code=status.HTTP_201_CREATED)
def create_issue_follow_up(
    issue_id: int,
    follow_up_in: IssueFollowUpCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """创建问题跟进记录"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type=follow_up_in.follow_up_type,
        content=follow_up_in.content,
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=follow_up_in.old_status,
        new_status=follow_up_in.new_status,
        attachments=str(follow_up_in.attachments) if follow_up_in.attachments else None,
    )

    db.add(follow_up)

    # 更新问题的跟进统计
    issue.follow_up_count = db.query(IssueFollowUpRecord).filter(IssueFollowUpRecord.issue_id == issue_id).count()
    issue.last_follow_up_at = datetime.now()

    db.commit()
    db.refresh(follow_up)

    return IssueFollowUpResponse(
        id=follow_up.id,
        issue_id=follow_up.issue_id,
        follow_up_type=follow_up.follow_up_type,
        content=follow_up.content,
        operator_id=follow_up.operator_id,
        operator_name=follow_up.operator_name,
        old_status=follow_up.old_status,
        new_status=follow_up.new_status,
        attachments=follow_up.attachments or [],
        created_at=follow_up.created_at,
    )
