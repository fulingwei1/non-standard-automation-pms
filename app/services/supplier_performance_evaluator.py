# -*- coding: utf-8 -*-
"""
供应商绩效评估服务

功能:
1. 准时交货率计算
2. 质量合格率计算
3. 价格竞争力评估
4. 响应速度评分
5. 综合评分和排名
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
    SupplierPerformance,
    Vendor,
)

logger = logging.getLogger(__name__)


class SupplierPerformanceEvaluator:
    """供应商绩效评估器"""
    
    # 评级标准
    RATING_STANDARDS = {
        'A+': Decimal('90'),
        'A': Decimal('80'),
        'B': Decimal('70'),
        'C': Decimal('60'),
        'D': Decimal('0'),
    }
    
    def __init__(self, db: Session, tenant_id: int = 1):
        self.db = db
        self.tenant_id = tenant_id
    
    def evaluate_supplier(
        self,
        supplier_id: int,
        evaluation_period: str,
        weight_config: Optional[Dict[str, Decimal]] = None
    ) -> Optional[SupplierPerformance]:
        """
        评估供应商绩效
        
        Args:
            supplier_id: 供应商ID
            evaluation_period: 评估期间（YYYY-MM）
            weight_config: 权重配置
            
        Returns:
            绩效评估记录
        """
        # 验证供应商存在
        supplier = self.db.query(Vendor).get(supplier_id)
        if not supplier:
            logger.error(f"供应商 {supplier_id} 不存在")
            return None
        
        # 解析评估期间
        try:
            year, month = map(int, evaluation_period.split('-'))
            period_start = date(year, month, 1)
            
            # 计算期间结束日期
            if month == 12:
                period_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(year, month + 1, 1) - timedelta(days=1)
        except ValueError:
            logger.error(f"无效的评估期间格式: {evaluation_period}")
            return None
        
        # 默认权重配置
        if weight_config is None:
            weight_config = {
                'on_time_delivery': Decimal('30'),
                'quality': Decimal('30'),
                'price': Decimal('20'),
                'response': Decimal('20'),
            }
        
        # 检查是否已有评估记录
        existing = self.db.query(SupplierPerformance).filter(
            and_(
                SupplierPerformance.supplier_id == supplier_id,
                SupplierPerformance.evaluation_period == evaluation_period
            )
        ).first()
        
        # 查询该期间的订单
        orders = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.order_date >= period_start,
                PurchaseOrder.order_date <= period_end
            )
        ).all()
        
        if not orders:
            logger.info(f"供应商 {supplier.supplier_code} 在 {evaluation_period} 期间无订单")
            # 如果无订单，仍然创建记录但评分为0
            if existing:
                return existing
        
        # 1. 计算准时交货率
        delivery_metrics = self._calculate_delivery_metrics(orders, period_start, period_end)
        
        # 2. 计算质量合格率
        quality_metrics = self._calculate_quality_metrics(orders, period_start, period_end)
        
        # 3. 计算价格竞争力
        price_metrics = self._calculate_price_competitiveness(supplier_id, period_start, period_end)
        
        # 4. 计算响应速度
        response_metrics = self._calculate_response_speed(supplier_id, period_start, period_end)
        
        # 5. 计算综合评分
        overall_score = self._calculate_overall_score(
            delivery_metrics,
            quality_metrics,
            price_metrics,
            response_metrics,
            weight_config
        )
        
        # 确定评级
        rating = self._determine_rating(overall_score)
        
        # 统计数据
        total_orders = len(orders)
        total_amount = sum(order.total_amount or Decimal('0') for order in orders)
        
        # 创建或更新评估记录
        if existing:
            performance = existing
        else:
            performance = SupplierPerformance(
                tenant_id=self.tenant_id,
                supplier_id=supplier_id,
                supplier_code=supplier.supplier_code,
                supplier_name=supplier.supplier_name,
                evaluation_period=evaluation_period,
                period_start=period_start,
                period_end=period_end,
            )
            self.db.add(performance)
        
        # 更新数据
        performance.total_orders = total_orders
        performance.total_amount = total_amount
        
        # 准时交货
        performance.on_time_delivery_rate = delivery_metrics['on_time_rate']
        performance.on_time_orders = delivery_metrics['on_time_orders']
        performance.late_orders = delivery_metrics['late_orders']
        performance.avg_delay_days = delivery_metrics['avg_delay_days']
        
        # 质量
        performance.quality_pass_rate = quality_metrics['pass_rate']
        performance.total_received_qty = quality_metrics['total_qty']
        performance.qualified_qty = quality_metrics['qualified_qty']
        performance.rejected_qty = quality_metrics['rejected_qty']
        
        # 价格
        performance.price_competitiveness = price_metrics['competitiveness']
        performance.avg_price_vs_market = price_metrics['vs_market']
        
        # 响应
        performance.response_speed_score = response_metrics['score']
        performance.avg_response_hours = response_metrics['avg_hours']
        
        # 综合
        performance.overall_score = overall_score
        performance.rating = rating
        performance.weight_config = {k: float(v) for k, v in weight_config.items()}
        
        # 详细数据
        performance.detail_data = {
            'delivery': {k: float(v) if isinstance(v, Decimal) else v for k, v in delivery_metrics.items()},
            'quality': {k: float(v) if isinstance(v, Decimal) else v for k, v in quality_metrics.items()},
            'price': {k: float(v) if isinstance(v, Decimal) else v for k, v in price_metrics.items()},
            'response': {k: float(v) if isinstance(v, Decimal) else v for k, v in response_metrics.items()},
        }
        
        performance.status = 'CALCULATED'
        
        self.db.commit()
        self.db.refresh(performance)
        
        logger.info(
            f"供应商 {supplier.supplier_code} {evaluation_period} 期间绩效评估完成: "
            f"综合评分 {overall_score}, 等级 {rating}"
        )
        
        return performance
    
    def _calculate_delivery_metrics(
        self,
        orders: List[PurchaseOrder],
        period_start: date,
        period_end: date
    ) -> Dict:
        """计算准时交货指标"""
        if not orders:
            return {
                'on_time_rate': Decimal('0'),
                'on_time_orders': 0,
                'late_orders': 0,
                'avg_delay_days': Decimal('0'),
            }
        
        on_time_orders = 0
        late_orders = 0
        total_delay_days = Decimal('0')
        
        for order in orders:
            # 获取收货记录
            receipts = self.db.query(GoodsReceipt).filter(
                and_(
                    GoodsReceipt.order_id == order.id,
                    GoodsReceipt.receipt_date >= period_start,
                    GoodsReceipt.receipt_date <= period_end
                )
            ).all()
            
            if not receipts:
                continue
            
            # 取最早的收货日期
            receipt_date = min(r.receipt_date for r in receipts)
            
            # 对比承诺交期或要求交期
            promised_date = order.promised_date or order.required_date
            
            if promised_date:
                if receipt_date <= promised_date:
                    on_time_orders += 1
                else:
                    late_orders += 1
                    delay_days = (receipt_date - promised_date).days
                    total_delay_days += Decimal(delay_days)
        
        total_delivered = on_time_orders + late_orders
        
        if total_delivered > 0:
            on_time_rate = Decimal(on_time_orders) / Decimal(total_delivered) * Decimal('100')
            avg_delay_days = total_delay_days / Decimal(late_orders) if late_orders > 0 else Decimal('0')
        else:
            on_time_rate = Decimal('0')
            avg_delay_days = Decimal('0')
        
        return {
            'on_time_rate': on_time_rate,
            'on_time_orders': on_time_orders,
            'late_orders': late_orders,
            'avg_delay_days': avg_delay_days,
        }
    
    def _calculate_quality_metrics(
        self,
        orders: List[PurchaseOrder],
        period_start: date,
        period_end: date
    ) -> Dict:
        """计算质量合格率指标"""
        total_qty = Decimal('0')
        qualified_qty = Decimal('0')
        rejected_qty = Decimal('0')
        
        for order in orders:
            # 查询收货明细
            receipt_items = self.db.query(GoodsReceiptItem).join(
                GoodsReceipt
            ).filter(
                and_(
                    GoodsReceipt.order_id == order.id,
                    GoodsReceipt.receipt_date >= period_start,
                    GoodsReceipt.receipt_date <= period_end
                )
            ).all()
            
            for item in receipt_items:
                total_qty += item.received_qty or Decimal('0')
                qualified_qty += item.qualified_qty or Decimal('0')
                rejected_qty += item.rejected_qty or Decimal('0')
        
        if total_qty > 0:
            pass_rate = qualified_qty / total_qty * Decimal('100')
        else:
            pass_rate = Decimal('0')
        
        return {
            'pass_rate': pass_rate,
            'total_qty': total_qty,
            'qualified_qty': qualified_qty,
            'rejected_qty': rejected_qty,
        }
    
    def _calculate_price_competitiveness(
        self,
        supplier_id: int,
        period_start: date,
        period_end: date
    ) -> Dict:
        """计算价格竞争力"""
        # 获取该供应商在此期间的平均价格
        supplier_avg_price = self.db.query(
            func.avg(PurchaseOrderItem.unit_price)
        ).join(
            PurchaseOrder
        ).filter(
            and_(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.order_date >= period_start,
                PurchaseOrder.order_date <= period_end,
                PurchaseOrderItem.unit_price > 0
            )
        ).scalar()
        
        if not supplier_avg_price:
            return {
                'competitiveness': Decimal('50'),
                'vs_market': Decimal('0'),
            }
        
        supplier_avg_price = Decimal(str(supplier_avg_price))
        
        # 获取市场平均价格（所有供应商）
        market_avg_price = self.db.query(
            func.avg(PurchaseOrderItem.unit_price)
        ).join(
            PurchaseOrder
        ).filter(
            and_(
                PurchaseOrder.order_date >= period_start,
                PurchaseOrder.order_date <= period_end,
                PurchaseOrderItem.unit_price > 0
            )
        ).scalar()
        
        if not market_avg_price:
            market_avg_price = supplier_avg_price
        else:
            market_avg_price = Decimal(str(market_avg_price))
        
        # 计算相对市场价格的百分比
        if market_avg_price > 0:
            vs_market = (supplier_avg_price - market_avg_price) / market_avg_price * Decimal('100')
        else:
            vs_market = Decimal('0')
        
        # 价格竞争力评分（价格越低，评分越高）
        if vs_market <= Decimal('-20'):  # 低于市场价20%以上
            competitiveness = Decimal('100')
        elif vs_market <= Decimal('-10'):  # 低于市场价10-20%
            competitiveness = Decimal('90')
        elif vs_market <= Decimal('0'):  # 低于市场价0-10%
            competitiveness = Decimal('80')
        elif vs_market <= Decimal('10'):  # 高于市场价0-10%
            competitiveness = Decimal('60')
        elif vs_market <= Decimal('20'):  # 高于市场价10-20%
            competitiveness = Decimal('40')
        else:  # 高于市场价20%以上
            competitiveness = Decimal('20')
        
        return {
            'competitiveness': competitiveness,
            'vs_market': vs_market,
        }
    
    def _calculate_response_speed(
        self,
        supplier_id: int,
        period_start: date,
        period_end: date
    ) -> Dict:
        """计算响应速度评分"""
        # 这里简化处理，可以根据实际业务调整
        # 例如：从询价到报价的时间、从下单到确认的时间等
        
        # 查询该期间订单的平均确认时间
        orders = self.db.query(PurchaseOrder).filter(
            and_(
                PurchaseOrder.supplier_id == supplier_id,
                PurchaseOrder.order_date >= period_start,
                PurchaseOrder.order_date <= period_end,
                PurchaseOrder.submitted_at.isnot(None),
                PurchaseOrder.approved_at.isnot(None)
            )
        ).all()
        
        if not orders:
            return {
                'score': Decimal('50'),
                'avg_hours': Decimal('0'),
            }
        
        total_hours = Decimal('0')
        count = 0
        
        for order in orders:
            if order.submitted_at and order.approved_at:
                response_time = order.approved_at - order.submitted_at
                hours = Decimal(response_time.total_seconds()) / Decimal('3600')
                total_hours += hours
                count += 1
        
        if count > 0:
            avg_hours = total_hours / Decimal(count)
        else:
            avg_hours = Decimal('0')
        
        # 根据平均响应时间评分
        if avg_hours <= Decimal('4'):  # 4小时内
            score = Decimal('100')
        elif avg_hours <= Decimal('8'):  # 8小时内
            score = Decimal('90')
        elif avg_hours <= Decimal('24'):  # 24小时内
            score = Decimal('80')
        elif avg_hours <= Decimal('48'):  # 48小时内
            score = Decimal('60')
        else:
            score = max(Decimal('30'), Decimal('60') - (avg_hours - Decimal('48')) / Decimal('24') * Decimal('5'))
        
        return {
            'score': score,
            'avg_hours': avg_hours,
        }
    
    def _calculate_overall_score(
        self,
        delivery_metrics: Dict,
        quality_metrics: Dict,
        price_metrics: Dict,
        response_metrics: Dict,
        weight_config: Dict[str, Decimal]
    ) -> Decimal:
        """计算综合评分"""
        # 获取各维度评分
        delivery_score = delivery_metrics['on_time_rate']
        quality_score = quality_metrics['pass_rate']
        price_score = price_metrics['competitiveness']
        response_score = response_metrics['score']
        
        # 获取权重
        w_delivery = weight_config.get('on_time_delivery', Decimal('30'))
        w_quality = weight_config.get('quality', Decimal('30'))
        w_price = weight_config.get('price', Decimal('20'))
        w_response = weight_config.get('response', Decimal('20'))
        
        # 计算加权平均
        overall = (
            delivery_score * w_delivery / Decimal('100') +
            quality_score * w_quality / Decimal('100') +
            price_score * w_price / Decimal('100') +
            response_score * w_response / Decimal('100')
        )
        
        return overall
    
    def _determine_rating(self, score: Decimal) -> str:
        """确定评级"""
        for rating, threshold in self.RATING_STANDARDS.items():
            if score >= threshold:
                return rating
        return 'D'
    
    def get_supplier_ranking(
        self,
        evaluation_period: str,
        limit: int = 10
    ) -> List[SupplierPerformance]:
        """
        获取供应商排名
        
        Args:
            evaluation_period: 评估期间
            limit: 返回数量
            
        Returns:
            排名列表
        """
        performances = self.db.query(SupplierPerformance).filter(
            SupplierPerformance.evaluation_period == evaluation_period
        ).order_by(
            SupplierPerformance.overall_score.desc()
        ).limit(limit).all()
        
        return performances
    
    def batch_evaluate_all_suppliers(self, evaluation_period: str) -> int:
        """
        批量评估所有供应商
        
        Args:
            evaluation_period: 评估期间
            
        Returns:
            评估数量
        """
        # 获取所有活跃的供应商
        suppliers = self.db.query(Vendor).filter(
            and_(
                Vendor.status == 'ACTIVE',
                Vendor.vendor_type == 'MATERIAL'
            )
        ).all()
        
        count = 0
        for supplier in suppliers:
            try:
                result = self.evaluate_supplier(supplier.id, evaluation_period)
                if result:
                    count += 1
            except Exception as e:
                logger.error(f"评估供应商 {supplier.supplier_code} 失败: {e}")
                continue
        
        logger.info(f"批量评估完成，共评估 {count} 个供应商")
        return count
