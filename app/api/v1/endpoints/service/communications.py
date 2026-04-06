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
from app.utils.db_helpers import save_obj

from .access import filter_owned_service_query, get_owned_service_object_or_404
from .number_utils import generate_communication_no

router = APIRouter()


def _normalize_communication_defaults(item: CustomerCommunication) -> CustomerCommunication:
    """兼容历史空值，避免响应模型校验失败。"""
    if item.follow_up_required is None:
        item.follow_up_required = False
    if not item.importance:
        item.importance = "中"
    return item


def _serialize_communication(item: CustomerCommunication) -> dict[str, Any]:
    _normalize_communication_defaults(item)
    return {
        "id": item.id,
        "communication_no": item.communication_no,
        "communication_type": item.communication_type,
        "customer_name": item.customer_name,
        "customer_contact": item.customer_contact,
        "customer_phone": item.customer_phone,
        "customer_email": item.customer_email,
        "project_code": item.project_code,
        "project_name": item.project_name,
        "communication_date": item.communication_date,
        "communication_time": item.communication_time,
        "duration": item.duration,
        "location": item.location,
        "topic": item.topic,
        "subject": item.subject,
        "content": item.content,
        "follow_up_required": item.follow_up_required,
        "follow_up_task": item.follow_up_task,
        "follow_up_due_date": item.follow_up_due_date,
        "follow_up_status": item.follow_up_status,
        "tags": item.tags,
        "importance": item.importance,
        "created_by": item.created_by,
        "created_by_name": item.created_by_name,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_customer_communication_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取客户沟通统计
    """
    query = filter_owned_service_query(
        db, db.query(CustomerCommunication), CustomerCommunication, current_user, owner_field="created_by"
    )

    total = query.count()

    # 本周沟通数
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    this_week = (
        query
        .filter(CustomerCommunication.communication_date >= week_start)
        .count()
    )

    # 本月沟通数
    this_month_start = date(today.year, today.month, 1)
    this_month = (
        query
        .filter(CustomerCommunication.communication_date >= this_month_start)
        .count()
    )

    # 待跟进数
    pending_follow_up = (
        query
        .filter(
            CustomerCommunication.follow_up_required,
            CustomerCommunication.follow_up_status == "待处理",
        )
        .count()
    )

    # 按类型统计
    by_type = {}
    from sqlalchemy import func

    types = (
        query.with_entities(CustomerCommunication.communication_type, func.count(CustomerCommunication.id))
        .group_by(CustomerCommunication.communication_type)
        .all()
    )
    for comm_type, count in types:
        by_type[comm_type] = count

    return {
        "total": total,
        "this_week": this_week,
        "this_month": this_month,
        "pending_follow_up": pending_follow_up,
        "by_type": by_type,
    }


@router.get(
    "",
    response_model=PaginatedResponse[CustomerCommunicationResponse],
    status_code=status.HTTP_200_OK,
)
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
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取客户沟通记录列表
    """
    query = db.query(CustomerCommunication)
    query = filter_owned_service_query(
        db, query, CustomerCommunication, current_user, owner_field="created_by"
    )

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
    query = apply_keyword_filter(
        query,
        CustomerCommunication,
        keyword,
        ["communication_no", "customer_name", "subject", "content"],
    )

    total = query.count()
    items = apply_pagination(
        query.order_by(desc(CustomerCommunication.communication_date)),
        pagination.offset,
        pagination.limit,
    ).all()

    # 获取创建人姓名
    serialized_items = []
    for item in items:
        _normalize_communication_defaults(item)
        if item.created_by:
            creator = db.query(User).filter(User.id == item.created_by).first()
            if creator:
                item.created_by_name = creator.real_name or creator.username
        serialized_items.append(_serialize_communication(item))

    return {
        "items": serialized_items,
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
    current_user: User = Depends(security.require_permission("service:create")),
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
    saved = save_obj(db, comm)
    return _serialize_communication(saved)


@router.get(
    "/{comm_id}", response_model=CustomerCommunicationResponse, status_code=status.HTTP_200_OK
)
def read_customer_communication(
    *,
    db: Session = Depends(deps.get_db),
    comm_id: int,
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取客户沟通记录详情
    """
    comm = get_owned_service_object_or_404(
        db,
        CustomerCommunication,
        comm_id,
        current_user,
        "沟通记录不存在",
        owner_field="created_by",
    )

    if comm.created_by and not comm.created_by_name:
        creator = db.query(User).filter(User.id == comm.created_by).first()
        if creator:
            comm.created_by_name = creator.real_name or creator.username

    return _serialize_communication(comm)


@router.put(
    "/{comm_id}", response_model=CustomerCommunicationResponse, status_code=status.HTTP_200_OK
)
def update_customer_communication(
    *,
    db: Session = Depends(deps.get_db),
    comm_id: int,
    comm_in: CustomerCommunicationUpdate,
    current_user: User = Depends(security.require_permission("service:update")),
) -> Any:
    """
    更新客户沟通记录
    """
    comm = get_owned_service_object_or_404(
        db,
        CustomerCommunication,
        comm_id,
        current_user,
        "沟通记录不存在",
        owner_field="created_by",
    )

    if comm_in.content is not None:
        comm.content = comm_in.content
    if comm_in.follow_up_task is not None:
        comm.follow_up_task = comm_in.follow_up_task
    if comm_in.follow_up_status is not None:
        comm.follow_up_status = comm_in.follow_up_status
    if comm_in.tags is not None:
        comm.tags = comm_in.tags

    saved = save_obj(db, comm)
    _normalize_communication_defaults(saved)
    return _serialize_communication(saved)
