# -*- coding: utf-8 -*-
"""
工单齐套查询端点
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader, BomItem
from app.models.production import WorkOrder, Workshop
from app.models.project import Machine, Project
from app.models.purchase import PurchaseOrderItem
from app.models.user import User
from app.schemas.common import ResponseModel

from .utils import calculate_work_order_kit_rate

router = APIRouter()


@router.get("/kit-check/work-orders", response_model=ResponseModel)
def get_work_orders_for_check(
    db: Session = Depends(deps.get_db),
    kit_status: Optional[str] = Query(None, description="齐套状态: complete/partial/shortage"),
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    plan_date: Optional[date] = Query(None, description="计划开工日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    待检查工单列表
    获取未来7天内计划开工的工单，用于齐套检查
    """
    # 默认查询未来7天的工单
    today = date.today()
    end_date = today + timedelta(days=7)

    # 构建查询
    query = db.query(WorkOrder).filter(
        WorkOrder.plan_start_date.isnot(None),
        WorkOrder.plan_start_date >= today,
        WorkOrder.plan_start_date <= end_date,
        WorkOrder.status.in_(['PENDING', 'ASSIGNED', 'READY']),  # 待开工状态
    )

    # 筛选条件
    if workshop_id:
        query = query.filter(WorkOrder.workshop_id == workshop_id)
    if project_id:
        query = query.filter(WorkOrder.project_id == project_id)
    if plan_date:
        query = query.filter(WorkOrder.plan_start_date == plan_date)

    # 总数
    total = query.count()

    # 分页
    work_orders = query.order_by(WorkOrder.plan_start_date, WorkOrder.priority).offset((page - 1) * page_size).limit(page_size).all()

    # 计算每个工单的齐套率
    work_order_list = []
    summary = {
        "total": 0,
        "complete": 0,
        "partial": 0,
        "shortage": 0,
    }

    for wo in work_orders:
        kit_data = calculate_work_order_kit_rate(db, wo)

        # 统计汇总
        summary["total"] += 1
        if kit_data["kit_status"] == "complete":
            summary["complete"] += 1
        elif kit_data["kit_status"] == "partial":
            summary["partial"] += 1
        else:
            summary["shortage"] += 1

        # 应用状态筛选
        if kit_status and kit_data["kit_status"] != kit_status:
            continue

        # 获取关联信息
        project = db.query(Project).filter(Project.id == wo.project_id).first() if wo.project_id else None
        machine = db.query(Machine).filter(Machine.id == wo.machine_id).first() if wo.machine_id else None
        workshop = db.query(Workshop).filter(Workshop.id == wo.workshop_id).first() if wo.workshop_id else None

        work_order_list.append({
            "id": wo.id,
            "work_order_no": wo.work_order_no,
            "task_name": wo.task_name,
            "project_id": wo.project_id,
            "project_name": project.project_name if project else None,
            "machine_id": wo.machine_id,
            "machine_name": machine.machine_name if machine else None,
            "workshop_id": wo.workshop_id,
            "workshop_name": workshop.workshop_name if workshop else None,
            "plan_start_date": wo.plan_start_date.isoformat() if wo.plan_start_date else None,
            "plan_qty": wo.plan_qty,
            "status": wo.status,
            "priority": wo.priority,
            "kit_rate": kit_data["kit_rate"],
            "kit_status": kit_data["kit_status"],
            "is_kit_complete": kit_data["is_kit_complete"],
            "total_items": kit_data["total_items"],
            "fulfilled_items": kit_data["fulfilled_items"],
            "shortage_items": kit_data["shortage_items"],
            "in_transit_items": kit_data["in_transit_items"],
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "work_orders": work_order_list,
            "summary": summary,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size,
            }
        }
    )


@router.get("/kit-check/work-orders/{work_order_id}", response_model=ResponseModel)
def get_work_order_kit_detail(
    *,
    db: Session = Depends(deps.get_db),
    work_order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工单齐套详情
    获取工单的BOM明细、库存、在途等详细信息
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")

    # 计算齐套率
    kit_data = calculate_work_order_kit_rate(db, work_order)

    # 获取BOM明细
    bom_items = []
    if work_order.machine_id:
        machine = db.query(Machine).filter(Machine.id == work_order.machine_id).first()
        if machine and machine.bom_id:
            bom_header = db.query(BomHeader).filter(BomHeader.id == machine.bom_id).first()
            if bom_header:
                bom_items_query = db.query(BomItem).filter(BomItem.bom_id == bom_header.id).all()
                for item in bom_items_query:
                    material = item.material
                    if not material:
                        continue

                    # 计算可用数量
                    available_qty = Decimal(material.current_stock or 0)

                    # 计算在途数量
                    in_transit_qty = Decimal(0)
                    po_items = (
                        db.query(PurchaseOrderItem)
                        .filter(PurchaseOrderItem.material_id == item.material_id)
                        .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
                        .all()
                    )
                    for po_item in po_items:
                        in_transit_qty += (Decimal(po_item.quantity or 0) - Decimal(po_item.received_qty or 0))

                    # 需求数量
                    required_qty = Decimal(item.quantity or 0) * Decimal(work_order.plan_qty or 1)
                    total_available = available_qty + in_transit_qty

                    # 确定状态
                    if total_available >= required_qty:
                        status = "fulfilled"
                    elif total_available > 0:
                        status = "partial"
                    else:
                        status = "shortage"

                    bom_items.append({
                        "material_id": material.id,
                        "material_code": material.material_code,
                        "material_name": material.material_name,
                        "specification": material.specification,
                        "unit": material.unit,
                        "bom_quantity": float(item.quantity or 0),
                        "required_qty": float(required_qty),
                        "available_qty": float(available_qty),
                        "in_transit_qty": float(in_transit_qty),
                        "total_available": float(total_available),
                        "shortage_qty": float(max(0, required_qty - total_available)),
                        "status": status,
                        "is_critical": item.is_critical or False,
                    })

    # 获取关联信息
    project = db.query(Project).filter(Project.id == work_order.project_id).first() if work_order.project_id else None
    machine = db.query(Machine).filter(Machine.id == work_order.machine_id).first() if work_order.machine_id else None
    workshop = db.query(Workshop).filter(Workshop.id == work_order.workshop_id).first() if work_order.workshop_id else None

    return ResponseModel(
        code=200,
        message="success",
        data={
            "work_order": {
                "id": work_order.id,
                "work_order_no": work_order.work_order_no,
                "task_name": work_order.task_name,
                "project_id": work_order.project_id,
                "project_name": project.project_name if project else None,
                "machine_id": work_order.machine_id,
                "machine_name": machine.machine_name if machine else None,
                "workshop_id": work_order.workshop_id,
                "workshop_name": workshop.workshop_name if workshop else None,
                "plan_start_date": work_order.plan_start_date.isoformat() if work_order.plan_start_date else None,
                "plan_qty": work_order.plan_qty,
                "status": work_order.status,
            },
            "kit_data": kit_data,
            "bom_items": bom_items,
        }
    )
