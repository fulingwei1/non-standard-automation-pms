# -*- coding: utf-8 -*-
"""
采购智能服务层

提取自 purchase_intelligence.py 的业务逻辑
"""

import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    Material,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseSuggestion,
    SupplierPerformance,
    SupplierQuotation,
    User,
    Vendor,
    PurchaseOrderTracking,
)
from app.schemas.purchase_intelligence import (
    PurchaseSuggestionResponse,
    SupplierPerformanceResponse,
    SupplierRankingItem,
    QuotationCompareItem,
    PurchaseOrderTrackingResponse,
)
from app.services.supplier_performance_evaluator import SupplierPerformanceEvaluator

logger = logging.getLogger(__name__)


class PurchaseIntelligenceService:
    """采购智能服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 采购建议相关 ====================

    def get_purchase_suggestions(
        self,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        material_id: Optional[int] = None,
        project_id: Optional[int] = None,
        urgency_level: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[PurchaseSuggestionResponse]:
        """获取采购建议列表"""
        query = self.db.query(PurchaseSuggestion)

        if status:
            query = query.filter(PurchaseSuggestion.status == status)
        if source_type:
            query = query.filter(PurchaseSuggestion.source_type == source_type)
        if material_id:
            query = query.filter(PurchaseSuggestion.material_id == material_id)
        if project_id:
            query = query.filter(PurchaseSuggestion.project_id == project_id)
        if urgency_level:
            query = query.filter(PurchaseSuggestion.urgency_level == urgency_level)

        suggestions = (
            query.order_by(desc(PurchaseSuggestion.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        # 填充关联数据
        result = []
        for s in suggestions:
            data = PurchaseSuggestionResponse.from_orm(s)

            # 填充供应商名称
            if s.suggested_supplier_id:
                supplier = self.db.query(Vendor).get(s.suggested_supplier_id)
                if supplier:
                    data.suggested_supplier_name = supplier.supplier_name

            # 填充订单编号
            if s.purchase_order_id:
                order = self.db.query(PurchaseOrder).get(s.purchase_order_id)
                if order:
                    data.purchase_order_no = order.order_no

            result.append(data)

        return result

    def approve_purchase_suggestion(
        self,
        suggestion_id: int,
        approved: bool,
        user_id: int,
        review_note: Optional[str] = None,
        suggested_supplier_id: Optional[int] = None,
    ) -> Tuple[PurchaseSuggestion, str]:
        """批准或拒绝采购建议"""
        suggestion = self.db.query(PurchaseSuggestion).get(suggestion_id)
        if not suggestion:
            raise ValueError("采购建议不存在")

        if suggestion.status != 'PENDING':
            raise ValueError(f"当前状态 {suggestion.status} 不允许审批")

        if approved:
            suggestion.status = 'APPROVED'
            message = "采购建议已批准"
        else:
            suggestion.status = 'REJECTED'
            message = "采购建议已拒绝"

        suggestion.reviewed_by = user_id
        suggestion.reviewed_at = datetime.now()
        suggestion.review_note = review_note

        if suggested_supplier_id:
            suggestion.suggested_supplier_id = suggested_supplier_id

        self.db.commit()

        return suggestion, message

    # ==================== 供应商绩效相关 ====================

    def get_supplier_performance(
        self,
        supplier_id: int,
        evaluation_period: Optional[str] = None,
        limit: int = 12,
    ) -> List[SupplierPerformanceResponse]:
        """获取供应商绩效记录"""
        query = self.db.query(SupplierPerformance).filter(
            SupplierPerformance.supplier_id == supplier_id
        )

        if evaluation_period:
            query = query.filter(SupplierPerformance.evaluation_period == evaluation_period)

        performances = query.order_by(desc(SupplierPerformance.period_end)).limit(limit).all()

        return [SupplierPerformanceResponse.from_orm(p) for p in performances]

    def evaluate_supplier_performance(
        self,
        supplier_id: int,
        evaluation_period: str,
        weight_config: Optional[Dict] = None,
    ) -> SupplierPerformance:
        """触发供应商绩效评估"""
        # 验证供应商存在
        supplier = self.db.query(Vendor).get(supplier_id)
        if not supplier:
            raise ValueError("供应商不存在")

        # 执行评估
        evaluator = SupplierPerformanceEvaluator(self.db)
        performance = evaluator.evaluate_supplier(
            supplier_id=supplier_id,
            evaluation_period=evaluation_period,
            weight_config=weight_config,
        )

        if not performance:
            raise RuntimeError("绩效评估失败")

        return performance

    def get_supplier_ranking(
        self,
        evaluation_period: str,
        limit: int = 20,
    ) -> Tuple[List[SupplierRankingItem], int]:
        """获取供应商排名"""
        performances = (
            self.db.query(SupplierPerformance)
            .filter(SupplierPerformance.evaluation_period == evaluation_period)
            .order_by(desc(SupplierPerformance.overall_score))
            .limit(limit)
            .all()
        )

        rankings = []
        for idx, p in enumerate(performances, start=1):
            rankings.append(
                SupplierRankingItem(
                    supplier_id=p.supplier_id,
                    supplier_code=p.supplier_code,
                    supplier_name=p.supplier_name,
                    overall_score=p.overall_score,
                    rating=p.rating,
                    on_time_delivery_rate=p.on_time_delivery_rate,
                    quality_pass_rate=p.quality_pass_rate,
                    price_competitiveness=p.price_competitiveness,
                    response_speed_score=p.response_speed_score,
                    total_orders=p.total_orders,
                    total_amount=p.total_amount,
                    evaluation_period=p.evaluation_period,
                    rank=idx,
                )
            )

        return rankings, len(rankings)

    # ==================== 报价相关 ====================

    def create_supplier_quotation(
        self,
        supplier_id: int,
        material_id: int,
        unit_price: float,
        currency: str,
        min_order_qty: int,
        lead_time_days: int,
        valid_from: date,
        valid_to: date,
        user_id: int,
        payment_terms: Optional[str] = None,
        warranty_period: Optional[str] = None,
        tax_rate: Optional[float] = None,
        remark: Optional[str] = None,
    ) -> SupplierQuotation:
        """创建供应商报价"""
        # 验证供应商
        supplier = self.db.query(Vendor).get(supplier_id)
        if not supplier:
            raise ValueError("供应商不存在")

        # 验证物料
        material = self.db.query(Material).get(material_id)
        if not material:
            raise ValueError("物料不存在")

        # 生成报价单号
        quotation_no = self._generate_quotation_no()

        # 创建报价
        quotation = SupplierQuotation(
            quotation_no=quotation_no,
            supplier_id=supplier_id,
            material_id=material_id,
            material_code=material.material_code,
            material_name=material.material_name,
            specification=material.specification,
            unit_price=unit_price,
            currency=currency,
            min_order_qty=min_order_qty,
            lead_time_days=lead_time_days,
            valid_from=valid_from,
            valid_to=valid_to,
            payment_terms=payment_terms,
            warranty_period=warranty_period,
            tax_rate=tax_rate,
            remark=remark,
            created_by=user_id,
        )

        self.db.add(quotation)
        self.db.commit()
        self.db.refresh(quotation)

        return quotation

    def compare_quotations(
        self,
        material_id: int,
        supplier_ids: Optional[List[int]] = None,
    ) -> Tuple[Material, List[QuotationCompareItem], Optional[int], Optional[int], str]:
        """比较供应商报价"""
        # 验证物料
        material = self.db.query(Material).get(material_id)
        if not material:
            raise ValueError("物料不存在")

        # 查询报价
        query = self.db.query(SupplierQuotation).filter(
            and_(
                SupplierQuotation.material_id == material_id,
                SupplierQuotation.status == 'ACTIVE',
                SupplierQuotation.valid_to >= date.today(),
            )
        )

        if supplier_ids:
            query = query.filter(SupplierQuotation.supplier_id.in_(supplier_ids))

        quotations = query.order_by(SupplierQuotation.unit_price).all()

        if not quotations:
            return material, [], None, None, ""

        # 获取供应商绩效
        supplier_performances = {}
        for q in quotations:
            latest_perf = (
                self.db.query(SupplierPerformance)
                .filter(SupplierPerformance.supplier_id == q.supplier_id)
                .order_by(desc(SupplierPerformance.period_end))
                .first()
            )

            if latest_perf:
                supplier_performances[q.supplier_id] = {
                    'score': latest_perf.overall_score,
                    'rating': latest_perf.rating,
                }

        # 构建比较数据
        compare_items = []
        for q in quotations:
            supplier = self.db.query(Vendor).get(q.supplier_id)
            perf = supplier_performances.get(q.supplier_id, {})

            compare_items.append(
                QuotationCompareItem(
                    quotation_id=q.id,
                    quotation_no=q.quotation_no,
                    supplier_id=q.supplier_id,
                    supplier_code=supplier.supplier_code if supplier else '',
                    supplier_name=supplier.supplier_name if supplier else '',
                    unit_price=q.unit_price,
                    currency=q.currency,
                    min_order_qty=q.min_order_qty,
                    lead_time_days=q.lead_time_days,
                    valid_from=q.valid_from,
                    valid_to=q.valid_to,
                    payment_terms=q.payment_terms,
                    tax_rate=q.tax_rate,
                    is_selected=q.is_selected,
                    performance_score=perf.get('score'),
                    performance_rating=perf.get('rating'),
                )
            )

        # 确定最优价格和推荐供应商
        best_price_supplier_id = quotations[0].supplier_id if quotations else None

        # 综合价格和绩效推荐
        recommended_supplier_id = None
        max_combined_score = 0

        for item in compare_items:
            # 综合评分 = 价格评分(40%) + 绩效评分(60%)
            price_score = (
                (1 - (item.unit_price - quotations[0].unit_price) / quotations[0].unit_price)
                * 100
            )
            perf_score = float(item.performance_score) if item.performance_score else 50

            combined_score = price_score * 0.4 + perf_score * 0.6

            if combined_score > max_combined_score:
                max_combined_score = combined_score
                recommended_supplier_id = item.supplier_id

        recommendation_reason = "基于价格和供应商绩效综合评估推荐"

        return (
            material,
            compare_items,
            best_price_supplier_id,
            recommended_supplier_id,
            recommendation_reason,
        )

    # ==================== 订单跟踪相关 ====================

    def get_purchase_order_tracking(
        self,
        order_id: int,
    ) -> List[PurchaseOrderTrackingResponse]:
        """获取采购订单跟踪记录"""
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError("采购订单不存在")

        trackings = (
            self.db.query(PurchaseOrderTracking)
            .filter(PurchaseOrderTracking.order_id == order_id)
            .order_by(PurchaseOrderTracking.event_time.desc())
            .all()
        )

        result = []
        for t in trackings:
            data = PurchaseOrderTrackingResponse.from_orm(t)

            if t.operator_id:
                operator = self.db.query(User).get(t.operator_id)
                if operator:
                    data.operator_name = operator.username

            result.append(data)

        return result

    def receive_purchase_order(
        self,
        order_id: int,
        receipt_date: date,
        items: List[Dict],
        user_id: int,
        delivery_note_no: Optional[str] = None,
        logistics_company: Optional[str] = None,
        tracking_no: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> Tuple[GoodsReceipt, str]:
        """收货确认"""
        order = self.db.query(PurchaseOrder).get(order_id)
        if not order:
            raise ValueError("采购订单不存在")

        # 生成收货单号
        receipt_no = self._generate_receipt_no()

        # 创建收货单
        receipt = GoodsReceipt(
            receipt_no=receipt_no,
            order_id=order_id,
            supplier_id=order.supplier_id,
            receipt_date=receipt_date,
            delivery_note_no=delivery_note_no,
            logistics_company=logistics_company,
            tracking_no=tracking_no,
            remark=remark,
            status='PENDING',
            created_by=user_id,
        )

        self.db.add(receipt)
        self.db.flush()

        # 创建收货明细
        for item_data in items:
            order_item = self.db.query(PurchaseOrderItem).get(item_data['order_item_id'])
            if not order_item:
                continue

            receipt_item = GoodsReceiptItem(
                receipt_id=receipt.id,
                order_item_id=order_item.id,
                material_code=order_item.material_code,
                material_name=order_item.material_name,
                delivery_qty=item_data['delivery_qty'],
                received_qty=item_data.get('received_qty', item_data['delivery_qty']),
                remark=item_data.get('remark'),
            )

            self.db.add(receipt_item)

            # 更新订单项收货数量
            order_item.received_qty = (
                order_item.received_qty or 0
            ) + receipt_item.received_qty

        # 创建跟踪记录
        tracking = PurchaseOrderTracking(
            order_id=order_id,
            order_no=order.order_no,
            event_type='RECEIVED',
            event_time=datetime.now(),
            event_description=f"收货确认，收货单号：{receipt_no}",
            new_status='RECEIVED',
            tracking_no=tracking_no,
            logistics_company=logistics_company,
            operator_id=user_id,
        )

        self.db.add(tracking)
        self.db.commit()

        return receipt, receipt_no

    def create_order_from_suggestion(
        self,
        suggestion_id: int,
        user_id: int,
        supplier_id: Optional[int] = None,
        required_date: Optional[date] = None,
        payment_terms: Optional[str] = None,
        delivery_address: Optional[str] = None,
        remark: Optional[str] = None,
    ) -> Tuple[PurchaseOrder, str]:
        """从采购建议创建采购订单"""
        suggestion = self.db.query(PurchaseSuggestion).get(suggestion_id)
        if not suggestion:
            raise ValueError("采购建议不存在")

        if suggestion.status != 'APPROVED':
            raise ValueError("只有已批准的建议才能创建订单")

        if suggestion.purchase_order_id:
            raise ValueError("该建议已创建订单")

        # 确定供应商
        final_supplier_id = supplier_id or suggestion.suggested_supplier_id
        if not final_supplier_id:
            raise ValueError("未指定供应商")

        supplier = self.db.query(Vendor).get(final_supplier_id)
        if not supplier:
            raise ValueError("供应商不存在")

        # 生成订单编号
        order_no = self._generate_purchase_order_no()

        # 计算金额
        unit_price = suggestion.estimated_unit_price or 0
        amount = suggestion.suggested_qty * unit_price
        tax_amount = (
            amount * (suggestion.material.standard_price or 13) / 100
            if suggestion.material
            else 0
        )
        amount_with_tax = amount + tax_amount

        # 创建采购订单
        order = PurchaseOrder(
            order_no=order_no,
            supplier_id=final_supplier_id,
            project_id=suggestion.project_id,
            order_type='NORMAL',
            order_title=f"采购建议转订单 - {suggestion.material_name}",
            total_amount=amount,
            tax_amount=tax_amount,
            amount_with_tax=amount_with_tax,
            order_date=date.today(),
            required_date=required_date or suggestion.required_date,
            status='DRAFT',
            payment_terms=payment_terms,
            delivery_address=delivery_address,
            remark=remark,
            created_by=user_id,
        )

        self.db.add(order)
        self.db.flush()

        # 创建订单明细
        order_item = PurchaseOrderItem(
            order_id=order.id,
            item_no=1,
            material_id=suggestion.material_id,
            material_code=suggestion.material_code,
            material_name=suggestion.material_name,
            specification=suggestion.specification,
            unit=suggestion.unit,
            quantity=suggestion.suggested_qty,
            unit_price=unit_price,
            amount=amount,
            tax_amount=tax_amount,
            amount_with_tax=amount_with_tax,
            required_date=required_date or suggestion.required_date,
            status='PENDING',
        )

        self.db.add(order_item)

        # 更新建议状态
        suggestion.purchase_order_id = order.id
        suggestion.status = 'ORDERED'
        suggestion.ordered_at = datetime.now()

        self.db.commit()

        return order, order_no

    # ==================== 辅助方法 ====================

    def _generate_quotation_no(self) -> str:
        """生成报价单号"""
        prefix = 'QT'
        date_str = datetime.now().strftime('%Y%m%d')

        latest = (
            self.db.query(SupplierQuotation)
            .filter(SupplierQuotation.quotation_no.like(f'{prefix}{date_str}%'))
            .order_by(desc(SupplierQuotation.quotation_no))
            .first()
        )

        if latest:
            last_seq = int(latest.quotation_no[-4:])
            seq = last_seq + 1
        else:
            seq = 1

        return f'{prefix}{date_str}{seq:04d}'

    def _generate_receipt_no(self) -> str:
        """生成收货单号"""
        prefix = 'GR'
        date_str = datetime.now().strftime('%Y%m%d')

        latest = (
            self.db.query(GoodsReceipt)
            .filter(GoodsReceipt.receipt_no.like(f'{prefix}{date_str}%'))
            .order_by(desc(GoodsReceipt.receipt_no))
            .first()
        )

        if latest:
            last_seq = int(latest.receipt_no[-4:])
            seq = last_seq + 1
        else:
            seq = 1

        return f'{prefix}{date_str}{seq:04d}'

    def _generate_purchase_order_no(self) -> str:
        """生成采购订单编号"""
        prefix = 'PO'
        date_str = datetime.now().strftime('%Y%m%d')

        latest = (
            self.db.query(PurchaseOrder)
            .filter(PurchaseOrder.order_no.like(f'{prefix}{date_str}%'))
            .order_by(desc(PurchaseOrder.order_no))
            .first()
        )

        if latest:
            last_seq = int(latest.order_no[-4:])
            seq = last_seq + 1
        else:
            seq = 1

        return f'{prefix}{date_str}{seq:04d}'
