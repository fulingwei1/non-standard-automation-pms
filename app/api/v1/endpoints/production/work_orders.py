# -*- coding: utf-8 -*-
"""
生产管理模块 - 工单管理端点

包含：工单CRUD、派工、状态变更、进度查询
"""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.production import (
    ProcessDict,
    ProductionPlan,
    Worker,
    WorkOrder,
    Workshop,
    Workstation,
)
from app.models.project import Machine, Project
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.production import (
    WorkOrderAssignRequest,
    WorkOrderCreate,
    WorkOrderProgressResponse,
    WorkOrderResponse,
)

from .utils import generate_work_order_no

router = APIRouter()


def _get_work_order_response(db: Session, order: WorkOrder) -> WorkOrderResponse:
    """构建工单响应对象的辅助函数"""
    project_name = None
    if order.project_id:
        project = db.query(Project).filter(Project.id == order.project_id).first()
        project_name = project.project_name if project else None

    machine_name = None
    if order.machine_id:
        machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
        machine_name = machine.machine_name if machine else None

    workshop_name = None
    if order.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == order.workshop_id).first()
        workshop_name = workshop.workshop_name if workshop else None

    workstation_name = None
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        workstation_name = workstation.workstation_name if workstation else None

    process_name = None
    if order.process_id:
        process = db.query(ProcessDict).filter(ProcessDict.id == order.process_id).first()
        process_name = process.process_name if process else None

    assigned_worker_name = None
    if order.assigned_to:
        worker = db.query(Worker).filter(Worker.id == order.assigned_to).first()
        assigned_worker_name = worker.worker_name if worker else None

    return WorkOrderResponse(
        id=order.id,
        work_order_no=order.work_order_no,
        task_name=order.task_name,
        task_type=order.task_type,
        project_id=order.project_id,
        project_name=project_name,
        machine_id=order.machine_id,
        machine_name=machine_name,
        production_plan_id=order.production_plan_id,
        process_id=order.process_id,
        process_name=process_name,
        workshop_id=order.workshop_id,
        workshop_name=workshop_name,
        workstation_id=order.workstation_id,
        workstation_name=workstation_name,
        material_name=order.material_name,
        specification=order.specification,
        plan_qty=order.plan_qty or 0,
        completed_qty=order.completed_qty or 0,
        qualified_qty=order.qualified_qty or 0,
        defect_qty=order.defect_qty or 0,
        standard_hours=float(order.standard_hours) if order.standard_hours else None,
        actual_hours=float(order.actual_hours) if order.actual_hours else 0,
        plan_start_date=order.plan_start_date,
        plan_end_date=order.plan_end_date,
        actual_start_time=order.actual_start_time,
        actual_end_time=order.actual_end_time,
        assigned_to=order.assigned_to,
        assigned_worker_name=assigned_worker_name,
        status=order.status,
        priority=order.priority,
        progress=order.progress or 0,
        work_content=order.work_content,
        remark=order.remark,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


# ==================== 生产工单管理 ====================

@router.get("/work-orders", response_model=PaginatedResponse)
def read_work_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
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
    offset = (page - 1) * page_size
    orders = query.order_by(desc(WorkOrder.created_at)).offset(offset).limit(page_size).all()

    items = [_get_work_order_response(db, order) for order in orders]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


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
        project = db.query(Project).filter(Project.id == order_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

    # 检查机台是否存在
    if order_in.machine_id:
        machine = db.query(Machine).filter(Machine.id == order_in.machine_id).first()
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在")

    # 检查生产计划是否存在
    if order_in.production_plan_id:
        plan = db.query(ProductionPlan).filter(ProductionPlan.id == order_in.production_plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="生产计划不存在")

    # 检查车间是否存在
    if order_in.workshop_id:
        workshop = db.query(Workshop).filter(Workshop.id == order_in.workshop_id).first()
        if not workshop:
            raise HTTPException(status_code=404, detail="车间不存在")

    # 检查工位是否存在
    if order_in.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order_in.workstation_id).first()
        if not workstation:
            raise HTTPException(status_code=404, detail="工位不存在")
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
    db.add(order)
    db.commit()
    db.refresh(order)

    return _get_work_order_response(db, order)


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
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    return _get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/assign", response_model=WorkOrderResponse)
def assign_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    assign_in: WorkOrderAssignRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    任务派工（指派人员/工位）
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status != "PENDING":
        raise HTTPException(status_code=400, detail="只有待派工状态的工单才能派工")

    # 检查工人是否存在
    worker = db.query(Worker).filter(Worker.id == assign_in.assigned_to).first()
    if not worker:
        raise HTTPException(status_code=404, detail="工人不存在")

    # 检查工位是否存在
    if assign_in.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == assign_in.workstation_id).first()
        if not workstation:
            raise HTTPException(status_code=404, detail="工位不存在")
        if order.workshop_id and workstation.workshop_id != order.workshop_id:
            raise HTTPException(status_code=400, detail="工位不属于该车间")

    order.assigned_to = assign_in.assigned_to
    order.assigned_at = datetime.now()
    order.assigned_by = current_user.id
    order.status = "ASSIGNED"

    if assign_in.workstation_id:
        order.workstation_id = assign_in.workstation_id

    db.add(order)
    db.commit()
    db.refresh(order)

    return _get_work_order_response(db, order)


