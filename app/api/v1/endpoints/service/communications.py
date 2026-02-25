# -*- coding: utf-8 -*-
"""
客户沟通管理 API endpoints
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.service import CustomerCommunication
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.service import (
    CustomerCommunicationCreate,
    CustomerCommunicationResponse,
    CustomerCommunicationUpdate,
)
from app.utils.db_helpers import get_or_404, save_obj

from .number_utils import generate_communication_no

router = APIRouter()


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
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
        CustomerCommunication.follow_up_required,
        CustomerCommunication.follow_up_status == "待处理"
    ).count()

    # 按类型统计
    by_type = {}
    from sqlalchemy import func
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


@router.get("", response_model=PaginatedResponse[CustomerCommunicationResponse], status_code=status.HTTP_200_OK)
def read_customer_communications(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
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

    # 应用关键词过滤（沟通编号/客户名称/主题/内容）
    query = apply_keyword_filter(query, CustomerCommunication, keyword, ["communication_no", "customer_name", "subject", "content"])

    total = query.count()
    items = apply_pagination(query.order_by(desc(CustomerCommunication.communication_date)), pagination.offset, pagination.limit).all()

    # 获取创建人姓名
    for item in items:
        if item.created_by:
            creator = db.query(User).filter(User.id == item.created_by).first()
            if creator:
                item.created_by_name = creator.name or creator.username

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total),
    }


@router.post("", response_model=CustomerCommunicationResponse, status_code=status.HTTP_201_CREATED)
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
    return save_obj(db, comm)


@router.get("/{comm_id}", response_model=CustomerCommunicationResponse, status_code=status.HTTP_200_OK)
def read_customer_communication(
    *,
    db: Session = Depends(deps.get_db),
    comm_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取客户沟通记录详情
    """
    comm = get_or_404(db, CustomerCommunication, comm_id, "沟通记录不存在")

    return comm


@router.put("/{comm_id}", response_model=CustomerCommunicationResponse, status_code=status.HTTP_200_OK)
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
    comm = get_or_404(db, CustomerCommunication, comm_id, "沟通记录不存在")

    if comm_in.content is not None:
        comm.content = comm_in.content
    if comm_in.follow_up_task is not None:
        comm.follow_up_task = comm_in.follow_up_task
    if comm_in.follow_up_status is not None:
        comm.follow_up_status = comm_in.follow_up_status
    if comm_in.tags is not None:
        comm.tags = comm_in.tags

    return save_obj(db, comm)
