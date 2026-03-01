# -*- coding: utf-8 -*-
"""
装配工艺齐套分析服务
基于装配工艺路径的智能齐套分析系统
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.assembly_kit import (
    AssemblyStage,
    AssemblyTemplate,
    CategoryStageMapping,
    BomItemAssemblyAttrs,
    MaterialReadiness,
)
from app.models.material import BomHeader, BomItem, Material
from app.models.project import Project, Machine
from app.models.purchase import PurchaseOrderItem


class AssemblyKitService:
    """装配工艺齐套分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 装配阶段管理 ====================
    
    def get_assembly_stages(self, active_only: bool = True) -> List[Dict]:
        """获取所有装配阶段定义"""
        query = self.db.query(AssemblyStage)
        if active_only:
            query = query.filter(AssemblyStage.is_active == True)
        
        stages = query.order_by(AssemblyStage.stage_order).all()
        return [
            {
                "id": s.id,
                "stage_code": s.stage_code,
                "stage_name": s.stage_name,
                "stage_order": s.stage_order,
                "description": s.description,
                "default_duration": s.default_duration,
                "color_code": s.color_code,
                "icon": s.icon,
            }
            for s in stages
        ]
    
    # ==================== 物料自动分配到工艺阶段 ====================
    
    def auto_assign_materials_to_stages(self, bom_id: int) -> Dict[str, Any]:
        """
        自动分配 BOM 物料到装配工艺阶段
        
        基于物料分类映射表自动分配
        """
        bom = self.db.query(BomHeader).filter(BomHeader.id == bom_id).first()
        if not bom:
            return {"error": "BOM 不存在"}
        
        bom_items = self.db.query(BomItem).filter(BomItem.bom_id == bom_id).all()
        
        assigned_count = 0
        skipped_count = 0
        
        for item in bom_items:
            if not item.material:
                skipped_count += 1
                continue
            
            # 检查是否已有装配属性
            existing = self.db.query(BomItemAssemblyAttrs).filter(
                BomItemAssemblyAttrs.bom_item_id == item.id
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # 根据物料分类查找映射
            category = item.material.category
            mapping = None
            
            if category:
                # 优先匹配分类 ID
                mapping = self.db.query(CategoryStageMapping).filter(
                    CategoryStageMapping.category_id == category.id,
                    CategoryStageMapping.is_active == True
                ).first()
            
            # 其次匹配关键词
            if not mapping and item.material.material_name:
                from sqlalchemy import text
                mapping = self.db.query(CategoryStageMapping).filter(
                    CategoryStageMapping.keywords.like(f'%{item.material.material_name}%'),
                    CategoryStageMapping.is_active == True
                ).first()
            
            if mapping:
                # 创建装配属性
                attrs = BomItemAssemblyAttrs(
                    bom_item_id=item.id,
                    bom_id=bom_id,
                    assembly_stage=mapping.stage_code,
                    stage_order=mapping.priority,
                    importance_level=mapping.importance_level,
                    is_blocking=mapping.is_blocking,
                    can_postpone=mapping.can_postpone,
                    lead_time_days=mapping.lead_time_buffer,
                    setting_source='AUTO',
                )
                self.db.add(attrs)
                assigned_count += 1
            else:
                # 无匹配，使用默认阶段（机械装配）
                attrs = BomItemAssemblyAttrs(
                    bom_item_id=item.id,
                    bom_id=bom_id,
                    assembly_stage='MECH',  # 默认机械阶段
                    stage_order=50,
                    importance_level='NORMAL',
                    is_blocking=False,
                    can_postpone=True,
                    setting_source='DEFAULT',
                )
                self.db.add(attrs)
                assigned_count += 1
        
        self.db.commit()
        
        return {
            "bom_id": bom_id,
            "total_items": len(bom_items),
            "assigned_count": assigned_count,
            "skipped_count": skipped_count,
            "message": f"已分配 {assigned_count} 项物料到装配阶段",
        }
    
    # ==================== 分阶段齐套率计算 ====================
    
    def calculate_stage_kit_rate(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        stage_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        计算分阶段齐套率
        
        Args:
            project_id: 项目 ID
            machine_id: 机台 ID（可选，不填则为项目级）
            stage_code: 阶段编码（可选，不填则计算所有阶段）
        
        Returns:
            各阶段齐套率计算结果
        """
        # 获取 BOM
        bom_query = self.db.query(BomHeader).filter(
            BomHeader.project_id == project_id,
            BomHeader.status == 'RELEASED'
        )
        
        if machine_id:
            bom_query = bom_query.filter(BomHeader.machine_id == machine_id)
        
        bom_headers = bom_query.all()
        if not bom_headers:
            return {"error": "未找到已发布 BOM"}
        
        bom_ids = [bom.id for bom in bom_headers]
        
        # 获取 BOM 明细及装配属性
        bom_items = self.db.query(BomItem).filter(BomItem.bom_id.in_(bom_ids)).all()
        
        # 获取装配属性
        assembly_attrs = self.db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_id.in_(bom_ids)
        ).all()
        
        attrs_map = {attr.bom_item_id: attr for attr in assembly_attrs}
        
        # 按阶段分组
        stages_data = {}
        
        for item in bom_items:
            attrs = attrs_map.get(item.id)
            stage = attrs.assembly_stage if attrs else 'UNKNOWN'
            
            if stage_code and stage != stage_code:
                continue
            
            if stage not in stages_data:
                stages_data[stage] = {
                    "total_items": 0,
                    "fulfilled_items": 0,
                    "shortage_items": 0,
                    "in_transit_items": 0,
                    "blocking_total": 0,
                    "blocking_fulfilled": 0,
                    "blocking_shortage": 0,
                    "items": [],
                }
            
            stage_data = stages_data[stage]
            stage_data["total_items"] += 1
            
            # 计算可用数量
            required_qty = float(item.quantity or 0)
            received_qty = float(item.received_qty or 0)
            
            # 库存数量
            stock_qty = 0
            if item.material:
                stock_qty = float(item.material.current_stock or 0)
            
            # 在途数量
            transit_qty = 0
            if item.material_id:
                po_items = self.db.query(PurchaseOrderItem).filter(
                    PurchaseOrderItem.material_id == item.material_id,
                    PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"])
                ).all()
                for po_item in po_items:
                    transit_qty += (float(po_item.quantity or 0) - float(po_item.received_qty or 0))
            
            available_qty = received_qty + stock_qty + transit_qty
            
            # 判断是否齐套
            is_fulfilled = available_qty >= required_qty
            is_blocking = attrs.is_blocking if attrs else False
            
            if is_fulfilled:
                stage_data["fulfilled_items"] += 1
                if is_blocking:
                    stage_data["blocking_fulfilled"] += 1
            else:
                stage_data["shortage_items"] += 1
                if is_blocking:
                    stage_data["blocking_shortage"] += 1
            
            if transit_qty > 0:
                stage_data["in_transit_items"] += 1
            
            if is_blocking:
                stage_data["blocking_total"] += 1
            
            stage_data["items"].append({
                "item_no": item.item_no,
                "material_code": item.material.material_code if item.material else None,
                "material_name": item.material.material_name if item.material else None,
                "required_qty": required_qty,
                "available_qty": available_qty,
                "is_fulfilled": is_fulfilled,
                "is_blocking": is_blocking,
                "stage": stage,
            })
        
        # 计算各阶段齐套率
        result = {
            "project_id": project_id,
            "machine_id": machine_id,
            "stages": {},
        }
        
        for stage, data in stages_data.items():
            # 整体齐套率
            overall_kit_rate = (
                data["fulfilled_items"] / data["total_items"] * 100
                if data["total_items"] > 0 else 0
            )
            
            # 阻塞性齐套率（更重要）
            blocking_kit_rate = (
                data["blocking_fulfilled"] / data["blocking_total"] * 100
                if data["blocking_total"] > 0 else 100  # 无阻塞物料时视为 100%
            )
            
            # 综合齐套率（阻塞性占 70% 权重）
            comprehensive_kit_rate = blocking_kit_rate * 0.7 + overall_kit_rate * 0.3
            
            # 确定状态
            if comprehensive_kit_rate >= 100:
                status = "complete"
            elif comprehensive_kit_rate >= 80:
                status = "partial"
            else:
                status = "shortage"
            
            result["stages"][stage] = {
                "stage_code": stage,
                "total_items": data["total_items"],
                "fulfilled_items": data["fulfilled_items"],
                "shortage_items": data["shortage_items"],
                "in_transit_items": data["in_transit_items"],
                "blocking_total": data["blocking_total"],
                "blocking_fulfilled": data["blocking_fulfilled"],
                "blocking_shortage": data["blocking_shortage"],
                "overall_kit_rate": round(overall_kit_rate, 2),
                "blocking_kit_rate": round(blocking_kit_rate, 2),
                "comprehensive_kit_rate": round(comprehensive_kit_rate, 2),
                "status": status,
            }
        
        return result
    
    # ==================== 齐套分析结果保存 ====================
    
    def save_readiness_analysis(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        planned_start_date: Optional[date] = None,
        target_stage: Optional[str] = None,
    ) -> MaterialReadiness:
        """保存齐套分析结果"""
        from app.utils.numerical_utils import generate_readiness_no
        
        # 计算齐套率
        kit_rate_result = self.calculate_stage_kit_rate(project_id, machine_id)
        
        # 整体统计
        total_items = sum(s["total_items"] for s in kit_rate_result["stages"].values())
        fulfilled_items = sum(s["fulfilled_items"] for s in kit_rate_result["stages"].values())
        shortage_items = sum(s["shortage_items"] for s in kit_rate_result["stages"].values())
        in_transit_items = sum(s["in_transit_items"] for s in kit_rate_result["stages"].values())
        blocking_total = sum(s["blocking_total"] for s in kit_rate_result["stages"].values())
        blocking_fulfilled = sum(s["blocking_fulfilled"] for s in kit_rate_result["stages"].values())
        
        # 整体齐套率
        overall_kit_rate = (
            fulfilled_items / total_items * 100 if total_items > 0 else 0
        )
        blocking_kit_rate = (
            blocking_fulfilled / blocking_total * 100 if blocking_total > 0 else 100
        )
        
        # 创建分析结果
        readiness = MaterialReadiness(
            readiness_no=generate_readiness_no(),
            project_id=project_id,
            machine_id=machine_id,
            planned_start_date=planned_start_date,
            target_stage=target_stage,
            overall_kit_rate=overall_kit_rate,
            blocking_kit_rate=blocking_kit_rate,
            stage_kit_rates=str(kit_rate_result["stages"]),  # JSON 字符串
            total_items=total_items,
            fulfilled_items=fulfilled_items,
            shortage_items=shortage_items,
            in_transit_items=in_transit_items,
            blocking_total=blocking_total,
            blocking_fulfilled=blocking_fulfilled,
        )
        
        self.db.add(readiness)
        self.db.commit()
        self.db.refresh(readiness)
        
        return readiness


    # ==================== 采购提前期分析 ====================
    
    def get_material_lead_time(self, material_id: int) -> Dict[str, Any]:
        """
        获取物料的采购提前期（从下单到到货的平均天数）
        
        基于历史采购订单数据计算
        """
        from app.models.purchase import PurchaseOrder, PurchaseOrderItem
        from datetime import datetime
        
        # 查询历史采购订单
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
        
        if not po_items:
            # 无历史数据，使用默认值
            return {
                "material_id": material_id,
                "avg_lead_time": 15,  # 默认 15 天
                "min_lead_time": 10,
                "max_lead_time": 20,
                "sample_count": 0,
                "last_purchase_date": None,
                "estimated_arrival": None,
            }
        
        # 计算提前期
        lead_times = []
        last_date = None
        
        for po_item, po in po_items:
            if po.order_date and po_item.received_date:
                days = (po_item.received_date - po.order_date).days
                if 0 < days < 180:  # 过滤异常数据
                    lead_times.append(days)
            
            if not last_date and po.order_date:
                last_date = po.order_date
        
        if not lead_times:
            return {
                "material_id": material_id,
                "avg_lead_time": 15,
                "min_lead_time": 10,
                "max_lead_time": 20,
                "sample_count": 0,
                "last_purchase_date": last_date,
                "estimated_arrival": None,
            }
        
        avg_lead_time = sum(lead_times) / len(lead_times)
        
        return {
            "material_id": material_id,
            "avg_lead_time": round(avg_lead_time, 1),
            "min_lead_time": min(lead_times),
            "max_lead_time": max(lead_times),
            "sample_count": len(lead_times),
            "last_purchase_date": last_date.isoformat() if last_date else None,
            "estimated_arrival": (last_date + timedelta(days=avg_lead_time)).isoformat() if last_date else None,
        }
    
    # ==================== 基于时间的齐套率预警 ====================
    
    def calculate_time_based_kit_rate(
        self,
        project_id: int,
        machine_id: Optional[int] = None,
        planned_start_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        基于时间的齐套率预警
        
        考虑：
        1. 采购提前期（下单到到货的天数）
        2. 生产周期（物料齐套到生产完成的天数）
        3. 计划开工日期
        
        返回：
        - 各阶段齐套率
        - 预计到货时间
        - 是否来得及（按计划在开工前齐套）
        - 预警级别（L1-L4）
        """
        from datetime import timedelta
        
        # 获取基础齐套率数据
        kit_rate_result = self.calculate_stage_kit_rate(project_id, machine_id)
        
        if "error" in kit_rate_result:
            return kit_rate_result
        
        # 获取 BOM 明细
        bom_query = self.db.query(BomHeader).filter(
            BomHeader.project_id == project_id,
            BomHeader.status == 'RELEASED'
        )
        if machine_id:
            bom_query = bom_query.filter(BomHeader.machine_id == machine_id)
        
        bom_headers = bom_query.all()
        if not bom_headers:
            return {"error": "未找到已发布 BOM"}
        
        bom_ids = [bom.id for bom in bom_headers]
        bom_items = self.db.query(BomItem).filter(BomItem.bom_id.in_(bom_ids)).all()
        
        # 获取装配属性
        assembly_attrs = self.db.query(BomItemAssemblyAttrs).filter(
            BomItemAssemblyAttrs.bom_id.in_(bom_ids)
        ).all()
        attrs_map = {attr.bom_item_id: attr for attr in assembly_attrs}
        
        # 分析每个物料的预计到货时间
        today = date.today()
        material_analysis = {}
        
        for item in bom_items:
            if not item.material:
                continue
            
            attrs = attrs_map.get(item.id)
            stage = attrs.assembly_stage if attrs else 'UNKNOWN'
            
            required_qty = float(item.quantity or 0)
            received_qty = float(item.received_qty or 0)
            stock_qty = float(item.material.current_stock or 0) if item.material else 0
            
            available_qty = received_qty + stock_qty
            shortage_qty = max(0, required_qty - available_qty)
            
            # 如果有短缺，计算预计到货时间
            estimated_arrival = None
            lead_time_days = 0
            is_urgent = False
            
            if shortage_qty > 0:
                # 查询在途采购
                from app.models.purchase import PurchaseOrderItem, PurchaseOrder
                po_items = self.db.query(PurchaseOrderItem, PurchaseOrder)\
                    .join(PurchaseOrder)\
                    .filter(
                        PurchaseOrderItem.material_id == item.material_id,
                        PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]),
                        (PurchaseOrderItem.quantity - PurchaseOrderItem.received_qty) > 0
                    )\
                    .all()
                
                if po_items:
                    # 有在途订单，估算到货时间
                    total_in_transit = sum(
                        (float(po_item.quantity or 0) - float(po_item.received_qty or 0))
                        for po_item, _ in po_items
                    )
                    
                    if total_in_transit >= shortage_qty:
                        # 在途数量足够
                        # 获取历史提前期
                        lead_info = self.get_material_lead_time(item.material_id)
                        lead_time_days = lead_info["avg_lead_time"]
                        
                        # 估算到货日期（假设最近一次下单是 3 天前）
                        estimated_arrival = today + timedelta(days=max(1, lead_time_days // 2))
                    else:
                        # 在途数量不足，需要新下单
                        lead_info = self.get_material_lead_time(item.material_id)
                        lead_time_days = lead_info["avg_lead_time"]
                        estimated_arrival = today + timedelta(days=lead_time_days)
                        is_urgent = True
                else:
                    # 无在途订单，需要立即下单
                    lead_info = self.get_material_lead_time(item.material_id)
                    lead_time_days = lead_info["avg_lead_time"]
                    estimated_arrival = today + timedelta(days=lead_time_days)
                    is_urgent = True
            
            # 判断是否能赶上计划开工
            can_meet_schedule = True
            days_to_start = None
            warning_level = "L4"  # 常规
            
            if planned_start_date and estimated_arrival:
                days_to_start = (planned_start_date - estimated_arrival).days
                
                if days_to_start < 0:
                    # 已经延期
                    can_meet_schedule = False
                    warning_level = "L1"  # 停工预警
                elif days_to_start < 3:
                    # 3 天内开工，风险高
                    can_meet_schedule = False
                    warning_level = "L2"  # 紧急预警
                elif days_to_start < 7:
                    # 7 天内开工，需注意
                    warning_level = "L3"  # 提前预警
                else:
                    warning_level = "L4"  # 常规
            
            if stage not in material_analysis:
                material_analysis[stage] = {
                    "total_items": 0,
                    "shortage_items": [],
                    "urgent_items": [],
                    "max_lead_time": 0,
                    "latest_arrival": None,
                    "warning_levels": {"L1": 0, "L2": 0, "L3": 0, "L4": 0},
                }
            
            stage_data = material_analysis[stage]
            stage_data["total_items"] += 1
            
            if shortage_qty > 0:
                shortage_item = {
                    "item_no": item.item_no,
                    "material_code": item.material.material_code,
                    "material_name": item.material.material_name,
                    "required_qty": required_qty,
                    "available_qty": available_qty,
                    "shortage_qty": shortage_qty,
                    "estimated_arrival": estimated_arrival.isoformat() if estimated_arrival else None,
                    "lead_time_days": lead_time_days,
                    "is_urgent": is_urgent,
                    "can_meet_schedule": can_meet_schedule,
                    "days_to_start": days_to_start,
                    "warning_level": warning_level,
                }
                
                stage_data["shortage_items"].append(shortage_item)
                
                if is_urgent:
                    stage_data["urgent_items"].append(shortage_item)
                
                stage_data["max_lead_time"] = max(stage_data["max_lead_time"], lead_time_days)
                stage_data["warning_levels"][warning_level] += 1
        
        # 整合结果
        result = {
            "project_id": project_id,
            "machine_id": machine_id,
            "planned_start_date": planned_start_date.isoformat() if planned_start_date else None,
            "analysis_date": today.isoformat(),
            "stages": {},
            "summary": {
                "total_shortage_items": sum(len(s["shortage_items"]) for s in material_analysis.values()),
                "total_urgent_items": sum(len(s["urgent_items"]) for s in material_analysis.values()),
                "l1_count": sum(s["warning_levels"]["L1"] for s in material_analysis.values()),
                "l2_count": sum(s["warning_levels"]["L2"] for s in material_analysis.values()),
                "l3_count": sum(s["warning_levels"]["L3"] for s in material_analysis.values()),
            },
        }
        
        # 合并齐套率数据和时间分析
        for stage_code, stage_data in material_analysis.items():
            kit_data = kit_rate_result["stages"].get(stage_code, {})
            
            # 确定最终预警级别（取最高）
            if stage_data["warning_levels"]["L1"] > 0:
                overall_warning = "L1"
            elif stage_data["warning_levels"]["L2"] > 0:
                overall_warning = "L2"
            elif stage_data["warning_levels"]["L3"] > 0:
                overall_warning = "L3"
            else:
                overall_warning = "L4"
            
            result["stages"][stage_code] = {
                **kit_data,
                "shortage_items": stage_data["shortage_items"],
                "urgent_items": stage_data["urgent_items"],
                "max_lead_time": stage_data["max_lead_time"],
                "overall_warning": overall_warning,
                "warning_details": stage_data["warning_levels"],
            }
        
        return result


def _to_decimal(value: Any) -> Decimal:
    """将数值安全转换为 Decimal。"""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _calc_percent(numerator: int, denominator: int) -> Decimal:
    """计算百分比，保留两位小数。"""
    if denominator <= 0:
        return Decimal("100")
    percent = (Decimal(numerator) / Decimal(denominator)) * Decimal("100")
    return percent.quantize(Decimal("0.01"))


def validate_analysis_inputs(
    db: Session,
    project_id: int,
    bom_id: int,
    machine_id: Optional[int] = None,
) -> Tuple[Project, BomHeader, Optional[Machine]]:
    """校验齐套分析入参并返回实体对象。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="项目不存在",
        )

    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BOM不存在",
        )

    bom_project_id = getattr(bom, "project_id", None)
    if isinstance(bom_project_id, str) and bom_project_id.isdigit():
        bom_project_id = int(bom_project_id)
    if isinstance(bom_project_id, int) and bom_project_id not in (0, project_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="BOM不属于指定项目",
        )

    machine = None
    if machine_id is not None:
        machine = db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="机台不存在",
            )

        machine_project_id = getattr(machine, "project_id", None)
        if isinstance(machine_project_id, str) and machine_project_id.isdigit():
            machine_project_id = int(machine_project_id)
        if isinstance(machine_project_id, int) and machine_project_id not in (0, project_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="机台不属于指定项目",
            )

    return project, bom, machine


def initialize_stage_results(stages: List[AssemblyStage]) -> Dict[str, Dict[str, Any]]:
    """初始化每个阶段的统计容器。"""
    results: Dict[str, Dict[str, Any]] = {}
    for stage in stages:
        results[stage.stage_code] = {
            "total": 0,
            "fulfilled": 0,
            "blocking_total": 0,
            "blocking_fulfilled": 0,
            "stage": stage,
        }
    return results


def get_expected_arrival_date(db: Session, material_id: int) -> Optional[date]:
    """查询物料预计到货日期（优先承诺交期，其次需求交期）。"""
    try:
        from app.models.purchase import PurchaseOrder

        query = db.query(PurchaseOrderItem).join(
            PurchaseOrder,
            PurchaseOrderItem.order_id == PurchaseOrder.id,
        ).filter(
            PurchaseOrderItem.material_id == material_id,
            PurchaseOrderItem.status.in_(
                ["APPROVED", "ORDERED", "PARTIAL_RECEIVED", "approved", "partial_received"]
            ),
            or_(
                PurchaseOrderItem.promised_date.isnot(None),
                PurchaseOrderItem.required_date.isnot(None),
            ),
        ).order_by(
            PurchaseOrderItem.promised_date.asc(),
            PurchaseOrderItem.required_date.asc(),
        )
        po_item = query.first()
    except Exception:
        return None

    if not po_item:
        return None
    return po_item.promised_date or po_item.required_date


def analyze_bom_item(
    db: Session,
    bom_item: BomItem,
    check_date: date,
    stage_map: Dict[str, AssemblyStage],
    stage_results: Dict[str, Dict[str, Any]],
    calculate_available_qty_func: Any,
) -> Optional[Dict[str, Any]]:
    """分析单条 BOM 明细，返回缺料明细（若无缺料则返回 None）。"""
    material = db.query(Material).filter(Material.id == bom_item.material_id).first()
    if not material:
        return None

    attrs = db.query(BomItemAssemblyAttrs).filter(
        BomItemAssemblyAttrs.bom_item_id == bom_item.id
    ).first()

    stage_code = attrs.assembly_stage if attrs and attrs.assembly_stage else "MECH"
    is_blocking = bool(attrs.is_blocking) if attrs else True

    if stage_code not in stage_results:
        fallback = next(iter(stage_results.keys()), "MECH")
        stage_code = fallback
        if stage_code not in stage_results:
            stage_results[stage_code] = {
                "total": 0,
                "fulfilled": 0,
                "blocking_total": 0,
                "blocking_fulfilled": 0,
                "stage": stage_map.get(stage_code),
            }

    required_qty = _to_decimal(getattr(bom_item, "quantity", None))
    stock_qty, allocated_qty, in_transit_qty, available_qty = calculate_available_qty_func(
        db, material.id, check_date
    )
    stock_qty = _to_decimal(stock_qty)
    allocated_qty = _to_decimal(allocated_qty)
    in_transit_qty = _to_decimal(in_transit_qty)
    available_qty = _to_decimal(available_qty)

    stage_stat = stage_results[stage_code]
    stage_stat["total"] += 1

    shortage_qty = max(Decimal("0"), required_qty - available_qty)
    is_fulfilled = shortage_qty <= 0
    if is_fulfilled:
        stage_stat["fulfilled"] += 1

    if is_blocking:
        stage_stat["blocking_total"] += 1
        if is_fulfilled:
            stage_stat["blocking_fulfilled"] += 1

    if is_fulfilled:
        return None

    shortage_rate = (
        (shortage_qty / required_qty) * Decimal("100") if required_qty > 0 else Decimal("0")
    )
    required_date = getattr(bom_item, "required_date", None)
    days_to_required = (required_date - check_date).days if required_date else 7

    from app.api.v1.endpoints.assembly_kit.kit_analysis.utils import determine_alert_level

    try:
        alert_level = determine_alert_level(db, is_blocking, shortage_rate, days_to_required)
    except Exception:
        alert_level = "L4"

    return {
        "bom_item_id": bom_item.id,
        "material_id": material.id,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "assembly_stage": stage_code,
        "is_blocking": is_blocking,
        "required_qty": required_qty,
        "stock_qty": stock_qty,
        "allocated_qty": allocated_qty,
        "in_transit_qty": in_transit_qty,
        "available_qty": available_qty,
        "shortage_qty": shortage_qty,
        "shortage_rate": shortage_rate,
        "alert_level": alert_level,
        "expected_arrival": get_expected_arrival_date(db, material.id),
        "required_date": required_date,
    }


def calculate_stage_kit_rates(
    stages: List[AssemblyStage],
    stage_results: Dict[str, Dict[str, Any]],
    shortage_details: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], bool, Optional[str], Optional[str], Dict[str, int], List[Dict[str, Any]]]:
    """汇总各阶段齐套率并返回开工判断。"""
    stage_kit_rates: List[Dict[str, Any]] = []

    ordered_stages = sorted(stages, key=lambda s: getattr(s, "stage_order", 0))
    overall_total = 0
    overall_fulfilled = 0
    overall_blocking_total = 0
    overall_blocking_fulfilled = 0

    first_blocked_stage: Optional[str] = None
    current_workable_stage: Optional[str] = None

    for stage in ordered_stages:
        stats = stage_results.get(stage.stage_code, {})
        total = int(stats.get("total", 0))
        fulfilled = int(stats.get("fulfilled", 0))
        blocking_total = int(stats.get("blocking_total", 0))
        blocking_fulfilled = int(stats.get("blocking_fulfilled", 0))

        overall_total += total
        overall_fulfilled += fulfilled
        overall_blocking_total += blocking_total
        overall_blocking_fulfilled += blocking_fulfilled

        kit_rate = _calc_percent(fulfilled, total)
        blocking_rate = _calc_percent(blocking_fulfilled, blocking_total)
        can_start = blocking_fulfilled >= blocking_total

        if first_blocked_stage is None and not can_start:
            first_blocked_stage = stage.stage_code
        if first_blocked_stage is None:
            current_workable_stage = stage.stage_code

        stage_kit_rates.append(
            {
                "stage_code": stage.stage_code,
                "stage_name": stage.stage_name,
                "stage_order": stage.stage_order,
                "total_items": total,
                "fulfilled_items": fulfilled,
                "kit_rate": kit_rate,
                "blocking_total": blocking_total,
                "blocking_fulfilled": blocking_fulfilled,
                "blocking_rate": blocking_rate,
                "can_start": can_start,
                "color_code": getattr(stage, "color_code", "#3B82F6"),
            }
        )

    can_proceed = first_blocked_stage is None
    overall_stats = {
        "total": overall_total,
        "fulfilled": overall_fulfilled,
        "blocking_total": overall_blocking_total,
        "blocking_fulfilled": overall_blocking_fulfilled,
    }
    all_blocking_items = [d for d in shortage_details if d.get("is_blocking")]

    return (
        stage_kit_rates,
        can_proceed,
        first_blocked_stage,
        current_workable_stage,
        overall_stats,
        all_blocking_items,
    )
