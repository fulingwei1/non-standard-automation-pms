# -*- coding: utf-8 -*-
"""
装配齐套分析优化服务
提供齐套分析结果的优化建议和自动优化功能
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import (
    BomItem,
    Material,
    MaterialReadiness,
    PurchaseOrder,
    PurchaseOrderItem,
    ShortageDetail,
)

logger = logging.getLogger(__name__)


class AssemblyKitOptimizer:
    """装配齐套分析优化服务"""

    @classmethod
    def optimize_estimated_ready_date(
        cls,
        db: Session,
        readiness: MaterialReadiness
    ) -> Optional[date]:
        """
        优化预计齐套日期

        通过以下方式优化：
        1. 检查是否可以提前采购
        2. 检查是否有替代物料
        3. 检查是否可以调整采购优先级
        """
        # 获取阻塞物料
        blocking_shortages = db.query(ShortageDetail).filter(
            ShortageDetail.readiness_id == readiness.id,
            ShortageDetail.is_blocking,
            ShortageDetail.shortage_qty > 0
        ).all()

        if not blocking_shortages:
            return readiness.estimated_ready_date

        # 分析每个阻塞物料的优化可能性
        optimized_dates = []

        for shortage in blocking_shortages:
            # 1. 检查是否有在途采购订单可以提前
            optimized_date = cls._optimize_by_purchase_order(
                db, shortage
            )
            if optimized_date:
                optimized_dates.append(optimized_date)

            # 2. 检查是否有替代物料
            substitute_date = cls._optimize_by_substitute(
                db, shortage
            )
            if substitute_date:
                optimized_dates.append(substitute_date)

        # 取最早的优化日期
        if optimized_dates:
            return min(optimized_dates)

        return readiness.estimated_ready_date

    @classmethod
    def _optimize_by_purchase_order(
        cls,
        db: Session,
        shortage: ShortageDetail
    ) -> Optional[date]:
        """通过采购订单优化（检查是否可以加急）"""
        if not shortage.material_id:
            return None

        # 查找该物料的采购订单
        po_items = db.query(PurchaseOrderItem).join(
            PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id
        ).filter(
            PurchaseOrderItem.material_id == shortage.material_id,
            PurchaseOrder.status.in_(['APPROVED', 'PARTIAL_RECEIVED']),
            PurchaseOrder.promised_date.isnot(None)
        ).order_by(PurchaseOrder.promised_date.asc()).all()

        if not po_items:
            return None

        # 检查是否可以提前（简化：如果承诺交期可以提前3天，返回优化后的日期）
        earliest_date = po_items[0].order.promised_date
        if earliest_date and earliest_date > date.today():
            # 假设可以提前3天
            optimized = earliest_date - timedelta(days=3)
            if optimized >= date.today():
                return optimized

        return None

    @classmethod
    def _optimize_by_substitute(
        cls,
        db: Session,
        shortage: ShortageDetail
    ) -> Optional[date]:
        """通过替代物料优化"""
        if not shortage.material_id:
            return None

        # 检查BOM项是否有替代物料配置
        bom_item = db.query(BomItem).filter(
            BomItem.id == shortage.bom_item_id
        ).first()

        if not bom_item:
            return None

        # 检查装配属性中的替代物料
        from app.models import BomItemAssemblyAttrs
        attr = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id,
            BomItemAssemblyAttrs.has_substitute
        ).first()

        if not attr or not attr.substitute_material_ids:
            return None

        # 检查替代物料的库存和采购情况
        import json
        try:
            substitute_ids = json.loads(attr.substitute_material_ids)
            if not isinstance(substitute_ids, list):
                return None

            for sub_material_id in substitute_ids:
                material = db.query(Material).filter(
                    Material.id == sub_material_id
                ).first()

                if not material:
                    continue

                # 检查库存
                stock_qty = getattr(material, 'current_stock', Decimal(0)) or Decimal(0)
                if stock_qty >= shortage.shortage_qty:
                    # 有足够库存，可以立即使用
                    return date.today()

                # 检查采购订单
                po_items = db.query(PurchaseOrderItem).join(
                    PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id
                ).filter(
                    PurchaseOrderItem.material_id == sub_material_id,
                    PurchaseOrder.status.in_(['APPROVED', 'PARTIAL_RECEIVED']),
                    PurchaseOrder.promised_date.isnot(None)
                ).order_by(PurchaseOrder.promised_date.asc()).first()

                if po_items and po_items.order.promised_date:
                    return po_items.order.promised_date
        except Exception:
            logger.debug("优化预计齐套日期失败，已忽略", exc_info=True)

        return None

    @classmethod
    def generate_optimization_suggestions(
        cls,
        db: Session,
        readiness: MaterialReadiness
    ) -> List[Dict]:
        """
        生成优化建议

        返回优化建议列表，包括：
        - 提前采购建议
        - 替代物料建议
        - 调整优先级建议
        """
        suggestions = []

        # 获取阻塞物料
        blocking_shortages = db.query(ShortageDetail).filter(
            ShortageDetail.readiness_id == readiness.id,
            ShortageDetail.is_blocking,
            ShortageDetail.shortage_qty > 0
        ).all()

        for shortage in blocking_shortages:
            # 1. 检查是否可以提前采购
            po_suggestion = cls._suggest_expedite_purchase(db, shortage)
            if po_suggestion:
                suggestions.append(po_suggestion)

            # 2. 检查替代物料
            substitute_suggestion = cls._suggest_substitute(db, shortage)
            if substitute_suggestion:
                suggestions.append(substitute_suggestion)

            # 3. 检查是否可以调整优先级
            priority_suggestion = cls._suggest_priority_adjustment(db, shortage)
            if priority_suggestion:
                suggestions.append(priority_suggestion)

        return suggestions

    @classmethod
    def _suggest_expedite_purchase(
        cls,
        db: Session,
        shortage: ShortageDetail
    ) -> Optional[Dict]:
        """建议加急采购"""
        if not shortage.material_id:
            return None

        # 查找采购订单
        po_items = db.query(PurchaseOrderItem).join(
            PurchaseOrder, PurchaseOrderItem.order_id == PurchaseOrder.id
        ).filter(
            PurchaseOrderItem.material_id == shortage.material_id,
            PurchaseOrder.status == 'APPROVED',
            PurchaseOrder.promised_date.isnot(None),
            PurchaseOrder.promised_date > shortage.required_date
        ).first()

        if po_items:
            delay_days = (po_items.order.promised_date - shortage.required_date).days
            return {
                'type': 'EXPEDITE_PURCHASE',
                'material_code': shortage.material_code,
                'material_name': shortage.material_name,
                'purchase_order_no': po_items.order.order_no,
                'current_promised_date': po_items.order.promised_date.isoformat(),
                'required_date': shortage.required_date.isoformat() if shortage.required_date else None,
                'delay_days': delay_days,
                'suggestion': f'建议将采购订单 {po_items.order.order_no} 的交期提前 {delay_days} 天',
                'priority': 'HIGH' if delay_days > 7 else 'MEDIUM'
            }

        return None

    @classmethod
    def _suggest_substitute(
        cls,
        db: Session,
        shortage: ShortageDetail
    ) -> Optional[Dict]:
        """建议使用替代物料"""
        bom_item = db.query(BomItem).filter(
            BomItem.id == shortage.bom_item_id
        ).first()

        if not bom_item:
            return None

        from app.models import BomItemAssemblyAttrs
        attr = db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_item_id == bom_item.id,
            BomItemAssemblyAttrs.has_substitute
        ).first()

        if not attr or not attr.substitute_material_ids:
            return None

        import json
        try:
            substitute_ids = json.loads(attr.substitute_material_ids)
            if not isinstance(substitute_ids, list):
                return None

            available_substitutes = []
            for sub_id in substitute_ids:
                material = db.query(Material).filter(Material.id == sub_id).first()
                if material:
                    stock_qty = getattr(material, 'current_stock', Decimal(0)) or Decimal(0)
                    if stock_qty >= shortage.shortage_qty:
                        available_substitutes.append({
                            'material_code': material.material_code,
                            'material_name': material.material_name,
                            'available_qty': float(stock_qty)
                        })

            if available_substitutes:
                return {
                    'type': 'USE_SUBSTITUTE',
                    'material_code': shortage.material_code,
                    'material_name': shortage.material_name,
                    'shortage_qty': float(shortage.shortage_qty),
                    'substitutes': available_substitutes,
                    'suggestion': f'建议使用替代物料，有 {len(available_substitutes)} 个替代方案可用',
                    'priority': 'HIGH'
                }
        except Exception:
            logger.debug("生成替代物料建议失败，已忽略", exc_info=True)

        return None

    @classmethod
    def _suggest_priority_adjustment(
        cls,
        db: Session,
        shortage: ShortageDetail
    ) -> Optional[Dict]:
        """建议调整采购优先级"""
        if not shortage.material_id or not shortage.purchase_order_id:
            return None

        po = db.query(PurchaseOrder).filter(
            PurchaseOrder.id == shortage.purchase_order_id
        ).first()

        if not po:
            return None

        # 检查是否紧急（距需求日期小于7天）
        if shortage.required_date:
            days_until_required = (shortage.required_date - date.today()).days
            if days_until_required < 7:
                return {
                    'type': 'ADJUST_PRIORITY',
                    'material_code': shortage.material_code,
                    'material_name': shortage.material_name,
                    'purchase_order_no': po.order_no,
                    'days_until_required': days_until_required,
                    'suggestion': f'该物料距需求日期仅 {days_until_required} 天，建议提高采购优先级',
                    'priority': 'HIGH' if days_until_required < 3 else 'MEDIUM'
                }

        return None
