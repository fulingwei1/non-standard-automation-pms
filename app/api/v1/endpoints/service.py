# -*- coding: utf-8 -*-
"""
客服服务 API endpoints
包含：服务工单、现场服务记录、客户沟通、满意度调查、知识库
"""

from typing import Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project, Customer
from app.models.service import (
    ServiceTicket, ServiceRecord, CustomerCommunication,
    CustomerSatisfaction, KnowledgeBase, SatisfactionSurveyTemplate
)
from app.schemas.service import (
    ServiceTicketCreate, ServiceTicketUpdate, ServiceTicketAssign, ServiceTicketClose,
    ServiceTicketResponse,
    ServiceRecordCreate, ServiceRecordUpdate, ServiceRecordResponse,
    CustomerCommunicationCreate, CustomerCommunicationUpdate, CustomerCommunicationResponse,
    CustomerSatisfactionCreate, CustomerSatisfactionUpdate, CustomerSatisfactionResponse,
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
    ServiceDashboardStatistics,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


# ==================== 辅助函数 ====================

def generate_ticket_no(db: Session) -> str:
    """生成服务工单号：SRV-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.service import ServiceTicket
    
    return generate_sequential_no(
        db=db,
        model_class=ServiceTicket,
        no_field='ticket_no',
        prefix='SRV',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_record_no(db: Session) -> str:
    """生成服务记录号：REC-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no
    from app.models.service import ServiceRecord
    
    return generate_sequential_no(
        db=db,
        model_class=ServiceRecord,
        no_field='record_no',
        prefix='REC',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def generate_communication_no(db: Session) -> str:
    """生成沟通记录号：COM-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_comm = (
        db.query(CustomerCommunication)
        .filter(CustomerCommunication.communication_no.like(f"COM-{today}-%"))
        .order_by(desc(CustomerCommunication.communication_no))
        .first()
    )
    if max_comm:
        seq = int(max_comm.communication_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"COM-{today}-{seq:03d}"


def generate_survey_no(db: Session) -> str:
    """生成调查号：SUR-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_survey = (
        db.query(CustomerSatisfaction)
        .filter(CustomerSatisfaction.survey_no.like(f"SUR-{today}-%"))
        .order_by(desc(CustomerSatisfaction.survey_no))
        .first()
    )
    if max_survey:
        seq = int(max_survey.survey_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"SUR-{today}-{seq:03d}"


def generate_article_no(db: Session) -> str:
    """生成文章编号：KB-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_article = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.article_no.like(f"KB-{today}-%"))
        .order_by(desc(KnowledgeBase.article_no))
        .first()
    )
    if max_article:
        seq = int(max_article.article_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"KB-{today}-{seq:03d}"


# ==================== 客服统计（给生产总监看） ====================

@router.get("/dashboard-statistics", response_model=ServiceDashboardStatistics, status_code=status.HTTP_200_OK)
def get_service_dashboard_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客服部统计（给生产总监看）
    """
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    
    # 服务案例统计
    active_cases = db.query(ServiceTicket).filter(
        ServiceTicket.status.in_(["PENDING", "IN_PROGRESS"])
    ).count()
    
    resolved_today = db.query(ServiceTicket).filter(
        ServiceTicket.status == "RESOLVED",
        ServiceTicket.resolved_time >= today_start
    ).count()
    
    pending_cases = db.query(ServiceTicket).filter(
        ServiceTicket.status == "PENDING"
    ).count()
    
    # 平均响应时间（从服务工单中计算：响应时间 - 报告时间）
    tickets_with_response = db.query(ServiceTicket).filter(
        ServiceTicket.response_time.isnot(None),
        ServiceTicket.reported_time.isnot(None)
    ).all()
    
    avg_response_time = 0.0
    if tickets_with_response:
        total_hours = 0
        for ticket in tickets_with_response:
            if ticket.response_time and ticket.reported_time:
                delta = ticket.response_time - ticket.reported_time
                total_hours += delta.total_seconds() / 3600.0
        avg_response_time = total_hours / len(tickets_with_response) if tickets_with_response else 0.0
    
    # 客户满意度（转换为百分制）
    completed_surveys = db.query(CustomerSatisfaction).filter(
        CustomerSatisfaction.status == "COMPLETED",
        CustomerSatisfaction.overall_score.isnot(None)
    ).all()
    
    customer_satisfaction = 0.0
    if completed_surveys:
        total_score = sum(float(s.overall_score) for s in completed_surveys)
        customer_satisfaction = (total_score / len(completed_surveys)) * 20  # 5分制转百分制
    
    # 现场服务（从服务记录中统计，使用INSTALLATION类型作为现场服务）
    on_site_services = db.query(ServiceRecord).filter(
        ServiceRecord.service_type.in_(["INSTALLATION", "REPAIR", "MAINTENANCE"]),
        ServiceRecord.status.in_(["SCHEDULED", "IN_PROGRESS"])
    ).count()
    
    # 在岗工程师（简化处理：查询有客服工程师角色的用户）
    from app.models.organization import UserRole, Role
    engineer_role = db.query(Role).filter(
        or_(
            Role.role_code == "customer_service_engineer",
            Role.role_code == "客服工程师",
            Role.role_name.like("%客服%")
        )
    ).first()
    
    total_engineers = 0
    active_engineers = 0
    if engineer_role:
        total_engineers = db.query(User).join(UserRole).filter(
            UserRole.role_id == engineer_role.id,
            User.is_active == True
        ).count()
        # 简化处理：假设所有工程师都在岗
        active_engineers = total_engineers
    else:
        # 如果没有找到角色，尝试从服务记录中统计
        engineers = db.query(ServiceRecord.service_engineer_id).distinct().all()
        total_engineers = len(engineers)
        active_engineers = total_engineers
    
    return ServiceDashboardStatistics(
        active_cases=active_cases,
        resolved_today=resolved_today,
        pending_cases=pending_cases,
        avg_response_time=avg_response_time,
        customer_satisfaction=customer_satisfaction,
        on_site_services=on_site_services,
        total_engineers=total_engineers,
        active_engineers=active_engineers,
    )


# ==================== 服务工单 ====================

@router.get("/service-tickets/project-members", response_model=dict, status_code=status.HTTP_200_OK)
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
        except:
            pass
    
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


@router.get("/service-tickets/{ticket_id}/projects", response_model=dict, status_code=status.HTTP_200_OK)
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


@router.get("/service-tickets/statistics", response_model=dict, status_code=status.HTTP_200_OK)
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


@router.get("/service-tickets", response_model=PaginatedResponse[ServiceTicketResponse], status_code=status.HTTP_200_OK)
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


@router.post("/service-tickets", response_model=ServiceTicketResponse, status_code=status.HTTP_201_CREATED)
def create_service_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_in: ServiceTicketCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建服务工单（支持多项目关联和直接分配）
    """
    from app.models.service import ServiceTicketProject, ServiceTicketCcUser
    
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
            if user_id != ticket_in.assignee_id:  # 处理人不作为抄送人
                cc_user = ServiceTicketCcUser(
                    ticket_id=ticket.id,
                    user_id=user_id,
                    notified_at=datetime.now()
                )
                db.add(cc_user)
    
    db.commit()
    
    # 创建SLA监控记录
    try:
        from app.services.sla_service import match_sla_policy, create_sla_monitor
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


@router.get("/service-tickets/{ticket_id}", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
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


@router.put("/service-tickets/{ticket_id}/assign", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
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


@router.put("/service-tickets/{ticket_id}/status", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
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


@router.put("/service-tickets/{ticket_id}/close", response_model=ServiceTicketResponse, status_code=status.HTTP_200_OK)
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
        from app.services.knowledge_extraction_service import auto_extract_knowledge_from_ticket
        auto_extract_knowledge_from_ticket(db, ticket, auto_publish=True)
    except Exception as e:
        import logging
        logging.error(f"自动提取知识失败: {e}")
    
    return ticket


# ==================== 现场服务记录 ====================

@router.get("/service-records/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_service_record_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取服务记录统计
    """
    total = db.query(ServiceRecord).count()
    in_progress = db.query(ServiceRecord).filter(ServiceRecord.status == "IN_PROGRESS").count()
    completed = db.query(ServiceRecord).filter(ServiceRecord.status == "COMPLETED").count()
    cancelled = db.query(ServiceRecord).filter(ServiceRecord.status == "CANCELLED").count()
    
    # 本月服务数
    today = date.today()
    this_month_start = date(today.year, today.month, 1)
    this_month = db.query(ServiceRecord).filter(ServiceRecord.service_date >= this_month_start).count()
    
    # 总服务时长
    total_duration = db.query(func.sum(ServiceRecord.duration_hours)).scalar() or 0
    
    return {
        "total": total,
        "in_progress": in_progress,
        "completed": completed,
        "cancelled": cancelled,
        "this_month": this_month,
        "total_duration": float(total_duration),
    }


@router.get("/service-records", response_model=PaginatedResponse[ServiceRecordResponse], status_code=status.HTTP_200_OK)
def read_service_records(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    service_type: Optional[str] = Query(None, description="服务类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取服务记录列表
    """
    query = db.query(ServiceRecord)
    
    if service_type:
        query = query.filter(ServiceRecord.service_type == service_type)
    if status:
        query = query.filter(ServiceRecord.status == status)
    if project_id:
        query = query.filter(ServiceRecord.project_id == project_id)
    if customer_id:
        query = query.filter(ServiceRecord.customer_id == customer_id)
    if date_from:
        query = query.filter(ServiceRecord.service_date >= date_from)
    if date_to:
        query = query.filter(ServiceRecord.service_date <= date_to)
    if keyword:
        query = query.filter(
            or_(
                ServiceRecord.record_no.like(f"%{keyword}%"),
                ServiceRecord.service_content.like(f"%{keyword}%"),
                ServiceRecord.location.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    items = query.order_by(desc(ServiceRecord.service_date)).offset((page - 1) * page_size).limit(page_size).all()
    
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
        if item.service_engineer_id:
            engineer = db.query(User).filter(User.id == item.service_engineer_id).first()
            if engineer:
                item.service_engineer_name = engineer.name or engineer.username
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("/service-records", response_model=ServiceRecordResponse, status_code=status.HTTP_201_CREATED)
def create_service_record(
    *,
    db: Session = Depends(deps.get_db),
    record_in: ServiceRecordCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建服务记录
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == record_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在 (ID: {record_in.project_id})")
    
    # 验证客户是否存在
    customer = db.query(Customer).filter(Customer.id == record_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户不存在 (ID: {record_in.customer_id})")
    
    # 验证服务工程师是否存在
    engineer = db.query(User).filter(User.id == record_in.service_engineer_id).first()
    if not engineer:
        raise HTTPException(status_code=404, detail=f"服务工程师不存在 (ID: {record_in.service_engineer_id})")
    
    record = ServiceRecord(
        record_no=generate_record_no(db),
        service_type=record_in.service_type,
        project_id=record_in.project_id,
        machine_no=record_in.machine_no,
        customer_id=record_in.customer_id,
        location=record_in.location,
        service_date=record_in.service_date,
        start_time=record_in.start_time,
        end_time=record_in.end_time,
        duration_hours=record_in.duration_hours,
        service_engineer_id=record_in.service_engineer_id,
        service_engineer_name=engineer.name or engineer.username,
        customer_contact=record_in.customer_contact,
        customer_phone=record_in.customer_phone,
        service_content=record_in.service_content,
        service_result=record_in.service_result,
        issues_found=record_in.issues_found,
        solution_provided=record_in.solution_provided,
        photos=record_in.photos or [],
        customer_satisfaction=record_in.customer_satisfaction,
        customer_feedback=record_in.customer_feedback,
        customer_signed=record_in.customer_signed or False,
        status=record_in.status or "SCHEDULED",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    # 获取项目名称和客户名称
    if record.project_id:
        project = db.query(Project).filter(Project.id == record.project_id).first()
        if project:
            record.project_name = project.project_name
    if record.customer_id:
        customer = db.query(Customer).filter(Customer.id == record.customer_id).first()
        if customer:
            record.customer_name = customer.customer_name
    
    return record


@router.post("/service-records/{record_id}/photos", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def upload_service_record_photo(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    file: UploadFile = File(..., description="照片文件"),
    description: Optional[str] = Form(None, description="照片描述"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上传服务记录照片
    """
    # 验证服务记录是否存在
    record = db.query(ServiceRecord).filter(ServiceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="服务记录不存在")
    
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只支持图片文件")
    
    # 验证文件大小（最大5MB）
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
    
    # 创建上传目录
    upload_dir = Path(settings.UPLOAD_DIR) / "service_records" / str(record_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = upload_dir / unique_filename
    
    # 保存文件
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 生成文件URL（相对路径）
    relative_path = f"service_records/{record_id}/{unique_filename}"
    
    # 更新服务记录的照片列表
    photos = record.photos or []
    photos.append({
        "url": relative_path,
        "filename": file.filename,
        "size": len(file_content),
        "type": file.content_type,
        "description": description,
        "uploaded_at": datetime.now().isoformat(),
        "uploaded_by": current_user.real_name or current_user.username,
    })
    record.photos = photos
    
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return ResponseModel(
        code=201,
        message="照片上传成功",
        data={
            "record_id": record_id,
            "photo": photos[-1],
            "total_photos": len(photos),
        }
    )


@router.delete("/service-records/{record_id}/photos/{photo_index}", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def delete_service_record_photo(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    photo_index: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除服务记录照片
    """
    # 验证服务记录是否存在
    record = db.query(ServiceRecord).filter(ServiceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="服务记录不存在")
    
    photos = record.photos or []
    if photo_index < 0 or photo_index >= len(photos):
        raise HTTPException(status_code=400, detail="照片索引无效")
    
    # 删除文件
    photo = photos[photo_index]
    if "url" in photo:
        file_path = Path(settings.UPLOAD_DIR) / photo["url"]
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                import logging
                logging.warning(f"删除照片文件失败: {str(e)}")
    
    # 从列表中移除
    photos.pop(photo_index)
    record.photos = photos
    
    db.add(record)
    db.commit()
    
    return ResponseModel(
        code=200,
        message="照片删除成功",
        data={
            "record_id": record_id,
            "total_photos": len(photos),
        }
    )


# ==================== 客户沟通 ====================

@router.get("/customer-communications/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_customer_communication_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户沟通统计
    """
    total = db.query(CustomerCommunication).count()
    
    # 本周沟通数
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    this_week = db.query(CustomerCommunication).filter(CustomerCommunication.communication_date >= week_start).count()
    
    # 本月沟通数
    this_month_start = date(today.year, today.month, 1)
    this_month = db.query(CustomerCommunication).filter(CustomerCommunication.communication_date >= this_month_start).count()
    
    # 待跟进数
    pending_follow_up = db.query(CustomerCommunication).filter(
        CustomerCommunication.follow_up_required == True,
        CustomerCommunication.follow_up_status == "待处理"
    ).count()
    
    # 按类型统计
    by_type = {}
    types = db.query(CustomerCommunication.communication_type, func.count(CustomerCommunication.id)).group_by(CustomerCommunication.communication_type).all()
    for comm_type, count in types:
        by_type[comm_type] = count
    
    return {
        "total": total,
        "this_week": this_week,
        "this_month": this_month,
        "pending_follow_up": pending_follow_up,
        "by_type": by_type,
    }


@router.get("/customer-communications", response_model=PaginatedResponse[CustomerCommunicationResponse], status_code=status.HTTP_200_OK)
def read_customer_communications(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    communication_type: Optional[str] = Query(None, description="沟通方式筛选"),
    topic: Optional[str] = Query(None, description="沟通主题筛选"),
    importance: Optional[str] = Query(None, description="重要性筛选"),
    follow_up_required: Optional[bool] = Query(None, description="是否需要跟进"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户沟通记录列表
    """
    query = db.query(CustomerCommunication)
    
    if communication_type:
        query = query.filter(CustomerCommunication.communication_type == communication_type)
    if topic:
        query = query.filter(CustomerCommunication.topic == topic)
    if importance:
        query = query.filter(CustomerCommunication.importance == importance)
    if follow_up_required is not None:
        query = query.filter(CustomerCommunication.follow_up_required == follow_up_required)
    if date_from:
        query = query.filter(CustomerCommunication.communication_date >= date_from)
    if date_to:
        query = query.filter(CustomerCommunication.communication_date <= date_to)
    if keyword:
        query = query.filter(
            or_(
                CustomerCommunication.communication_no.like(f"%{keyword}%"),
                CustomerCommunication.customer_name.like(f"%{keyword}%"),
                CustomerCommunication.subject.like(f"%{keyword}%"),
                CustomerCommunication.content.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    items = query.order_by(desc(CustomerCommunication.communication_date)).offset((page - 1) * page_size).limit(page_size).all()
    
    # 获取创建人姓名
    for item in items:
        if item.created_by:
            creator = db.query(User).filter(User.id == item.created_by).first()
            if creator:
                item.created_by_name = creator.name or creator.username
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("/customer-communications", response_model=CustomerCommunicationResponse, status_code=status.HTTP_201_CREATED)
def create_customer_communication(
    *,
    db: Session = Depends(deps.get_db),
    comm_in: CustomerCommunicationCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建客户沟通记录
    """
    comm = CustomerCommunication(
        communication_no=generate_communication_no(db),
        communication_type=comm_in.communication_type,
        customer_name=comm_in.customer_name,
        customer_contact=comm_in.customer_contact,
        customer_phone=comm_in.customer_phone,
        customer_email=comm_in.customer_email,
        project_code=comm_in.project_code,
        project_name=comm_in.project_name,
        communication_date=comm_in.communication_date,
        communication_time=comm_in.communication_time,
        duration=comm_in.duration,
        location=comm_in.location,
        topic=comm_in.topic,
        subject=comm_in.subject,
        content=comm_in.content,
        follow_up_required=comm_in.follow_up_required or False,
        follow_up_task=comm_in.follow_up_task,
        follow_up_due_date=comm_in.follow_up_due_date,
        tags=comm_in.tags or [],
        importance=comm_in.importance or "中",
        created_by=current_user.id,
        created_by_name=current_user.real_name or current_user.username,
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)
    
    return comm


@router.get("/customer-communications/{comm_id}", response_model=CustomerCommunicationResponse, status_code=status.HTTP_200_OK)
def read_customer_communication(
    *,
    db: Session = Depends(deps.get_db),
    comm_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户沟通记录详情
    """
    comm = db.query(CustomerCommunication).filter(CustomerCommunication.id == comm_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="沟通记录不存在")
    
    return comm


@router.put("/customer-communications/{comm_id}", response_model=CustomerCommunicationResponse, status_code=status.HTTP_200_OK)
def update_customer_communication(
    *,
    db: Session = Depends(deps.get_db),
    comm_id: int,
    comm_in: CustomerCommunicationUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新客户沟通记录
    """
    comm = db.query(CustomerCommunication).filter(CustomerCommunication.id == comm_id).first()
    if not comm:
        raise HTTPException(status_code=404, detail="沟通记录不存在")
    
    if comm_in.content is not None:
        comm.content = comm_in.content
    if comm_in.follow_up_task is not None:
        comm.follow_up_task = comm_in.follow_up_task
    if comm_in.follow_up_status is not None:
        comm.follow_up_status = comm_in.follow_up_status
    if comm_in.tags is not None:
        comm.tags = comm_in.tags
    
    db.add(comm)
    db.commit()
    db.refresh(comm)
    
    return comm


# ==================== 满意度调查 ====================

@router.get("/customer-satisfactions/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_customer_satisfaction_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查统计
    """
    total = db.query(CustomerSatisfaction).count()
    sent = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.status.in_(["SENT", "PENDING", "COMPLETED"])).count()
    pending = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.status == "PENDING").count()
    completed = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.status == "COMPLETED").count()
    
    # 计算平均分
    completed_surveys = db.query(CustomerSatisfaction).filter(
        CustomerSatisfaction.status == "COMPLETED",
        CustomerSatisfaction.overall_score.isnot(None)
    ).all()
    average_score = 0.0
    if completed_surveys:
        total_score = sum(float(s.overall_score) for s in completed_surveys)
        average_score = round(total_score / len(completed_surveys), 1)
    
    # 计算回复率
    response_rate = 0.0
    if total > 0:
        response_rate = round((completed / total) * 100, 1)
    
    return {
        "total": total,
        "sent": sent,
        "pending": pending,
        "completed": completed,
        "average_score": average_score,
        "response_rate": response_rate,
    }

@router.get("/customer-satisfactions", response_model=PaginatedResponse[CustomerSatisfactionResponse], status_code=status.HTTP_200_OK)
def read_customer_satisfactions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    survey_type: Optional[str] = Query(None, description="调查类型筛选"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查列表
    """
    query = db.query(CustomerSatisfaction)
    
    if status:
        query = query.filter(CustomerSatisfaction.status == status)
    if survey_type:
        query = query.filter(CustomerSatisfaction.survey_type == survey_type)
    if date_from:
        query = query.filter(CustomerSatisfaction.survey_date >= date_from)
    if date_to:
        query = query.filter(CustomerSatisfaction.survey_date <= date_to)
    if keyword:
        query = query.filter(
            or_(
                CustomerSatisfaction.survey_no.like(f"%{keyword}%"),
                CustomerSatisfaction.customer_name.like(f"%{keyword}%"),
                CustomerSatisfaction.project_name.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    items = query.order_by(desc(CustomerSatisfaction.survey_date)).offset((page - 1) * page_size).limit(page_size).all()
    
    # 获取创建人姓名
    for item in items:
        if item.created_by:
            creator = db.query(User).filter(User.id == item.created_by).first()
            if creator:
                item.created_by_name = creator.name or creator.username
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("/customer-satisfactions", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_201_CREATED)
def create_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_in: CustomerSatisfactionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建满意度调查
    """
    survey = CustomerSatisfaction(
        survey_no=generate_survey_no(db),
        survey_type=survey_in.survey_type,
        customer_name=survey_in.customer_name,
        customer_contact=survey_in.customer_contact,
        customer_email=survey_in.customer_email,
        customer_phone=survey_in.customer_phone,
        project_code=survey_in.project_code,
        project_name=survey_in.project_name,
        survey_date=survey_in.survey_date,
        send_method=survey_in.send_method,
        deadline=survey_in.deadline,
        status="DRAFT",
        created_by=current_user.id,
        created_by_name=current_user.real_name or current_user.username,
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)
    
    return survey


@router.get("/customer-satisfactions/{survey_id}", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK)
def read_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查详情
    """
    survey = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="满意度调查不存在")
    
    return survey


@router.put("/customer-satisfactions/{survey_id}", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK)
def update_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    survey_in: CustomerSatisfactionUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新满意度调查
    """
    survey = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="满意度调查不存在")
    
    if survey_in.status is not None:
        survey.status = survey_in.status
        if survey_in.status == "SENT" and not survey.send_date:
            survey.send_date = date.today()
    if survey_in.response_date is not None:
        survey.response_date = survey_in.response_date
    if survey_in.overall_score is not None:
        survey.overall_score = survey_in.overall_score
    if survey_in.scores is not None:
        survey.scores = survey_in.scores
    if survey_in.feedback is not None:
        survey.feedback = survey_in.feedback
    if survey_in.suggestions is not None:
        survey.suggestions = survey_in.suggestions
    
    if survey_in.status == "COMPLETED" and survey.overall_score:
        survey.status = "COMPLETED"
    
    db.add(survey)
    db.commit()
    db.refresh(survey)
    
    return survey


@router.post("/customer-satisfactions/{survey_id}/send", response_model=CustomerSatisfactionResponse, status_code=status.HTTP_200_OK)
def send_customer_satisfaction(
    *,
    db: Session = Depends(deps.get_db),
    survey_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发送满意度调查
    """
    survey = db.query(CustomerSatisfaction).filter(CustomerSatisfaction.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="满意度调查不存在")
    
    if survey.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="调查已完成，无法发送")
    
    survey.status = "SENT"
    survey.send_date = date.today()
    
    db.add(survey)
    db.commit()
    db.refresh(survey)
    
    return survey


# ==================== 满意度调查模板 ====================

@router.get("/satisfaction-templates", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def list_satisfaction_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    survey_type: Optional[str] = Query(None, description="调查类型筛选"),
    is_active: Optional[bool] = Query(True, description="是否启用"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查模板列表
    """
    query = db.query(SatisfactionSurveyTemplate)
    
    if survey_type:
        query = query.filter(SatisfactionSurveyTemplate.survey_type == survey_type)
    if is_active is not None:
        query = query.filter(SatisfactionSurveyTemplate.is_active == is_active)
    if keyword:
        query = query.filter(
            or_(
                SatisfactionSurveyTemplate.template_name.like(f"%{keyword}%"),
                SatisfactionSurveyTemplate.template_code.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    items = query.order_by(desc(SatisfactionSurveyTemplate.usage_count), desc(SatisfactionSurveyTemplate.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/satisfaction-templates/{template_id}", response_model=dict, status_code=status.HTTP_200_OK)
def get_satisfaction_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取满意度调查模板详情
    """
    template = db.query(SatisfactionSurveyTemplate).filter(SatisfactionSurveyTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="调查模板不存在")
    
    return {
        "id": template.id,
        "template_name": template.template_name,
        "template_code": template.template_code,
        "survey_type": template.survey_type,
        "questions": template.questions or [],
        "default_send_method": template.default_send_method,
        "default_deadline_days": template.default_deadline_days,
    }


# ==================== 知识库 ====================

@router.get("/knowledge-base/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_knowledge_base_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库统计
    """
    total = db.query(KnowledgeBase).count()
    published = db.query(KnowledgeBase).filter(KnowledgeBase.status == "已发布").count()
    faq = db.query(KnowledgeBase).filter(KnowledgeBase.is_faq == True).count()
    featured = db.query(KnowledgeBase).filter(KnowledgeBase.is_featured == True).count()
    
    # 总浏览量
    total_views = db.query(func.sum(KnowledgeBase.view_count)).scalar() or 0
    
    return {
        "total": total,
        "published": published,
        "faq": faq,
        "featured": featured,
        "total_views": int(total_views),
    }

@router.get("/knowledge-base/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_knowledge_base_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库统计
    """
    total = db.query(KnowledgeBase).count()
    published = db.query(KnowledgeBase).filter(KnowledgeBase.status == "已发布").count()
    faq = db.query(KnowledgeBase).filter(KnowledgeBase.is_faq == True).count()
    featured = db.query(KnowledgeBase).filter(KnowledgeBase.is_featured == True).count()
    
    # 总浏览量
    total_views = db.query(func.sum(KnowledgeBase.view_count)).scalar() or 0
    
    return {
        "total": total,
        "published": published,
        "faq": faq,
        "featured": featured,
        "total_views": int(total_views),
    }


@router.get("/knowledge-base", response_model=PaginatedResponse[KnowledgeBaseResponse], status_code=status.HTTP_200_OK)
def read_knowledge_base(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_faq: Optional[bool] = Query(None, description="是否FAQ筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库文章列表
    """
    query = db.query(KnowledgeBase)
    
    if category:
        query = query.filter(KnowledgeBase.category == category)
    if is_faq is not None:
        query = query.filter(KnowledgeBase.is_faq == is_faq)
    if status:
        query = query.filter(KnowledgeBase.status == status)
    if keyword:
        query = query.filter(
            or_(
                KnowledgeBase.article_no.like(f"%{keyword}%"),
                KnowledgeBase.title.like(f"%{keyword}%"),
                KnowledgeBase.content.like(f"%{keyword}%"),
            )
        )
    
    # 精选优先，然后按浏览量排序
    total = query.count()
    items = query.order_by(
        desc(KnowledgeBase.is_featured),
        desc(KnowledgeBase.view_count)
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    # 获取作者姓名
    for item in items:
        if item.author_id:
            author = db.query(User).filter(User.id == item.author_id).first()
            if author:
                item.author_name = author.name or author.username
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("/knowledge-base", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_in: KnowledgeBaseCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建知识库文章
    """
    article = KnowledgeBase(
        article_no=generate_article_no(db),
        title=article_in.title,
        category=article_in.category,
        content=article_in.content,
        tags=article_in.tags or [],
        is_faq=article_in.is_faq or False,
        is_featured=article_in.is_featured or False,
        status=article_in.status or "DRAFT",
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    
    return article


@router.get("/knowledge-base/{article_id}", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def read_knowledge_base_article(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库文章详情（增加浏览量）
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 增加浏览量
    article.view_count = (article.view_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)
    
    return article


@router.put("/knowledge-base/{article_id}", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def update_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    article_in: KnowledgeBaseUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新知识库文章
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    if article_in.title is not None:
        article.title = article_in.title
    if article_in.category is not None:
        article.category = article_in.category
    if article_in.content is not None:
        article.content = article_in.content
    if article_in.tags is not None:
        article.tags = article_in.tags
    if article_in.is_faq is not None:
        article.is_faq = article_in.is_faq
    if article_in.is_featured is not None:
        article.is_featured = article_in.is_featured
    if article_in.status is not None:
        article.status = article_in.status
    
    db.add(article)
    db.commit()
    db.refresh(article)
    
    return article


@router.delete("/knowledge-base/{article_id}", status_code=status.HTTP_200_OK)
def delete_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除知识库文章
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    db.delete(article)
    db.commit()
    
    return {"message": "文章已删除"}


@router.post("/knowledge-base/{article_id}/like", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def like_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    点赞知识库文章
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    article.like_count = (article.like_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)
    
    return article


@router.post("/knowledge-base/{article_id}/helpful", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def mark_knowledge_base_helpful(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记知识库文章为有用
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    article.helpful_count = (article.helpful_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.post("/knowledge-base/{article_id}/adopt", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def adopt_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记采用知识库文章（表示该文档被实际应用到工作中）
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.adopt_count = (article.adopt_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


# 知识库上传目录
KNOWLEDGE_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "knowledge_base"
KNOWLEDGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型（文档和视频）
ALLOWED_EXTENSIONS = {
    # 文档
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.md', '.csv', '.rtf', '.odt', '.ods', '.odp',
    # 图片
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    # 视频
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v',
    # 压缩包
    '.zip', '.rar', '.7z', '.tar', '.gz',
}

# 最大文件大小：200MB
MAX_FILE_SIZE = 200 * 1024 * 1024

# 用户上传配额：5GB
USER_UPLOAD_QUOTA = 5 * 1024 * 1024 * 1024


def get_user_total_upload_size(db: Session, user_id: int) -> int:
    """获取用户已上传文件的总大小"""
    result = db.query(func.sum(KnowledgeBase.file_size)).filter(
        KnowledgeBase.author_id == user_id,
        KnowledgeBase.file_size.isnot(None)
    ).scalar()
    return result or 0


@router.get("/knowledge-base/quota", response_model=dict, status_code=status.HTTP_200_OK)
def get_upload_quota(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取当前用户的上传配额使用情况
    """
    used = get_user_total_upload_size(db, current_user.id)
    return {
        "quota": USER_UPLOAD_QUOTA,
        "used": used,
        "remaining": USER_UPLOAD_QUOTA - used,
        "quota_gb": USER_UPLOAD_QUOTA / (1024 * 1024 * 1024),
        "used_gb": used / (1024 * 1024 * 1024),
        "remaining_gb": (USER_UPLOAD_QUOTA - used) / (1024 * 1024 * 1024),
        "usage_percent": (used / USER_UPLOAD_QUOTA * 100) if USER_UPLOAD_QUOTA > 0 else 0,
    }


@router.post("/knowledge-base/upload", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def upload_knowledge_document(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(..., description="上传的文件（最大200MB）"),
    title: str = Form(..., description="文档标题"),
    category: str = Form(..., description="分类"),
    tags: Optional[str] = Form(None, description="标签（逗号分隔）"),
    content: Optional[str] = Form(None, description="文档描述"),
    allow_download: bool = Form(True, description="是否允许他人下载"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上传知识库文档（支持文档、图片、视频，最大200MB，用户配额5GB）
    """
    # 验证文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 读取文件内容并验证大小
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制。最大允许: 200MB，当前文件: {file_size / (1024*1024):.2f}MB"
        )

    # 检查用户上传配额
    current_used = get_user_total_upload_size(db, current_user.id)
    if current_used + file_size > USER_UPLOAD_QUOTA:
        remaining = USER_UPLOAD_QUOTA - current_used
        raise HTTPException(
            status_code=400,
            detail=f"上传配额不足。您的配额: 5GB，已使用: {current_used / (1024*1024*1024):.2f}GB，"
                   f"剩余: {remaining / (1024*1024*1024):.2f}GB，当前文件: {file_size / (1024*1024):.2f}MB"
        )

    # 创建上传目录（按日期分组）
    date_dir = datetime.now().strftime("%Y%m")
    upload_dir = KNOWLEDGE_UPLOAD_DIR / date_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = upload_dir / unique_filename

    # 保存文件
    with open(file_path, "wb") as f:
        f.write(file_content)

    # 相对路径用于存储
    relative_path = f"knowledge_base/{date_dir}/{unique_filename}"

    # 解析标签
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # 创建知识库记录
    article = KnowledgeBase(
        article_no=generate_article_no(db),
        title=title,
        category=category,
        content=content or "",
        tags=tag_list,
        is_faq=False,
        is_featured=False,
        status="已发布",
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
        file_path=relative_path,
        file_name=file.filename,
        file_size=file_size,
        file_type=file.content_type,
        allow_download=allow_download,
        download_count=0,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.get("/knowledge-base/{article_id}/download")
async def download_knowledge_document(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载知识库文档
    """
    from fastapi.responses import FileResponse

    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    if not article.file_path:
        raise HTTPException(status_code=404, detail="该文章没有附件")

    # 检查下载权限（作者始终可以下载自己的文件）
    is_author = article.author_id == current_user.id
    if not is_author and not article.allow_download:
        raise HTTPException(status_code=403, detail="该文档不允许下载")

    # 构建文件路径
    file_path = Path(settings.UPLOAD_DIR) / article.file_path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 安全检查：确保路径在允许的范围内
    try:
        file_path.resolve().relative_to(Path(settings.UPLOAD_DIR).resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝")

    # 增加下载计数（非作者下载时计数）
    if not is_author:
        article.download_count = (article.download_count or 0) + 1
        db.add(article)
        db.commit()

    return FileResponse(
        path=str(file_path),
        filename=article.file_name or file_path.name,
        media_type=article.file_type or "application/octet-stream",
    )


# ==================== 知识库特定功能 ====================

@router.get("/knowledge/issues", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_knowledge_issues(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="问题分类筛选"),
    severity: Optional[str] = Query(None, description="严重程度筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    问题库列表
    从问题管理模块中提取已解决的问题，形成问题库
    """
    from app.models.issue import Issue
    
    query = db.query(Issue).filter(
        Issue.status.in_(["RESOLVED", "CLOSED"]),
        Issue.solution.isnot(None)  # 必须有解决方案
    )
    
    if category:
        query = query.filter(Issue.category == category)
    if severity:
        query = query.filter(Issue.severity == severity)
    if keyword:
        query = query.filter(
            or_(
                Issue.title.like(f"%{keyword}%"),
                Issue.description.like(f"%{keyword}%"),
                Issue.solution.like(f"%{keyword}%")
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    issues = query.order_by(desc(Issue.resolved_at), desc(Issue.created_at)).offset(offset).limit(page_size).all()
    
    # 构建问题库列表
    issue_list = []
    for issue in issues:
        issue_list.append({
            "id": issue.id,
            "issue_no": issue.issue_no,
            "title": issue.title,
            "description": issue.description,
            "category": issue.category,
            "severity": issue.severity,
            "solution": issue.solution,
            "project_id": issue.project_id,
            "project_name": issue.project.project_name if issue.project else None,
            "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
            "resolved_by_name": issue.resolved_by_name,
            "tags": issue.tags
        })
    
    return PaginatedResponse(
        items=issue_list,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/knowledge/solutions", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_knowledge_solutions(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案库列表
    从知识库中提取标记为解决方案的文章，或从问题库中提取解决方案
    """
    # 从知识库中查找方案类文章
    query = db.query(KnowledgeBase).filter(
        KnowledgeBase.status == "PUBLISHED",
        or_(
            KnowledgeBase.category == "SOLUTION",
            KnowledgeBase.category == "TROUBLESHOOTING",
            KnowledgeBase.tags.contains(["解决方案"]) if KnowledgeBase.tags else False
        )
    )
    
    if category:
        query = query.filter(KnowledgeBase.category == category)
    if keyword:
        query = query.filter(
            or_(
                KnowledgeBase.title.like(f"%{keyword}%"),
                KnowledgeBase.content.like(f"%{keyword}%")
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    articles = query.order_by(desc(KnowledgeBase.view_count), desc(KnowledgeBase.created_at)).offset(offset).limit(page_size).all()
    
    # 构建方案库列表
    solution_list = []
    for article in articles:
        solution_list.append({
            "id": article.id,
            "article_no": article.article_no,
            "title": article.title,
            "content": article.content[:200] if article.content else "",  # 摘要
            "category": article.category,
            "tags": article.tags or [],
            "view_count": article.view_count or 0,
            "like_count": article.like_count or 0,
            "author_name": article.author_name,
            "created_at": article.created_at.isoformat() if article.created_at else None
        })
    
    return PaginatedResponse(
        items=solution_list,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/knowledge/search", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def search_knowledge(
    *,
    db: Session = Depends(deps.get_db),
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    search_type: Optional[str] = Query("all", description="搜索类型：all/issues/solutions/articles"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    搜索知识库
    综合搜索问题库、方案库和知识库文章
    """
    results = []
    
    if search_type in ["all", "articles"]:
        # 搜索知识库文章
        articles = db.query(KnowledgeBase).filter(
            KnowledgeBase.status == "PUBLISHED",
            or_(
                KnowledgeBase.title.like(f"%{keyword}%"),
                KnowledgeBase.content.like(f"%{keyword}%")
            )
        ).limit(20).all()
        
        for article in articles:
            results.append({
                "type": "article",
                "id": article.id,
                "title": article.title,
                "content": article.content[:200] if article.content else "",
                "category": article.category,
                "url": f"/knowledge-base/{article.id}"
            })
    
    if search_type in ["all", "issues"]:
        # 搜索问题库
        from app.models.issue import Issue
        issues = db.query(Issue).filter(
            Issue.status.in_(["RESOLVED", "CLOSED"]),
            Issue.solution.isnot(None),
            or_(
                Issue.title.like(f"%{keyword}%"),
                Issue.description.like(f"%{keyword}%"),
                Issue.solution.like(f"%{keyword}%")
            )
        ).limit(20).all()
        
        for issue in issues:
            results.append({
                "type": "issue",
                "id": issue.id,
                "title": issue.title,
                "content": issue.solution[:200] if issue.solution else "",
                "category": issue.category,
                "url": f"/issues/{issue.id}"
            })
    
    if search_type in ["all", "solutions"]:
        # 搜索方案库（从知识库中）
        solutions = db.query(KnowledgeBase).filter(
            KnowledgeBase.status == "PUBLISHED",
            KnowledgeBase.category.in_(["SOLUTION", "TROUBLESHOOTING"]),
            or_(
                KnowledgeBase.title.like(f"%{keyword}%"),
                KnowledgeBase.content.like(f"%{keyword}%")
            )
        ).limit(20).all()
        
        for solution in solutions:
            results.append({
                "type": "solution",
                "id": solution.id,
                "title": solution.title,
                "content": solution.content[:200] if solution.content else "",
                "category": solution.category,
                "url": f"/knowledge-base/{solution.id}"
            })
    
    # 分页
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_results = results[start:end]
    
    return PaginatedResponse(
        items=paginated_results,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/knowledge", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_knowledge_entry(
    *,
    db: Session = Depends(deps.get_db),
    title: str = Body(..., description="知识条目标题"),
    content: str = Body(..., description="知识条目内容"),
    category: str = Body(..., description="分类"),
    tags: Optional[List[str]] = Body(None, description="标签列表"),
    entry_type: str = Body("article", description="条目类型：article/issue/solution"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加知识条目
    快速添加知识库文章
    """
    article = KnowledgeBase(
        article_no=generate_article_no(db),
        title=title,
        category=category,
        content=content,
        tags=tags or [],
        is_faq=False,
        is_featured=False,
        status="PUBLISHED",  # 直接发布
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
    )
    
    db.add(article)
    db.commit()
    db.refresh(article)
    
    return ResponseModel(
        code=200,
        message="知识条目添加成功",
        data={
            "id": article.id,
            "article_no": article.article_no,
            "title": article.title,
            "category": article.category,
            "entry_type": entry_type,
            "created_at": article.created_at.isoformat() if article.created_at else None
        }
    )

