# -*- coding: utf-8 -*-
"""
服务工单管理 API endpoints
"""

from datetime import date, datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Customer, Project
from app.models.service import ServiceTicket
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.service import (
    ServiceTicketAssign,
    ServiceTicketClose,
    ServiceTicketCreate,
    ServiceTicketResponse,
    ServiceTicketUpdate,
)

from .number_utils import generate_ticket_no

router = APIRouter()


@router.get("/project-members", response_model=dict, status_code=status.HTTP_200_OK)
def get_project_members_for_ticket(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: str = Query(..., description="项目ID列表，逗号分隔（如：1,2,3）"),
    include_roles: Optional[str] = Query(None, description="包含的角色，逗号分隔（可选）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目相关人员（用于工单分配）
    根据项目ID列表获取所有相关人员，自动去重
    """
    from app.services.ticket_assignment_service import get_project_members_for_ticket

    # 解析项目ID列表
    try:
        project_id_list = [int(pid.strip()) for pid in project_ids.split(",") if pid.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="项目ID格式错误，应为逗号分隔的数字")

    if not project_id_list:
        raise HTTPException(status_code=400, detail="至少需要一个项目ID")

    # 解析角色列表（可选）
    role_list = None
    if include_roles:
        try:
            role_list = [role.strip() for role in include_roles.split(",") if role.strip()]
        except (ValueError, AttributeError) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"解析角色列表失败: {e}, include_roles: {include_roles}")
            role_list = None

    # 获取项目成员
    members = get_project_members_for_ticket(
        db=db,
        project_ids=project_id_list,
        include_roles=role_list,
        exclude_user_id=current_user.id  # 排除当前用户
    )

    return {
        "members": members,
        "total": len(members)
    }


@router.get("/{ticket_id}/projects", response_model=dict, status_code=status.HTTP_200_OK)
def get_ticket_related_projects(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单关联的所有项目
    """
    from app.services.ticket_assignment_service import get_ticket_related_projects

    projects_data = get_ticket_related_projects(db, ticket_id)

    return projects_data


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_service_ticket_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取服务工单统计
    """
    total = db.query(ServiceTicket).count()
    pending = db.query(ServiceTicket).filter(ServiceTicket.status == "PENDING").count()
    in_progress = db.query(ServiceTicket).filter(ServiceTicket.status == "IN_PROGRESS").count()
    resolved = db.query(ServiceTicket).filter(ServiceTicket.status == "RESOLVED").count()
    closed = db.query(ServiceTicket).filter(ServiceTicket.status == "CLOSED").count()
    urgent = db.query(ServiceTicket).filter(ServiceTicket.urgency == "URGENT").count()

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "urgent": urgent,
    }


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


@router.put("/{ticket_id}/assign", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
def assign_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    assign_in: ServiceTicketAssign,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分配服务工单（支持抄送人员）
    """
    from app.models.service import ServiceTicketCcUser

    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")

    assignee = db.query(User).filter(User.id == assign_in.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")

    # 验证抄送人员（如果提供了）
    if assign_in.cc_user_ids:
        for user_id in assign_in.cc_user_ids:
            if not db.query(User).filter(User.id == user_id).first():
                raise HTTPException(status_code=404, detail=f"抄送人员不存在 (ID: {user_id})")

    ticket.assigned_to_id = assign_in.assignee_id
    ticket.assigned_to_name = assignee.name or assignee.username
    ticket.assigned_time = datetime.now()
    ticket.status = "IN_PROGRESS"

    # 记录响应时间（首次分配时）
    if not ticket.response_time:
        ticket.response_time = datetime.now()

    # 更新时间线
    if not ticket.timeline:
        ticket.timeline = []
    ticket.timeline.append({
        "type": "ASSIGNED",
        "timestamp": datetime.now().isoformat(),
        "user": current_user.real_name or current_user.username,
        "description": f"工单已分配给 {assignee.name or assignee.username}",
    })

    # 更新抄送人员
    if assign_in.cc_user_ids is not None:
        # 删除旧的抄送人员
        db.query(ServiceTicketCcUser).filter(
            ServiceTicketCcUser.ticket_id == ticket_id
        ).delete()

        # 添加新的抄送人员（排除处理人）
        for user_id in assign_in.cc_user_ids:
            if user_id != assign_in.assignee_id:
                cc_user = ServiceTicketCcUser(
                    ticket_id=ticket_id,
                    user_id=user_id,
                    notified_at=datetime.now()
                )
                db.add(cc_user)

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 同步SLA监控状态
    try:
        from app.services.sla_service import sync_ticket_to_sla_monitor
        sync_ticket_to_sla_monitor(db, ticket)
    except Exception as e:
        import logging
        logging.error(f"同步SLA监控状态失败: {e}")

    return ticket


@router.put("/{ticket_id}/status", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
def update_service_ticket_status(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    status: str = Query(..., description="新状态：PENDING/IN_PROGRESS/RESOLVED/CLOSED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新工单状态
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")

    if status not in ["PENDING", "IN_PROGRESS", "RESOLVED", "CLOSED"]:
        raise HTTPException(status_code=400, detail="无效的状态值")

    old_status = ticket.status
    ticket.status = status

    # 如果状态变为已解决或已关闭，记录解决时间
    if status in ["RESOLVED", "CLOSED"] and not ticket.resolved_time:
        ticket.resolved_time = datetime.now()

    # 如果状态变为处理中，记录响应时间（如果还没有）
    if status == "IN_PROGRESS" and not ticket.response_time:
        ticket.response_time = datetime.now()

    # 更新时间线
    if not ticket.timeline:
        ticket.timeline = []
    ticket.timeline.append({
        "type": "STATUS_CHANGE",
        "timestamp": datetime.now().isoformat(),
        "user": current_user.real_name or current_user.username,
        "description": f"状态变更：{old_status} → {status}",
    })

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 同步SLA监控状态
    try:
        from app.services.sla_service import sync_ticket_to_sla_monitor
        sync_ticket_to_sla_monitor(db, ticket)
    except Exception as e:
        import logging
        logging.error(f"同步SLA监控状态失败: {e}")

    return ticket


@router.put("/{ticket_id}/close", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
def close_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    close_in: ServiceTicketClose,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关闭服务工单
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")

    if ticket.status == "CLOSED":
        raise HTTPException(status_code=400, detail="工单已关闭")

    ticket.solution = close_in.solution
    ticket.root_cause = close_in.root_cause
    ticket.preventive_action = close_in.preventive_action
    ticket.satisfaction = close_in.satisfaction
    ticket.feedback = close_in.feedback
    ticket.resolved_time = datetime.now()
    ticket.status = "CLOSED"

    # 更新时间线
    if not ticket.timeline:
        ticket.timeline = []
    ticket.timeline.append({
        "type": "CLOSED",
        "timestamp": datetime.now().isoformat(),
        "user": current_user.real_name or current_user.username,
        "description": "工单已关闭",
    })

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 同步SLA监控状态
    try:
        from app.services.sla_service import sync_ticket_to_sla_monitor
        sync_ticket_to_sla_monitor(db, ticket)
    except Exception as e:
        import logging
        logging.error(f"同步SLA监控状态失败: {e}")

    # 自动提取知识
    try:
        from app.services.knowledge_extraction_service import (
            auto_extract_knowledge_from_ticket,
        )
        auto_extract_knowledge_from_ticket(db, ticket, auto_publish=True)
    except Exception as e:
        import logging
        logging.error(f"自动提取知识失败: {e}")

    return ticket
