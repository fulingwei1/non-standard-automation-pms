# -*- coding: utf-8 -*-
"""
安装调试派工 API endpoints
包含：安装调试派工单的CRUD、派工、状态流转等
"""

from typing import Any, List, Optional
from datetime import datetime, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project, Machine, Customer
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.service import ServiceRecord
from app.schemas.installation_dispatch import (
    InstallationDispatchOrderCreate,
    InstallationDispatchOrderUpdate,
    InstallationDispatchOrderAssign,
    InstallationDispatchOrderStart,
    InstallationDispatchOrderComplete,
    InstallationDispatchOrderProgress,
    InstallationDispatchOrderResponse,
    InstallationDispatchOrderBatchAssign,
    InstallationDispatchStatistics,
)
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


# ==================== 辅助函数 ====================

def generate_order_no(db: Session) -> str:
    """生成安装调试派工单号：IDO-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_order = (
        db.query(InstallationDispatchOrder)
        .filter(InstallationDispatchOrder.order_no.like(f"IDO-{today}-%"))
        .order_by(desc(InstallationDispatchOrder.order_no))
        .first()
    )
    if max_order:
        seq = int(max_order.order_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"IDO-{today}-{seq:03d}"


# ==================== 统计 ====================

@router.get("/statistics", response_model=InstallationDispatchStatistics, status_code=status.HTTP_200_OK)
def get_installation_dispatch_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    获取安装调试派工统计
    """
    total = db.query(InstallationDispatchOrder).count()
    pending = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "PENDING").count()
    assigned = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "ASSIGNED").count()
    in_progress = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "IN_PROGRESS").count()
    completed = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "COMPLETED").count()
    cancelled = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "CANCELLED").count()
    urgent = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.priority == "URGENT").count()
    
    return InstallationDispatchStatistics(
        total=total,
        pending=pending,
        assigned=assigned,
        in_progress=in_progress,
        completed=completed,
        cancelled=cancelled,
        urgent=urgent,
    )


# ==================== 安装调试派工单 ====================

