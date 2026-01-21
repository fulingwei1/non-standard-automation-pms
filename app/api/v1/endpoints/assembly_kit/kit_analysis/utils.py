# -*- coding: utf-8 -*-
"""
齐套分析 - 工具函数
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import Material, ShortageAlertRule

logger = logging.getLogger(__name__)


def generate_readiness_no() -> str:
    """生成齐套分析单号"""
    now = datetime.now()
    return f"KR{now.strftime('%Y%m%d%H%M%S')}"


def calculate_available_qty(
    db: Session,
    material_id: int,
    check_date: date
) -> Tuple[Decimal, Decimal, Decimal, Decimal]:
    """计算物料可用数量

    返回: (库存数量, 已分配数量, 在途数量, 可用数量)
    """
    from app.models import PurchaseOrder, PurchaseOrderItem

    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        return (Decimal(0), Decimal(0), Decimal(0), Decimal(0))

    # 库存数量(简化处理，实际应从库存表获取)
    stock_qty = getattr(material, 'stock_qty', Decimal(0)) or Decimal(0)

    # 已分配数量(简化处理)
    allocated_qty = Decimal(0)

    # 在途数量(已采购未到货，预计在check_date前到货)
    in_transit_qty = Decimal(0)
    try:
        in_transit = db.query(func.sum(PurchaseOrderItem.quantity)).join(
            PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id
        ).filter(
            PurchaseOrderItem.material_id == material_id,
            PurchaseOrder.status.in_(['approved', 'partial_received']),
            PurchaseOrder.expected_date <= check_date
        ).scalar()
        in_transit_qty = Decimal(in_transit or 0)
    except Exception:
        logger.debug("查询在途数量失败，已忽略", exc_info=True)

    available = max(Decimal(0), stock_qty - allocated_qty + in_transit_qty)
    return (stock_qty, allocated_qty, in_transit_qty, available)


def calculate_estimated_ready_date(
    db: Session,
    blocking_items: List[Dict],
    check_date: date
) -> Optional[date]:
    """
    计算预计完全齐套日期

    基于阻塞物料的预计到货日期，取最晚的日期
    """
    from app.models import PurchaseOrder, PurchaseOrderItem

    if not blocking_items:
        return None

    latest_date = None

    for item in blocking_items:
        material_id = item.get("material_id")
        shortage_qty = item.get("shortage_qty", Decimal(0))
        expected_arrival = item.get("expected_arrival")

        # 如果缺料明细中已有预计到货日期，直接使用
        if expected_arrival:
            if latest_date is None or expected_arrival > latest_date:
                latest_date = expected_arrival
            continue

        # 否则从采购订单查找
        if not material_id or shortage_qty <= 0:
            continue

        try:
            po_items = db.query(PurchaseOrderItem).join(
                PurchaseOrder, PurchaseOrderItem.po_id == PurchaseOrder.id
            ).filter(
                PurchaseOrderItem.material_id == material_id,
                PurchaseOrder.status.in_(['approved', 'partial_received']),
                or_(
                    PurchaseOrder.promised_date.isnot(None),
                    PurchaseOrder.required_date.isnot(None)
                )
            ).order_by(
                PurchaseOrder.promised_date.desc(),
                PurchaseOrder.required_date.desc()
            ).all()
        except Exception:
            logger.debug("查询采购订单失败，已忽略", exc_info=True)
            po_items = []

        for po_item in po_items:
            if po_item.order:
                # 优先使用承诺交期，其次使用要求交期
                expected_date = po_item.order.promised_date or po_item.order.required_date
                if expected_date:
                    if latest_date is None or expected_date > latest_date:
                        latest_date = expected_date
                    break

    return latest_date


def determine_alert_level(
    db: Session,
    is_blocking: bool,
    shortage_rate: Decimal,
    days_to_required: int
) -> str:
    """确定预警级别"""
    rules = db.query(ShortageAlertRule).filter(
        ShortageAlertRule.is_active == True
    ).order_by(ShortageAlertRule.days_before_required).all()

    for rule in rules:
        if rule.only_blocking and not is_blocking:
            continue
        if shortage_rate < (rule.min_shortage_rate or 0):
            continue
        if days_to_required <= rule.days_before_required:
            return rule.alert_level

    return "L4"  # 默认常规预警
