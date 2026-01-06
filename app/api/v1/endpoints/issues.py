"""
问题管理中心 API endpoints
"""
from typing import Any, List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.api import deps
from app.core.security import get_current_user
from app.models.issue import Issue, IssueFollowUpRecord
from app.models.user import User
from app.models.project import Project, Machine
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
    PaginatedResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()


def generate_issue_no(db: Session) -> str:
    """生成问题编号"""
    today = datetime.now().strftime('%Y%m%d')
    count = db.query(Issue).filter(Issue.issue_no.like(f'IS{today}%')).count()
    return f'IS{today}{str(count + 1).zfill(3)}'


@router.get("/", response_model=IssueListResponse)
def list_issues(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
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
    is_blocking: Optional[bool] = Query(None, description="是否阻塞"),
    is_overdue: Optional[bool] = Query(None, description="是否逾期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> Any:
    """获取问题列表"""
    query = db.query(Issue)
    
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
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取问题详情"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
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
    )


@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue(
    issue_in: IssueCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """创建问题"""
    # 生成问题编号
    issue_no = generate_issue_no(db)
    
    # 获取处理人姓名（安全处理NULL情况）
    assignee_name = None
    if issue_in.assignee_id:
        assignee = db.query(User).filter(User.id == issue_in.assignee_id).first()
        assignee_name = assignee.real_name if assignee else None

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
        reporter_name=current_user.real_name,
        report_date=datetime.now(),
        assignee_id=issue_in.assignee_id,
        assignee_name=assignee_name,
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


@router.put("/{issue_id}", response_model=IssueResponse)
def update_issue(
    issue_id: int,
    issue_in: IssueUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """更新问题"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")
    
    # 更新字段
    update_data = issue_in.model_dump(exclude_unset=True)
    if 'attachments' in update_data:
        update_data['attachments'] = str(update_data['attachments'])
    if 'tags' in update_data:
        update_data['tags'] = str(update_data['tags'])
    if 'assignee_id' in update_data and update_data['assignee_id']:
        assignee = db.query(User).filter(User.id == update_data['assignee_id']).first()
        if assignee:
            update_data['assignee_name'] = assignee.real_name
    
    for field, value in update_data.items():
        setattr(issue, field, value)
    
    db.commit()
    db.refresh(issue)
    
    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/assign", response_model=IssueResponse)
def assign_issue(
    issue_id: int,
    assign_req: IssueAssignRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
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
    issue.assignee_name = assignee.real_name
    issue.due_date = assign_req.due_date

    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='ASSIGNMENT',
        content=assign_req.comment or f"问题已分配给 {assignee.real_name}",
        operator_id=current_user.id,
        operator_name=current_user.real_name,
        old_status=None,
        new_status=None,
    )
    db.add(follow_up)
    
    db.commit()
    db.refresh(issue)
    
    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: int,
    resolve_req: IssueResolveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
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
    issue.resolved_by_name = current_user.real_name

    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='SOLUTION',
        content=resolve_req.comment or "问题已解决",
        operator_id=current_user.id,
        operator_name=current_user.real_name,
        old_status=old_status,
        new_status='RESOLVED',
    )
    db.add(follow_up)
    
    db.commit()
    db.refresh(issue)
    
    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/verify", response_model=IssueResponse)
def verify_issue(
    issue_id: int,
    verify_req: IssueVerifyRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
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
    issue.verified_by_name = current_user.real_name
    issue.verified_result = verify_req.verified_result
    
    if verify_req.verified_result == 'VERIFIED':
        issue.status = 'CLOSED'
    
    # 创建跟进记录
    follow_up = IssueFollowUpRecord(
        issue_id=issue_id,
        follow_up_type='VERIFICATION',
        content=verify_req.comment or f"问题验证结果：{verify_req.verified_result}",
        operator_id=current_user.id,
        operator_name=current_user.real_name,
        old_status='RESOLVED',
        new_status=issue.status,
    )
    db.add(follow_up)

    db.commit()
    db.refresh(issue)

    return get_issue(issue.id, db, current_user)


@router.post("/{issue_id}/status", response_model=IssueResponse)
def change_issue_status(
    issue_id: int,
    status_req: IssueStatusChangeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(get_current_user),
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
        operator_name=current_user.real_name,
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
        operator_name=current_user.real_name,
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
    current_user: User = Depends(get_current_user),
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

