# -*- coding: utf-8 -*-
"""
仓储管理 - 入库/出库/库存 CRUD
"""

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.models.warehouse import (
    Warehouse,
    InboundOrder,
    InboundOrderItem,
    OutboundOrder,
    OutboundOrderItem,
    Inventory,
)

router = APIRouter()


# ==================== Schemas ====================

class WarehouseOut(BaseModel):
    id: int
    warehouse_code: str
    warehouse_name: str
    warehouse_type: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class InboundItemCreate(BaseModel):
    material_code: str
    material_name: Optional[str] = None
    specification: Optional[str] = None
    unit: str = "件"
    planned_quantity: float
    location_id: Optional[int] = None
    remark: Optional[str] = None


class InboundOrderCreate(BaseModel):
    order_type: str = "PURCHASE"
    warehouse_id: Optional[int] = None
    source_no: Optional[str] = None
    supplier_name: Optional[str] = None
    planned_date: Optional[date] = None
    remark: Optional[str] = None
    items: List[InboundItemCreate] = []


class InboundItemOut(BaseModel):
    id: int
    material_code: str
    material_name: Optional[str] = None
    specification: Optional[str] = None
    unit: str = "件"
    planned_quantity: float
    received_quantity: float = 0
    location_id: Optional[int] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class InboundOrderOut(BaseModel):
    id: int
    order_no: str
    order_type: str
    warehouse_id: Optional[int] = None
    source_no: Optional[str] = None
    supplier_name: Optional[str] = None
    status: str
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    operator: Optional[str] = None
    remark: Optional[str] = None
    total_quantity: float = 0
    received_quantity: float = 0
    created_at: Optional[datetime] = None
    items: List[InboundItemOut] = []

    class Config:
        from_attributes = True


class OutboundItemCreate(BaseModel):
    material_code: str
    material_name: Optional[str] = None
    specification: Optional[str] = None
    unit: str = "件"
    planned_quantity: float
    location_id: Optional[int] = None
    remark: Optional[str] = None


class OutboundOrderCreate(BaseModel):
    order_type: str = "PRODUCTION"
    warehouse_id: Optional[int] = None
    target_no: Optional[str] = None
    department: Optional[str] = None
    planned_date: Optional[date] = None
    remark: Optional[str] = None
    is_urgent: bool = False
    items: List[OutboundItemCreate] = []


class OutboundItemOut(BaseModel):
    id: int
    material_code: str
    material_name: Optional[str] = None
    specification: Optional[str] = None
    unit: str = "件"
    planned_quantity: float
    picked_quantity: float = 0
    location_id: Optional[int] = None
    remark: Optional[str] = None

    class Config:
        from_attributes = True


class OutboundOrderOut(BaseModel):
    id: int
    order_no: str
    order_type: str
    warehouse_id: Optional[int] = None
    target_no: Optional[str] = None
    department: Optional[str] = None
    status: str
    planned_date: Optional[date] = None
    actual_date: Optional[date] = None
    operator: Optional[str] = None
    remark: Optional[str] = None
    total_quantity: float = 0
    picked_quantity: float = 0
    is_urgent: bool = False
    created_at: Optional[datetime] = None
    items: List[OutboundItemOut] = []

    class Config:
        from_attributes = True


class InventoryOut(BaseModel):
    id: int
    warehouse_id: int
    location_id: Optional[int] = None
    material_code: str
    material_name: Optional[str] = None
    specification: Optional[str] = None
    unit: str = "件"
    quantity: float = 0
    reserved_quantity: float = 0
    available_quantity: float = 0
    min_stock: float = 0
    max_stock: float = 0
    batch_no: Optional[str] = None
    last_inbound_date: Optional[datetime] = None
    last_outbound_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    pendingInbound: int = 0
    todayInbound: int = 0
    pendingOutbound: int = 0
    urgentOutbound: int = 0
    alerts: int = 0
    lowStock: int = 0
    totalItems: int = 0
    totalValue: float = 0


def _generate_order_no(db: Session, prefix: str) -> str:
    """生成单号: prefix + YYYYMMDD + 4位序号"""
    today = date.today().strftime("%Y%m%d")
    pattern = f"{prefix}{today}%"
    if prefix == "IN":
        last = db.query(InboundOrder).filter(InboundOrder.order_no.like(pattern)).order_by(desc(InboundOrder.order_no)).first()
    else:
        last = db.query(OutboundOrder).filter(OutboundOrder.order_no.like(pattern)).order_by(desc(OutboundOrder.order_no)).first()
    if last:
        seq = int(last.order_no[-4:]) + 1
    else:
        seq = 1
    return f"{prefix}{today}{seq:04d}"


# ==================== 仓库 ====================

