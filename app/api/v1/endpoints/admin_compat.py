# -*- coding: utf-8 -*-
"""行政管理接口（ADMIN-07 做实：用品/车辆/资产/费用真库 CRUD）。

此前整文件硬编码演示数据（A4 复印纸/固定车辆/写死费用统计），且前端
adminApi 的全部写操作（申领/审批/用车/资产增删改）404。现按前端既有
调用面补齐真实实现；响应保留 camelCase 兼容键。/stats 委托 admin_stats
（ADMIN-05 范围）不在本文件重复实现。
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.api.v1.endpoints.admin_stats import collect_admin_stats
from app.core import security
from app.models.admin_office import (
    AdminAsset,
    AdminExpense,
    AdminSupply,
    AdminSupplyRequest,
    AdminVehicle,
    AdminVehicleRequest,
)
from app.models.user import User
from app.utils.db_helpers import get_or_404

router = APIRouter()


# ==================== 序列化（兼容前端 camelCase 键） ====================


def _supply_view(s: AdminSupply) -> Dict[str, Any]:
    stock = s.current_stock or 0
    min_stock = s.min_stock or 0
    unit_price = float(s.unit_price or 0)
    return {
        "id": s.id,
        "name": s.name,
        "category": s.category,
        "specification": s.specification,
        "unit": s.unit,
        "quantity": stock,
        "currentStock": stock,
        "minStock": min_stock,
        "unitPrice": unit_price,
        "totalValue": round(stock * unit_price, 2),
        "status": "low" if stock < min_stock else "normal",
        "supplier": s.supplier,
        "lastPurchaseDate": s.last_purchase_date.isoformat() if s.last_purchase_date else None,
    }


def _vehicle_view(v: AdminVehicle) -> Dict[str, Any]:
    return {
        "id": v.id,
        "plateNumber": v.plate_no,
        "plate_no": v.plate_no,
        "model": v.model,
        "seats": v.seats,
        "status": v.status,
        "currentDriver": v.current_driver,
        "remark": v.remark,
    }


def _asset_view(a: AdminAsset) -> Dict[str, Any]:
    return {
        "id": a.id,
        "asset_no": a.asset_no,
        "assetNo": a.asset_no,
        "name": a.name,
        "category": a.category,
        "specification": a.specification,
        "value": float(a.value or 0),
        "purchaseDate": a.purchase_date.isoformat() if a.purchase_date else None,
        "custodian": a.custodian,
        "location": a.location,
        "status": a.status,
        "remark": a.remark,
    }


def _request_view(r) -> Dict[str, Any]:
    return {
        "id": r.id,
        "status": r.status,
        "requested_by": r.requested_by,
        "approved_by": r.approved_by,
        "approved_at": r.approved_at.isoformat() if r.approved_at else None,
        "approval_comment": r.approval_comment,
    }


def _parse_date(value) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


# ==================== 总览 ====================


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(deps.get_db),
    _current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    return {"code": 200, "message": "success", "data": collect_admin_stats(db)}


# ==================== 办公用品 ====================


@router.get("/supplies")
def list_supplies(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    supplies = db.query(AdminSupply).order_by(AdminSupply.id.asc()).all()
    items = [_supply_view(s) for s in supplies]
    return {"items": items, "total": len(items)}


@router.get("/supplies/inventory")
def get_supplies_inventory(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    supplies = db.query(AdminSupply).order_by(AdminSupply.id.asc()).all()
    items = [_supply_view(s) for s in supplies]
    return {
        "items": items,
        "total": len(items),
        "totalValue": round(sum(i["totalValue"] for i in items), 2),
        "lowStockItems": [i for i in items if i["status"] == "low"],
    }


@router.post("/supplies/request", status_code=201)
def create_supply_request(
    payload: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:create")),
) -> Dict[str, Any]:
    """创建用品申领单（PENDING，审批通过才扣库存）。"""
    supply = get_or_404(db, AdminSupply, payload.get("supply_id"), "用品不存在")
    quantity = int(payload.get("quantity") or 0)
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="申领数量必须大于 0")
    request = AdminSupplyRequest(
        supply_id=supply.id,
        quantity=quantity,
        reason=payload.get("reason"),
        status="PENDING",
        requested_by=current_user.id,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return {**_request_view(request), "supply_id": supply.id, "quantity": quantity}


@router.put("/supplies/{request_id}/approve")
def approve_supply_request(
    request_id: int,
    payload: dict = Body(default={}),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:update")),
) -> Dict[str, Any]:
    """审批用品申领：通过即扣减库存（库存不足拒绝）。"""
    request = get_or_404(db, AdminSupplyRequest, request_id, "申领单不存在")
    if request.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"申领单状态 {request.status} 不可审批")
    supply = get_or_404(db, AdminSupply, request.supply_id, "用品不存在")
    if (supply.current_stock or 0) < request.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"库存不足：现有 {supply.current_stock or 0}，申领 {request.quantity}",
        )
    supply.current_stock = (supply.current_stock or 0) - request.quantity
    request.status = "APPROVED"
    request.approved_by = current_user.id
    request.approved_at = datetime.now()
    request.approval_comment = payload.get("comment")
    db.commit()
    db.refresh(request)
    return _request_view(request)


@router.put("/supplies/{request_id}/reject")
def reject_supply_request(
    request_id: int,
    payload: dict = Body(default={}),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:update")),
) -> Dict[str, Any]:
    request = get_or_404(db, AdminSupplyRequest, request_id, "申领单不存在")
    if request.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"申领单状态 {request.status} 不可驳回")
    request.status = "REJECTED"
    request.approved_by = current_user.id
    request.approved_at = datetime.now()
    request.approval_comment = payload.get("comment")
    db.commit()
    db.refresh(request)
    return _request_view(request)


@router.get("/supplies/{supply_id}")
def get_supply(
    supply_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    return _supply_view(get_or_404(db, AdminSupply, supply_id, "用品不存在"))


# ==================== 车辆 ====================


@router.get("/vehicles")
def list_vehicles(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    vehicles = db.query(AdminVehicle).order_by(AdminVehicle.id.asc()).all()
    items = [_vehicle_view(v) for v in vehicles]
    return {"items": items, "total": len(items)}


@router.get("/vehicles/available")
def list_available_vehicles(
    date: Optional[str] = Query(None, description="用车日期（预留）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    vehicles = (
        db.query(AdminVehicle)
        .filter(AdminVehicle.status == "AVAILABLE")
        .order_by(AdminVehicle.id.asc())
        .all()
    )
    items = [_vehicle_view(v) for v in vehicles]
    return {"items": items, "total": len(items)}


@router.post("/vehicles/request", status_code=201)
def create_vehicle_request(
    payload: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:create")),
) -> Dict[str, Any]:
    use_date = _parse_date(payload.get("use_date")) or date.today()
    vehicle_id = payload.get("vehicle_id")
    if vehicle_id:
        vehicle = get_or_404(db, AdminVehicle, vehicle_id, "车辆不存在")
        if vehicle.status != "AVAILABLE":
            raise HTTPException(status_code=400, detail=f"车辆当前状态 {vehicle.status} 不可申请")
    request = AdminVehicleRequest(
        vehicle_id=vehicle_id,
        use_date=use_date,
        destination=payload.get("destination"),
        purpose=payload.get("purpose"),
        status="PENDING",
        requested_by=current_user.id,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return {**_request_view(request), "vehicle_id": vehicle_id, "use_date": use_date.isoformat()}


@router.put("/vehicles/{request_id}/approve")
def approve_vehicle_request(
    request_id: int,
    payload: dict = Body(default={}),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:update")),
) -> Dict[str, Any]:
    """审批用车：通过后车辆置 IN_USE。"""
    request = get_or_404(db, AdminVehicleRequest, request_id, "用车申请不存在")
    if request.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"申请状态 {request.status} 不可审批")
    if request.vehicle_id:
        vehicle = get_or_404(db, AdminVehicle, request.vehicle_id, "车辆不存在")
        if vehicle.status != "AVAILABLE":
            raise HTTPException(status_code=400, detail=f"车辆当前状态 {vehicle.status} 不可派出")
        vehicle.status = "IN_USE"
    request.status = "APPROVED"
    request.approved_by = current_user.id
    request.approved_at = datetime.now()
    request.approval_comment = payload.get("comment")
    db.commit()
    db.refresh(request)
    return _request_view(request)


@router.put("/vehicles/{request_id}/reject")
def reject_vehicle_request(
    request_id: int,
    payload: dict = Body(default={}),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:update")),
) -> Dict[str, Any]:
    request = get_or_404(db, AdminVehicleRequest, request_id, "用车申请不存在")
    if request.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"申请状态 {request.status} 不可驳回")
    request.status = "REJECTED"
    request.approved_by = current_user.id
    request.approved_at = datetime.now()
    request.approval_comment = payload.get("comment")
    db.commit()
    db.refresh(request)
    return _request_view(request)


@router.get("/vehicles/{vehicle_id}")
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    return _vehicle_view(get_or_404(db, AdminVehicle, vehicle_id, "车辆不存在"))


# ==================== 固定资产 ====================


@router.get("/assets")
def list_assets(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    assets = db.query(AdminAsset).order_by(AdminAsset.id.asc()).all()
    items = [_asset_view(a) for a in assets]
    return {"items": items, "total": len(items)}


@router.get("/assets/statistics")
def get_asset_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    total_count = db.query(func.count(AdminAsset.id)).scalar() or 0
    total_value = float(db.query(func.sum(AdminAsset.value)).scalar() or 0)
    by_status = {
        status: count
        for status, count in db.query(AdminAsset.status, func.count(AdminAsset.id))
        .group_by(AdminAsset.status)
        .all()
    }
    by_category = [
        {"category": category or "未分类", "count": count, "value": float(value or 0)}
        for category, count, value in db.query(
            AdminAsset.category, func.count(AdminAsset.id), func.sum(AdminAsset.value)
        )
        .group_by(AdminAsset.category)
        .all()
    ]
    return {
        "total_count": total_count,
        "total": total_count,
        "total_value": total_value,
        "totalValue": total_value,
        "by_status": by_status,
        "by_category": by_category,
        "maintenance": by_status.get("REPAIRING", 0),
    }


@router.post("/assets", status_code=201)
def create_asset(
    payload: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:create")),
) -> Dict[str, Any]:
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="资产名称不能为空")
    asset_no = payload.get("asset_no") or f"AST-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}"
    asset = AdminAsset(
        asset_no=asset_no,
        name=name,
        category=payload.get("category"),
        specification=payload.get("specification"),
        value=payload.get("value") or 0,
        purchase_date=_parse_date(payload.get("purchase_date")),
        custodian=payload.get("custodian"),
        location=payload.get("location"),
        status=payload.get("status") or "IN_USE",
        remark=payload.get("remark"),
        created_by=current_user.id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _asset_view(asset)


@router.put("/assets/{asset_id}")
def update_asset(
    asset_id: int,
    payload: dict = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:update")),
) -> Dict[str, Any]:
    asset = get_or_404(db, AdminAsset, asset_id, "资产不存在")
    for field in ("name", "category", "specification", "custodian", "location", "status", "remark"):
        if payload.get(field) is not None:
            setattr(asset, field, payload[field])
    if payload.get("value") is not None:
        asset.value = payload["value"]
    if payload.get("purchase_date"):
        asset.purchase_date = _parse_date(payload["purchase_date"])
    db.commit()
    db.refresh(asset)
    return _asset_view(asset)


@router.delete("/assets/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:delete")),
) -> Dict[str, Any]:
    asset = get_or_404(db, AdminAsset, asset_id, "资产不存在")
    db.delete(asset)
    db.commit()
    return {"success": True, "id": asset_id}


@router.get("/assets/{asset_id}")
def get_asset(
    asset_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    return _asset_view(get_or_404(db, AdminAsset, asset_id, "资产不存在"))


# ==================== 费用 ====================


@router.get("/expenses")
def list_expenses(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    expenses = db.query(AdminExpense).order_by(AdminExpense.expense_date.desc()).limit(200).all()
    items = [
        {
            "id": e.id,
            "expense_no": e.expense_no,
            "category": e.category,
            "amount": float(e.amount or 0),
            "expense_date": e.expense_date.isoformat() if e.expense_date else None,
            "description": e.description,
            "status": e.status,
        }
        for e in expenses
    ]
    return {"items": items, "total": len(items)}


@router.get("/expenses/statistics")
def get_expense_statistics(
    period: str = Query("month", description="统计周期: month/quarter/year"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("user:read")),
) -> Dict[str, Any]:
    """行政费用统计：按真实费用记录聚合（不再返回写死数字）。"""
    today = date.today()
    if period == "year":
        start = date(today.year, 1, 1)
    elif period == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start = date(today.year, quarter_start_month, 1)
    else:
        start = date(today.year, today.month, 1)

    total_amount = float(
        db.query(func.sum(AdminExpense.amount))
        .filter(AdminExpense.expense_date >= start)
        .scalar()
        or 0
    )
    record_count = (
        db.query(func.count(AdminExpense.id)).filter(AdminExpense.expense_date >= start).scalar()
        or 0
    )
    by_category = [
        {"category": category or "未分类", "amount": float(amount or 0), "count": count}
        for category, amount, count in db.query(
            AdminExpense.category, func.sum(AdminExpense.amount), func.count(AdminExpense.id)
        )
        .filter(AdminExpense.expense_date >= start)
        .group_by(AdminExpense.category)
        .all()
    ]
    return {
        "period": period,
        "start_date": start.isoformat(),
        "total_amount": total_amount,
        "record_count": record_count,
        "by_category": by_category,
    }
