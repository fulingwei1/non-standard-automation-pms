# -*- coding: utf-8 -*-
"""
EXCEPTIONS - 自动生成
从 alerts.py 拆分
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.alert import (
    ExceptionAction,
    ExceptionEscalation,
    ExceptionEvent,
)
from app.models.issue import Issue
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.alert import (
    ExceptionEventCreate,
    ExceptionEventResponse,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .notifications import generate_exception_no

router = APIRouter(tags=["exceptions"])

# ==================== 路由定义 ====================
# 共 7 个路由

@router.get("/exceptions", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def read_exception_events(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（异常编号/标题）"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    event_type: Optional[str] = Query(None, description="异常类型筛选"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    responsible_user_id: Optional[int] = Query(None, description="责任人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取异常事件列表（支持分页和筛选）
    """
    query = db.query(ExceptionEvent)

    # 关键词搜索
    query = apply_keyword_filter(query, ExceptionEvent, keyword, ["event_no", "event_title"])

    # 项目筛选
    if project_id:
        query = query.filter(ExceptionEvent.project_id == project_id)

    # 异常类型筛选
    if event_type:
        query = query.filter(ExceptionEvent.event_type == event_type)

    # 严重程度筛选
    if severity:
        query = query.filter(ExceptionEvent.severity == severity)

    # 状态筛选
    if status:
        query = query.filter(ExceptionEvent.status == status)

    # 责任人筛选
    if responsible_user_id:
        query = query.filter(ExceptionEvent.responsible_user_id == responsible_user_id)

    # 计算总数
    total = query.count()

    # 分页
    events = apply_pagination(query.order_by(ExceptionEvent.created_at.desc()), pagination.offset, pagination.limit).all()

    # 构建响应数据
    items = []
    for event in events:
        discovered_by_name = None
        if event.discovered_by:
            user = db.query(User).filter(User.id == event.discovered_by).first()
            discovered_by_name = user.real_name if user else None

        items.append({
            "id": event.id,
            "event_no": event.event_no,
            "source_type": event.source_type,
            "project_id": event.project_id,
            "project_name": event.project.project_name if event.project else None,
            "machine_id": event.machine_id,
            "machine_name": event.machine.machine_name if event.machine else None,
            "event_type": event.event_type,
            "severity": event.severity,
            "event_title": event.event_title,
            "status": event.status,
            "discovered_at": event.discovered_at.isoformat() if event.discovered_at else None,
            "discovered_by_name": discovered_by_name,
            "schedule_impact": event.schedule_impact or 0,
            "cost_impact": float(event.cost_impact) if event.cost_impact else 0,
            "responsible_user_id": event.responsible_user_id,
            "due_date": event.due_date.isoformat() if event.due_date else None,
            "is_overdue": event.is_overdue or False,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        })

    return pagination.to_response(items, total)


