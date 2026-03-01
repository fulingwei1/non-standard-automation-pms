# -*- coding: utf-8 -*-
"""
装配工艺齐套分析服务 - 增强版
考虑：
1. 采购承诺交期
2. 相似物料历史数据
3. 春节假期因素
"""

from typing import Any, Dict, List, Optional
from datetime import date, timedelta, datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.assembly_kit import (
    AssemblyStage,
    AssemblyTemplate,
    CategoryStageMapping,
    BomItemAssemblyAttrs,
    MaterialReadiness,
)
from app.models.material import BomHeader, BomItem, Material, MaterialCategory
from app.models.project import Project, Machine
from app.models.purchase import PurchaseOrder, PurchaseOrderItem


class AssemblyKitServiceEnhanced:
    """装配工艺齐套分析服务 - 增强版"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 春节假期配置 ====================
    
    def get_spring_festival_impact(self, query_date: date) -> Dict[str, Any]:
        """
        获取春节假期影响
        
        返回：
        - 是否在春节期间
        - 假期前后范围
        - 建议增加的提前期天数
        """
        # 春节日期（2024-2030 年）
        spring_festivals = {
            2024: date(2024, 2, 10),
            2025: date(2025, 1, 29),
            2026: date(2026, 2, 17),
            2027: date(2027, 2, 6),
            2028: date(2028, 1, 26),
            2029: date(2029, 2, 13),
            2030: date(2030, 2, 3),
        }
        
        year = query_date.year
        spring_festival = spring_festivals.get(year)
        
        if not spring_festival:
            return {
                "is_spring_festival_period": False,
                "festival_date": None,
                "pre_festival_start": None,
                "post_festival_end": None,
                "extra_lead_time": 0,
                "reason": "非春节假期影响范围",
            }
        
        # 春节前 15 天开始影响（供应商提前放假）
        pre_festival_start = spring_festival - timedelta(days=15)
        # 春节后 15 天结束影响（供应商晚开工 + 物流恢复）
        post_festival_end = spring_festival + timedelta(days=15)
        
        is_pre_festival = pre_festival_start <= query_date < spring_festival
        is_during_festival = spring_festival <= query_date <= spring_festival + timedelta(days=7)
        is_post_festival = spring_festival < query_date <= post_festival_end
        
        is_affected = is_pre_festival or is_during_festival or is_post_festival
        
        # 计算额外提前期
        extra_lead_time = 0
        reason = ""
        
        if is_during_festival:
            extra_lead_time = 20  # 春节期间 +20 天
            reason = "春节期间，供应商放假 + 物流停运"
        elif is_pre_festival:
            # 越接近春节，影响越大
            days_to_festival = (spring_festival - query_date).days
            extra_lead_time = min(20, max(5, 20 - days_to_festival))
            reason = f"春节前期，供应商提前放假（还有{days_to_festival}天过年）"
        elif is_post_festival:
            days_after_festival = (query_date - spring_festival).days
            extra_lead_time = max(0, 15 - days_after_festival)
            reason = f"春节后期，供应商晚开工 + 物流恢复中（过年后{days_after_festival}天）"
        
        return {
            "is_spring_festival_period": is_affected,
            "festival_date": spring_festival.isoformat(),
            "pre_festival_start": pre_festival_start.isoformat(),
            "post_festival_end": post_festival_end.isoformat(),
            "extra_lead_time": extra_lead_time,
            "reason": reason,
            "is_pre_festival": is_pre_festival,
            "is_during_festival": is_during_festival,
            "is_post_festival": is_post_festival,
        }
    
    # ==================== 采购承诺交期 ====================
    
    def get_promised_delivery_date(self, material_id: int) -> Optional[date]:
        """
        获取采购承诺交期
        
        优先级：
        1. 在途订单的承诺交期
        2. 最近一次采购的实际到货日期推算
        """
        from app.models.purchase import PurchaseOrder, PurchaseOrderItem
        
        # 1. 查询在途订单的承诺交期
        po_items = self.db.query(PurchaseOrderItem, PurchaseOrder)\
            .join(PurchaseOrder)\
            .filter(
                PurchaseOrderItem.material_id == material_id,
                PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]),
                (PurchaseOrderItem.quantity - PurchaseOrderItem.received_qty) > 0,
                PurchaseOrderItem.promised_delivery_date != None
            )\
            .order_by(PurchaseOrderItem.promised_delivery_date)\
            .all()
        
        if po_items:
            # 返回最早的承诺交期
            return po_items[0][0].promised_delivery_date
        
        # 2. 无承诺交期，使用历史数据推算
        return self.get_estimated_delivery_from_history(material_id)
    
    def get_estimated_delivery_from_history(
        self,
        material_id: int,
        order_date: Optional[date] = None
    ) -> Optional[date]:
        """
        根据历史数据推算预计到货日期
        
        考虑：
        1. 该物料历史采购提前期
        2. 相似物料（同分类/同供应商）的历史提前期
        """
        if order_date is None:
            order_date = date.today()
        
        from sqlalchemy import text
        
        # 1. 该物料的历史提前期
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return None
        
        # 查询该物料历史采购订单
        from app.models.purchase import PurchaseOrder, PurchaseOrderItem
        po_items = self.db.query(PurchaseOrderItem, PurchaseOrder)\
            .join(PurchaseOrder)\
            .filter(
                PurchaseOrderItem.material_id == material_id,
                PurchaseOrder.status.in_(["COMPLETED", "PARTIAL_RECEIVED"]),
                PurchaseOrder.order_date != None,
                PurchaseOrderItem.received_date != None
            )\
            .order_by(PurchaseOrder.order_date.desc())\
            .limit(10)\
            .all()
        
        lead_times = []
        for po_item, po in po_items:
            if po.order_date and po_item.received_date:
                days = (po_item.received_date - po.order_date).days
                if 0 < days < 180:
                    lead_times.append(days)
        
        if lead_times:
            # 有历史数据，取平均
            avg_lead_time = sum(lead_times) / len(lead_times)
            return order_date + timedelta(days=int(avg_lead_time))
        
        # 2. 无历史数据，查询相似物料
        similar_lead_times = self.get_similar_material_lead_times(material)
        
        if similar_lead_times:
            avg_lead_time = sum(similar_lead_times) / len(similar_lead_times)
            return order_date + timedelta(days=int(avg_lead_time))
        
        # 3. 无任何参考，使用默认值
        return order_date + timedelta(days=15)
    
    def get_similar_material_lead_times(self, material: Material) -> List[int]:
        """
        获取相似物料的历史提前期
        
        相似度优先级：
        1. 同分类 + 同供应商
        2. 同分类
        3. 同供应商
        """
        from app.models.purchase import PurchaseOrder, PurchaseOrderItem
        
        lead_times = []
        
        # 1. 同分类 + 同供应商
        if material.category_id and material.supplier_id:
            similar_items = self.db.query(PurchaseOrderItem, PurchaseOrder)\
                .join(PurchaseOrder)\
                .join(Material, PurchaseOrderItem.material_id == Material.id)\
                .filter(
                    Material.category_id == material.category_id,
                    Material.supplier_id == material.supplier_id,
                    PurchaseOrder.status.in_(["COMPLETED", "PARTIAL_RECEIVED"]),
                    PurchaseOrder.order_date != None,
                    PurchaseOrderItem.received_date != None,
                    PurchaseOrderItem.material_id != material.id
                )\
                .order_by(PurchaseOrder.order_date.desc())\
                .limit(20)\
                .all()
            
            for po_item, po in similar_items:
                if po.order_date and po_item.received_date:
                    days = (po_item.received_date - po.order_date).days
                    if 0 < days < 180:
                        lead_times.append(days)
            
            if lead_times:
                return lead_times
        
        # 2. 同分类
        if material.category_id:
            similar_items = self.db.query(PurchaseOrderItem, PurchaseOrder)\
                .join(PurchaseOrder)\
                .join(Material, PurchaseOrderItem.material_id == Material.id)\
                .filter(
                    Material.category_id == material.category_id,
                    PurchaseOrder.status.in_(["COMPLETED", "PARTIAL_RECEIVED"]),
                    PurchaseOrder.order_date != None,
                    PurchaseOrderItem.received_date != None,
                    PurchaseOrderItem.material_id != material.id
                )\
                .order_by(PurchaseOrder.order_date.desc())\
                .limit(20)\
                .all()
            
            for po_item, po in similar_items:
                if po.order_date and po_item.received_date:
                    days = (po_item.received_date - po.order_date).days
                    if 0 < days < 180:
                        lead_times.append(days)
            
            if lead_times:
                return lead_times
        
        # 3. 同供应商
        if material.supplier_id:
            similar_items = self.db.query(PurchaseOrderItem, PurchaseOrder)\
                .join(PurchaseOrder)\
                .filter(
                    PurchaseOrderItem.supplier_id == material.supplier_id,
                    PurchaseOrder.status.in_(["COMPLETED", "PARTIAL_RECEIVED"]),
                    PurchaseOrder.order_date != None,
                    PurchaseOrderItem.received_date != None,
                    PurchaseOrderItem.material_id != material.id
                )\
                .order_by(PurchaseOrder.order_date.desc())\
                .limit(20)\
                .all()
            
            for po_item, po in similar_items:
                if po.order_date and po_item.received_date:
                    days = (po_item.received_date - po.order_date).days
                    if 0 < days < 180:
                        lead_times.append(days)
            
            if lead_times:
                return lead_times
        
        return lead_times
    
    # ==================== 增强版时间预警 ====================
    
    def calculate_enhanced_time_based_kit_rate(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        planned_start_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        增强版基于时间的齐套率预警
        
        考虑：
        1. 采购承诺交期（优先级最高）
        2. 相似物料历史数据（无承诺交期时使用）
        3. 春节假期因素（自动增加提前期）
        """
        from datetime import timedelta
        
        today = date.today()
        
        # 获取春节影响
        spring_festival_info = self.get_spring_festival_impact(today)
        
        # 获取基础齐套率数据
        kit_rate_result = self.calculate_time_based_kit_rate(project_id, machine_id, planned_start_date)
        
        if "error" in kit_rate_result:
            return kit_rate_result
        
        # 增强每个缺料物料的预计到货时间
        for stage_code, stage_data in kit_rate_result.get("stages", {}).items():
            if "shortage_items" not in stage_data:
                continue
            
            for item in stage_data["shortage_items"]:
                material_id = item.get("material_id")
                if not material_id:
                    continue
                
                # 1. 优先使用采购承诺交期
                promised_date = self.get_promised_delivery_date(material_id)
                
                if promised_date:
                    # 有承诺交期
                    estimated_arrival = promised_date
                    item["delivery_source"] = "promised"
                    item["promised_delivery_date"] = promised_date.isoformat()
                else:
                    # 无承诺交期，使用历史推算
                    estimated_arrival = self.get_estimated_delivery_from_history(material_id, today)
                    item["delivery_source"] = "estimated"
                
                item["estimated_arrival"] = estimated_arrival.isoformat() if estimated_arrival else None
                
                # 2. 应用春节假期影响
                if spring_festival_info["is_spring_festival_period"]:
                    # 春节期间，额外增加提前期
                    extra_days = spring_festival_info["extra_lead_time"]
                    if estimated_arrival:
                        # 如果预计到货在春节期间，顺延
                        if estimated_arrival >= date.fromisoformat(spring_festival_info["pre_festival_start"]) and \
                           estimated_arrival <= date.fromisoformat(spring_festival_info["post_festival_end"]):
                            estimated_arrival = estimated_arrival + timedelta(days=extra_days)
                            item["estimated_arrival"] = estimated_arrival.isoformat()
                            item["spring_festival_delay"] = extra_days
                            item["spring_festival_reason"] = spring_festival_info["reason"]
                
                # 3. 重新计算距离开工天数
                if planned_start_date and estimated_arrival:
                    item["days_to_start"] = (planned_start_date - estimated_arrival).days
                    
                    # 重新确定预警级别
                    days_to_start = item["days_to_start"]
                    if days_to_start < 0:
                        item["warning_level"] = "L1"
                    elif days_to_start < 3:
                        item["warning_level"] = "L2"
                    elif days_to_start < 7:
                        item["warning_level"] = "L3"
                    else:
                        item["warning_level"] = "L4"
        
        # 添加春节影响说明
        kit_rate_result["spring_festival_info"] = spring_festival_info
        
        return kit_rate_result
