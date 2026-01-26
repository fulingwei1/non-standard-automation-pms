# -*- coding: utf-8 -*-
"""
发货单统计
"""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.business_support import DeliveryOrder
from app.models.user import User
from app.schemas.business_support import DeliveryStatistics
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/delivery-orders/statistics", response_model=ResponseModel[DeliveryStatistics], summary="获取发货统计")
async def get_delivery_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    发货统计（给生产总监看）
    """
    try:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())

        # 本周开始日期
        week_start = today - timedelta(days=today.weekday())

        # 待发货（已审批但未发货）
        pending_shipments = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "approved"
        ).count()

        # 今日已发
        shipped_today = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "shipped",
            DeliveryOrder.ship_date >= today_start
        ).count()

        # 在途订单（已发货但未签收）
        in_transit = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "shipped",
            DeliveryOrder.receive_date.is_(None)
        ).count()

        # 本周已送达
        delivered_this_week = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "received",
            DeliveryOrder.receive_date >= week_start
        ).count()

        # 准时发货率（计划发货日期 vs 实际发货日期）
        all_shipped = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status.in_(["shipped", "received"]),
            DeliveryOrder.delivery_date.isnot(None),
            DeliveryOrder.ship_date.isnot(None)
        ).all()

        on_time_count = 0
        for order in all_shipped:
            if order.ship_date.date() <= order.delivery_date:
                on_time_count += 1

        on_time_shipping_rate = (on_time_count / len(all_shipped) * 100) if all_shipped else 0.0

        # 平均发货时间（从发货到签收）
        delivered_orders = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "received",
            DeliveryOrder.ship_date.isnot(None),
            DeliveryOrder.receive_date.isnot(None)
        ).all()

        avg_shipping_time = 0.0
        if delivered_orders:
            total_days = sum(
                (order.receive_date - order.ship_date.date()).days
                for order in delivered_orders
            )
            avg_shipping_time = total_days / len(delivered_orders) if delivered_orders else 0.0

        # 总订单数
        total_orders = db.query(DeliveryOrder).count()

        return ResponseModel(
            code=200,
            message="获取发货统计成功",
            data=DeliveryStatistics(
                pending_shipments=pending_shipments,
                shipped_today=shipped_today,
                in_transit=in_transit,
                delivered_this_week=delivered_this_week,
                on_time_shipping_rate=on_time_shipping_rate,
                avg_shipping_time=avg_shipping_time,
                total_orders=total_orders,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发货统计失败: {str(e)}")
