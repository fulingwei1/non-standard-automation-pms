# -*- coding: utf-8 -*-
"""
问题模板管理端点

包含：模板CRUD、从模板创建问题
"""

import json
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.issue import Issue, IssueTemplate
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query
from app.schemas.issue import (
    IssueFromTemplateRequest,
    IssueResponse,
    IssueTemplateCreate,
    IssueTemplateListResponse,
    IssueTemplateResponse,
    IssueTemplateUpdate,
)

from .utils import generate_issue_no

router = APIRouter()


def _build_template_response(template: IssueTemplate) -> IssueTemplateResponse:
    """构建模板响应对象"""
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


def _build_issue_response(issue: Issue) -> IssueResponse:
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
        follow_up_count=issue.follow_up_count,
        last_follow_up_at=issue.last_follow_up_at,
        impact_scope=issue.impact_scope,
        impact_level=issue.impact_level,
        is_blocking=issue.is_blocking,
        attachments=json.loads(issue.attachments) if issue.attachments else [],
        tags=json.loads(issue.tags) if issue.tags else [],
        root_cause=getattr(issue, 'root_cause', None),
        responsible_engineer_id=getattr(issue, 'responsible_engineer_id', None),
        responsible_engineer_name=getattr(issue, 'responsible_engineer_name', None),
        estimated_inventory_loss=getattr(issue, 'estimated_inventory_loss', None),
        estimated_extra_hours=getattr(issue, 'estimated_extra_hours', None),
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        project_code=issue.project.project_code if issue.project else None,
        project_name=issue.project.project_name if issue.project else None,
        machine_code=issue.machine.machine_code if issue.machine else None,
        machine_name=issue.machine.machine_name if issue.machine else None,
        service_ticket_id=issue.service_ticket_id,
        service_ticket_no=issue.service_ticket.ticket_no if issue.service_ticket else None,
    )


@router.get("/", response_model=IssueTemplateListResponse)
def list_issue_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（模板编码/名称）"),
    category: Optional[str] = Query(None, description="问题分类筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
) -> Any:
    """获取问题模板列表"""
    query = db.query(IssueTemplate)

    # 应用关键词过滤（模板编码/名称）
    from app.common.query_filters import apply_keyword_filter
    query = apply_keyword_filter(query, IssueTemplate, keyword, ["template_code", "template_name"])

    # 分类筛选
    if category:
        query = query.filter(IssueTemplate.category == category)

    # 状态筛选
    if is_active is not None:
        query = query.filter(IssueTemplate.is_active == is_active)

    # 总数
    total = query.count()

    # 分页
    templates = query.order_by(desc(IssueTemplate.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    # 构建响应
    items = [_build_template_response(t) for t in templates]

    return IssueTemplateListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.get("/{template_id}", response_model=IssueTemplateResponse)
def get_issue_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """获取问题模板详情"""
    template = db.query(IssueTemplate).filter(IssueTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="问题模板不存在")

    return _build_template_response(template)


@router.post("/", response_model=IssueTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_issue_template(
    template_in: IssueTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
) -> Any:
    """创建问题模板"""
    base_code = template_in.template_code or f"TEMPLATE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    candidate_code = base_code
    while db.query(IssueTemplate.id).filter(IssueTemplate.template_code == candidate_code).first():
        candidate_code = f"{base_code}-{uuid4().hex[:4].upper()}"

    # 创建模板
    template = IssueTemplate(
        template_name=template_in.template_name,
        template_code=candidate_code,
        category=template_in.category,
        issue_type=template_in.issue_type,
        default_severity=template_in.default_severity,
        default_priority=template_in.default_priority,
        default_impact_level=template_in.default_impact_level,
        title_template=template_in.title_template,
        description_template=template_in.description_template,
        solution_template=template_in.solution_template,
        default_tags=json.dumps(template_in.default_tags, ensure_ascii=False)
        if template_in.default_tags is not None
        else None,
        default_impact_scope=template_in.default_impact_scope,
        default_is_blocking=template_in.default_is_blocking,
        is_active=template_in.is_active if template_in.is_active is not None else True,
        remark=template_in.remark,
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return _build_template_response(template)


@router.put("/{template_id}", response_model=IssueTemplateResponse)
def update_issue_template(
    template_id: int,
    template_in: IssueTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
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
        tags_value = update_data['default_tags']
        update_data['default_tags'] = (
            json.dumps(tags_value, ensure_ascii=False) if tags_value is not None else None
        )

    # 更新字段
    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)

    return _build_template_response(template)


@router.delete("/{template_id}", response_model=ResponseModel)
def delete_issue_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
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


@router.post("/{template_id}/create-issue", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def create_issue_from_template(
    template_id: int,
    issue_in: IssueFromTemplateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("issue:read")),
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

    # 获取处理人名称
    assignee_name = None
    if issue_in.assignee_id:
        assignee = db.query(User).filter(User.id == issue_in.assignee_id).first()
        if assignee:
            assignee_name = assignee.real_name or assignee.username

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
        assignee_name=assignee_name,
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

    return _build_issue_response(issue)
