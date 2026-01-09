# -*- coding: utf-8 -*-
"""
排产建议服务
实现优先级评分模型和排产建议生成算法
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models import (
    Project, Machine, MaterialReadiness, SchedulingSuggestion,
    BomHeader, Customer
)
from app.services.resource_allocation_service import ResourceAllocationService


class SchedulingSuggestionService:
    """排产建议服务"""
    
    # 项目优先级分数映射
    PRIORITY_SCORES = {
        'P1': 30,  # 最高优先级
        'P2': 24,
        'P3': 18,
        'P4': 12,
        'P5': 6    # 最低优先级
    }
    
    # 交期压力分数映射
    DEADLINE_PRESSURE_SCORES = {
        (0, 7): 25,      # 距交期 ≤ 7天 = 25分
        (8, 14): 20,     # 距交期 ≤ 14天 = 20分
        (15, 30): 15,    # 距交期 ≤ 30天 = 15分
        (31, 60): 10,    # 距交期 ≤ 60天 = 10分
        (61, None): 5   # 距交期 > 60天 = 5分
    }
    
    # 客户重要度分数映射
    CUSTOMER_IMPORTANCE_SCORES = {
        'A': 15,  # A级客户
        'B': 12,  # B级客户
        'C': 9,   # C级客户
        'D': 6    # D级客户
    }
    
    # 合同金额分数映射
    CONTRACT_AMOUNT_SCORES = [
        (500000, 10),   # ≥ 50万 = 10分
        (200000, 7),    # ≥ 20万 = 7分
        (100000, 5),    # ≥ 10万 = 5分
        (0, 3)          # < 10万 = 3分
    ]
    
    @classmethod
    def calculate_priority_score(
        cls,
        db: Session,
        project: Project,
        readiness: Optional[MaterialReadiness] = None
    ) -> Dict:
        """
        计算项目优先级评分
        
        优先级评分 = 
        项目优先级分（30分）
        + 交期压力分（25分）
        + 齐套程度分（20分）
        + 客户重要度分（15分）
        + 合同金额分（10分）
        """
        score = 0.0
        factors = {}
        
        # 1. 项目优先级分（30分）
        # 处理不同的优先级格式：P1/P2/P3 或 HIGH/MEDIUM/LOW 或 NORMAL
        priority_value = project.priority or 'P3'
        # 如果优先级不是P1-P5格式，尝试转换
        if priority_value not in cls.PRIORITY_SCORES:
            priority_map = {
                'HIGH': 'P1',
                'MEDIUM': 'P3',
                'LOW': 'P5',
                'NORMAL': 'P3',
                'URGENT': 'P1',
                'CRITICAL': 'P1'
            }
            priority_value = priority_map.get(priority_value.upper(), 'P3')
        
        priority_score = cls.PRIORITY_SCORES.get(priority_value, 18)
        score += priority_score
        factors['priority'] = {
            'score': priority_score,
            'max': 30,
            'value': priority_value,
            'description': f'项目优先级：{priority_value}'
        }
        
        # 2. 交期压力分（25分）
        deadline_score = cls._calculate_deadline_pressure(project)
        score += deadline_score
        factors['deadline'] = {
            'score': deadline_score,
            'max': 25,
            'value': project.planned_end_date.isoformat() if project.planned_end_date else None,
            'description': cls._get_deadline_description(project)
        }
        
        # 3. 齐套程度分（20分）
        if readiness:
            kit_rate_score = float(readiness.blocking_kit_rate or 0) * 0.2
            score += kit_rate_score
            factors['kit_rate'] = {
                'score': round(kit_rate_score, 2),
                'max': 20,
                'value': float(readiness.blocking_kit_rate or 0),
                'description': f'阻塞齐套率：{readiness.blocking_kit_rate}%'
            }
        else:
            factors['kit_rate'] = {
                'score': 0,
                'max': 20,
                'value': None,
                'description': '未进行齐套分析'
            }
        
        # 4. 客户重要度分（15分）
        customer_score = cls._calculate_customer_importance(db, project)
        score += customer_score
        factors['customer'] = {
            'score': customer_score,
            'max': 15,
            'value': project.customer_id,
            'description': cls._get_customer_description(db, project)
        }
        
        # 5. 合同金额分（10分）
        contract_score = cls._calculate_contract_amount_score(project)
        score += contract_score
        factors['contract'] = {
            'score': contract_score,
            'max': 10,
            'value': float(project.contract_amount or 0),
            'description': f'合同金额：{project.contract_amount or 0}元'
        }
        
        return {
            'total_score': round(score, 2),
            'factors': factors,
            'max_score': 100
        }
    
    @classmethod
    def _calculate_deadline_pressure(cls, project: Project) -> float:
        """计算交期压力分"""
        if not project.planned_end_date:
            return 5.0  # 无交期，给最低分
        
        today = date.today()
        days_until_deadline = (project.planned_end_date - today).days
        
        for (min_days, max_days), score in cls.DEADLINE_PRESSURE_SCORES.items():
            if max_days is None:
                if days_until_deadline >= min_days:
                    return float(score)
            else:
                if min_days <= days_until_deadline <= max_days:
                    return float(score)
        
        return 5.0
    
    @classmethod
    def _get_deadline_description(cls, project: Project) -> str:
        """获取交期描述"""
        if not project.planned_end_date:
            return '无交期'
        
        today = date.today()
        days = (project.planned_end_date - today).days
        
        if days < 0:
            return f'已逾期 {abs(days)} 天'
        elif days <= 7:
            return f'距交期 {days} 天（紧急）'
        elif days <= 14:
            return f'距交期 {days} 天（紧张）'
        elif days <= 30:
            return f'距交期 {days} 天（正常）'
        else:
            return f'距交期 {days} 天（宽松）'
    
    @classmethod
    def _calculate_customer_importance(cls, db: Session, project: Project) -> float:
        """计算客户重要度分"""
        if not project.customer_id:
            return 6.0  # 默认C级
        
        customer = db.query(Customer).filter(Customer.id == project.customer_id).first()
        if not customer:
            return 6.0
        
        # 从客户信用等级获取重要度（credit_level: A/B/C/D）
        # 如果没有credit_level，根据合同金额推断
        credit_level = getattr(customer, 'credit_level', None) or 'C'
        
        # 如果信用等级为A，提升为A级客户
        if credit_level.upper() == 'A':
            return float(cls.CUSTOMER_IMPORTANCE_SCORES.get('A', 15))
        
        # 根据合同金额推断客户重要度
        contract_amount = float(project.contract_amount or 0)
        if contract_amount >= 1000000:  # 100万以上
            return float(cls.CUSTOMER_IMPORTANCE_SCORES.get('A', 15))
        elif contract_amount >= 500000:  # 50万以上
            return float(cls.CUSTOMER_IMPORTANCE_SCORES.get('B', 12))
        elif contract_amount >= 200000:  # 20万以上
            return float(cls.CUSTOMER_IMPORTANCE_SCORES.get('C', 9))
        else:
            return float(cls.CUSTOMER_IMPORTANCE_SCORES.get('D', 6))
    
    @classmethod
    def _get_customer_description(cls, db: Session, project: Project) -> str:
        """获取客户描述"""
        if not project.customer_id:
            return '无客户信息'
        
        customer = db.query(Customer).filter(Customer.id == project.customer_id).first()
        if not customer:
            return '客户不存在'
        
        credit_level = getattr(customer, 'credit_level', None) or 'C'
        return f'客户：{customer.customer_name}（信用等级：{credit_level}）'
    
    @classmethod
    def _calculate_contract_amount_score(cls, project: Project) -> float:
        """计算合同金额分"""
        amount = float(project.contract_amount or 0)
        
        for threshold, score in cls.CONTRACT_AMOUNT_SCORES:
            if amount >= threshold:
                return float(score)
        
        return 3.0
    
    @classmethod
    def generate_scheduling_suggestions(
        cls,
        db: Session,
        scope: str = 'WEEKLY',
        project_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        生成智能排产建议
        
        Args:
            scope: 排产范围 ('WEEKLY', 'MONTHLY')
            project_ids: 指定项目ID列表，None表示所有待排产项目
        """
        # 1. 获取所有待排产项目
        query = db.query(Project).filter(
            Project.status.in_(['S4', 'S5'])  # 加工制造、装配调试阶段
        )
        
        if project_ids:
            query = query.filter(Project.id.in_(project_ids))
        
        projects = query.all()
        
        if not projects:
            return []
        
        # 2. 获取最新齐套分析结果
        suggestions = []
        for project in projects:
            # 获取最新齐套分析
            readiness = db.query(MaterialReadiness).filter(
                MaterialReadiness.project_id == project.id
            ).order_by(MaterialReadiness.analysis_time.desc()).first()
            
            if not readiness:
                # 没有齐套分析，标记为需要分析
                suggestions.append({
                    'project_id': project.id,
                    'status': 'NEED_ANALYSIS',
                    'message': '需要先进行齐套分析'
                })
                continue
            
            # 3. 计算优先级评分
            score_result = cls.calculate_priority_score(db, project, readiness)
            
            # 4. 判断是否可以排产
            if readiness.can_start:
                # 可以开工
                workable_stage = readiness.current_workable_stage or 'FRAME'
                next_stage = cls._get_next_stage(workable_stage)
                
                # 计算建议开始和结束日期
                suggested_start_date = project.planned_start_date or date.today()
                # 估算工期（根据阶段，简化处理）
                stage_durations = {
                    'FRAME': 7,
                    'MECH': 14,
                    'ELECTRIC': 10,
                    'WIRING': 5,
                    'DEBUG': 7,
                    'COSMETIC': 3
                }
                duration_days = stage_durations.get(workable_stage, 7)
                suggested_end_date = suggested_start_date + timedelta(days=duration_days)
                
                # 检查资源可用性
                machine = None
                if readiness.machine_id:
                    machine = db.query(Machine).filter(Machine.id == readiness.machine_id).first()
                
                resource_allocation = ResourceAllocationService.allocate_resources(
                    db,
                    project.id,
                    readiness.machine_id,
                    suggested_start_date,
                    suggested_end_date
                )
                
                if next_stage:
                    # 检查下一阶段是否可以开始
                    stage_rates = readiness.stage_kit_rates or {}
                    next_stage_info = stage_rates.get(next_stage, {})
                    
                    if next_stage_info.get('can_start', False):
                        suggested_stage = next_stage
                        status = 'READY'
                        blocking_items = []
                    else:
                        suggested_stage = workable_stage
                        status = 'WAITING'
                        # 获取下一阶段的阻塞物料
                        blocking_items = cls._get_blocking_items(db, readiness, next_stage)
                else:
                    suggested_stage = workable_stage
                    status = 'READY'
                    blocking_items = []
                
                # 如果资源不可用，调整状态
                if not resource_allocation['can_allocate']:
                    if status == 'READY':
                        status = 'WAIT_RESOURCE'
                
                suggestion = {
                    'project_id': project.id,
                    'project_no': project.project_code or project.project_name,
                    'project_name': project.project_name,
                    'status': status,
                    'suggested_stage': suggested_stage,
                    'suggested_start_date': suggested_start_date.isoformat(),
                    'suggested_end_date': suggested_end_date.isoformat(),
                    'priority_score': score_result['total_score'],
                    'score_factors': score_result['factors'],
                    'current_kit_rate': float(readiness.blocking_kit_rate or 0),
                    'blocking_items': blocking_items,
                    'resource_allocation': {
                        'can_allocate': resource_allocation['can_allocate'],
                        'available_workstations': len(resource_allocation['workstations']),
                        'available_workers': len(resource_allocation['workers']),
                        'conflicts': resource_allocation.get('conflicts', []),
                        'reason': resource_allocation.get('reason')
                    },
                    'suggestion_type': 'CAN_START' if status == 'READY' else ('WAIT_RESOURCE' if status == 'WAIT_RESOURCE' else 'WAIT_MATERIAL')
                }
            else:
                # 不能排产
                blocking_stage = readiness.first_blocked_stage or 'FRAME'
                blocking_items = cls._get_blocking_items(db, readiness, blocking_stage)
                
                suggestion = {
                    'project_id': project.id,
                    'project_no': project.project_code or project.project_name,
                    'project_name': project.project_name,
                    'status': 'BLOCKED',
                    'blocking_stage': blocking_stage,
                    'priority_score': score_result['total_score'],
                    'score_factors': score_result['factors'],
                    'current_kit_rate': float(readiness.blocking_kit_rate or 0),
                    'blocking_items': blocking_items,
                    'estimated_ready_date': readiness.estimated_ready_date.isoformat() if readiness.estimated_ready_date else None,
                    'suggestion_type': 'BLOCKED'
                }
            
            suggestions.append(suggestion)
        
        # 5. 按优先级排序
        suggestions.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return suggestions
    
    @classmethod
    def _get_next_stage(cls, current_stage: str) -> Optional[str]:
        """获取下一阶段"""
        stage_order = {
            'FRAME': 1,
            'MECH': 2,
            'ELECTRIC': 3,
            'WIRING': 4,
            'DEBUG': 5,
            'COSMETIC': 6
        }
        
        current_order = stage_order.get(current_stage, 0)
        if current_order >= 6:
            return None
        
        for stage, order in stage_order.items():
            if order == current_order + 1:
                return stage
        
        return None
    
    @classmethod
    def _get_blocking_items(
        cls,
        db: Session,
        readiness: MaterialReadiness,
        stage_code: str
    ) -> List[Dict]:
        """获取阻塞物料列表"""
        from app.models import ShortageDetail
        
        shortages = db.query(ShortageDetail).filter(
            ShortageDetail.readiness_id == readiness.id,
            ShortageDetail.assembly_stage == stage_code,
            ShortageDetail.is_blocking == True,
            ShortageDetail.shortage_qty > 0
        ).all()
        
        return [
            {
                'material_code': s.material_code,
                'material_name': s.material_name,
                'shortage_qty': float(s.shortage_qty),
                'expected_arrival': s.expected_arrival.isoformat() if s.expected_arrival else None
            }
            for s in shortages
        ]
