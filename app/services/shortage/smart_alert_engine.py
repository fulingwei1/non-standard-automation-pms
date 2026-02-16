# -*- coding: utf-8 -*-
"""
智能缺料预警引擎

Team 3: 智能缺料预警系统
核心预警逻辑，包括扫描、分析、影响评估
"""
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.shortage.smart_alert import ShortageAlert, ShortageHandlingPlan
from app.models.material import Material
from app.models.project import Project
from app.models.production.work_order import WorkOrder
from app.models.inventory import Inventory
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.core.exceptions import BusinessException

logger = logging.getLogger(__name__)


class SmartAlertEngine:
    """智能预警引擎"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def scan_and_alert(
        self,
        project_id: Optional[int] = None,
        material_id: Optional[int] = None,
        days_ahead: int = 30
    ) -> List[ShortageAlert]:
        """
        扫描并生成缺料预警
        
        Args:
            project_id: 项目ID（可选，为空则扫描全部）
            material_id: 物料ID（可选）
            days_ahead: 提前天数（扫描未来N天的需求）
        
        Returns:
            生成的预警列表
        """
        logger.info(f"开始扫描缺料预警: project_id={project_id}, material_id={material_id}, days_ahead={days_ahead}")
        
        alerts = []
        
        # 1. 获取需求数据（从工单、BOM等）
        demands = self._collect_material_demands(
            project_id=project_id,
            material_id=material_id,
            days_ahead=days_ahead
        )
        
        # 2. 对每个物料需求进行分析
        for demand in demands:
            # 获取库存和在途
            available_qty = self._get_available_qty(demand['material_id'])
            in_transit_qty = self._get_in_transit_qty(demand['material_id'])
            
            shortage_qty = demand['required_qty'] - available_qty - in_transit_qty
            
            # 有缺口才预警
            if shortage_qty > 0:
                # 计算预警级别
                alert_level = self.calculate_alert_level(
                    shortage_qty=shortage_qty,
                    required_qty=demand['required_qty'],
                    days_to_shortage=demand['days_to_required'],
                    is_critical_path=demand.get('is_critical_path', False)
                )
                
                # 预测影响
                impact = self.predict_impact(
                    material_id=demand['material_id'],
                    shortage_qty=shortage_qty,
                    required_date=demand['required_date'],
                    project_id=demand['project_id']
                )
                
                # 创建预警
                alert = self._create_alert(
                    project_id=demand['project_id'],
                    material_id=demand['material_id'],
                    material_code=demand['material_code'],
                    material_name=demand['material_name'],
                    required_qty=demand['required_qty'],
                    available_qty=available_qty,
                    shortage_qty=shortage_qty,
                    in_transit_qty=in_transit_qty,
                    required_date=demand['required_date'],
                    alert_level=alert_level,
                    impact=impact,
                    work_order_id=demand.get('work_order_id')
                )
                
                alerts.append(alert)
                
                # 自动生成处理方案
                if alert_level in ['CRITICAL', 'URGENT']:
                    solutions = self.generate_solutions(alert)
                    logger.info(f"为预警 {alert.alert_no} 生成了 {len(solutions)} 个处理方案")
        
        logger.info(f"扫描完成，生成 {len(alerts)} 个预警")
        return alerts
    
    def calculate_alert_level(
        self,
        shortage_qty: Decimal,
        required_qty: Decimal,
        days_to_shortage: int,
        is_critical_path: bool = False
    ) -> str:
        """
        计算预警级别
        
        级别定义:
        - INFO: 轻微缺口，时间充裕
        - WARNING: 缺口较大或时间紧张
        - CRITICAL: 严重缺口或即将断料
        - URGENT: 已断料或关键路径受阻
        
        Args:
            shortage_qty: 缺料数量
            required_qty: 需求数量
            days_to_shortage: 距离需求日期天数
            is_critical_path: 是否关键路径
        
        Returns:
            预警级别
        """
        shortage_rate = float(shortage_qty / required_qty) if required_qty > 0 else 0
        
        # 已经延期或当天需要
        if days_to_shortage <= 0:
            return 'URGENT'
        
        # 关键路径物料
        if is_critical_path:
            if days_to_shortage <= 3 or shortage_rate > 0.5:
                return 'URGENT'
            elif days_to_shortage <= 7 or shortage_rate > 0.3:
                return 'CRITICAL'
            else:
                return 'WARNING'
        
        # 非关键路径
        if days_to_shortage <= 3 and shortage_rate > 0.7:
            return 'URGENT'
        elif days_to_shortage <= 7 and shortage_rate > 0.5:
            return 'CRITICAL'
        elif days_to_shortage <= 14 and shortage_rate > 0.3:
            return 'WARNING'
        elif shortage_rate > 0.5:
            return 'WARNING'
        else:
            return 'INFO'
    
    def predict_impact(
        self,
        material_id: int,
        shortage_qty: Decimal,
        required_date: date,
        project_id: Optional[int] = None
    ) -> Dict:
        """
        预测缺料影响
        
        Returns:
            {
                'estimated_delay_days': 延期天数,
                'estimated_cost_impact': 成本影响,
                'affected_projects': 受影响项目列表,
                'risk_score': 风险评分
            }
        """
        impact = {
            'estimated_delay_days': 0,
            'estimated_cost_impact': Decimal('0'),
            'affected_projects': [],
            'risk_score': 0
        }
        
        # 1. 查找使用该物料的所有项目
        affected_projects = self._find_affected_projects(material_id, project_id)
        impact['affected_projects'] = [
            {'id': p['id'], 'name': p['name'], 'required_qty': p['required_qty']}
            for p in affected_projects
        ]
        
        # 2. 预估延期天数（基于供应商平均交期）
        avg_lead_time = self._get_average_lead_time(material_id)
        impact['estimated_delay_days'] = max(
            0,
            avg_lead_time - (required_date - datetime.now().date()).days
        )
        
        # 3. 预估成本影响（停工损失 + 加急成本）
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if material:
            # 简化计算：缺料数量 * 单价 * 1.5（加急系数）
            unit_cost = material.standard_price or Decimal('0')
            impact['estimated_cost_impact'] = shortage_qty * unit_cost * Decimal('1.5')
        
        # 4. 计算风险评分
        impact['risk_score'] = self._calculate_risk_score(
            delay_days=impact['estimated_delay_days'],
            cost_impact=impact['estimated_cost_impact'],
            project_count=len(affected_projects),
            shortage_qty=shortage_qty
        )
        
        return impact
    
    def generate_solutions(self, alert: ShortageAlert) -> List[ShortageHandlingPlan]:
        """
        AI生成处理方案
        
        生成多个可选方案并进行评分排序
        
        Returns:
            处理方案列表（已排序）
        """
        solutions = []
        
        # 方案1: 紧急采购
        urgent_purchase = self._generate_urgent_purchase_plan(alert)
        if urgent_purchase:
            solutions.append(urgent_purchase)
        
        # 方案2: 替代料
        substitutes = self._generate_substitute_plans(alert)
        solutions.extend(substitutes)
        
        # 方案3: 项目间调拨
        transfers = self._generate_transfer_plans(alert)
        solutions.extend(transfers)
        
        # 方案4: 分批交付
        partial = self._generate_partial_delivery_plan(alert)
        if partial:
            solutions.append(partial)
        
        # 方案5: 重排期
        reschedule = self._generate_reschedule_plan(alert)
        if reschedule:
            solutions.append(reschedule)
        
        # 对方案进行评分和排序
        for solution in solutions:
            self._score_solution(solution, alert)
        
        solutions.sort(key=lambda x: x.ai_score, reverse=True)
        
        # 设置推荐标记
        if solutions:
            solutions[0].is_recommended = True
            for i, sol in enumerate(solutions):
                sol.recommendation_rank = i + 1
        
        # 保存到数据库
        for solution in solutions:
            self.db.add(solution)
        
        self.db.commit()
        
        return solutions
    
    # ========== 内部辅助方法 ==========
    
    def _collect_material_demands(
        self,
        project_id: Optional[int],
        material_id: Optional[int],
        days_ahead: int
    ) -> List[Dict]:
        """收集物料需求数据"""
        demands = []
        
        # 从工单中获取需求
        query = self.db.query(
            WorkOrder.id.label('work_order_id'),
            WorkOrder.project_id,
            WorkOrder.material_id,
            Material.material_code,
            Material.material_name,
            WorkOrder.planned_quantity.label('required_qty'),
            WorkOrder.planned_start_date.label('required_date'),
            WorkOrder.is_critical_path
        ).join(Material, Material.id == WorkOrder.material_id)
        
        # 过滤条件
        filters = [
            WorkOrder.status.in_(['PENDING', 'CONFIRMED', 'IN_PROGRESS']),
            WorkOrder.planned_start_date <= datetime.now().date() + timedelta(days=days_ahead)
        ]
        
        if project_id:
            filters.append(WorkOrder.project_id == project_id)
        if material_id:
            filters.append(WorkOrder.material_id == material_id)
        
        query = query.filter(and_(*filters))
        
        for row in query.all():
            days_to_required = (row.required_date - datetime.now().date()).days
            demands.append({
                'work_order_id': row.work_order_id,
                'project_id': row.project_id,
                'material_id': row.material_id,
                'material_code': row.material_code,
                'material_name': row.material_name,
                'required_qty': row.required_qty,
                'required_date': row.required_date,
                'days_to_required': days_to_required,
                'is_critical_path': row.is_critical_path or False
            })
        
        return demands
    
    def _get_available_qty(self, material_id: int) -> Decimal:
        """获取可用库存"""
        result = self.db.query(
            func.sum(Inventory.available_quantity)
        ).filter(
            Inventory.material_id == material_id
        ).scalar()
        
        return result or Decimal('0')
    
    def _get_in_transit_qty(self, material_id: int) -> Decimal:
        """获取在途数量"""
        result = self.db.query(
            func.sum(PurchaseOrderItem.quantity - PurchaseOrderItem.received_quantity)
        ).join(
            PurchaseOrder,
            PurchaseOrder.id == PurchaseOrderItem.purchase_order_id
        ).filter(
            and_(
                PurchaseOrderItem.material_id == material_id,
                PurchaseOrder.status.in_(['CONFIRMED', 'IN_TRANSIT']),
                PurchaseOrderItem.quantity > PurchaseOrderItem.received_quantity
            )
        ).scalar()
        
        return result or Decimal('0')
    
    def _create_alert(self, **kwargs) -> ShortageAlert:
        """创建预警记录"""
        alert_no = self._generate_alert_no()
        
        alert = ShortageAlert(
            alert_no=alert_no,
            project_id=kwargs['project_id'],
            material_id=kwargs['material_id'],
            material_code=kwargs['material_code'],
            material_name=kwargs['material_name'],
            required_qty=kwargs['required_qty'],
            available_qty=kwargs['available_qty'],
            shortage_qty=kwargs['shortage_qty'],
            in_transit_qty=kwargs['in_transit_qty'],
            required_date=kwargs['required_date'],
            alert_level=kwargs['alert_level'],
            alert_date=datetime.now().date(),
            days_to_shortage=(kwargs['required_date'] - datetime.now().date()).days,
            work_order_id=kwargs.get('work_order_id'),
            impact_projects=kwargs['impact']['affected_projects'],
            estimated_delay_days=kwargs['impact']['estimated_delay_days'],
            estimated_cost_impact=kwargs['impact']['estimated_cost_impact'],
            risk_score=kwargs['impact']['risk_score'],
            status='PENDING',
            detected_at=datetime.now(),
            alert_source='AUTO'
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def _find_affected_projects(self, material_id: int, project_id: Optional[int]) -> List[Dict]:
        """查找受影响的项目"""
        # 简化实现，实际应从BOM、工单等获取
        query = self.db.query(
            Project.id,
            Project.project_name.label('name'),
            func.sum(WorkOrder.planned_quantity).label('required_qty')
        ).join(
            WorkOrder,
            WorkOrder.project_id == Project.id
        ).filter(
            WorkOrder.material_id == material_id,
            WorkOrder.status.in_(['PENDING', 'CONFIRMED', 'IN_PROGRESS'])
        ).group_by(Project.id, Project.project_name)
        
        if project_id:
            query = query.filter(Project.id == project_id)
        
        return [
            {'id': row.id, 'name': row.name, 'required_qty': float(row.required_qty)}
            for row in query.all()
        ]
    
    def _get_average_lead_time(self, material_id: int) -> int:
        """获取物料平均交期"""
        # 从历史采购订单计算
        result = self.db.query(
            func.avg(
                func.julianday(PurchaseOrder.actual_delivery_date) -
                func.julianday(PurchaseOrder.order_date)
            )
        ).join(
            PurchaseOrderItem,
            PurchaseOrderItem.purchase_order_id == PurchaseOrder.id
        ).filter(
            and_(
                PurchaseOrderItem.material_id == material_id,
                PurchaseOrder.actual_delivery_date.isnot(None)
            )
        ).scalar()
        
        return int(result) if result else 15  # 默认15天
    
    def _calculate_risk_score(
        self,
        delay_days: int,
        cost_impact: Decimal,
        project_count: int,
        shortage_qty: Decimal
    ) -> Decimal:
        """计算风险评分 0-100"""
        score = 0
        
        # 延期天数权重 40%
        if delay_days > 30:
            score += 40
        elif delay_days > 15:
            score += 30
        elif delay_days > 7:
            score += 20
        elif delay_days > 0:
            score += 10
        
        # 成本影响权重 30%
        if cost_impact > 100000:
            score += 30
        elif cost_impact > 50000:
            score += 20
        elif cost_impact > 10000:
            score += 10
        
        # 受影响项目数权重 20%
        if project_count > 5:
            score += 20
        elif project_count > 3:
            score += 15
        elif project_count > 1:
            score += 10
        
        # 缺料数量权重 10%
        if shortage_qty > 1000:
            score += 10
        elif shortage_qty > 100:
            score += 7
        elif shortage_qty > 10:
            score += 5
        
        return Decimal(str(min(score, 100)))
    
    def _generate_alert_no(self) -> str:
        """生成预警单号"""
        today = datetime.now().strftime('%Y%m%d')
        count = self.db.query(func.count(ShortageAlert.id)).filter(
            ShortageAlert.alert_date == datetime.now().date()
        ).scalar() or 0
        return f"SA{today}{count + 1:04d}"
    
    # ========== 处理方案生成 ==========
    
    def _generate_urgent_purchase_plan(self, alert: ShortageAlert) -> Optional[ShortageHandlingPlan]:
        """生成紧急采购方案"""
        plan = ShortageHandlingPlan(
            plan_no=self._generate_plan_no(),
            alert_id=alert.id,
            solution_type='URGENT_PURCHASE',
            solution_name='紧急采购',
            solution_description='从供应商紧急采购所需物料',
            proposed_qty=alert.shortage_qty,
            proposed_date=datetime.now().date() + timedelta(days=7),
            estimated_lead_time=7,
            estimated_cost=alert.shortage_qty * Decimal('1.2'),  # 加急溢价20%
            advantages=['快速解决', '数量充足', '质量保证'],
            disadvantages=['成本较高', '需要审批'],
            risks=['供应商可能无货', '物流延误']
        )
        return plan
    
    def _generate_substitute_plans(self, alert: ShortageAlert) -> List[ShortageHandlingPlan]:
        """生成替代料方案（简化）"""
        # 实际应查询material_substitutes表
        return []
    
    def _generate_transfer_plans(self, alert: ShortageAlert) -> List[ShortageHandlingPlan]:
        """生成调拨方案（简化）"""
        # 实际应查询其他项目的库存
        return []
    
    def _generate_partial_delivery_plan(self, alert: ShortageAlert) -> Optional[ShortageHandlingPlan]:
        """生成分批交付方案"""
        if alert.available_qty > 0:
            plan = ShortageHandlingPlan(
                plan_no=self._generate_plan_no(),
                alert_id=alert.id,
                solution_type='PARTIAL_DELIVERY',
                solution_name='分批交付',
                solution_description=f'先使用现有库存 {alert.available_qty}，余量分批采购',
                proposed_qty=alert.available_qty,
                proposed_date=datetime.now().date(),
                estimated_lead_time=0,
                estimated_cost=Decimal('0'),
                advantages=['快速启动', '降低风险'],
                disadvantages=['需要分批管理', '可能影响后续'],
                risks=['后续批次延误']
            )
            return plan
        return None
    
    def _generate_reschedule_plan(self, alert: ShortageAlert) -> Optional[ShortageHandlingPlan]:
        """生成重排期方案"""
        plan = ShortageHandlingPlan(
            plan_no=self._generate_plan_no(),
            alert_id=alert.id,
            solution_type='RESCHEDULE',
            solution_name='生产重排期',
            solution_description='调整生产计划，等待物料到货后生产',
            proposed_date=alert.required_date + timedelta(days=alert.estimated_delay_days),
            estimated_lead_time=alert.estimated_delay_days,
            estimated_cost=Decimal('0'),
            advantages=['成本最低', '不需要额外资源'],
            disadvantages=['延期交付', '影响客户满意度'],
            risks=['客户投诉', '合同违约']
        )
        return plan
    
    def _score_solution(self, solution: ShortageHandlingPlan, alert: ShortageAlert):
        """对方案进行评分"""
        # 可行性评分 (0-100)
        solution.feasibility_score = self._score_feasibility(solution)
        
        # 成本评分 (0-100，成本越低分越高)
        solution.cost_score = self._score_cost(solution, alert)
        
        # 时间评分 (0-100，时间越短分越高)
        solution.time_score = self._score_time(solution, alert)
        
        # 风险评分 (0-100，风险越低分越高)
        solution.risk_score = self._score_risk(solution)
        
        # 综合评分
        weights = {'feasibility': 0.3, 'cost': 0.3, 'time': 0.3, 'risk': 0.1}
        solution.score_weights = weights
        
        solution.ai_score = (
            solution.feasibility_score * Decimal(str(weights['feasibility'])) +
            solution.cost_score * Decimal(str(weights['cost'])) +
            solution.time_score * Decimal(str(weights['time'])) +
            solution.risk_score * Decimal(str(weights['risk']))
        )
        
        solution.score_explanation = (
            f"可行性: {solution.feasibility_score}分, "
            f"成本: {solution.cost_score}分, "
            f"时间: {solution.time_score}分, "
            f"风险: {solution.risk_score}分"
        )
    
    def _score_feasibility(self, solution: ShortageHandlingPlan) -> Decimal:
        """可行性评分"""
        scores = {
            'URGENT_PURCHASE': 80,
            'SUBSTITUTE': 60,
            'TRANSFER': 70,
            'PARTIAL_DELIVERY': 85,
            'RESCHEDULE': 90
        }
        return Decimal(str(scores.get(solution.solution_type, 50)))
    
    def _score_cost(self, solution: ShortageHandlingPlan, alert: ShortageAlert) -> Decimal:
        """成本评分"""
        if not solution.estimated_cost:
            return Decimal('100')
        
        cost_ratio = float(solution.estimated_cost / alert.estimated_cost_impact) if alert.estimated_cost_impact > 0 else 1
        if cost_ratio < 0.5:
            return Decimal('100')
        elif cost_ratio < 1.0:
            return Decimal('80')
        elif cost_ratio < 1.5:
            return Decimal('60')
        else:
            return Decimal('40')
    
    def _score_time(self, solution: ShortageHandlingPlan, alert: ShortageAlert) -> Decimal:
        """时间评分"""
        lead_time = solution.estimated_lead_time or 0
        if lead_time == 0:
            return Decimal('100')
        elif lead_time <= 3:
            return Decimal('90')
        elif lead_time <= 7:
            return Decimal('70')
        elif lead_time <= 14:
            return Decimal('50')
        else:
            return Decimal('30')
    
    def _score_risk(self, solution: ShortageHandlingPlan) -> Decimal:
        """风险评分"""
        risk_count = len(solution.risks) if solution.risks else 0
        if risk_count == 0:
            return Decimal('100')
        elif risk_count <= 2:
            return Decimal('80')
        elif risk_count <= 4:
            return Decimal('60')
        else:
            return Decimal('40')
    
    def _generate_plan_no(self) -> str:
        """生成方案编号"""
        today = datetime.now().strftime('%Y%m%d')
        count = self.db.query(func.count(ShortageHandlingPlan.id)).filter(
            func.date(ShortageHandlingPlan.created_at) == datetime.now().date()
        ).scalar() or 0
        return f"SP{today}{count + 1:04d}"
