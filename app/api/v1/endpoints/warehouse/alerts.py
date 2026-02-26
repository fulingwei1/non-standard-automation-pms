# -*- coding: utf-8 -*-
"""
仓储管理 - 库存预警
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.base import get_db
from app.models.warehouse import Inventory

router = APIRouter()


class AlertOut(BaseModel):
    id: int
    warehouse_id: int
    material_code: str
    material_name: Optional[str] = None
    specification: Optional[str] = None
    unit: str = "件"
    quantity: float = 0
    available_quantity: float = 0
    min_stock: float = 0
    max_stock: float = 0
    alert_type: str = ""  # LOW / OVERSTOCK
    shortage: float = 0  # 缺口数量

    class Config:
        from_attributes = True


class AlertSummary(BaseModel):
    low_stock_count: int = 0
    overstock_count: int = 0
    total_alerts: int = 0


@router.get("/alerts/summary", response_model=AlertSummary)
def get_alert_summary(db: Session = Depends(get_db)):
    low = db.query(func.count(Inventory.id)).filter(
        Inventory.available_quantity <= Inventory.min_stock,
        Inventory.min_stock > 0,
    ).scalar() or 0
    over = db.query(func.count(Inventory.id)).filter(
        Inventory.quantity > Inventory.max_stock,
        Inventory.max_stock > 0,
    ).scalar() or 0
    return AlertSummary(low_stock_count=low, overstock_count=over, total_alerts=low + over)


@router.get("/alerts", response_model=dict)
def list_alerts(
    alert_type: Optional[str] = Query(None, description="LOW or OVERSTOCK"),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # Build two queries and union
    results = []

    if alert_type != "OVERSTOCK":
        low_q = db.query(Inventory).filter(
            Inventory.available_quantity <= Inventory.min_stock,
            Inventory.min_stock > 0,
        )
        if keyword:
            low_q = low_q.filter(
                (Inventory.material_code.contains(keyword)) |
                (Inventory.material_name.contains(keyword))
            )
        for inv in low_q.all():
            results.append({
                **AlertOut.model_validate(inv).model_dump(),
                "alert_type": "LOW",
                "shortage": float(inv.min_stock - inv.available_quantity),
            })

    if alert_type != "LOW":
        over_q = db.query(Inventory).filter(
            Inventory.quantity > Inventory.max_stock,
            Inventory.max_stock > 0,
        )
        if keyword:
            over_q = over_q.filter(
                (Inventory.material_code.contains(keyword)) |
                (Inventory.material_name.contains(keyword))
            )
        for inv in over_q.all():
            results.append({
                **AlertOut.model_validate(inv).model_dump(),
                "alert_type": "OVERSTOCK",
                "shortage": float(inv.quantity - inv.max_stock),
            })

    total = len(results)
    start = (page - 1) * page_size
    return {
        "items": results[start:start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