@router.post("/work-orders/batch-assign", response_model=ResponseModel)
def batch_assign_work_orders(
    *,
    db: Session = Depends(deps.get_db),
    order_ids: List[int] = Body(..., description="工单ID列表"),
    assign_in: WorkOrderAssignRequest = Body(..., description="派工信息"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量派工
    """
    success_count = 0
    failed_orders = []

    for order_id in order_ids:
        try:
            order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
            if not order:
                failed_orders.append({"order_id": order_id, "reason": "工单不存在"})
                continue

            if order.status != "PENDING":
                failed_orders.append({"order_id": order_id, "reason": f"工单状态为{order.status}，不能派工"})
                continue

            # 验证工人
            if assign_in.assigned_to:
                worker = db.query(Worker).filter(Worker.id == assign_in.assigned_to).first()
                if not worker:
                    failed_orders.append({"order_id": order_id, "reason": "工人不存在"})
                    continue
                order.assigned_to = assign_in.assigned_to
                order.assigned_to_name = worker.worker_name

            # 验证工位
            if assign_in.workstation_id:
                workstation = db.query(Workstation).filter(Workstation.id == assign_in.workstation_id).first()
                if not workstation:
                    failed_orders.append({"order_id": order_id, "reason": "工位不存在"})
                    continue
                order.workstation_id = assign_in.workstation_id

            order.status = "ASSIGNED"
            order.assigned_at = datetime.now()
            order.assigned_by = current_user.id

            db.add(order)
            success_count += 1
        except Exception as e:
            failed_orders.append({"order_id": order_id, "reason": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量派工完成：成功 {success_count} 个，失败 {len(failed_orders)} 个",
        data={"success_count": success_count, "failed_orders": failed_orders}
    )


@router.put("/work-orders/{order_id}/start", response_model=WorkOrderResponse)
def start_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail="只有已派工的工单才能开始")

    order.status = "STARTED"
    order.actual_start_time = datetime.now()

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = order.id
            workstation.current_worker_id = order.assigned_to
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return _get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/complete", response_model=WorkOrderResponse)
def complete_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status not in ["STARTED", "PAUSED"]:
        raise HTTPException(status_code=400, detail="只有已开始或已暂停的工单才能完成")

    order.status = "COMPLETED"
    order.actual_end_time = datetime.now()
    order.progress = 100

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            workstation.current_work_order_id = None
            workstation.current_worker_id = None
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return _get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/pause", response_model=WorkOrderResponse)
def pause_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    pause_reason: Optional[str] = Body(None, description="暂停原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    暂停工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status != "STARTED":
        raise HTTPException(status_code=400, detail="只有已开始的工单才能暂停")

    order.status = "PAUSED"
    if pause_reason:
        order.remark = (order.remark or "") + f"\n暂停原因：{pause_reason}"

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return _get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/resume", response_model=WorkOrderResponse)
def resume_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    恢复工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status != "PAUSED":
        raise HTTPException(status_code=400, detail="只有已暂停的工单才能恢复")

    order.status = "STARTED"

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = order.id
            workstation.current_worker_id = order.assigned_to
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return _get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/cancel", response_model=WorkOrderResponse)
def cancel_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    cancel_reason: Optional[str] = Body(None, description="取消原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="已完成或已取消的工单不能再次取消")

    order.status = "CANCELLED"
    if cancel_reason:
        order.remark = (order.remark or "") + f"\n取消原因：{cancel_reason}"

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            workstation.current_work_order_id = None
            workstation.current_worker_id = None
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return _get_work_order_response(db, order)


@router.get("/work-orders/{order_id}/progress", response_model=WorkOrderProgressResponse)
def get_work_order_progress(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单进度
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 计算效率
    efficiency = None
    if order.standard_hours and order.actual_hours and order.actual_hours > 0:
        efficiency = float((order.standard_hours / order.actual_hours) * 100)

    return WorkOrderProgressResponse(
        work_order_id=order.id,
        work_order_no=order.work_order_no,
        task_name=order.task_name,
        plan_qty=order.plan_qty or 0,
        completed_qty=order.completed_qty or 0,
        qualified_qty=order.qualified_qty or 0,
        defect_qty=order.defect_qty or 0,
        progress=order.progress or 0,
        status=order.status,
        plan_start_date=order.plan_start_date,
        plan_end_date=order.plan_end_date,
        actual_start_time=order.actual_start_time,
        actual_end_time=order.actual_end_time,
        standard_hours=float(order.standard_hours) if order.standard_hours else None,
        actual_hours=float(order.actual_hours) if order.actual_hours else 0,
        efficiency=efficiency,
    )
