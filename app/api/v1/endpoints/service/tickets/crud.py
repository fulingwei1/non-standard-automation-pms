# -*- coding: utf-8 -*-
"""
服务工单管理 - CRUD操作
"""
from typing import Any, Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Customer, Project
from app.models.service import ServiceTicket
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.service import ServiceTicketCreate, ServiceTicketResponse

from fastapi import APIRouter

from ..number_utils import generate_ticket_no

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ServiceTicketResponse], status_code=status.HTTP_200_OK)
def read_service_tickets(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    urgency: Optional[str] = Query(None, description="紧急程度筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（工单号/问题描述）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取服务工单列表
    """
    query = db.query(ServiceTicket)

    if status:
        query = query.filter(ServiceTicket.status == status)
    if urgency:
        query = query.filter(ServiceTicket.urgency == urgency)
    if project_id:
        query = query.filter(ServiceTicket.project_id == project_id)
    if customer_id:
        query = query.filter(ServiceTicket.customer_id == customer_id)
    if keyword:
        query = query.filter(
            or_(
                ServiceTicket.ticket_no.like(f"%{keyword}%"),
                ServiceTicket.problem_desc.like(f"%{keyword}%"),
            )
        )

    total = query.count()
    items = query.order_by(desc(ServiceTicket.created_at)).offset((page - 1) * page_size).limit(page_size).all()

    # 获取项目名称和客户名称
    for item in items:
        if item.project_id:
            project = db.query(Project).filter(Project.id == item.project_id).first()
            if project:
                item.project_name = project.project_name
        if item.customer_id:
            customer = db.query(Customer).filter(Customer.id == item.customer_id).first()
            if customer:
                item.customer_name = customer.customer_name

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("", response_model=ServiceTicketResponse, status_code=status.HTTP_201_CREATED)
def create_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_in: ServiceTicketCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建服务工单（支持多项目关联和直接分配）
    """
    from datetime import datetime

    from app.models.service import ServiceTicketCcUser, ServiceTicketProject

    # 验证主项目是否存在
    project = db.query(Project).filter(Project.id == ticket_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在 (ID: {ticket_in.project_id})")

    # 验证关联项目（如果提供了）
    all_project_ids = [ticket_in.project_id]
    if ticket_in.project_ids:
        all_project_ids.extend(ticket_in.project_ids)
        all_project_ids = list(set(all_project_ids))  # 去重

        for project_id in all_project_ids:
            if not db.query(Project).filter(Project.id == project_id).first():
                raise HTTPException(status_code=404, detail=f"关联项目不存在 (ID: {project_id})")

    # 验证客户是否存在
    customer = db.query(Customer).filter(Customer.id == ticket_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户不存在 (ID: {ticket_in.customer_id})")

    # 验证处理人（如果创建时指定）
    assignee = None
    if ticket_in.assignee_id:
        assignee = db.query(User).filter(User.id == ticket_in.assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="处理人不存在")

    # 验证抄送人员（如果提供了）
    if ticket_in.cc_user_ids:
        for user_id in ticket_in.cc_user_ids:
            if not db.query(User).filter(User.id == user_id).first():
                raise HTTPException(status_code=404, detail=f"抄送人员不存在 (ID: {user_id})")

    # 创建工单
    ticket = ServiceTicket(
        ticket_no=generate_ticket_no(db),
        project_id=ticket_in.project_id,  # 主项目
        customer_id=ticket_in.customer_id,
        problem_type=ticket_in.problem_type,
        problem_desc=ticket_in.problem_desc,
        urgency=ticket_in.urgency,
        reported_by=ticket_in.reported_by,
        reported_time=ticket_in.reported_time,
        status="PENDING" if not ticket_in.assignee_id else "IN_PROGRESS",  # 如果指定了处理人，直接变为处理中
        assigned_to_id=ticket_in.assignee_id,
        assigned_to_name=(assignee.name or assignee.username) if assignee else None,
        assigned_time=datetime.now() if ticket_in.assignee_id else None,
        response_time=datetime.now() if ticket_in.assignee_id else None,
        timeline=[{
            "type": "REPORTED",
            "timestamp": ticket_in.reported_time.isoformat(),
            "user": ticket_in.reported_by,
            "description": "客户报告问题",
        }],
    )

    # 如果创建时指定了处理人，添加分配记录
    if ticket_in.assignee_id and assignee:
        ticket.timeline.append({
            "type": "ASSIGNED",
            "timestamp": datetime.now().isoformat(),
            "user": current_user.real_name or current_user.username,
            "description": f"工单已分配给 {assignee.name or assignee.username}",
        })

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 创建项目关联
    for project_id in all_project_ids:
        is_primary = (project_id == ticket_in.project_id)
        ticket_project = ServiceTicketProject(
            ticket_id=ticket.id,
            project_id=project_id,
            is_primary=is_primary
        )
        db.add(ticket_project)

    # 创建抄送人员
    if ticket_in.cc_user_ids:
        for user_id in ticket_in.cc_user_ids:
            if user_id != ticket.assignee_id:  # 处理人不作为抄送人
                cc_user = ServiceTicketCcUser(
                    ticket_id=ticket.id,
                    user_id=user_id,
                    notified_at=datetime.now()
                )
                db.add(cc_user)

    db.commit()

    # 创建SLA监控记录
    try:
        from app.services.sla_service import create_sla_monitor, match_sla_policy
        policy = match_sla_policy(db, ticket.problem_type, ticket.urgency)
        if policy:
            create_sla_monitor(db, ticket, policy)
    except Exception as e:
        # SLA监控创建失败不影响工单创建
        import logging
        logging.error(f"创建SLA监控记录失败: {e}")

    # 获取项目名称和客户名称
    if ticket.project_id:
        project = db.query(Project).filter(Project.id == ticket.project_id).first()
        if project:
            ticket.project_name = project.project_name
    if ticket.customer_id:
        customer = db.query(Customer).filter(Customer.id == ticket.customer_id).first()
        if customer:
            ticket.customer_name = customer.customer_name

    return ticket


@router.get("/{ticket_id}", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
def read_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取服务工单详情
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")

    # 获取项目名称和客户名称
    if ticket.project_id:
        project = db.query(Project).filter(Project.id == ticket.project_id).first()
        if project:
            ticket.project_name = project.project_name
    if ticket.customer_id:
        customer = db.query(Customer).filter(Customer.id == ticket.customer_id).first()
        if customer:
            ticket.customer_name = customer.customer_name

    return ticket
