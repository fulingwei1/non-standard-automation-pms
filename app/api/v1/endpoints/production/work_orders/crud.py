# -*- coding: utf-8 -*-
"""
工单管理 - CRUD操作
"""
from typing import Any, Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.production import ProductionPlan, WorkOrder, Workshop, Workstation
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.production import WorkOrderCreate, WorkOrderResponse

from fastapi import APIRouter

from ..utils import generate_work_order_no
from .utils import get_work_order_response
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


@router.get("/work-orders", response_model=PaginatedResponse)
def read_work_orders(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    assigned_to: Optional[int] = Query(None, description="指派给筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单列表（分页+筛选）
    """
    query = db.query(WorkOrder)

    if project_id:
        query = query.filter(WorkOrder.project_id == project_id)

    if workshop_id:
        query = query.filter(WorkOrder.workshop_id == workshop_id)

    if status:
        query = query.filter(WorkOrder.status == status)

    if priority:
        query = query.filter(WorkOrder.priority == priority)

    if assigned_to:
        query = query.filter(WorkOrder.assigned_to == assigned_to)

    total = query.count()
    orders = apply_pagination(query.order_by(desc(WorkOrder.created_at)), pagination.offset, pagination.limit).all()

    items = [get_work_order_response(db, order) for order in orders]

    return pagination.to_response(items, total)


@router.post("/work-orders", response_model=WorkOrderResponse)
def create_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: WorkOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工单
    """
    # 检查项目是否存在
    if order_in.project_id:
        project = get_or_404(db, Project, order_in.project_id, "项目不存在")

    # 检查机台是否存在
    if order_in.machine_id:
        machine = get_or_404(db, Machine, order_in.machine_id, "机台不存在")

    # 检查生产计划是否存在
    if order_in.production_plan_id:
        plan = get_or_404(db, ProductionPlan, order_in.production_plan_id, "生产计划不存在")

    # 检查车间是否存在
    if order_in.workshop_id:
        workshop = get_or_404(db, Workshop, order_in.workshop_id, "车间不存在")

    # 检查工位是否存在
    if order_in.workstation_id:
        workstation = get_or_404(db, Workstation, order_in.workstation_id, "工位不存在")
        if workstation.workshop_id != order_in.workshop_id:
            raise HTTPException(status_code=400, detail="工位不属于该车间")

    # 生成工单编号
    work_order_no = generate_work_order_no(db)

    order = WorkOrder(
        work_order_no=work_order_no,
        status="PENDING",
        progress=0,
        completed_qty=0,
        qualified_qty=0,
        defect_qty=0,
        actual_hours=0,
        created_by=current_user.id,
        **order_in.model_dump()
    )
    save_obj(db, order)

    return get_work_order_response(db, order)


@router.get("/work-orders/{order_id}", response_model=WorkOrderResponse)
def read_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单详情
    """
    order = get_or_404(db, WorkOrder, order_id, detail="工单不存在")

    return get_work_order_response(db, order)
