# -*- coding: utf-8 -*-
"""
安装调试派工单 CRUD 端点
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.project import Customer, Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.installation_dispatch import (
    InstallationDispatchOrderCreate,
    InstallationDispatchOrderResponse,
    InstallationDispatchOrderUpdate,
)

from .utils import generate_order_no

router = APIRouter()


def _enrich_order_with_relations(order: InstallationDispatchOrder, db: Session) -> InstallationDispatchOrder:
    """为派工单填充关联信息"""
    if order.project_id:
        project = db.query(Project).filter(Project.id == order.project_id).first()
        if project:
            order.project_name = project.project_name
            order.project_code = project.project_code
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
        if machine:
            order.machine_no = machine.machine_no
    if order.customer_id:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
        if customer:
            order.customer_name = customer.customer_name
    return order


@router.get("/orders", response_model=PaginatedResponse[InstallationDispatchOrderResponse], status_code=status.HTTP_200_OK)
def read_installation_dispatch_orders(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    order_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    assigned_to_id: Optional[int] = Query(None, description="派工人员ID筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（派工单号/任务标题）"),
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    获取安装调试派工单列表
    """
    query = db.query(InstallationDispatchOrder)

    if order_status:
        query = query.filter(InstallationDispatchOrder.status == order_status)
    if priority:
        query = query.filter(InstallationDispatchOrder.priority == priority)
    if project_id:
        query = query.filter(InstallationDispatchOrder.project_id == project_id)
    if machine_id:
        query = query.filter(InstallationDispatchOrder.machine_id == machine_id)
    if customer_id:
        query = query.filter(InstallationDispatchOrder.customer_id == customer_id)
    if assigned_to_id:
        query = query.filter(InstallationDispatchOrder.assigned_to_id == assigned_to_id)
    if task_type:
        query = query.filter(InstallationDispatchOrder.task_type == task_type)

    # 应用关键词过滤（派工单号/任务标题）
    query = apply_keyword_filter(query, InstallationDispatchOrder, keyword, ["order_no", "task_title"])

    total = query.count()
    items = apply_pagination(query.order_by(desc(InstallationDispatchOrder.created_at)), pagination.offset, pagination.limit).all()

    # 获取关联信息
    for item in items:
        _enrich_order_with_relations(item, db)

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total),
    }


@router.post("/orders", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_201_CREATED)
def create_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: InstallationDispatchOrderCreate,
    current_user: User = Depends(security.require_permission("installation_dispatch:create")),
) -> Any:
    """
    创建安装调试派工单
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == order_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证客户是否存在
    customer = db.query(Customer).filter(Customer.id == order_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="客户不存在")

    # 验证机台是否存在（如果提供）
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")
        if machine.project_id != order_in.project_id:
            raise HTTPException(status_code=400, detail="机台不属于该项目")

    order = InstallationDispatchOrder(
        order_no=generate_order_no(db),
        project_id=order_in.project_id,
        machine_id=order_in.machine_id,
        customer_id=order_in.customer_id,
        task_type=order_in.task_type,
        task_title=order_in.task_title,
        task_description=order_in.task_description,
        location=order_in.location,
        scheduled_date=order_in.scheduled_date,
        estimated_hours=order_in.estimated_hours,
        priority=order_in.priority,
        customer_contact=order_in.customer_contact,
        customer_phone=order_in.customer_phone,
        customer_address=order_in.customer_address,
        status="PENDING",
        progress=0,
        remark=order_in.remark,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)


@router.get("/orders/{order_id}", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def read_installation_dispatch_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    获取安装调试派工单详情
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    return _enrich_order_with_relations(order, db)


@router.put("/orders/{order_id}", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def update_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    order_in: InstallationDispatchOrderUpdate,
    current_user: User = Depends(security.require_permission("installation_dispatch:update")),
) -> Any:
    """
    更新安装调试派工单
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    if order.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="已完成或已取消的派工单不能修改")

    # 更新字段
    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)
