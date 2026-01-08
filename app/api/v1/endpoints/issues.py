"""
问题管理中心 API endpoints
"""
from typing import Any, List, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
import io
import pandas as pd
import json

from app.api import deps
from app.models.issue import Issue, IssueFollowUpRecord, IssueTemplate, IssueStatisticsSnapshot
from app.models.user import User
from app.models.project import Project, Machine
from app.models.progress import Task
from app.models.acceptance import AcceptanceOrder
from app.models.alert import AlertRule, AlertRecord
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum, AlertStatusEnum
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
    IssueStatistics,
    EngineerIssueStatistics,
    PaginatedResponse,
    IssueTemplateCreate,
    IssueTemplateUpdate,
    IssueTemplateResponse,
    IssueTemplateListResponse,
    IssueFromTemplateRequest,
    IssueStatisticsSnapshotResponse,
    IssueStatisticsSnapshotListResponse,
)
from app.services.issue_cost_service import IssueCostService
from decimal import Decimal
from app.schemas.common import ResponseModel

router = APIRouter()
template_router = APIRouter()  # 问题模板管理专用router


def create_blocking_issue_alert(db: Session, issue: Issue) -> Optional[AlertRecord]:
    """
    为阻塞问题创建预警记录
    
    Args:
        db: 数据库会话
        issue: 问题对象
    
    Returns:
        AlertRecord: 创建的预警记录，如果已存在则返回None
    """
    if not issue.is_blocking or issue.status == 'DELETED':
        return None
    
    # 检查是否已有预警记录
    existing_alert = db.query(AlertRecord).filter(
        AlertRecord.target_type == 'ISSUE',
        AlertRecord.target_id == issue.id,
        AlertRecord.status.in_(['PENDING', 'ACKNOWLEDGED', 'PROCESSING'])
    ).first()
    
    if existing_alert:
        return None  # 已存在预警，不重复创建
    
    # 获取或创建预警规则
    rule = db.query(AlertRule).filter(
        AlertRule.rule_code == 'BLOCKING_ISSUE',
        AlertRule.is_enabled == True
    ).first()
    
    if not rule:
        # 创建默认规则
        rule = AlertRule(
            rule_code='BLOCKING_ISSUE',
            rule_name='阻塞问题预警',
            rule_type=AlertRuleTypeEnum.QUALITY_ISSUE.value,
            target_type='ISSUE',
            condition_type='THRESHOLD',
            condition_operator='EQ',
            threshold_value='1',
            alert_level=AlertLevelEnum.WARNING.value,
            is_enabled=True,
            is_system=True,
            description='当问题被标记为阻塞时触发预警'
        )
        db.add(rule)
        db.flush()
    
    # 根据问题严重程度设置预警级别
    alert_level = AlertLevelEnum.WARNING.value
    if issue.severity == 'CRITICAL':
        alert_level = AlertLevelEnum.URGENT.value
    elif issue.severity == 'MAJOR':
        alert_level = AlertLevelEnum.CRITICAL.value
    elif issue.severity == 'MINOR':
        alert_level = AlertLevelEnum.WARNING.value
    
    # 生成预警编号
    today = datetime.now().strftime('%Y%m%d')
    count = db.query(AlertRecord).filter(
        AlertRecord.alert_no.like(f'AL{today}%')
    ).count()
    alert_no = f'AL{today}{str(count + 1).zfill(4)}'
    
    # 构建预警内容
    alert_content = f'问题 {issue.issue_no} 标记为阻塞问题'
    if issue.impact_scope:
        alert_content += f'，影响范围：{issue.impact_scope}'
    if issue.description:
        alert_content += f'。问题描述：{issue.description[:100]}'
    
    # 创建预警记录
    alert = AlertRecord(
        alert_no=alert_no,
        rule_id=rule.id,
        target_type='ISSUE',
        target_id=issue.id,
        target_no=issue.issue_no,
        target_name=issue.title,
        project_id=issue.project_id,
        machine_id=issue.machine_id,
        alert_level=alert_level,
        alert_title=f'阻塞问题：{issue.title}',
        alert_content=alert_content,
        alert_data={
            'issue_no': issue.issue_no,
            'severity': issue.severity,
            'priority': issue.priority,
            'impact_scope': issue.impact_scope,
            'impact_level': issue.impact_level,
        },
        status=AlertStatusEnum.PENDING.value,
        triggered_at=datetime.now()
    )
    
    db.add(alert)
    db.flush()
    
    return alert


def close_blocking_issue_alerts(db: Session, issue: Issue) -> int:
    """
    关闭阻塞问题的相关预警记录
    
    Args:
        db: 数据库会话
        issue: 问题对象
    
    Returns:
        int: 关闭的预警数量
    """
    # 查找所有待处理/已确认/处理中的预警
    alerts = db.query(AlertRecord).filter(
        AlertRecord.target_type == 'ISSUE',
        AlertRecord.target_id == issue.id,
        AlertRecord.status.in_(['PENDING', 'ACKNOWLEDGED', 'PROCESSING'])
    ).all()
    
    closed_count = 0
    for alert in alerts:
        alert.status = AlertStatusEnum.RESOLVED.value
        alert.handle_end_at = datetime.now()
        alert.handle_result = f'问题 {issue.issue_no} 已解决，自动关闭预警'
        closed_count += 1
    
    return closed_count


def generate_issue_no(db: Session) -> str:
    """生成问题编号"""
    today = datetime.now().strftime('%Y%m%d')
    count = db.query(Issue).filter(Issue.issue_no.like(f'IS{today}%')).count()
    return f'IS{today}{str(count + 1).zfill(3)}'


