# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务
提供BOM级联分析、影响范围计算、呆滞料识别等功能
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.ecn import Ecn, EcnAffectedMaterial, EcnBomImpact
from app.models.material import BomHeader, BomItem, Material
from app.models.project import Machine, Project
from app.models.purchase import PurchaseOrder, PurchaseOrderItem


class EcnBomAnalysisService:
    """ECN BOM影响分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_bom_impact(
        self,
        ecn_id: int,
        machine_id: Optional[int] = None,
        include_cascade: bool = True
    ) -> Dict[str, Any]:
        """
        分析ECN对BOM的影响
        
        Args:
            ecn_id: ECN ID
            machine_id: 设备ID（可选，如果ECN已关联设备则自动获取）
            include_cascade: 是否包含级联影响分析
        
        Returns:
            分析结果字典
        """
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError(f"ECN {ecn_id} 不存在")
        
        # 获取设备ID
        if not machine_id:
            machine_id = ecn.machine_id
        
        if not machine_id:
            raise ValueError("需要指定设备ID或ECN必须关联设备")
        
        # 获取受影响的物料
        affected_materials = self.db.query(EcnAffectedMaterial).filter(
            EcnAffectedMaterial.ecn_id == ecn_id
        ).all()
        
        if not affected_materials:
            return {
                "ecn_id": ecn_id,
                "machine_id": machine_id,
                "has_impact": False,
                "message": "没有受影响的物料"
            }
        
        # 获取设备的BOM
        machine = self.db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise ValueError(f"设备 {machine_id} 不存在")
        
        bom_headers = self.db.query(BomHeader).filter(
            BomHeader.machine_id == machine_id,
            BomHeader.status == 'RELEASED',
            BomHeader.is_latest == True
        ).all()
        
        if not bom_headers:
            return {
                "ecn_id": ecn_id,
                "machine_id": machine_id,
                "has_impact": False,
                "message": "设备没有已发布的BOM"
            }
        
        # 分析每个BOM的影响
        bom_impacts = []
        total_cost_impact = Decimal(0)
        total_affected_items = 0
        max_schedule_impact = 0
        
        for bom_header in bom_headers:
            impact_result = self._analyze_single_bom(
                ecn_id=ecn_id,
                bom_header=bom_header,
                affected_materials=affected_materials,
                include_cascade=include_cascade
            )
            
            if impact_result["has_impact"]:
                bom_impacts.append(impact_result)
                total_cost_impact += Decimal(impact_result.get("cost_impact", 0))
                total_affected_items += impact_result.get("affected_item_count", 0)
                max_schedule_impact = max(
                    max_schedule_impact,
                    impact_result.get("schedule_impact_days", 0)
                )
        
        # 保存分析结果
        for bom_header in bom_headers:
            self._save_bom_impact(
                ecn_id=ecn_id,
                bom_version_id=bom_header.id,
                machine_id=machine_id,
                project_id=ecn.project_id,
                affected_item_count=total_affected_items,
                total_cost_impact=total_cost_impact,
                schedule_impact_days=max_schedule_impact,
                impact_analysis={
                    "bom_impacts": bom_impacts,
                    "analysis_time": datetime.now().isoformat()
                }
            )
        
        return {
            "ecn_id": ecn_id,
            "machine_id": machine_id,
            "project_id": ecn.project_id,
            "has_impact": len(bom_impacts) > 0,
            "total_cost_impact": float(total_cost_impact),
            "total_affected_items": total_affected_items,
            "max_schedule_impact_days": max_schedule_impact,
            "bom_impacts": bom_impacts,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _analyze_single_bom(
        self,
        ecn_id: int,
        bom_header: BomHeader,
        affected_materials: List[EcnAffectedMaterial],
        include_cascade: bool = True
    ) -> Dict[str, Any]:
        """分析单个BOM的影响"""
        # 获取BOM所有物料项
        bom_items = self.db.query(BomItem).filter(
            BomItem.bom_id == bom_header.id
        ).all()
        
        # 构建物料编码到BOM项的映射
        material_code_to_items = {}
        material_id_to_items = {}
        for item in bom_items:
            if item.material_code:
                if item.material_code not in material_code_to_items:
                    material_code_to_items[item.material_code] = []
                material_code_to_items[item.material_code].append(item)
            if item.material_id:
                if item.material_id not in material_id_to_items:
                    material_id_to_items[item.material_id] = []
                material_id_to_items[item.material_id].append(item)
        
        # 分析直接影响
        direct_impact = []
        affected_item_ids = set()
        
        for affected_mat in affected_materials:
            # 通过物料编码匹配
            if affected_mat.material_code in material_code_to_items:
                for bom_item in material_code_to_items[affected_mat.material_code]:
                    affected_item_ids.add(bom_item.id)
                    direct_impact.append({
                        "bom_item_id": bom_item.id,
                        "material_code": bom_item.material_code,
                        "material_name": bom_item.material_name,
                        "change_type": affected_mat.change_type,
                        "impact": self._get_impact_description(affected_mat)
                    })
            
            # 通过物料ID匹配
            if affected_mat.material_id and affected_mat.material_id in material_id_to_items:
                for bom_item in material_id_to_items[affected_mat.material_id]:
                    if bom_item.id not in affected_item_ids:
                        affected_item_ids.add(bom_item.id)
                        direct_impact.append({
                            "bom_item_id": bom_item.id,
                            "material_code": bom_item.material_code,
                            "material_name": bom_item.material_name,
                            "change_type": affected_mat.change_type,
                            "impact": self._get_impact_description(affected_mat)
                        })
        
        # 分析级联影响
        cascade_impact = []
        if include_cascade:
            cascade_impact = self._analyze_cascade_impact(
                bom_items=bom_items,
                affected_item_ids=affected_item_ids
            )
        
        # 计算成本影响
        cost_impact = self._calculate_cost_impact(
            affected_materials=affected_materials,
            bom_items=bom_items,
            affected_item_ids=affected_item_ids
        )
        
        # 计算交期影响
        schedule_impact = self._calculate_schedule_impact(
            affected_materials=affected_materials,
            bom_items=bom_items,
            affected_item_ids=affected_item_ids
        )
        
        return {
            "bom_id": bom_header.id,
            "bom_no": bom_header.bom_no,
            "bom_name": bom_header.bom_name,
            "has_impact": len(direct_impact) > 0 or len(cascade_impact) > 0,
            "direct_impact": direct_impact,
            "cascade_impact": cascade_impact,
            "affected_item_count": len(affected_item_ids) + len(cascade_impact),
            "cost_impact": float(cost_impact),
            "schedule_impact_days": schedule_impact
        }
    
    def _analyze_cascade_impact(
        self,
        bom_items: List[BomItem],
        affected_item_ids: Set[int]
    ) -> List[Dict[str, Any]]:
        """分析级联影响（父子关系）"""
        cascade_impact = []
        
        # 构建父子关系映射
        parent_to_children = {}
        item_id_to_item = {}
        
        for item in bom_items:
            item_id_to_item[item.id] = item
            if item.parent_item_id:
                if item.parent_item_id not in parent_to_children:
                    parent_to_children[item.parent_item_id] = []
                parent_to_children[item.parent_item_id].append(item)
        
        # 向上追溯：如果子物料受影响，父物料也可能受影响
        processed_ids = set(affected_item_ids)
        queue = list(affected_item_ids)
        
        while queue:
            item_id = queue.pop(0)
            item = item_id_to_item.get(item_id)
            if not item:
                continue
            
            # 找到父物料
            if item.parent_item_id and item.parent_item_id not in processed_ids:
                parent_item = item_id_to_item.get(item.parent_item_id)
                if parent_item:
                    cascade_impact.append({
                        "bom_item_id": parent_item.id,
                        "material_code": parent_item.material_code,
                        "material_name": parent_item.material_name,
                        "impact": "因子物料变更可能受影响",
                        "cascade_type": "UPWARD"
                    })
                    processed_ids.add(item.parent_item_id)
                    queue.append(item.parent_item_id)
            
            # 向下追溯：如果父物料受影响，子物料也可能受影响
            if item_id in parent_to_children:
                for child_item in parent_to_children[item_id]:
                    if child_item.id not in processed_ids:
                        cascade_impact.append({
                            "bom_item_id": child_item.id,
                            "material_code": child_item.material_code,
                            "material_name": child_item.material_name,
                            "impact": "因父物料变更可能受影响",
                            "cascade_type": "DOWNWARD"
                        })
                        processed_ids.add(child_item.id)
        
        return cascade_impact
    
    def _calculate_cost_impact(
        self,
        affected_materials: List[EcnAffectedMaterial],
        bom_items: List[BomItem],
        affected_item_ids: Set[int]
    ) -> Decimal:
        """计算成本影响"""
        total_impact = Decimal(0)
        
        # 从受影响物料中获取成本影响
        for affected_mat in affected_materials:
            if affected_mat.cost_impact:
                total_impact += Decimal(affected_mat.cost_impact)
        
        # 从BOM项中计算变更成本
        for item_id in affected_item_ids:
            bom_item = next((item for item in bom_items if item.id == item_id), None)
            if bom_item and bom_item.amount:
                # 如果物料被删除，成本影响为负
                affected_mat = next(
                    (am for am in affected_materials 
                     if am.material_code == bom_item.material_code or 
                        am.material_id == bom_item.material_id),
                    None
                )
                if affected_mat and affected_mat.change_type == 'DELETE':
                    total_impact -= Decimal(bom_item.amount)
                elif affected_mat and affected_mat.change_type == 'ADD':
                    # 新增物料的成本需要从新规格中获取
                    if affected_mat.cost_impact:
                        total_impact += Decimal(affected_mat.cost_impact)
        
        return total_impact
    
    def _calculate_schedule_impact(
        self,
        affected_materials: List[EcnAffectedMaterial],
        bom_items: List[BomItem],
        affected_item_ids: Set[int]
    ) -> int:
        """计算交期影响（天数）"""
        max_impact_days = 0
        
        for item_id in affected_item_ids:
            bom_item = next((item for item in bom_items if item.id == item_id), None)
            if not bom_item:
                continue
            
            # 获取物料信息
            material = self.db.query(Material).filter(
                Material.id == bom_item.material_id
            ).first()
            
            if material and material.lead_time_days:
                # 如果物料变更，可能需要重新采购，影响交期
                affected_mat = next(
                    (am for am in affected_materials 
                     if am.material_code == bom_item.material_code or 
                        am.material_id == bom_item.material_id),
                    None
                )
                
                if affected_mat:
                    # 变更类型影响交期
                    if affected_mat.change_type in ['UPDATE', 'REPLACE']:
                        # 更新或替换可能需要重新采购
                        max_impact_days = max(max_impact_days, material.lead_time_days)
                    elif affected_mat.change_type == 'ADD':
                        # 新增物料需要采购周期
                        max_impact_days = max(max_impact_days, material.lead_time_days)
        
        return max_impact_days
    
    def _get_impact_description(self, affected_mat: EcnAffectedMaterial) -> str:
        """获取影响描述"""
        change_type_map = {
            'ADD': '新增',
            'DELETE': '删除',
            'UPDATE': '修改',
            'REPLACE': '替换'
        }
        
        desc = change_type_map.get(affected_mat.change_type, affected_mat.change_type)
        
        if affected_mat.old_quantity and affected_mat.new_quantity:
            desc += f"（数量：{affected_mat.old_quantity} → {affected_mat.new_quantity}）"
        elif affected_mat.old_specification and affected_mat.new_specification:
            desc += f"（规格变更）"
        
        return desc
    
    def _save_bom_impact(
        self,
        ecn_id: int,
        bom_version_id: int,
        machine_id: int,
        project_id: int,
        affected_item_count: int,
        total_cost_impact: Decimal,
        schedule_impact_days: int,
        impact_analysis: Dict[str, Any]
    ):
        """保存BOM影响分析结果"""
        # 检查是否已存在
        existing = self.db.query(EcnBomImpact).filter(
            EcnBomImpact.ecn_id == ecn_id,
            EcnBomImpact.bom_version_id == bom_version_id
        ).first()
        
        if existing:
            # 更新
            existing.affected_item_count = affected_item_count
            existing.total_cost_impact = total_cost_impact
            existing.schedule_impact_days = schedule_impact_days
            existing.impact_analysis = impact_analysis
            existing.analysis_status = 'COMPLETED'
            existing.analyzed_at = datetime.now()
        else:
            # 创建
            bom_impact = EcnBomImpact(
                ecn_id=ecn_id,
                bom_version_id=bom_version_id,
                machine_id=machine_id,
                project_id=project_id,
                affected_item_count=affected_item_count,
                total_cost_impact=total_cost_impact,
                schedule_impact_days=schedule_impact_days,
                impact_analysis=impact_analysis,
                analysis_status='COMPLETED',
                analyzed_at=datetime.now()
            )
            self.db.add(bom_impact)
        
        self.db.commit()
    
    def check_obsolete_material_risk(
        self,
        ecn_id: int
    ) -> Dict[str, Any]:
        """
        检查呆滞料风险
        
        Args:
            ecn_id: ECN ID
        
        Returns:
            呆滞料风险分析结果
        """
        ecn = self.db.query(Ecn).filter(Ecn.id == ecn_id).first()
        if not ecn:
            raise ValueError(f"ECN {ecn_id} 不存在")
        
        affected_materials = self.db.query(EcnAffectedMaterial).filter(
            EcnAffectedMaterial.ecn_id == ecn_id,
            EcnAffectedMaterial.change_type.in_(['DELETE', 'REPLACE'])
        ).all()
        
        if not affected_materials:
            return {
                "ecn_id": ecn_id,
                "has_obsolete_risk": False,
                "message": "没有删除或替换的物料"
            }
        
        obsolete_risks = []
        total_obsolete_cost = Decimal(0)
        
        for affected_mat in affected_materials:
            if not affected_mat.material_id:
                continue
            
            material = self.db.query(Material).filter(
                Material.id == affected_mat.material_id
            ).first()
            
            if not material:
                continue
            
            # 获取当前库存
            current_stock = Decimal(material.current_stock or 0)
            
            # 检查是否有在途采购订单
            po_items = self.db.query(PurchaseOrderItem).join(PurchaseOrder).filter(
                PurchaseOrderItem.material_id == material.id,
                PurchaseOrder.status.in_(['APPROVED', 'ORDERED', 'PARTIAL_RECEIVED'])
            ).all()
            
            in_transit_qty = sum(Decimal(item.quantity or 0) - Decimal(item.received_qty or 0) 
                                for item in po_items)
            
            # 计算呆滞料数量
            obsolete_qty = current_stock + in_transit_qty
            obsolete_cost = obsolete_qty * Decimal(material.last_price or material.standard_price or 0)
            
            if obsolete_qty > 0:
                # 判断风险级别
                risk_level = self._calculate_obsolete_risk_level(obsolete_qty, obsolete_cost)
                
                obsolete_risks.append({
                    "material_id": material.id,
                    "material_code": material.material_code,
                    "material_name": material.material_name,
                    "current_stock": float(current_stock),
                    "in_transit_qty": float(in_transit_qty),
                    "obsolete_quantity": float(obsolete_qty),
                    "obsolete_cost": float(obsolete_cost),
                    "risk_level": risk_level,
                    "change_type": affected_mat.change_type
                })
                
                total_obsolete_cost += obsolete_cost
                
                # 更新受影响物料的风险信息
                affected_mat.is_obsolete_risk = True
                affected_mat.obsolete_risk_level = risk_level
                affected_mat.obsolete_quantity = obsolete_qty
                affected_mat.obsolete_cost = obsolete_cost
                affected_mat.obsolete_analysis = (
                    f"物料将被{'删除' if affected_mat.change_type == 'DELETE' else '替换'}，"
                    f"当前库存{current_stock}，在途{in_transit_qty}，"
                    f"预计呆滞{obsolete_qty}，成本{obsolete_cost:.2f}元"
                )
        
        self.db.commit()
        
        return {
            "ecn_id": ecn_id,
            "has_obsolete_risk": len(obsolete_risks) > 0,
            "total_obsolete_cost": float(total_obsolete_cost),
            "obsolete_risks": obsolete_risks,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _calculate_obsolete_risk_level(
        self,
        obsolete_qty: Decimal,
        obsolete_cost: Decimal
    ) -> str:
        """计算呆滞料风险级别"""
        # 风险级别判定规则
        if obsolete_cost >= 100000:  # 10万元以上
            return 'CRITICAL'
        elif obsolete_cost >= 50000:  # 5-10万元
            return 'HIGH'
        elif obsolete_cost >= 10000:  # 1-5万元
            return 'MEDIUM'
        else:  # 1万元以下
            return 'LOW'