@router.get("/warehouses", response_model=List[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).filter(Warehouse.is_active == True).all()


# ==================== 工作台统计 ====================

@router.get("/stats", response_model=StatsOut)
def get_warehouse_stats(db: Session = Depends(get_db)):
    today = date.today()
    pending_inbound = db.query(func.count(InboundOrder.id)).filter(
        InboundOrder.status.in_(['DRAFT', 'PENDING', 'RECEIVING'])
    ).scalar() or 0
    today_inbound = db.query(func.count(InboundOrder.id)).filter(
        func.date(InboundOrder.created_at) == today
    ).scalar() or 0
    pending_outbound = db.query(func.count(OutboundOrder.id)).filter(
        OutboundOrder.status.in_(['DRAFT', 'PENDING', 'PICKING'])
    ).scalar() or 0
    urgent_outbound = db.query(func.count(OutboundOrder.id)).filter(
        OutboundOrder.is_urgent == True,
        OutboundOrder.status.in_(['DRAFT', 'PENDING', 'PICKING'])
    ).scalar() or 0
    low_stock = db.query(func.count(Inventory.id)).filter(
        Inventory.available_quantity <= Inventory.min_stock,
        Inventory.min_stock > 0
    ).scalar() or 0
    total_items = db.query(func.count(Inventory.id)).scalar() or 0

    return StatsOut(
        pendingInbound=pending_inbound,
        todayInbound=today_inbound,
        pendingOutbound=pending_outbound,
        urgentOutbound=urgent_outbound,
        alerts=low_stock,
        lowStock=low_stock,
        totalItems=total_items,
    )


# ==================== 入库单 ====================

@router.get("/inbound", response_model=dict)
def list_inbound_orders(
    status: Optional[str] = Query(None),
    order_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(InboundOrder)
    if status:
        q = q.filter(InboundOrder.status == status)
    if order_type:
        q = q.filter(InboundOrder.order_type == order_type)
    if keyword:
        q = q.filter(
            (InboundOrder.order_no.contains(keyword)) |
            (InboundOrder.source_no.contains(keyword)) |
            (InboundOrder.supplier_name.contains(keyword))
        )
    total = q.count()
    items = q.order_by(desc(InboundOrder.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [InboundOrderOut.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/inbound/{order_id}", response_model=InboundOrderOut)
def get_inbound_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(InboundOrder).filter(InboundOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    return order


@router.post("/inbound", response_model=InboundOrderOut)
def create_inbound_order(data: InboundOrderCreate, db: Session = Depends(get_db)):
    order_no = _generate_order_no(db, "IN")
    total_qty = sum(item.planned_quantity for item in data.items)
    order = InboundOrder(
        order_no=order_no,
        order_type=data.order_type,
        warehouse_id=data.warehouse_id,
        source_no=data.source_no,
        supplier_name=data.supplier_name,
        planned_date=data.planned_date,
        remark=data.remark,
        total_quantity=total_qty,
        status="DRAFT",
    )
    db.add(order)
    db.flush()

    for item_data in data.items:
        item = InboundOrderItem(
            order_id=order.id,
            **item_data.model_dump(),
        )
        db.add(item)

    db.commit()
    db.refresh(order)
    return order


@router.put("/inbound/{order_id}/status")
def update_inbound_status(
    order_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db),
):
    order = db.query(InboundOrder).filter(InboundOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    order.status = status
    if status == "COMPLETED":
        order.actual_date = date.today()
    db.commit()
    return {"message": "状态更新成功", "status": status}


# ==================== 出库单 ====================

@router.get("/outbound", response_model=dict)
def list_outbound_orders(
    status: Optional[str] = Query(None),
    order_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(OutboundOrder)
    if status:
        q = q.filter(OutboundOrder.status == status)
    if order_type:
        q = q.filter(OutboundOrder.order_type == order_type)
    if keyword:
        q = q.filter(
            (OutboundOrder.order_no.contains(keyword)) |
            (OutboundOrder.target_no.contains(keyword)) |
            (OutboundOrder.department.contains(keyword))
        )
    total = q.count()
    items = q.order_by(desc(OutboundOrder.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [OutboundOrderOut.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/outbound/{order_id}", response_model=OutboundOrderOut)
def get_outbound_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OutboundOrder).filter(OutboundOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    return order


@router.post("/outbound", response_model=OutboundOrderOut)
def create_outbound_order(data: OutboundOrderCreate, db: Session = Depends(get_db)):
    order_no = _generate_order_no(db, "OUT")
    total_qty = sum(item.planned_quantity for item in data.items)
    order = OutboundOrder(
        order_no=order_no,
        order_type=data.order_type,
        warehouse_id=data.warehouse_id,
        target_no=data.target_no,
        department=data.department,
        planned_date=data.planned_date,
        remark=data.remark,
        is_urgent=data.is_urgent,
        total_quantity=total_qty,
        status="DRAFT",
    )
    db.add(order)
    db.flush()

    for item_data in data.items:
        item = OutboundOrderItem(
            order_id=order.id,
            **item_data.model_dump(),
        )
        db.add(item)

    db.commit()
    db.refresh(order)
    return order


@router.put("/outbound/{order_id}/status")
def update_outbound_status(
    order_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db),
):
    order = db.query(OutboundOrder).filter(OutboundOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    order.status = status
    if status == "COMPLETED":
        order.actual_date = date.today()
    db.commit()
    return {"message": "状态更新成功", "status": status}


# ==================== 库存 ====================

@router.get("/inventory", response_model=dict)
def list_inventory(
    warehouse_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Inventory)
    if warehouse_id:
        q = q.filter(Inventory.warehouse_id == warehouse_id)
    if keyword:
        q = q.filter(
            (Inventory.material_code.contains(keyword)) |
            (Inventory.material_name.contains(keyword))
        )
    if low_stock:
        q = q.filter(
            Inventory.available_quantity <= Inventory.min_stock,
            Inventory.min_stock > 0,
        )
    total = q.count()
    items = q.order_by(desc(Inventory.updated_at)).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [InventoryOut.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
