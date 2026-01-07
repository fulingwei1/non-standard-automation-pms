# -*- coding: utf-8 -*-
"""
齐套检查 API endpoints
包含：工单齐套检查、齐套详情、开工确认、检查历史
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.project import Project, Machine
from app.models.material import BomHeader, BomItem, Material
from app.models.purchase import PurchaseOrderItem
from app.models.production import WorkOrder, Workshop
from app.models.shortage import KitCheck
from app.schemas.common import ResponseModel, PaginatedResponse

router = APIRouter()


def generate_check_no(db: Session) -> str:
    """生成齐套检查编号：KC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_check = (
        db.query(KitCheck)
        .filter(KitCheck.check_no.like(f"KC-{today}-%"))
        .order_by(desc(KitCheck.check_no))
        .first()
    )
    if max_check:
        seq = int(max_check.check_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"KC-{today}-{seq:03d}"


def calculate_work_order_kit_rate(
    db: Session,
    work_order: WorkOrder,
) -> Dict[str, Any]:
    """
    计算工单齐套率
    
    Args:
        db: 数据库会话
        work_order: 工单对象
    
    Returns:
        包含齐套率统计信息的字典
    """
    # 获取工单关联的机台BOM
    bom_items = []
    if work_order.machine_id:
        machine = db.query(Machine).filter(Machine.id == work_order.machine_id).first()
        if machine and machine.bom_id:
            bom_header = db.query(BomHeader).filter(BomHeader.id == machine.bom_id).first()
            if bom_header:
                bom_items = db.query(BomItem).filter(BomItem.bom_id == bom_header.id).all()
    
    if not bom_items:
        return {
            "total_items": 0,
            "fulfilled_items": 0,
            "shortage_items": 0,
            "in_transit_items": 0,
            "kit_rate": 0.0,
            "kit_status": "shortage",
            "is_kit_complete": False,
            "shortage_details": [],
        }
    
    total_items = len(bom_items)
    fulfilled_items = 0
    shortage_items = 0
    in_transit_items = 0
    shortage_details = []
    
    for item in bom_items:
        material = item.material
        if not material:
            continue
        
        # 计算可用数量 = 当前库存
        available_qty = Decimal(material.current_stock or 0)
        
        # 计算在途数量 = 已采购但未到货的数量
        in_transit_qty = Decimal(0)
        po_items = (
            db.query(PurchaseOrderItem)
            .filter(PurchaseOrderItem.material_id == item.material_id)
            .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
            .all()
        )
        for po_item in po_items:
            in_transit_qty += (Decimal(po_item.quantity or 0) - Decimal(po_item.received_qty or 0))
        
        # 总可用数量 = 可用数量 + 在途数量
        total_available = available_qty + in_transit_qty
        
        # 需求数量 = BOM用量 * 工单计划数量
        required_qty = Decimal(item.quantity or 0) * Decimal(work_order.plan_qty or 1)
        
        if total_available >= required_qty:
            fulfilled_items += 1
        elif total_available > 0:
            in_transit_items += 1
            shortage_details.append({
                "material_id": material.id,
                "material_code": material.material_code,
                "material_name": material.material_name,
                "required_qty": float(required_qty),
                "available_qty": float(available_qty),
                "in_transit_qty": float(in_transit_qty),
                "shortage_qty": float(required_qty - total_available),
                "status": "partial",
            })
        else:
            shortage_items += 1
            shortage_details.append({
                "material_id": material.id,
                "material_code": material.material_code,
                "material_name": material.material_name,
                "required_qty": float(required_qty),
                "available_qty": float(available_qty),
                "in_transit_qty": float(in_transit_qty),
                "shortage_qty": float(required_qty),
                "status": "shortage",
            })
    
    # 计算齐套率
    kit_rate = (fulfilled_items / total_items * 100) if total_items > 0 else 0.0
    
    # 确定齐套状态
    if fulfilled_items == total_items:
        kit_status = "complete"
        is_kit_complete = True
    elif fulfilled_items > 0:
        kit_status = "partial"
        is_kit_complete = False
    else:
        kit_status = "shortage"
        is_kit_complete = False
    
    return {
        "total_items": total_items,
        "fulfilled_items": fulfilled_items,
        "shortage_items": shortage_items,
        "in_transit_items": in_transit_items,
        "kit_rate": round(float(kit_rate), 2),
        "kit_status": kit_status,
        "is_kit_complete": is_kit_complete,
        "shortage_details": shortage_details,
    }


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


@router.post("/kit-check/work-orders/{work_order_id}/check", response_model=ResponseModel)
def check_work_order_kit(
    *,
    db: Session = Depends(deps.get_db),
    work_order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行齐套检查
    计算工单的齐套率并返回检查结果
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    # 计算齐套率
    kit_data = calculate_work_order_kit_rate(db, work_order)
    
    # 保存检查记录到 mat_kit_check 表
    check_record = KitCheck(
        check_no=generate_check_no(db),
        check_type='work_order',
        work_order_id=work_order_id,
        project_id=work_order.project_id,
        total_items=kit_data["total_items"],
        fulfilled_items=kit_data["fulfilled_items"],
        shortage_items=kit_data["shortage_items"],
        in_transit_items=kit_data["in_transit_items"],
        kit_rate=Decimal(str(kit_data["kit_rate"])),
        kit_status=kit_data["kit_status"],
        shortage_summary=kit_data.get("shortage_details", []),
        check_time=datetime.now(),
        check_method='manual',
        checked_by=current_user.id,
        can_start=kit_data["is_kit_complete"],
    )
    
    db.add(check_record)
    db.commit()
    db.refresh(check_record)
    
    return ResponseModel(
        code=200,
        message="齐套检查完成",
        data={
            "check_id": check_record.id,
            "check_no": check_record.check_no,
            "work_order_id": work_order_id,
            "work_order_no": work_order.work_order_no,
            "kit_data": kit_data,
            "check_time": check_record.check_time.isoformat(),
            "checked_by": current_user.id,
        }
    )


@router.post("/kit-check/work-orders/{work_order_id}/confirm", response_model=ResponseModel)
def confirm_work_order_start(
    *,
    db: Session = Depends(deps.get_db),
    work_order_id: int,
    confirm_type: str = Body(..., description="确认类型: start_now/wait/partial_start"),
    confirm_note: Optional[str] = Body(None, description="确认说明"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    确认开工
    确认工单物料齐套，可以开工（支持强制开工）
    """
    work_order = db.query(WorkOrder).filter(WorkOrder.id == work_order_id).first()
    if not work_order:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if confirm_type not in ["start_now", "wait", "partial_start"]:
        raise HTTPException(status_code=400, detail="确认类型必须是 start_now、wait 或 partial_start")
    
    # 计算齐套率
    kit_data = calculate_work_order_kit_rate(db, work_order)
    
    # 如果齐套率不足且不是强制开工，需要提示
    if kit_data["kit_rate"] < 100 and confirm_type == "start_now":
        # 允许强制开工，但记录说明
        pass
    
    # 更新工单状态
    if confirm_type == "start_now":
        work_order.status = "READY"  # 或 "IN_PROGRESS"，根据业务需求
    elif confirm_type == "wait":
        work_order.status = "PENDING"
    elif confirm_type == "partial_start":
        work_order.status = "READY"
    
    # 查找或创建最新的检查记录
    latest_check = (
        db.query(KitCheck)
        .filter(KitCheck.work_order_id == work_order_id)
        .order_by(desc(KitCheck.check_time))
        .first()
    )
    
    if not latest_check:
        # 如果没有检查记录，先创建一个
        latest_check = KitCheck(
            check_no=generate_check_no(db),
            check_type='work_order',
            work_order_id=work_order_id,
            project_id=work_order.project_id,
            total_items=kit_data["total_items"],
            fulfilled_items=kit_data["fulfilled_items"],
            shortage_items=kit_data["shortage_items"],
            in_transit_items=kit_data["in_transit_items"],
            kit_rate=Decimal(str(kit_data["kit_rate"])),
            kit_status=kit_data["kit_status"],
            shortage_summary=kit_data.get("shortage_details", []),
            check_time=datetime.now(),
            check_method='manual',
            checked_by=current_user.id,
        )
        db.add(latest_check)
    
    # 更新确认信息
    latest_check.start_confirmed = (confirm_type in ["start_now", "partial_start"])
    latest_check.confirm_time = datetime.now()
    latest_check.confirmed_by = current_user.id
    latest_check.confirm_remark = confirm_note
    latest_check.can_start = (confirm_type in ["start_now", "partial_start"])
    
    db.add(work_order)
    db.add(latest_check)
    db.commit()
    db.refresh(work_order)
    db.refresh(latest_check)
    
    return ResponseModel(
        code=200,
        message="开工确认成功",
        data={
            "work_order_id": work_order_id,
            "work_order_no": work_order.work_order_no,
            "confirm_type": confirm_type,
            "confirm_note": confirm_note,
            "kit_rate": kit_data["kit_rate"],
            "confirmed_by": current_user.id,
            "confirmed_at": datetime.now().isoformat(),
        }
    )


@router.get("/kit-check/history", response_model=ResponseModel)
def get_kit_check_history(
    db: Session = Depends(deps.get_db),
    work_order_id: Optional[int] = Query(None, description="工单ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    齐套检查历史
    获取历史齐套检查记录
    """
    query = db.query(KitCheck)
    
    # 筛选条件
    if work_order_id:
        query = query.filter(KitCheck.work_order_id == work_order_id)
    if project_id:
        query = query.filter(KitCheck.project_id == project_id)
    if start_date:
        query = query.filter(func.date(KitCheck.check_time) >= start_date)
    if end_date:
        query = query.filter(func.date(KitCheck.check_time) <= end_date)
    
    # 总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    checks = query.order_by(desc(KitCheck.check_time)).offset(offset).limit(page_size).all()
    
    # 构建返回数据
    history = []
    for check in checks:
        # 获取关联信息
        work_order = db.query(WorkOrder).filter(WorkOrder.id == check.work_order_id).first() if check.work_order_id else None
        project = db.query(Project).filter(Project.id == check.project_id).first() if check.project_id else None
        checker = db.query(User).filter(User.id == check.checked_by).first() if check.checked_by else None
        confirmer = db.query(User).filter(User.id == check.confirmed_by).first() if check.confirmed_by else None
        
        history.append({
            "id": check.id,
            "check_no": check.check_no,
            "check_type": check.check_type,
            "work_order_id": check.work_order_id,
            "work_order_no": work_order.work_order_no if work_order else None,
            "project_id": check.project_id,
            "project_name": project.project_name if project else None,
            "total_items": check.total_items,
            "fulfilled_items": check.fulfilled_items,
            "shortage_items": check.shortage_items,
            "in_transit_items": check.in_transit_items,
            "kit_rate": float(check.kit_rate) if check.kit_rate else 0.0,
            "kit_status": check.kit_status,
            "check_time": check.check_time.isoformat() if check.check_time else None,
            "check_method": check.check_method,
            "checked_by": check.checked_by,
            "checker_name": checker.real_name or checker.username if checker else None,
            "can_start": check.can_start,
            "start_confirmed": check.start_confirmed,
            "confirm_time": check.confirm_time.isoformat() if check.confirm_time else None,
            "confirmed_by": check.confirmed_by,
            "confirmer_name": confirmer.real_name or confirmer.username if confirmer else None,
            "confirm_remark": check.confirm_remark,
            "shortage_summary": check.shortage_summary,
        })
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "history": history,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size,
            }
        }
    )