@router.get("/", response_model=IssueListResponse)
def list_issues(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    category: Optional[str] = Query(None, description="问题分类"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    machine_id: Optional[int] = Query(None, description="机台ID"),
    task_id: Optional[int] = Query(None, description="任务ID"),
    issue_type: Optional[str] = Query(None, description="问题类型"),
    severity: Optional[str] = Query(None, description="严重程度"),
    priority: Optional[str] = Query(None, description="优先级"),
    status: Optional[str] = Query(None, description="状态"),
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
    if status:
        query = query.filter(Issue.status == status)
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
        item = IssueResponse(
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
        items.append(item)
    
    return IssueListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取问题详情"""
    from sqlalchemy.orm import joinedload
    
    issue = db.query(Issue).options(
        joinedload(Issue.project),
        joinedload(Issue.machine)
    ).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")
    
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


@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue_in: IssueCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """创建问题"""
    # 生成问题编号
    issue_no = generate_issue_no(db)
    
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
        assignee_name=(lambda aid: (lambda u: u.real_name or u.username if u else None)(db.query(User).filter(User.id == aid).first()) if aid else None)(issue_in.assignee_id),
        due_date=issue_in.due_date,
        status='OPEN',
        impact_scope=issue_in.impact_scope,
        impact_level=issue_in.impact_level,
        is_blocking=issue_in.is_blocking,
        root_cause=issue_in.root_cause,
        responsible_engineer_id=issue_in.responsible_engineer_id,
        responsible_engineer_name=(lambda eid: (lambda u: u.real_name or u.username if u else None)(db.query(User).filter(User.id == eid).first()) if eid else None)(issue_in.responsible_engineer_id),
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
    current_user: User = Depends(deps.get_current_user),
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
            # 从非阻塞变为阻塞，创建预警
            create_blocking_issue_alert(db, issue)
        elif old_is_blocking and not new_is_blocking:
            # 从阻塞变为非阻塞，关闭预警
            close_blocking_issue_alerts(db, issue)
        elif old_is_blocking and new_is_blocking:
            # 保持阻塞状态，但可能更新了严重程度等信息，更新预警
            # 这里可以选择更新现有预警或创建新预警
            # 为了简化，我们只确保有预警记录存在
            create_blocking_issue_alert(db, issue)
    except Exception as e:
        # 预警处理失败不影响问题更新
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
    current_user: User = Depends(deps.get_current_user),
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
        # 通知发送失败不影响分配操作
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
    current_user: User = Depends(deps.get_current_user),
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
    
    db.commit()
    db.refresh(issue)
    
    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/verify", response_model=IssueResponse)
def verify_issue(
    issue_id: int,
    verify_req: IssueVerifyRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
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
    current_user: User = Depends(deps.get_current_user),
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
    current_user: User = Depends(deps.get_current_user),
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
    current_user: User = Depends(deps.get_current_user),
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


@router.get("/statistics/overview", response_model=IssueStatistics)
def get_issue_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    project_id: Optional[int] = Query(None, description="项目ID"),
) -> Any:
    """获取问题统计"""
    query = db.query(Issue)
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    
    total = query.count()
    open_count = query.filter(Issue.status == 'OPEN').count()
    processing_count = query.filter(Issue.status == 'PROCESSING').count()
    resolved_count = query.filter(Issue.status == 'RESOLVED').count()
    closed_count = query.filter(Issue.status == 'CLOSED').count()
    overdue_count = query.filter(
        and_(
            Issue.due_date.isnot(None),
            Issue.due_date < date.today(),
            Issue.status.in_(['OPEN', 'PROCESSING'])
        )
    ).count()
    blocking_count = query.filter(Issue.is_blocking == True).count()
    
    # 按严重程度统计
    by_severity = {}
    for severity in ['CRITICAL', 'MAJOR', 'MINOR']:
        by_severity[severity] = query.filter(Issue.severity == severity).count()
    
    # 按分类统计
    by_category = {}
    categories = db.query(Issue.category).distinct().all()
    for cat in categories:
        by_category[cat[0]] = query.filter(Issue.category == cat[0]).count()
    
    # 按类型统计
    by_type = {}
    types = db.query(Issue.issue_type).distinct().all()
    for t in types:
        by_type[t[0]] = query.filter(Issue.issue_type == t[0]).count()
    
    return IssueStatistics(
        total=total,
        open=open_count,
        processing=processing_count,
        resolved=resolved_count,
        closed=closed_count,
        overdue=overdue_count,
        blocking=blocking_count,
        by_severity=by_severity,
        by_category=by_category,
        by_type=by_type,
    )


@router.get("/statistics/engineer-design-issues", response_model=List[EngineerIssueStatistics])
def get_engineer_design_issues_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    engineer_id: Optional[int] = Query(None, description="工程师ID（可选，不提供则统计所有工程师）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    project_id: Optional[int] = Query(None, description="项目ID"),
) -> Any:
    """
    按工程师统计设计问题及其导致的损失
    
    统计root_cause='DESIGN_ERROR'的问题，按responsible_engineer_id分组，
    汇总库存损失和额外工时
    """
    # 查询设计问题
    query = db.query(Issue).filter(
        Issue.root_cause == 'DESIGN_ERROR',
        Issue.status != 'DELETED'
    )
    
    # 筛选条件
    if engineer_id:
        query = query.filter(Issue.responsible_engineer_id == engineer_id)
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if start_date:
        query = query.filter(Issue.report_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Issue.report_date <= datetime.combine(end_date, datetime.max.time()))
    
    issues = query.all()
    
    # 按工程师分组统计
    engineer_stats = {}
    for issue in issues:
        if not issue.responsible_engineer_id:
            continue
        
        eng_id = issue.responsible_engineer_id
        if eng_id not in engineer_stats:
            engineer_stats[eng_id] = {
                'engineer_id': eng_id,
                'engineer_name': issue.responsible_engineer_name or '未知',
                'total_issues': 0,
                'design_issues': 0,
                'total_inventory_loss': Decimal(0),
                'total_extra_hours': Decimal(0),
                'issues': []
            }
        
        stats = engineer_stats[eng_id]
        stats['total_issues'] += 1
        stats['design_issues'] += 1
        
        # 累加预估的库存损失和额外工时
        if issue.estimated_inventory_loss:
            stats['total_inventory_loss'] += issue.estimated_inventory_loss or Decimal(0)
        if issue.estimated_extra_hours:
            stats['total_extra_hours'] += issue.estimated_extra_hours or Decimal(0)
        
        # 从关联的成本和工时记录中获取实际损失
        try:
            cost_summary = IssueCostService.get_issue_cost_summary(db, issue.issue_no)
            if cost_summary.get('inventory_loss', 0) > 0:
                stats['total_inventory_loss'] += cost_summary['inventory_loss']
            if cost_summary.get('total_hours', 0) > 0:
                stats['total_extra_hours'] += cost_summary['total_hours']
        except Exception as e:
            # 如果查询失败，只记录错误，不影响统计
            import logging
            logging.warning(f"Failed to get cost summary for issue {issue.issue_no}: {e}")
        
        # 构建问题响应
        issue_response = IssueResponse(
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
            follow_up_count=issue.follow_up_count,
            last_follow_up_at=issue.last_follow_up_at,
            impact_scope=issue.impact_scope,
            impact_level=issue.impact_level,
            is_blocking=issue.is_blocking,
            attachments=json.loads(issue.attachments) if issue.attachments else [],
            tags=json.loads(issue.tags) if issue.tags else [],
            root_cause=issue.root_cause,
            responsible_engineer_id=issue.responsible_engineer_id,
            responsible_engineer_name=issue.responsible_engineer_name,
            estimated_inventory_loss=issue.estimated_inventory_loss,
            estimated_extra_hours=issue.estimated_extra_hours,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            project_code=issue.project.project_code if issue.project else None,
            project_name=issue.project.project_name if issue.project else None,
            machine_code=issue.machine.machine_code if issue.machine else None,
            machine_name=issue.machine.machine_name if issue.machine else None,
        )
        stats['issues'].append(issue_response)
    
    # 转换为响应列表
    result = [EngineerIssueStatistics(**stats) for stats in engineer_stats.values()]
    
    # 按设计问题数降序排序
    result.sort(key=lambda x: x.design_issues, reverse=True)
    
    return result


@router.post("/{issue_id}/close", response_model=IssueResponse)
def close_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """关闭问题（直接关闭，无需验证）"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    if issue.status == 'CLOSED':
        raise HTTPException(status_code=400, detail="问题已关闭")
    
    # 更新状态为已关闭
    issue.status = 'CLOSED'
    
    # 记录跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='STATUS_CHANGE',
        content=f'问题已关闭',
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=issue.status,
        new_status='CLOSED',
    )
    db.add(follow_up)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    return get_issue(issue_id, db, current_user)


@router.post("/{issue_id}/cancel", response_model=IssueResponse)
def cancel_issue(
    issue_id: int,
    cancel_reason: Optional[str] = Query(None, description="取消原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """取消/撤销问题"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    if issue.status in ['CLOSED', 'CANCELLED']:
        raise HTTPException(status_code=400, detail="问题已关闭或已取消")
    
    # 更新状态为已取消
    old_status = issue.status
    issue.status = 'CANCELLED'
    
    # 记录跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='STATUS_CHANGE',
        content=f'问题已取消：{cancel_reason or "无原因"}',
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=old_status,
        new_status='CANCELLED',
    )
    db.add(follow_up)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    return get_issue(issue_id, db, current_user)


@router.get("/{issue_id}/related", response_model=List[IssueResponse])
def get_related_issues(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取关联的父子问题"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    related_issues = []
    
    # 获取父问题
    if issue.related_issue_id:
        parent = db.query(Issue).filter(Issue.id == issue.related_issue_id).first()
        if parent:
            related_issues.append(get_issue(parent.id, db, current_user))
    
    # 获取子问题
    children = db.query(Issue).filter(Issue.related_issue_id == issue_id).all()
    for child in children:
        related_issues.append(get_issue(child.id, db, current_user))
    
    return related_issues


@router.post("/{issue_id}/related", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_related_issue(
    issue_id: int,
    issue_in: IssueCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """创建关联问题（子问题或关联问题）"""
    parent_issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not parent_issue:
        raise HTTPException(status_code=404, detail="父问题不存在")
    
    # 生成问题编号
    issue_no = generate_issue_no(db)
    
    # 创建关联问题
    issue = Issue(
        issue_no=issue_no,
        category=issue_in.category,
        project_id=issue_in.project_id or parent_issue.project_id,
        machine_id=issue_in.machine_id or parent_issue.machine_id,
        task_id=issue_in.task_id or parent_issue.task_id,
        acceptance_order_id=issue_in.acceptance_order_id or parent_issue.acceptance_order_id,
        related_issue_id=issue_id,  # 关联到父问题
        issue_type=issue_in.issue_type,
        severity=issue_in.severity,
        priority=issue_in.priority,
        title=issue_in.title,
        description=issue_in.description,
        reporter_id=current_user.id,
        reporter_name=current_user.real_name or current_user.username,
        report_date=datetime.now(),
        assignee_id=issue_in.assignee_id,
        assignee_name=db.query(User).filter(User.id == issue_in.assignee_id).first().real_name if issue_in.assignee_id else None,
        due_date=issue_in.due_date,
        status='OPEN',
        impact_scope=issue_in.impact_scope,
        impact_level=issue_in.impact_level,
        is_blocking=issue_in.is_blocking,
        attachments=str(issue_in.attachments) if issue_in.attachments else None,
        tags=str(issue_in.tags) if issue_in.tags else None,
    )
    
    db.add(issue)
    db.commit()
    db.refresh(issue)
    
    return get_issue(issue.id, db, current_user)


@router.get("/projects/{project_id}/issues", response_model=IssueListResponse)
def get_project_issues(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """获取项目下的所有问题"""
    return list_issues(
        db=db,
        current_user=current_user,
        project_id=project_id,
        page=page,
        page_size=page_size,
        status=status,
    )


@router.get("/machines/{machine_id}/issues", response_model=IssueListResponse)
def get_machine_issues(
    machine_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """获取机台下的所有问题"""
    return list_issues(
        db=db,
        current_user=current_user,
        machine_id=machine_id,
        page=page,
        page_size=page_size,
        status=status,
    )


# ==================== 批量操作 ====================

@router.post("/batch-assign", response_model=ResponseModel)
def batch_assign_issues(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    assignee_id: int = Body(..., description="处理人ID"),
    due_date: Optional[date] = Body(None, description="要求完成日期"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """批量分配问题"""
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")
    
    success_count = 0
    failed_issues = []
    
    for issue_id in issue_ids:
        try:
            issue = db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                failed_issues.append({"issue_id": issue_id, "reason": "问题不存在"})
                continue
            
            issue.assignee_id = assignee_id
            issue.assignee_name = assignee.real_name or assignee.username
            if due_date:
                issue.due_date = due_date
            
            # 创建跟进记录
            follow_up = IssueFollowUpRecord(
                issue_id=issue_id,
                follow_up_type='ASSIGNMENT',
                content=f"批量分配给 {assignee.real_name or assignee.username}",
                operator_id=current_user.id,
                operator_name=current_user.real_name or current_user.username,
                old_status=None,
                new_status=None,
            )
            db.add(follow_up)
            db.add(issue)
            success_count += 1
        except Exception as e:
            failed_issues.append({"issue_id": issue_id, "reason": str(e)})
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量分配完成：成功 {success_count} 个，失败 {len(failed_issues)} 个",
        data={"success_count": success_count, "failed_issues": failed_issues}
    )


@router.post("/batch-status", response_model=ResponseModel)
def batch_change_issue_status(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    new_status: str = Body(..., description="新状态"),
    comment: Optional[str] = Body(None, description="备注"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """批量更新问题状态"""
    success_count = 0
    failed_issues = []
    
    for issue_id in issue_ids:
        try:
            issue = db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                failed_issues.append({"issue_id": issue_id, "reason": "问题不存在"})
                continue
            
            old_status = issue.status
            issue.status = new_status
            
            # 创建跟进记录
            follow_up = IssueFollowUpRecord(
                issue_id=issue_id,
                follow_up_type='STATUS_CHANGE',
                content=comment or f"批量状态变更：{old_status} → {new_status}",
                operator_id=current_user.id,
                operator_name=current_user.real_name or current_user.username,
                old_status=old_status,
                new_status=new_status,
            )
            db.add(follow_up)
            db.add(issue)
            success_count += 1
        except Exception as e:
            failed_issues.append({"issue_id": issue_id, "reason": str(e)})
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量状态变更完成：成功 {success_count} 个，失败 {len(failed_issues)} 个",
        data={"success_count": success_count, "failed_issues": failed_issues}
    )


@router.post("/batch-close", response_model=ResponseModel)
def batch_close_issues(
    *,
    db: Session = Depends(deps.get_db),
    issue_ids: List[int] = Body(..., description="问题ID列表"),
    comment: Optional[str] = Body(None, description="关闭原因"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """批量关闭问题"""
    success_count = 0
    failed_issues = []
    
    for issue_id in issue_ids:
        try:
            issue = db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                failed_issues.append({"issue_id": issue_id, "reason": "问题不存在"})
                continue
            
            if issue.status == 'CLOSED':
                failed_issues.append({"issue_id": issue_id, "reason": "问题已关闭"})
                continue
            
            old_status = issue.status
            issue.status = 'CLOSED'
            
            # 创建跟进记录
            follow_up = IssueFollowUpRecord(
                issue_id=issue_id,
                follow_up_type='STATUS_CHANGE',
                content=comment or "批量关闭",
                operator_id=current_user.id,
                operator_name=current_user.real_name or current_user.username,
                old_status=old_status,
                new_status='CLOSED',
            )
            db.add(follow_up)
            db.add(issue)
            success_count += 1
        except Exception as e:
            failed_issues.append({"issue_id": issue_id, "reason": str(e)})
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message=f"批量关闭完成：成功 {success_count} 个，失败 {len(failed_issues)} 个",
        data={"success_count": success_count, "failed_issues": failed_issues}
    )


# ==================== 导入导出 ====================

# 检查Excel库是否可用
try:
    import pandas as pd
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


@router.get("/export", response_class=StreamingResponse)
def export_issues(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    category: Optional[str] = Query(None, description="问题分类"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
) -> Any:
    """导出问题到Excel"""
    if not EXCEL_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Excel处理库未安装，请安装pandas和openpyxl"
        )
    
    query = db.query(Issue)
    
    if category:
        query = query.filter(Issue.category == category)
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if status:
        query = query.filter(Issue.status == status)
    if start_date:
        query = query.filter(Issue.report_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Issue.report_date <= datetime.combine(end_date, datetime.max.time()))
    
    issues = query.order_by(desc(Issue.created_at)).all()
    
    # 构建DataFrame
    data = []
    for issue in issues:
        data.append({
            '问题编号': issue.issue_no,
            '问题分类': issue.category,
            '问题类型': issue.issue_type,
            '严重程度': issue.severity,
            '优先级': issue.priority,
            '标题': issue.title,
            '描述': issue.description or '',
            '提出人': issue.reporter_name or '',
            '提出时间': issue.report_date.strftime('%Y-%m-%d %H:%M:%S') if issue.report_date else '',
            '处理人': issue.assignee_name or '',
            '要求完成日期': issue.due_date.strftime('%Y-%m-%d') if issue.due_date else '',
            '状态': issue.status,
            '解决方案': issue.solution or '',
            '解决时间': issue.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if issue.resolved_at else '',
            '是否阻塞': '是' if issue.is_blocking else '否',
            '跟进次数': issue.follow_up_count or 0,
            '创建时间': issue.created_at.strftime('%Y-%m-%d %H:%M:%S') if issue.created_at else '',
        })
    
    df = pd.DataFrame(data)
    
    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='问题列表', index=False)
        
        # 设置列宽
        worksheet = writer.sheets['问题列表']
        column_widths = {
            'A': 15,  # 问题编号
            'B': 12,  # 问题分类
            'C': 12,  # 问题类型
            'D': 10,  # 严重程度
            'E': 8,   # 优先级
            'F': 30,  # 标题
            'G': 50,  # 描述
            'H': 12,  # 提出人
            'I': 18,  # 提出时间
            'J': 12,  # 处理人
            'K': 12,  # 要求完成日期
            'L': 10,  # 状态
            'M': 50,  # 解决方案
            'N': 18,  # 解决时间
            'O': 8,   # 是否阻塞
            'P': 10,  # 跟进次数
            'Q': 18,  # 创建时间
        }
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width
    
    output.seek(0)
    
    filename = f"问题列表_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/import", response_model=ResponseModel)
async def import_issues(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """从Excel导入问题"""
    if not EXCEL_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Excel处理库未安装，请安装pandas和openpyxl"
        )
    
    try:
        file_content = await file.read()
        df = pd.read_excel(io.BytesIO(file_content))
        
        # 验证必需的列
        required_columns = ['问题分类', '问题类型', '严重程度', '标题', '描述']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
            )
        
        imported_count = 0
        failed_rows = []
        
        for index, row in df.iterrows():
            try:
                # 生成问题编号
                issue_no = generate_issue_no(db)
                
                # 创建问题
                issue = Issue(
                    issue_no=issue_no,
                    category=str(row.get('问题分类', 'OTHER')).strip(),
                    project_id=int(row['项目ID']) if pd.notna(row.get('项目ID')) else None,
                    issue_type=str(row.get('问题类型', 'OTHER')).strip(),
                    severity=str(row.get('严重程度', 'MINOR')).strip(),
                    priority=str(row.get('优先级', 'MEDIUM')).strip(),
                    title=str(row.get('标题', '')).strip(),
                    description=str(row.get('描述', '')).strip(),
                    reporter_id=current_user.id,
                    reporter_name=current_user.real_name or current_user.username,
                    report_date=datetime.now(),
                    assignee_id=int(row['处理人ID']) if pd.notna(row.get('处理人ID')) else None,
                    due_date=pd.to_datetime(row['要求完成日期']).date() if pd.notna(row.get('要求完成日期')) else None,
                    status=str(row.get('状态', 'OPEN')).strip(),
                    is_blocking=str(row.get('是否阻塞', '否')).strip().lower() in ['是', 'true', '1'],
                )
                
                db.add(issue)
                db.flush()
                imported_count += 1
            except Exception as e:
                failed_rows.append({"row_index": index + 2, "error": str(e)})
        
        db.commit()
        
        if failed_rows:
            return ResponseModel(
                code=200,
                message=f"部分成功导入。成功 {imported_count} 条，失败 {len(failed_rows)} 条。",
                data={"imported_count": imported_count, "failed_rows": failed_rows[:10]}
            )
        
        return ResponseModel(
            code=200,
            message=f"成功导入 {imported_count} 条问题",
            data={"imported_count": imported_count}
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"文件处理失败: {e}")


# ==================== 看板数据 ====================

@router.get("/board", response_model=dict)
def get_issue_board(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取问题看板数据（按状态分组）"""
    query = db.query(Issue)
    
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    
    issues = query.all()
    
    # 按状态分组
    board = {
        "OPEN": [],
        "PROCESSING": [],
        "RESOLVED": [],
        "VERIFIED": [],
        "CLOSED": [],
        "CANCELLED": [],
    }
    
    for issue in issues:
        status = issue.status or "OPEN"
        if status not in board:
            status = "OPEN"
        
        board[status].append({
            "id": issue.id,
            "issue_no": issue.issue_no,
            "title": issue.title,
            "severity": issue.severity,
            "priority": issue.priority,
            "assignee_name": issue.assignee_name,
            "due_date": issue.due_date.isoformat() if issue.due_date else None,
            "is_blocking": issue.is_blocking,
            "project_name": issue.project.project_name if issue.project else None,
        })
    
    return {
        "columns": [
            {"key": "OPEN", "title": "待处理", "count": len(board["OPEN"])},
            {"key": "PROCESSING", "title": "处理中", "count": len(board["PROCESSING"])},
            {"key": "RESOLVED", "title": "已解决", "count": len(board["RESOLVED"])},
            {"key": "VERIFIED", "title": "已验证", "count": len(board["VERIFIED"])},
            {"key": "CLOSED", "title": "已关闭", "count": len(board["CLOSED"])},
            {"key": "CANCELLED", "title": "已取消", "count": len(board["CANCELLED"])},
        ],
        "issues": board,
    }


# ==================== 趋势分析 ====================

@router.get("/statistics/trend", response_model=dict)
def get_issue_trend(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    group_by: str = Query("day", description="分组方式：day/week/month"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取问题趋势分析数据"""
    if not start_date:
        start_date = date.today() - timedelta(days=30)
    if not end_date:
        end_date = date.today()
    
    query = db.query(Issue).filter(
        Issue.report_date >= datetime.combine(start_date, datetime.min.time()),
        Issue.report_date <= datetime.combine(end_date, datetime.max.time())
    )
    
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    
    issues = query.all()
    
    # 按日期分组统计
    trend_data = {}
    for issue in issues:
        report_date = issue.report_date.date() if issue.report_date else date.today()
        
        # 根据group_by确定分组键
        if group_by == "week":
            days_since_monday = report_date.weekday()
            week_start = report_date - timedelta(days=days_since_monday)
            key = week_start.isoformat()
        elif group_by == "month":
            key = date(report_date.year, report_date.month, 1).isoformat()
        else:  # day
            key = report_date.isoformat()
        
        if key not in trend_data:
            trend_data[key] = {
                "date": key,
                "created": 0,
                "resolved": 0,
                "closed": 0,
            }
        
        trend_data[key]["created"] += 1
        
        if issue.resolved_at:
            resolved_date = issue.resolved_at.date()
            if group_by == "week":
                days_since_monday = resolved_date.weekday()
                week_start = resolved_date - timedelta(days=days_since_monday)
                resolved_key = week_start.isoformat()
            elif group_by == "month":
                resolved_key = date(resolved_date.year, resolved_date.month, 1).isoformat()
            else:
                resolved_key = resolved_date.isoformat()
            
            if resolved_key not in trend_data:
                trend_data[resolved_key] = {
                    "date": resolved_key,
                    "created": 0,
                    "resolved": 0,
                    "closed": 0,
                }
            trend_data[resolved_key]["resolved"] += 1
        
        if issue.status == "CLOSED":
            # 假设关闭时间就是更新时间（实际应该有closed_at字段）
            closed_date = issue.updated_at.date() if issue.updated_at else None
            if closed_date:
                if group_by == "week":
                    days_since_monday = closed_date.weekday()
                    week_start = closed_date - timedelta(days=days_since_monday)
                    closed_key = week_start.isoformat()
                elif group_by == "month":
                    closed_key = date(closed_date.year, closed_date.month, 1).isoformat()
                else:
                    closed_key = closed_date.isoformat()
                
                if closed_key not in trend_data:
                    trend_data[closed_key] = {
                        "date": closed_key,
                        "created": 0,
                        "resolved": 0,
                        "closed": 0,
                    }
                trend_data[closed_key]["closed"] += 1
    
    # 排序并填充缺失日期
    result = []
    current_date = start_date
    while current_date <= end_date:
        if group_by == "week":
            days_since_monday = current_date.weekday()
            week_start = current_date - timedelta(days=days_since_monday)
            key = week_start.isoformat()
        elif group_by == "month":
            key = date(current_date.year, current_date.month, 1).isoformat()
        else:
            key = current_date.isoformat()
        
        if key in trend_data:
            result.append(trend_data[key])
        else:
            result.append({
                "date": key,
                "created": 0,
                "resolved": 0,
                "closed": 0,
            })
        
        if group_by == "week":
            current_date += timedelta(days=7)
        elif group_by == "month":
            # 移动到下个月
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        else:
            current_date += timedelta(days=1)
    
    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "group_by": group_by,
        "trend": result,
    }


# ==================== 删除问题（软删除）====================

@router.delete("/{issue_id}", response_model=ResponseModel)
def delete_issue(
    issue_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """删除问题（软删除，仅管理员）"""
    # 检查是否为管理员
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员才能删除问题")
    
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    # 软删除：将状态标记为DELETED（如果状态字段支持）或使用其他方式
    # 这里假设使用状态字段，如果Issue模型有is_deleted字段则使用该字段
    # 暂时使用状态标记
    if issue.status == 'DELETED':
        raise HTTPException(status_code=400, detail="问题已删除")
    
    old_status = issue.status
    issue.status = 'DELETED'
    
    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='STATUS_CHANGE',
        content=f"问题已删除（管理员操作）",
        operator_id=current_user.id,
        operator_name=current_user.real_name or current_user.username,
        old_status=old_status,
        new_status='DELETED',
    )
    db.add(follow_up)
    db.add(issue)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="问题已删除"
    )


# ==================== 任务问题列表 ====================

@router.get("/tasks/{task_id}/issues", response_model=IssueListResponse)
def get_task_issues(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """获取任务下的所有问题"""
    # 验证任务是否存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return list_issues(
        db=db,
        current_user=current_user,
        task_id=task_id,
        page=page,
        page_size=page_size,
        status=status,
    )


# ==================== 验收问题列表 ====================

@router.get("/acceptance-orders/{order_id}/issues", response_model=IssueListResponse)
def get_acceptance_order_issues(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
) -> Any:
    """获取验收单下的所有问题"""
    # 验证验收单是否存在
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")
    
    query = db.query(Issue).filter(Issue.acceptance_order_id == order_id)
    
    if status:
        query = query.filter(Issue.status == status)
    
    # 排除已删除的问题
    query = query.filter(Issue.status != 'DELETED')
    
    total = query.count()
    issues = query.order_by(desc(Issue.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for issue in issues:
        items.append(IssueResponse(
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
            attachments=issue.attachments or [],
            tags=issue.tags or [],
            follow_up_count=issue.follow_up_count,
            last_follow_up_at=issue.last_follow_up_at,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            project_code=issue.project.project_code if issue.project else None,
            project_name=issue.project.project_name if issue.project else None,
            machine_code=issue.machine.machine_code if issue.machine else None,
            machine_name=issue.machine.machine_name if issue.machine else None,
        ))
    
    return IssueListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


# ==================== 问题原因分析 ====================

@router.get("/statistics/cause-analysis", response_model=dict)
def get_issue_cause_analysis(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    top_n: int = Query(10, ge=1, le=50, description="返回Top N原因"),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取问题原因分析（Top N原因统计）"""
    query = db.query(Issue).filter(Issue.status != 'DELETED')
    
    if project_id:
        query = query.filter(Issue.project_id == project_id)
    if start_date:
        query = query.filter(Issue.report_date >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Issue.report_date <= datetime.combine(end_date, datetime.max.time()))
    
    issues = query.all()
    
    # 分析问题原因（从描述、解决方案、影响范围等字段提取）
    # 这里使用简单的关键词匹配，实际可以使用NLP技术
    cause_keywords = {
        '设计': ['设计', '图纸', '规格', '参数', '方案'],
        '工艺': ['工艺', '加工', '装配', '焊接', '涂装'],
        '物料': ['物料', '材料', '零件', '配件', '缺料'],
        '质量': ['质量', '缺陷', '不合格', '不良', '瑕疵'],
        '进度': ['进度', '延期', '延迟', '时间', '计划'],
        '人员': ['人员', '人力', '技能', '培训', '经验'],
        '设备': ['设备', '机器', '工具', '故障', '维护'],
        '沟通': ['沟通', '协调', '配合', '信息', '反馈'],
        '其他': []
    }
    
    cause_stats = {}
    for keyword, patterns in cause_keywords.items():
        cause_stats[keyword] = {
            "cause": keyword,
            "count": 0,
            "issues": []
        }
    
    for issue in issues:
        # 合并所有文本字段进行分析
        text_content = f"{issue.description or ''} {issue.solution or ''} {issue.impact_scope or ''}".lower()
        
        matched = False
        for keyword, patterns in cause_keywords.items():
            if keyword == '其他':
                continue
            for pattern in patterns:
                if pattern in text_content:
                    cause_stats[keyword]["count"] += 1
                    cause_stats[keyword]["issues"].append({
                        "issue_id": issue.id,
                        "issue_no": issue.issue_no,
                        "title": issue.title,
                    })
                    matched = True
                    break
            if matched:
                break
        
        if not matched:
            cause_stats['其他']["count"] += 1
            cause_stats['其他']["issues"].append({
                "issue_id": issue.id,
                "issue_no": issue.issue_no,
                "title": issue.title,
            })
    
    # 按数量排序，取Top N
    sorted_causes = sorted(
        [stats for stats in cause_stats.values() if stats["count"] > 0],
        key=lambda x: x["count"],
        reverse=True
    )[:top_n]
    
    # 计算百分比
    total_issues = len(issues)
    for cause in sorted_causes:
        cause["percentage"] = round((cause["count"] / total_issues * 100) if total_issues > 0 else 0, 2)
        # 只返回问题ID列表，不返回完整问题信息（避免响应过大）
        cause["issue_ids"] = [item["issue_id"] for item in cause["issues"]]
        cause.pop("issues", None)
    
    return {
        "total_issues": total_issues,
        "top_causes": sorted_causes,
        "analysis_period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }
    }


# ==================== 问题模板管理 ====================

@template_router.get("/", response_model=IssueTemplateListResponse)
def list_issue_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（模板编码/名称）"),
    category: Optional[str] = Query(None, description="问题分类筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
) -> Any:
    """获取问题模板列表"""
    query = db.query(IssueTemplate)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                IssueTemplate.template_code.like(f'%{keyword}%'),
                IssueTemplate.template_name.like(f'%{keyword}%')
            )
        )
    
    # 分类筛选
    if category:
        query = query.filter(IssueTemplate.category == category)
    
    # 状态筛选
    if is_active is not None:
        query = query.filter(IssueTemplate.is_active == is_active)
    
    # 总数
    total = query.count()
    
    # 分页
    templates = query.order_by(desc(IssueTemplate.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    # 构建响应
    items = []
    for template in templates:
        item = IssueTemplateResponse(
            id=template.id,
            template_name=template.template_name,
            template_code=template.template_code,
            category=template.category,
            issue_type=template.issue_type,
            default_severity=template.default_severity,
            default_priority=template.default_priority,
            default_impact_level=template.default_impact_level,
            title_template=template.title_template,
            description_template=template.description_template,
            solution_template=template.solution_template,
            default_tags=json.loads(template.default_tags) if template.default_tags else [],
            default_impact_scope=template.default_impact_scope,
            default_is_blocking=template.default_is_blocking,
            is_active=template.is_active,
            remark=template.remark,
            usage_count=template.usage_count,
            last_used_at=template.last_used_at,
            created_at=template.created_at,
            updated_at=template.updated_at,
        )
        items.append(item)
    
    return IssueTemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@template_router.get("/{template_id}", response_model=IssueTemplateResponse)
def get_issue_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取问题模板详情"""
    template = db.query(IssueTemplate).filter(IssueTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="问题模板不存在")
    
    return IssueTemplateResponse(
        id=template.id,
        template_name=template.template_name,
        template_code=template.template_code,
        category=template.category,
        issue_type=template.issue_type,
        default_severity=template.default_severity,
        default_priority=template.default_priority,
        default_impact_level=template.default_impact_level,
        title_template=template.title_template,
        description_template=template.description_template,
        solution_template=template.solution_template,
        default_tags=json.loads(template.default_tags) if template.default_tags else [],
        default_impact_scope=template.default_impact_scope,
        default_is_blocking=template.default_is_blocking,
        is_active=template.is_active,
        remark=template.remark,
        usage_count=template.usage_count,
        last_used_at=template.last_used_at,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@template_router.post("/", response_model=IssueTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_issue_template(
    template_in: IssueTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """创建问题模板"""
    # 验证模板编码唯一性
    existing = db.query(IssueTemplate).filter(IssueTemplate.template_code == template_in.template_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")
    
    # 创建模板
    template = IssueTemplate(
        template_name=template_in.template_name,
        template_code=template_in.template_code,
        category=template_in.category,
        issue_type=template_in.issue_type,
        default_severity=template_in.default_severity,
        default_priority=template_in.default_priority,
        default_impact_level=template_in.default_impact_level,
        title_template=template_in.title_template,
        description_template=template_in.description_template,
        solution_template=template_in.solution_template,
        default_tags=str(template_in.default_tags) if template_in.default_tags else None,
        default_impact_scope=template_in.default_impact_scope,
        default_is_blocking=template_in.default_is_blocking,
        is_active=template_in.is_active if template_in.is_active is not None else True,
        remark=template_in.remark,
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return get_issue_template(template.id, db, current_user)


@template_router.put("/{template_id}", response_model=IssueTemplateResponse)
def update_issue_template(
    template_id: int,
    template_in: IssueTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """更新问题模板"""
    template = db.query(IssueTemplate).filter(IssueTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="问题模板不存在")
    
    # 如果更新模板编码，验证唯一性
    update_data = template_in.dict(exclude_unset=True)
    if 'template_code' in update_data:
        existing = db.query(IssueTemplate).filter(
            IssueTemplate.template_code == update_data['template_code'],
            IssueTemplate.id != template_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="模板编码已存在")
    
    # 处理JSON字段
    if 'default_tags' in update_data:
        update_data['default_tags'] = str(update_data['default_tags'])
    
    # 更新字段
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    return get_issue_template(template.id, db, current_user)


@template_router.delete("/{template_id}", response_model=ResponseModel)
def delete_issue_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """删除问题模板（软删除）"""
    template = db.query(IssueTemplate).filter(IssueTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="问题模板不存在")
    
    # 软删除：设置is_active=False
    template.is_active = False
    
    db.commit()
    
    return ResponseModel(
        code=200,
        message="问题模板已删除"
    )


@template_router.post("/{template_id}/create-issue", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue_from_template(
    template_id: int,
    issue_in: IssueFromTemplateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """从模板创建问题"""
    # 获取模板
    template = db.query(IssueTemplate).filter(IssueTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="问题模板不存在")
    
    if not template.is_active:
        raise HTTPException(status_code=400, detail="问题模板未启用")
    
    # 从模板获取默认值
    category = template.category
    issue_type = template.issue_type
    severity = issue_in.severity or template.default_severity or 'MINOR'
    priority = issue_in.priority or template.default_priority or 'MEDIUM'
    impact_level = template.default_impact_level
    is_blocking = template.default_is_blocking
    
    # 处理模板变量替换
    title = issue_in.title or template.title_template
    description = issue_in.description or template.description_template or ''
    
    # 如果有关联对象，获取变量值进行替换
    if issue_in.project_id:
        project = db.query(Project).filter(Project.id == issue_in.project_id).first()
        if project:
            title = title.replace('{project_name}', project.project_name or '')
            title = title.replace('{project_code}', project.project_code or '')
            description = description.replace('{project_name}', project.project_name or '')
            description = description.replace('{project_code}', project.project_code or '')
    
    if issue_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == issue_in.machine_id).first()
        if machine:
            title = title.replace('{machine_name}', machine.machine_name or '')
            title = title.replace('{machine_code}', machine.machine_code or '')
            description = description.replace('{machine_name}', machine.machine_name or '')
            description = description.replace('{machine_code}', machine.machine_code or '')
    
    # 替换其他常见变量
    title = title.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
    description = description.replace('{date}', datetime.now().strftime('%Y-%m-%d'))
    
    # 生成问题编号
    issue_no = generate_issue_no(db)
    
    # 创建问题
    issue = Issue(
        issue_no=issue_no,
        category=category,
        project_id=issue_in.project_id,
        machine_id=issue_in.machine_id,
        task_id=issue_in.task_id,
        acceptance_order_id=issue_in.acceptance_order_id,
        related_issue_id=None,
        issue_type=issue_type,
        severity=severity,
        priority=priority,
        title=title,
        description=description,
        reporter_id=current_user.id,
        reporter_name=current_user.real_name or current_user.username,
        report_date=datetime.now(),
        assignee_id=issue_in.assignee_id,
        assignee_name=(lambda aid: (lambda u: u.real_name or u.username if u else None)(db.query(User).filter(User.id == aid).first()) if aid else None)(issue_in.assignee_id),
        due_date=issue_in.due_date,
        status='OPEN',
        impact_scope=template.default_impact_scope,
        impact_level=impact_level,
        is_blocking=is_blocking,
        attachments=None,
        tags=str(template.default_tags) if template.default_tags else None,
    )
    
    db.add(issue)
    
    # 更新模板使用统计
    template.usage_count = (template.usage_count or 0) + 1
    template.last_used_at = datetime.now()
    
    db.commit()
    db.refresh(issue)
    
    return get_issue(issue.id, db, current_user)
