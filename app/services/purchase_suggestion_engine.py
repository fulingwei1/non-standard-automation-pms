# -*- coding: utf-8 -*-
"""
智能采购建议引擎

功能:
1. 基于缺料预警生成采购建议
2. 基于安全库存生成采购建议  
3. 基于历史消耗预测生成采购建议
4. AI推荐最佳供应商
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models import (
    Material,
    MaterialShortage,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseSuggestion,
    SupplierPerformance,
    Vendor,
)

logger = logging.getLogger(__name__)


class PurchaseSuggestionEngine:
    """智能采购建议引擎"""
    
    def __init__(self, db: Session, tenant_id: int = 1):
        self.db = db
        self.tenant_id = tenant_id
    
    def generate_from_shortages(
        self, 
        project_id: Optional[int] = None,
        min_urgency: str = "NORMAL"
    ) -> List[PurchaseSuggestion]:
        """
        基于缺料预警生成采购建议
        
        Args:
            project_id: 项目ID（可选）
            min_urgency: 最低紧急程度
            
        Returns:
            生成的采购建议列表
        """
        # 查询未解决的缺料记录
        query = self.db.query(MaterialShortage).filter(
            MaterialShortage.status.in_(['OPEN', 'ACKNOWLEDGED'])
        )
        
        if project_id:
            query = query.filter(MaterialShortage.project_id == project_id)
        
        shortages = query.all()
        suggestions = []
        
        for shortage in shortages:
            # 检查是否已有建议
            existing = self.db.query(PurchaseSuggestion).filter(
                and_(
                    PurchaseSuggestion.source_type == 'SHORTAGE',
                    PurchaseSuggestion.source_id == shortage.id,
                    PurchaseSuggestion.status.in_(['PENDING', 'APPROVED'])
                )
            ).first()
            
            if existing:
                logger.info(f"缺料 {shortage.id} 已有建议 {existing.suggestion_no}")
                continue
            
            # 获取物料信息
            material = self.db.query(Material).get(shortage.material_id)
            if not material:
                logger.warning(f"物料 {shortage.material_id} 不存在")
                continue
            
            # 确定紧急程度
            urgency = self._determine_urgency(shortage)
            
            # 推荐供应商
            supplier_id, confidence, reason, alternatives = self._recommend_supplier(material.id)
            
            # 预估价格
            unit_price = material.last_price or material.standard_price
            total_amount = shortage.shortage_qty * unit_price if unit_price else None
            
            # 创建建议
            suggestion = PurchaseSuggestion(
                tenant_id=self.tenant_id,
                suggestion_no=self._generate_suggestion_no(),
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                unit=material.unit,
                suggested_qty=shortage.shortage_qty,
                current_stock=material.current_stock,
                safety_stock=material.safety_stock,
                source_type='SHORTAGE',
                source_id=shortage.id,
                project_id=shortage.project_id,
                required_date=shortage.required_date,
                urgency_level=urgency,
                suggested_supplier_id=supplier_id,
                ai_confidence=confidence,
                recommendation_reason=reason,
                alternative_suppliers=alternatives,
                estimated_unit_price=unit_price,
                estimated_total_amount=total_amount,
                status='PENDING',
            )
            
            self.db.add(suggestion)
            suggestions.append(suggestion)
        
        self.db.commit()
        logger.info(f"基于缺料生成 {len(suggestions)} 条采购建议")
        return suggestions
    
    def generate_from_safety_stock(self) -> List[PurchaseSuggestion]:
        """
        基于安全库存生成采购建议
        
        Returns:
            生成的采购建议列表
        """
        # 查询当前库存低于安全库存的物料
        materials = self.db.query(Material).filter(
            and_(
                Material.is_active == True,
                Material.safety_stock > 0,
                Material.current_stock < Material.safety_stock
            )
        ).all()
        
        suggestions = []
        
        for material in materials:
            # 检查是否已有建议
            existing = self.db.query(PurchaseSuggestion).filter(
                and_(
                    PurchaseSuggestion.material_id == material.id,
                    PurchaseSuggestion.source_type == 'SAFETY_STOCK',
                    PurchaseSuggestion.status.in_(['PENDING', 'APPROVED'])
                )
            ).first()
            
            if existing:
                continue
            
            # 计算建议采购数量（补充到安全库存的1.2倍）
            shortage_qty = material.safety_stock - material.current_stock
            suggested_qty = max(shortage_qty * Decimal('1.2'), material.min_order_qty)
            
            # 推荐供应商
            supplier_id, confidence, reason, alternatives = self._recommend_supplier(material.id)
            
            # 预估价格
            unit_price = material.last_price or material.standard_price
            total_amount = suggested_qty * unit_price if unit_price else None
            
            # 预计交期（当前日期 + 采购周期）
            required_date = date.today() + timedelta(days=material.lead_time_days or 7)
            
            # 创建建议
            suggestion = PurchaseSuggestion(
                tenant_id=self.tenant_id,
                suggestion_no=self._generate_suggestion_no(),
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                unit=material.unit,
                suggested_qty=suggested_qty,
                current_stock=material.current_stock,
                safety_stock=material.safety_stock,
                source_type='SAFETY_STOCK',
                required_date=required_date,
                urgency_level='NORMAL',
                suggested_supplier_id=supplier_id,
                ai_confidence=confidence,
                recommendation_reason=reason,
                alternative_suppliers=alternatives,
                estimated_unit_price=unit_price,
                estimated_total_amount=total_amount,
                status='PENDING',
            )
            
            self.db.add(suggestion)
            suggestions.append(suggestion)
        
        self.db.commit()
        logger.info(f"基于安全库存生成 {len(suggestions)} 条采购建议")
        return suggestions
    
    def generate_from_forecast(
        self,
        material_id: int,
        forecast_months: int = 3
    ) -> Optional[PurchaseSuggestion]:
        """
        基于历史消耗预测生成采购建议
        
        Args:
            material_id: 物料ID
            forecast_months: 预测月份数
            
        Returns:
            生成的采购建议（如果需要）
        """
        material = self.db.query(Material).get(material_id)
        if not material:
            return None
        
        # 计算历史平均消耗
        avg_monthly_consumption = self._calculate_avg_consumption(material_id, months=6)
        
        if not avg_monthly_consumption or avg_monthly_consumption <= 0:
            logger.info(f"物料 {material.material_code} 无历史消耗数据")
            return None
        
        # 预测未来需求
        forecast_demand = avg_monthly_consumption * forecast_months
        
        # 计算当前可用库存
        available_stock = material.current_stock
        
        # 如果预测需求大于可用库存，生成建议
        if forecast_demand > available_stock:
            suggested_qty = forecast_demand - available_stock
            
            # 检查是否已有建议
            existing = self.db.query(PurchaseSuggestion).filter(
                and_(
                    PurchaseSuggestion.material_id == material.id,
                    PurchaseSuggestion.source_type == 'FORECAST',
                    PurchaseSuggestion.status.in_(['PENDING', 'APPROVED'])
                )
            ).first()
            
            if existing:
                return None
            
            # 推荐供应商
            supplier_id, confidence, reason, alternatives = self._recommend_supplier(material.id)
            
            # 预估价格
            unit_price = material.last_price or material.standard_price
            total_amount = suggested_qty * unit_price if unit_price else None
            
            # 预计交期
            required_date = date.today() + timedelta(days=30)
            
            # 创建建议
            suggestion = PurchaseSuggestion(
                tenant_id=self.tenant_id,
                suggestion_no=self._generate_suggestion_no(),
                material_id=material.id,
                material_code=material.material_code,
                material_name=material.material_name,
                specification=material.specification,
                unit=material.unit,
                suggested_qty=suggested_qty,
                current_stock=material.current_stock,
                safety_stock=material.safety_stock,
                source_type='FORECAST',
                required_date=required_date,
                urgency_level='NORMAL',
                suggested_supplier_id=supplier_id,
                ai_confidence=confidence,
                recommendation_reason=reason,
                alternative_suppliers=alternatives,
                estimated_unit_price=unit_price,
                estimated_total_amount=total_amount,
                status='PENDING',
            )
            
            self.db.add(suggestion)
            self.db.commit()
            
            logger.info(f"基于预测为物料 {material.material_code} 生成采购建议")
            return suggestion
        
        return None
    
    def _recommend_supplier(
        self,
        material_id: int,
        weight_config: Optional[Dict[str, Decimal]] = None
    ) -> Tuple[Optional[int], Optional[Decimal], Optional[Dict], Optional[List]]:
        """
        AI推荐最佳供应商
        
        Args:
            material_id: 物料ID
            weight_config: 权重配置
            
        Returns:
            (supplier_id, confidence, reason, alternatives)
        """
        if weight_config is None:
            weight_config = {
                'performance': Decimal('40'),
                'price': Decimal('30'),
                'delivery': Decimal('20'),
                'history': Decimal('10'),
            }
        
        # 获取物料的所有供应商
        from app.models import MaterialSupplier
        
        material_suppliers = self.db.query(MaterialSupplier).filter(
            and_(
                MaterialSupplier.material_id == material_id,
                MaterialSupplier.is_active == True
            )
        ).all()
        
        if not material_suppliers:
            return None, None, None, None
        
        # 评分每个供应商
        supplier_scores = []
        
        for ms in material_suppliers:
            score_data = self._calculate_supplier_score(
                ms.supplier_id,
                material_id,
                weight_config
            )
            supplier_scores.append({
                'supplier_id': ms.supplier_id,
                'supplier_code': ms.vendor.supplier_code if ms.vendor else '',
                'supplier_name': ms.vendor.supplier_name if ms.vendor else '',
                'total_score': score_data['total_score'],
                'details': score_data,
                'price': ms.price,
                'lead_time': ms.lead_time_days,
            })
        
        # 按总分排序
        supplier_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        if not supplier_scores:
            return None, None, None, None
        
        # 最佳供应商
        best = supplier_scores[0]
        
        # 备选供应商（前3名）
        alternatives = [
            {
                'supplier_id': s['supplier_id'],
                'supplier_name': s['supplier_name'],
                'score': float(s['total_score']),
                'price': float(s['price']) if s['price'] else None,
            }
            for s in supplier_scores[1:3]
        ]
        
        # 推荐理由
        reason = {
            'total_score': float(best['total_score']),
            'performance_score': float(best['details'].get('performance_score', 0)),
            'price_score': float(best['details'].get('price_score', 0)),
            'delivery_score': float(best['details'].get('delivery_score', 0)),
            'history_score': float(best['details'].get('history_score', 0)),
        }
        
        confidence = min(best['total_score'], Decimal('100'))
        
        return best['supplier_id'], confidence, reason, alternatives
    
    def _calculate_supplier_score(
        self,
        supplier_id: int,
        material_id: int,
        weight_config: Dict[str, Decimal]
    ) -> Dict:
        """计算供应商评分"""
        scores = {
            'performance_score': Decimal('0'),
            'price_score': Decimal('0'),
            'delivery_score': Decimal('0'),
            'history_score': Decimal('0'),
            'total_score': Decimal('0'),
        }
        
        # 1. 绩效评分（查询最近的绩效记录）
        latest_performance = self.db.query(SupplierPerformance).filter(
            SupplierPerformance.supplier_id == supplier_id
        ).order_by(SupplierPerformance.period_end.desc()).first()
        
        if latest_performance:
            scores['performance_score'] = latest_performance.overall_score
        else:
            scores['performance_score'] = Decimal('60')  # 默认及格分
        
        # 2. 价格评分（相对于其他供应商）
        from app.models import MaterialSupplier
        
        all_prices = self.db.query(MaterialSupplier.price).filter(
            and_(
                MaterialSupplier.material_id == material_id,
                MaterialSupplier.is_active == True,
                MaterialSupplier.price > 0
            )
        ).all()
        
        if all_prices:
            prices = [p[0] for p in all_prices]
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            
            current_supplier = self.db.query(MaterialSupplier).filter(
                and_(
                    MaterialSupplier.material_id == material_id,
                    MaterialSupplier.supplier_id == supplier_id
                )
            ).first()
            
            if current_supplier and current_supplier.price > 0:
                # 价格越低，评分越高
                if current_supplier.price <= min_price:
                    scores['price_score'] = Decimal('100')
                else:
                    # 线性插值：最低价100分，平均价60分
                    if avg_price > min_price:
                        scores['price_score'] = Decimal('100') - (
                            (current_supplier.price - min_price) / (avg_price - min_price) * Decimal('40')
                        )
                    else:
                        scores['price_score'] = Decimal('80')
            else:
                scores['price_score'] = Decimal('50')
        else:
            scores['price_score'] = Decimal('50')
        
        # 3. 交货期评分
        current_supplier = self.db.query(MaterialSupplier).filter(
            and_(
                MaterialSupplier.material_id == material_id,
                MaterialSupplier.supplier_id == supplier_id
            )
        ).first()
        
        if current_supplier:
            # 交期越短，评分越高（假设30天以内为满分）
            if current_supplier.lead_time_days <= 7:
                scores['delivery_score'] = Decimal('100')
            elif current_supplier.lead_time_days <= 15:
                scores['delivery_score'] = Decimal('85')
            elif current_supplier.lead_time_days <= 30:
                scores['delivery_score'] = Decimal('70')
            else:
                scores['delivery_score'] = max(
                    Decimal('40'),
                    Decimal('70') - (current_supplier.lead_time_days - 30) * Decimal('2')
                )
        else:
            scores['delivery_score'] = Decimal('50')
        
        # 4. 历史合作评分（订单数量和金额）
        order_count = self.db.query(func.count(PurchaseOrder.id)).filter(
            PurchaseOrder.supplier_id == supplier_id
        ).scalar() or 0
        
        if order_count >= 20:
            scores['history_score'] = Decimal('100')
        elif order_count >= 10:
            scores['history_score'] = Decimal('80')
        elif order_count >= 5:
            scores['history_score'] = Decimal('60')
        else:
            scores['history_score'] = Decimal('40')
        
        # 计算加权总分
        scores['total_score'] = (
            scores['performance_score'] * weight_config.get('performance', Decimal('40')) / Decimal('100') +
            scores['price_score'] * weight_config.get('price', Decimal('30')) / Decimal('100') +
            scores['delivery_score'] * weight_config.get('delivery', Decimal('20')) / Decimal('100') +
            scores['history_score'] * weight_config.get('history', Decimal('10')) / Decimal('100')
        )
        
        return scores
    
    def _determine_urgency(self, shortage: MaterialShortage) -> str:
        """确定紧急程度"""
        if not shortage.required_date:
            return 'NORMAL'
        
        days_until = (shortage.required_date - date.today()).days
        
        if days_until < 0:
            return 'URGENT'
        elif days_until <= 3:
            return 'HIGH'
        elif days_until <= 7:
            return 'NORMAL'
        else:
            return 'LOW'
    
    def _calculate_avg_consumption(self, material_id: int, months: int = 6) -> Optional[Decimal]:
        """计算平均月消耗量"""
        # 查询历史采购数据
        from datetime import datetime
        
        start_date = datetime.now() - timedelta(days=months * 30)
        
        result = self.db.query(
            func.sum(PurchaseOrderItem.received_qty)
        ).join(
            PurchaseOrder
        ).filter(
            and_(
                PurchaseOrderItem.material_id == material_id,
                PurchaseOrder.order_date >= start_date.date(),
                PurchaseOrderItem.received_qty > 0
            )
        ).scalar()
        
        if result and result > 0:
            return result / Decimal(months)
        
        return None
    
    def _generate_suggestion_no(self) -> str:
        """生成建议编号"""
        from datetime import datetime
        
        prefix = 'PS'
        date_str = datetime.now().strftime('%Y%m%d')
        
        # 查询当天最大序号
        latest = self.db.query(PurchaseSuggestion).filter(
            PurchaseSuggestion.suggestion_no.like(f'{prefix}{date_str}%')
        ).order_by(PurchaseSuggestion.suggestion_no.desc()).first()
        
        if latest:
            last_seq = int(latest.suggestion_no[-4:])
            seq = last_seq + 1
        else:
            seq = 1
        
        return f'{prefix}{date_str}{seq:04d}'