@router.get("/orders", response_model=PaginatedResponse[InstallationDispatchOrderResponse], status_code=status.HTTP_200_OK)
def read_installation_dispatch_orders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
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
    
    if status:
        query = query.filter(InstallationDispatchOrder.status == status)
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
    if keyword:
        query = query.filter(
            or_(
                InstallationDispatchOrder.order_no.like(f"%{keyword}%"),
                InstallationDispatchOrder.task_title.like(f"%{keyword}%"),
            )
        )
    
    total = query.count()
    items = query.order_by(desc(InstallationDispatchOrder.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    # 获取关联信息
    for item in items:
        if item.project_id:
            project = db.query(Project).filter(Project.id == item.project_id).first()
            if project:
                item.project_name = project.project_name
                item.project_code = project.project_code
        if item.machine_id:
            machine = db.query(Machine).filter(Machine.id == item.machine_id).first()
            if machine:
                item.machine_no = machine.machine_no
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
    
    # 获取关联信息
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


@router.put("/orders/{order_id}/assign", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def assign_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    assign_in: InstallationDispatchOrderAssign,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    派工安装调试派工单
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")
    
    if order.status != "PENDING":
        raise HTTPException(status_code=400, detail="只有待派工状态的派工单才能派工")
    
    # 验证派工人员是否存在
    assignee = db.query(User).filter(User.id == assign_in.assigned_to_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="派工人员不存在")
    
    order.assigned_to_id = assign_in.assigned_to_id
    order.assigned_to_name = assignee.real_name or assignee.username
    order.assigned_by_id = current_user.id
    order.assigned_by_name = current_user.real_name or current_user.username
    order.assigned_time = datetime.now()
    order.status = "ASSIGNED"
    if assign_in.remark:
        order.remark = (order.remark or "") + f"\n派工备注：{assign_in.remark}"
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_installation_dispatch_order(order.id, db, current_user)


@router.post("/orders/batch-assign", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_assign_installation_dispatch_orders(
    *,
    db: Session = Depends(deps.get_db),
    batch_assign_in: InstallationDispatchOrderBatchAssign,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    批量派工安装调试派工单
    """
    # 验证派工人员是否存在
    assignee = db.query(User).filter(User.id == batch_assign_in.assigned_to_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="派工人员不存在")
    
    success_count = 0
    failed_orders = []
    
    for order_id in batch_assign_in.order_ids:
        try:
            order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
            if not order:
                failed_orders.append({"order_id": order_id, "reason": "派工单不存在"})
                continue
            
            if order.status != "PENDING":
                failed_orders.append({"order_id": order_id, "reason": f"派工单状态为{order.status}，不能派工"})
                continue
            
            order.assigned_to_id = batch_assign_in.assigned_to_id
            order.assigned_to_name = assignee.real_name or assignee.username
            order.assigned_by_id = current_user.id
            order.assigned_by_name = current_user.real_name or current_user.username
            order.assigned_time = datetime.now()
            order.status = "ASSIGNED"
            if batch_assign_in.remark:
                order.remark = (order.remark or "") + f"\n批量派工备注：{batch_assign_in.remark}"
            
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


@router.put("/orders/{order_id}/start", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def start_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    start_in: InstallationDispatchOrderStart,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    开始安装调试任务
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")
    
    if order.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail="只有已派工状态的派工单才能开始")
    
    if order.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能开始分配给自己的任务")
    
    order.status = "IN_PROGRESS"
    order.start_time = start_in.start_time or datetime.now()
    order.progress = 0
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_installation_dispatch_order(order.id, db, current_user)


@router.put("/orders/{order_id}/progress", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def update_installation_dispatch_order_progress(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    progress_in: InstallationDispatchOrderProgress,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    更新安装调试任务进度
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")
    
    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只有进行中状态的派工单才能更新进度")
    
    order.progress = progress_in.progress
    if progress_in.execution_notes:
        order.execution_notes = (order.execution_notes or "") + f"\n{datetime.now().strftime('%Y-%m-%d %H:%M')}：{progress_in.execution_notes}"
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_installation_dispatch_order(order.id, db, current_user)


@router.put("/orders/{order_id}/complete", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def complete_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    complete_in: InstallationDispatchOrderComplete,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    完成安装调试任务
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")
    
    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只有进行中状态的派工单才能完成")
    
    order.status = "COMPLETED"
    order.end_time = complete_in.end_time or datetime.now()
    order.actual_hours = complete_in.actual_hours
    order.progress = 100
    
    if complete_in.execution_notes:
        order.execution_notes = (order.execution_notes or "") + f"\n完成说明：{complete_in.execution_notes}"
    if complete_in.issues_found:
        order.issues_found = complete_in.issues_found
    if complete_in.solution_provided:
        order.solution_provided = complete_in.solution_provided
    if complete_in.photos:
        order.photos = complete_in.photos
    
    # 自动创建现场服务记录
    try:
        from app.api.v1.endpoints.service import generate_record_no
        
        # 获取机台号
        machine_no = None
        if order.machine_id:
            machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
            if machine:
                machine_no = machine.machine_no
        
        service_record = ServiceRecord(
            record_no=generate_record_no(db),
            service_type="INSTALLATION",
            project_id=order.project_id,
            machine_no=machine_no,
            customer_id=order.customer_id,
            location=order.location,
            service_date=order.scheduled_date,
            start_time=order.start_time.strftime("%H:%M") if order.start_time else None,
            end_time=order.end_time.strftime("%H:%M") if order.end_time else None,
            duration_hours=complete_in.actual_hours or order.estimated_hours,
            service_engineer_id=order.assigned_to_id,
            service_engineer_name=order.assigned_to_name,
            customer_contact=order.customer_contact,
            customer_phone=order.customer_phone,
            service_content=order.task_description or order.task_title,
            service_result=complete_in.execution_notes,
            issues_found=complete_in.issues_found,
            solution_provided=complete_in.solution_provided,
            photos=complete_in.photos,
            status="COMPLETED",
        )
        db.add(service_record)
        db.flush()
        order.service_record_id = service_record.id
    except Exception as e:
        # 如果创建服务记录失败，不影响派工单完成
        import logging
        logging.warning(f"自动创建现场服务记录失败：{str(e)}")
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_installation_dispatch_order(order.id, db, current_user)


@router.put("/orders/{order_id}/cancel", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def cancel_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    取消安装调试派工单
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")
    
    if order.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="已完成或已取消的派工单不能再次取消")
    
    order.status = "CANCELLED"
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return read_installation_dispatch_order(order.id, db, current_user)
