# -*- coding: utf-8 -*-
"""
物料交期预测
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import Material
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.user import User
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/materials/{material_id}/lead-time-forecast", response_model=dict, status_code=status.HTTP_200_OK)
def get_material_lead_time_forecast(
    material_id: int,
    db: Session = Depends(deps.get_db),
    days: int = Query(90, description="统计天数（默认90天）"),
    current_user: User = Depends(security.require_permission("procurement:read")),
) -> Any:
    """
    物料交期预测（基于历史）
    """
    material = get_or_404(db, Material, material_id, "物料不存在")

    # 查询历史采购订单的到货时间
    cutoff_date = datetime.now() - timedelta(days=days)

    po_items = (
        db.query(PurchaseOrderItem)
        .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
        .filter(PurchaseOrderItem.material_id == material_id)
        .filter(PurchaseOrder.status.in_(["APPROVED", "ORDERED", "RECEIVED", "CLOSED"]))
        .filter(PurchaseOrder.created_at >= cutoff_date)
        .all()
    )

    # 计算平均交期
    lead_times = []
    for po_item in po_items:
        if po_item.received_at and po_item.purchase_order:
            order_date = po_item.purchase_order.created_at.date()
            receive_date = po_item.received_at.date() if isinstance(po_item.received_at, datetime) else po_item.received_at
            lead_time = (receive_date - order_date).days
            if lead_time > 0:
                lead_times.append(lead_time)

    if lead_times:
        avg_lead_time = sum(lead_times) / len(lead_times)
        min_lead_time = min(lead_times)
        max_lead_time = max(lead_times)
    else:
        # 使用物料的标准交期
        avg_lead_time = material.lead_time_days or 7
        min_lead_time = avg_lead_time - 2
        max_lead_time = avg_lead_time + 5

    return {
        "material_id": material_id,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "standard_lead_time": material.lead_time_days or 0,
        "historical_count": len(lead_times),
        "forecast_avg_lead_time": round(avg_lead_time, 1),
        "forecast_min_lead_time": round(min_lead_time, 1),
        "forecast_max_lead_time": round(max_lead_time, 1),
        "recommended_lead_time": round(avg_lead_time + 2, 1)  # 建议交期 = 平均交期 + 2天缓冲
    }