@router.post("/exceptions", response_model=ExceptionEventResponse, status_code=status.HTTP_201_CREATED)
def create_exception_event(
    *,
    db: Session = Depends(deps.get_db),
    event_in: ExceptionEventCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建异常事件
    """
    # 验证项目
    if event_in.project_id:
        project = db.query(Project).filter(Project.id == event_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

    # 验证设备
    if event_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == event_in.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="设备不存在")

    # 生成异常编号
    event_no = generate_exception_no(db)

    # 创建异常事件
    event = ExceptionEvent(
        event_no=event_no,
        source_type=event_in.source_type,
        source_id=event_in.source_id,
        alert_id=event_in.alert_id,
        project_id=event_in.project_id,
        machine_id=event_in.machine_id,
        event_type=event_in.event_type,
        severity=event_in.severity,
        event_title=event_in.event_title,
        event_description=event_in.event_description,
        discovered_at=datetime.now(),
        discovered_by=current_user.id,
        discovery_location=event_in.discovery_location,
        impact_scope=event_in.impact_scope,
        impact_description=event_in.impact_description,
        schedule_impact=event_in.schedule_impact,
        cost_impact=event_in.cost_impact or 0,
        responsible_dept=event_in.responsible_dept,
        responsible_user_id=event_in.responsible_user_id,
        due_date=event_in.due_date,
        status="OPEN",
        attachments=event_in.attachments,
        created_by=current_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return read_exception_event(event.id, db, current_user)


@router.get("/exceptions/{event_id}", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def read_exception_event(
    event_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取异常事件详情
    """
    event = db.query(ExceptionEvent).filter(ExceptionEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="异常事件不存在")

    # 获取发现人姓名
    discovered_by_name = None
    if event.discovered_by:
        user = db.query(User).filter(User.id == event.discovered_by).first()
        discovered_by_name = user.real_name if user else None

    # 获取处理记录
    actions = event.actions.order_by(ExceptionAction.created_at.desc()).all()
    action_list = []
    for action in actions:
        action_user = db.query(User).filter(User.id == action.created_by).first()
        action_list.append({
            "id": action.id,
            "action_type": action.action_type,
            "action_content": action.action_content,
            "old_status": action.old_status,
            "new_status": action.new_status,
            "action_user_id": action.created_by,
            "action_user_name": action_user.real_name if action_user else None,
            "created_at": action.created_at.isoformat() if action.created_at else None,
        })

    return {
        "id": event.id,
        "event_no": event.event_no,
        "source_type": event.source_type,
        "alert_id": event.alert_id,
        "project_id": event.project_id,
        "project_name": event.project.project_name if event.project else None,
        "machine_id": event.machine_id,
        "machine_name": event.machine.machine_name if event.machine else None,
        "event_type": event.event_type,
        "severity": event.severity,
        "event_title": event.event_title,
        "event_description": event.event_description,
        "discovered_at": event.discovered_at,
        "discovered_by": event.discovered_by,
        "discovered_by_name": discovered_by_name,
        "discovery_location": event.discovery_location,
        "impact_scope": event.impact_scope,
        "impact_description": event.impact_description,
        "schedule_impact": event.schedule_impact or 0,
        "cost_impact": event.cost_impact or 0,
        "status": event.status,
        "responsible_dept": event.responsible_dept,
        "responsible_user_id": event.responsible_user_id,
        "due_date": event.due_date,
        "is_overdue": event.is_overdue or False,
        "root_cause": event.root_cause,
        "cause_category": event.cause_category,
        "solution": event.solution,
        "preventive_measures": event.preventive_measures,
        "resolved_at": event.resolved_at,
        "resolved_by": event.resolved_by,
        "resolution_note": event.resolution_note,
        "verified_at": event.verified_at,
        "verified_by": event.verified_by,
        "verification_result": event.verification_result,
        "attachments": event.attachments,
        "actions": action_list,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }


@router.put("/exceptions/{event_id}/status", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def update_exception_status(
    *,
    db: Session = Depends(deps.get_db),
    event_id: int,
    status: str = Query(..., description="新状态"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新异常状态
    """
    event = db.query(ExceptionEvent).filter(ExceptionEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="异常事件不存在")

    event.status = status

    # 如果状态为RESOLVED，记录解决时间
    if status == "RESOLVED" and not event.resolved_at:
        event.resolved_at = datetime.now()
        event.resolved_by = current_user.id

    db.add(event)
    db.commit()
    db.refresh(event)

    return read_exception_event(event_id, db, current_user)


@router.post("/exceptions/{event_id}/actions", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_exception_action(
    *,
    db: Session = Depends(deps.get_db),
    event_id: int,
    action_type: str = Query(..., description="操作类型"),
    action_content: str = Query(..., description="操作内容"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加处理记录
    """
    event = db.query(ExceptionEvent).filter(ExceptionEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="异常事件不存在")

    action = ExceptionAction(
        event_id=event_id,
        action_type=action_type,
        action_content=action_content,
        old_status=event.status,
        new_status=event.status,
        created_by=current_user.id,
    )
    db.add(action)
    db.commit()

    return ResponseModel(
        code=200,
        message="处理记录已添加",
        data={
            "action_id": action.id,
            "event_id": event_id,
        }
    )


@router.post("/exceptions/{event_id}/escalate", response_model=ExceptionEventResponse, status_code=status.HTTP_200_OK)
def escalate_exception(
    *,
    db: Session = Depends(deps.get_db),
    event_id: int,
    escalate_to_user_id: Optional[int] = Query(None, description="升级到用户ID"),
    escalate_to_dept: Optional[str] = Query(None, description="升级到部门"),
    escalation_reason: Optional[str] = Query(None, description="升级原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    异常升级
    """
    event = db.query(ExceptionEvent).filter(ExceptionEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="异常事件不存在")

    # 创建升级记录
    escalation = ExceptionEscalation(
        event_id=event_id,
        escalated_from=current_user.id,
        escalated_to=escalate_to_user_id or current_user.id,  # 如果没有指定，使用当前用户
        escalated_at=datetime.now(),
        escalation_reason=escalation_reason,
        escalation_level=1,  # 升级层级，可以根据实际情况计算
    )
    db.add(escalation)

    # 更新责任人
    if escalate_to_user_id:
        event.responsible_user_id = escalate_to_user_id
    if escalate_to_dept:
        event.responsible_dept = escalate_to_dept

    # 如果严重程度不是最高，可以提升严重程度
    if event.severity == "MINOR":
        event.severity = "MAJOR"
    elif event.severity == "MAJOR":
        event.severity = "CRITICAL"

    db.add(event)
    db.commit()
    db.refresh(event)

    return read_exception_event(event_id, db, current_user)


@router.post("/exceptions/from-issue", response_model=ExceptionEventResponse, status_code=status.HTTP_201_CREATED)
def create_exception_from_issue(
    *,
    db: Session = Depends(deps.get_db),
    issue_id: int = Query(..., description="问题ID"),
    event_type: str = Query(..., description="异常类型"),
    severity: str = Query(..., description="严重程度"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从问题创建异常事件
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    # 生成异常编号
    event_no = generate_exception_no(db)

    # 创建异常事件
    event = ExceptionEvent(
        event_no=event_no,
        source_type="ISSUE",
        source_id=issue_id,
        project_id=issue.project_id,
        machine_id=issue.machine_id,
        event_type=event_type,
        severity=severity,
        event_title=f"问题转异常：{issue.issue_title}",
        event_description=issue.issue_description or "",
        discovered_at=issue.created_at or datetime.now(),
        discovered_by=issue.reporter_id or current_user.id,
        impact_scope="LOCAL",
        schedule_impact=0,
        cost_impact=0,
        status="OPEN",
        created_by=current_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return read_exception_event(event.id, db, current_user)


# ==================== 项目健康度快照 ====================
