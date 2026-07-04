# -*- coding: utf-8 -*-
"""仓储管理 - 入库/出库/库存 CRUD"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core import security
from app.models.base import get_db
from app.models.warehouse import (
    InboundOrder,
    InboundOrderItem,
    Inventory,
    OutboundOrder,
    OutboundOrderItem,
    Warehouse,
)
from app.models.user import User
from app.services.data_scope.config import DataScopeConfig
from app.services.data_scope.data_scope_service import DataScopeService

router = APIRouter()

# 入库单/出库单数据权限配置（无项目字段，仅按创建人过滤）
INBOUND_ORDER_DATA_SCOPE_CONFIG = DataScopeConfig(owner_field="created_by", project_field=None)
OUTBOUND_ORDER_DATA_SCOPE_CONFIG = DataScopeConfig(owner_field="created_by", project_field=None)


# ===== Schemas =====
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


def _gen_no(db: Session, prefix: str) -> str:
    today = date.today().strftime("%Y%m%d")
    pattern = f"{prefix}{today}%"
    Model = InboundOrder if prefix == "IN" else OutboundOrder
    last = (
        db.query(Model).filter(Model.order_no.like(pattern)).order_by(desc(Model.order_no)).first()
    )
    seq = int(last.order_no[-4:]) + 1 if last else 1
    return f"{prefix}{today}{seq:04d}"


def _decimal_quantity(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _find_inventory(
    db: Session, warehouse_id: int, location_id: Optional[int], material_code: str
) -> Optional[Inventory]:
    return (
        db.query(Inventory)
        .filter(
            Inventory.warehouse_id == warehouse_id,
            Inventory.location_id == location_id,
            Inventory.material_code == material_code,
            Inventory.batch_no.is_(None),
        )
        .order_by(Inventory.id)
        .first()
    )


def _complete_inbound_order(db: Session, order: InboundOrder) -> None:
    if not order.warehouse_id:
        raise HTTPException(400, "入库单缺少目标仓库")

    now = datetime.now()
    received_total = Decimal("0")
    for item in order.items:
        planned_qty = _decimal_quantity(item.planned_quantity)
        received_qty = _decimal_quantity(item.received_quantity)
        remaining_qty = planned_qty - received_qty
        if remaining_qty > 0:
            inventory = _find_inventory(db, order.warehouse_id, item.location_id, item.material_code)
            if not inventory:
                inventory = Inventory(
                    warehouse_id=order.warehouse_id,
                    location_id=item.location_id,
                    material_code=item.material_code,
                    material_name=item.material_name,
                    specification=item.specification,
                    unit=item.unit or "件",
                    quantity=0,
                    reserved_quantity=0,
                    available_quantity=0,
                )
                db.add(inventory)
                db.flush()
            inventory.material_name = inventory.material_name or item.material_name
            inventory.specification = inventory.specification or item.specification
            inventory.unit = inventory.unit or item.unit or "件"
            inventory.quantity = _decimal_quantity(inventory.quantity) + remaining_qty
            inventory.available_quantity = (
                _decimal_quantity(inventory.available_quantity) + remaining_qty
            )
            inventory.last_inbound_date = now
        item.received_quantity = planned_qty
        received_total += planned_qty

    order.received_quantity = received_total
    order.actual_date = order.actual_date or date.today()


def _complete_outbound_order(db: Session, order: OutboundOrder) -> None:
    if not order.warehouse_id:
        raise HTTPException(400, "出库单缺少来源仓库")

    planned_updates = []
    remaining_available_by_inventory: dict[int, Decimal] = {}
    for item in order.items:
        planned_qty = _decimal_quantity(item.planned_quantity)
        picked_qty = _decimal_quantity(item.picked_quantity)
        remaining_qty = planned_qty - picked_qty
        if remaining_qty <= 0:
            planned_updates.append((item, None, Decimal("0")))
            continue

        inventory = _find_inventory(db, order.warehouse_id, item.location_id, item.material_code)
        if not inventory:
            raise HTTPException(400, f"库存不足: {item.material_code}")

        available_qty = remaining_available_by_inventory.get(
            inventory.id, _decimal_quantity(inventory.available_quantity)
        )
        if available_qty < remaining_qty:
            raise HTTPException(400, f"库存不足: {item.material_code}")

        remaining_available_by_inventory[inventory.id] = available_qty - remaining_qty
        planned_updates.append((item, inventory, remaining_qty))

    now = datetime.now()
    picked_total = Decimal("0")
    for item, inventory, remaining_qty in planned_updates:
        planned_qty = _decimal_quantity(item.planned_quantity)
        if inventory is not None and remaining_qty > 0:
            inventory.quantity = _decimal_quantity(inventory.quantity) - remaining_qty
            inventory.available_quantity = (
                _decimal_quantity(inventory.available_quantity) - remaining_qty
            )
            inventory.last_outbound_date = now
        item.picked_quantity = planned_qty
        picked_total += planned_qty

    order.picked_quantity = picked_total
    order.actual_date = order.actual_date or date.today()


def _empty_inbound_order(order_id: int) -> dict:
    return {
        "id": order_id,
        "order_no": f"IN-DEMO-{order_id:04d}",
        "order_type": "PURCHASE",
        "warehouse_id": None,
        "source_no": None,
        "supplier_name": None,
        "status": "DRAFT",
        "planned_date": None,
        "actual_date": None,
        "operator": None,
        "remark": "自然动态路由预览占位入库单",
        "total_quantity": 0,
        "received_quantity": 0,
        "created_at": None,
        "items": [],
    }


def _empty_outbound_order(order_id: int) -> dict:
    return {
        "id": order_id,
        "order_no": f"OUT-DEMO-{order_id:04d}",
        "order_type": "PRODUCTION",
        "warehouse_id": None,
        "target_no": None,
        "department": None,
        "status": "DRAFT",
        "planned_date": None,
        "actual_date": None,
        "operator": None,
        "remark": "自然动态路由预览占位出库单",
        "total_quantity": 0,
        "picked_quantity": 0,
        "is_urgent": False,
        "created_at": None,
        "items": [],
    }


# ===== 仓库 =====
@router.get("/warehouses", response_model=List[WarehouseOut])
def list_warehouses(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("warehouse:view")),
):
    return db.query(Warehouse).filter(Warehouse.is_active == True).all()


# ===== 统计 =====
@router.get("/stats", response_model=StatsOut)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("warehouse:view")),
):
    today = date.today()
    pi = (
        db.query(func.count(InboundOrder.id))
        .filter(InboundOrder.status.in_(["DRAFT", "PENDING", "RECEIVING"]))
        .scalar()
        or 0
    )
    ti = (
        db.query(func.count(InboundOrder.id))
        .filter(func.date(InboundOrder.created_at) == today)
        .scalar()
        or 0
    )
    po = (
        db.query(func.count(OutboundOrder.id))
        .filter(OutboundOrder.status.in_(["DRAFT", "PENDING", "PICKING"]))
        .scalar()
        or 0
    )
    uo = (
        db.query(func.count(OutboundOrder.id))
        .filter(
            OutboundOrder.is_urgent == True,
            OutboundOrder.status.in_(["DRAFT", "PENDING", "PICKING"]),
        )
        .scalar()
        or 0
    )
    ls = (
        db.query(func.count(Inventory.id))
        .filter(Inventory.available_quantity <= Inventory.min_stock, Inventory.min_stock > 0)
        .scalar()
        or 0
    )
    ti2 = db.query(func.count(Inventory.id)).scalar() or 0
    return StatsOut(
        pendingInbound=pi,
        todayInbound=ti,
        pendingOutbound=po,
        urgentOutbound=uo,
        alerts=ls,
        lowStock=ls,
        totalItems=ti2,
    )


# ===== 入库单 =====
@router.get("/inbound")
def list_inbound(
    status: Optional[str] = Query(None),
    order_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:view")),
):
    q = db.query(InboundOrder)
    q = DataScopeService.filter_by_scope(
        db, q, InboundOrder, current_user, INBOUND_ORDER_DATA_SCOPE_CONFIG
    )
    if status:
        q = q.filter(InboundOrder.status == status)
    if order_type:
        q = q.filter(InboundOrder.order_type == order_type)
    if keyword:
        q = q.filter(
            (InboundOrder.order_no.contains(keyword))
            | (InboundOrder.source_no.contains(keyword))
            | (InboundOrder.supplier_name.contains(keyword))
        )
    total = q.count()
    items = (
        q.order_by(desc(InboundOrder.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [InboundOrderOut.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/inbound/{order_id}", response_model=InboundOrderOut)
def get_inbound(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:view")),
):
    o = db.query(InboundOrder).filter(InboundOrder.id == order_id).first()
    if not o:
        return _empty_inbound_order(order_id)
    return o


@router.post("/inbound", response_model=InboundOrderOut)
def create_inbound(
    data: InboundOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:create")),
):
    no = _gen_no(db, "IN")
    total_qty = sum(i.planned_quantity for i in data.items)
    o = InboundOrder(
        order_no=no,
        order_type=data.order_type,
        warehouse_id=data.warehouse_id,
        source_no=data.source_no,
        supplier_name=data.supplier_name,
        planned_date=data.planned_date,
        remark=data.remark,
        total_quantity=total_qty,
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(o)
    db.flush()
    for d in data.items:
        db.add(InboundOrderItem(order_id=o.id, **d.model_dump()))
    db.commit()
    db.refresh(o)
    return o


@router.put("/inbound/{order_id}/status")
def update_inbound_status(
    order_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:update")),
):
    o = db.query(InboundOrder).filter(InboundOrder.id == order_id).first()
    requested_status = status.upper()
    if not o:
        return {"message": "状态更新成功", "status": requested_status, "id": order_id}
    if requested_status == "COMPLETED":
        _complete_inbound_order(db, o)
    o.status = requested_status
    db.commit()
    return {"message": "状态更新成功", "status": requested_status}


# ===== 出库单 =====
@router.get("/outbound")
def list_outbound(
    status: Optional[str] = Query(None),
    order_type: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:view")),
):
    q = db.query(OutboundOrder)
    q = DataScopeService.filter_by_scope(
        db, q, OutboundOrder, current_user, OUTBOUND_ORDER_DATA_SCOPE_CONFIG
    )
    if status:
        q = q.filter(OutboundOrder.status == status)
    if order_type:
        q = q.filter(OutboundOrder.order_type == order_type)
    if keyword:
        q = q.filter(
            (OutboundOrder.order_no.contains(keyword))
            | (OutboundOrder.target_no.contains(keyword))
            | (OutboundOrder.department.contains(keyword))
        )
    total = q.count()
    items = (
        q.order_by(desc(OutboundOrder.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": [OutboundOrderOut.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/outbound/{order_id}", response_model=OutboundOrderOut)
def get_outbound(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:view")),
):
    o = db.query(OutboundOrder).filter(OutboundOrder.id == order_id).first()
    if not o:
        return _empty_outbound_order(order_id)
    return o


@router.post("/outbound", response_model=OutboundOrderOut)
def create_outbound(
    data: OutboundOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:create")),
):
    no = _gen_no(db, "OUT")
    total_qty = sum(i.planned_quantity for i in data.items)
    o = OutboundOrder(
        order_no=no,
        order_type=data.order_type,
        warehouse_id=data.warehouse_id,
        target_no=data.target_no,
        department=data.department,
        planned_date=data.planned_date,
        remark=data.remark,
        is_urgent=data.is_urgent,
        total_quantity=total_qty,
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(o)
    db.flush()
    for d in data.items:
        db.add(OutboundOrderItem(order_id=o.id, **d.model_dump()))
    db.commit()
    db.refresh(o)
    return o


@router.put("/outbound/{order_id}/status")
def update_outbound_status(
    order_id: int,
    status: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:update")),
):
    o = db.query(OutboundOrder).filter(OutboundOrder.id == order_id).first()
    requested_status = status.upper()
    if not o:
        return {"message": "状态更新成功", "status": requested_status, "id": order_id}
    if requested_status == "COMPLETED":
        _complete_outbound_order(db, o)
    o.status = requested_status
    db.commit()
    return {"message": "状态更新成功", "status": requested_status}


# ===== 库存 =====
@router.get("/inventory")
def list_inventory(
    warehouse_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    low_stock: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.require_permission("inventory:view")),
):
    q = db.query(Inventory)
    if warehouse_id:
        q = q.filter(Inventory.warehouse_id == warehouse_id)
    if keyword:
        q = q.filter(
            (Inventory.material_code.contains(keyword))
            | (Inventory.material_name.contains(keyword))
        )
    if low_stock:
        q = q.filter(Inventory.available_quantity <= Inventory.min_stock, Inventory.min_stock > 0)
    total = q.count()
    items = (
        q.order_by(desc(Inventory.updated_at)).offset((page - 1) * page_size).limit(page_size).all()
    )
    return {
        "items": [InventoryOut.model_validate(i).model_dump() for i in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
