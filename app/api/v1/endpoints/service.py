# -*- coding: utf-8 -*-
"""
客服服务 API endpoints
包含：服务工单、现场服务记录、客户沟通、满意度调查、知识库
"""

from typing import Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project, Customer
from app.models.service import (
    ServiceTicket, ServiceRecord, CustomerCommunication,
    CustomerSatisfaction, KnowledgeBase
)
from app.schemas.service import (
    ServiceTicketCreate, ServiceTicketUpdate, ServiceTicketAssign, ServiceTicketClose,
    ServiceTicketResponse,
    ServiceRecordCreate, ServiceRecordUpdate, ServiceRecordResponse,
    CustomerCommunicationCreate, CustomerCommunicationUpdate, CustomerCommunicationResponse,
    CustomerSatisfactionCreate, CustomerSatisfactionUpdate, CustomerSatisfactionResponse,
    KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


# ==================== 辅助函数 ====================

def generate_ticket_no(db: Session) -> str:
    """生成服务工单号：SRV-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_ticket = (
        db.query(ServiceTicket)
        .filter(ServiceTicket.ticket_no.like(f"SRV-{today}-%"))
        .order_by(desc(ServiceTicket.ticket_no))
        .first()
    )
    if max_ticket:
        seq = int(max_ticket.ticket_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"SRV-{today}-{seq:03d}"


def generate_record_no(db: Session) -> str:
    """生成服务记录号：REC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_record = (
        db.query(ServiceRecord)
        .filter(ServiceRecord.record_no.like(f"REC-{today}-%"))
        .order_by(desc(ServiceRecord.record_no))
        .first()
    )
    if max_record:
        seq = int(max_record.record_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"REC-{today}-{seq:03d}"


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


# ==================== 服务工单 ====================

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
    创建服务工单
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == ticket_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在 (ID: {ticket_in.project_id})")
    
    # 验证客户是否存在
    customer = db.query(Customer).filter(Customer.id == ticket_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户不存在 (ID: {ticket_in.customer_id})")
    
    ticket = ServiceTicket(
        ticket_no=generate_ticket_no(db),
        project_id=ticket_in.project_id,
        customer_id=ticket_in.customer_id,
        problem_type=ticket_in.problem_type,
        problem_desc=ticket_in.problem_desc,
        urgency=ticket_in.urgency,
        reported_by=ticket_in.reported_by,
        reported_time=ticket_in.reported_time,
        status="PENDING",
        timeline=[{
            "type": "REPORTED",
            "timestamp": ticket_in.reported_time.isoformat(),
            "user": ticket_in.reported_by,
            "description": "客户报告问题",
        }],
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
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
    分配服务工单
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="服务工单不存在")
    
    assignee = db.query(User).filter(User.id == assign_in.assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")
    
    ticket.assigned_to_id = assign_in.assignee_id
    ticket.assigned_to_name = assignee.name or assignee.username
    ticket.assigned_time = datetime.now()
    ticket.status = "IN_PROGRESS"
    
    # 更新时间线
    if not ticket.timeline:
        ticket.timeline = []
    ticket.timeline.append({
        "type": "ASSIGNED",
        "timestamp": datetime.now().isoformat(),
        "user": current_user.real_name or current_user.username,
        "description": f"工单已分配给 {assignee.name or assignee.username}",
    })
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
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

